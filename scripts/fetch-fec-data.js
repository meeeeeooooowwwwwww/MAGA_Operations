// FEC API Data Acquisition Script
// Data source: https://www.fec.gov/data/
// API Docs: https://api.open.fec.gov/developers/

const fetch = require('node-fetch');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const fs = require('fs');

// Try to load environment variables from a .env file
try {
    require('dotenv').config();
} catch (e) {
    console.log('dotenv not found, using process.env or defaults');
}

// Configuration
const dbPath = path.resolve(__dirname, '../data/politicians.db');
let db;

// API key from environment or use the provided key
const FEC_API_KEY = process.env.FEC_API_KEY || 'HdDVejhIz7UdnfCnGfasrfGija6y1QTxCos6NmkT';
const FEC_API_BASE = 'https://api.open.fec.gov/v1';
const DEBUG_LEVEL = parseInt(process.env.DEBUG_LEVEL || '1', 10);
const MAX_POLITICIANS = parseInt(process.env.MAX_POLITICIANS || '0', 10); // 0 means no limit
const API_CALLS_PER_HOUR = parseInt(process.env.API_CALLS_PER_HOUR || '900', 10); // Stay under 1000/hour limit
const BATCH_SIZE = parseInt(process.env.BATCH_SIZE || '5', 10);

// Cache directory for FEC API responses
const CACHE_DIR = path.resolve(__dirname, '../cache/fec');
if (!fs.existsSync(CACHE_DIR)) {
    fs.mkdirSync(CACHE_DIR, { recursive: true });
}

// Progress tracking file
const PROGRESS_FILE = path.resolve(CACHE_DIR, 'progress.json');

// Logger function with debug levels
function log(message, level = 1) {
    if (level <= DEBUG_LEVEL) {
        console.log(`[${new Date().toISOString()}] ${message}`);
    }
}

// Initialize the database connection
function initDb() {
    return new Promise((resolve, reject) => {
        db = new sqlite3.Database(dbPath, sqlite3.OPEN_READWRITE, (err) => {
            if (err) {
                reject(new Error(`Error opening database: ${err.message}`));
                return;
            }
            log('Connected to the SQLite database.');
            resolve(db);
        });
    });
}

// Close the database connection
function closeDb() {
    return new Promise((resolve, reject) => {
        if (!db) {
            resolve();
            return;
        }
        
        // Check if database is already closed
        try {
            // Simple query to check if db is open
            db.get("SELECT 1", [], function(err) {
                if (err && err.message.includes('SQLITE_MISUSE')) {
                    // Database is already closed
                    log('Database was already closed.', 1);
                    resolve();
                    return;
                }
                
                // If we get here, the database is still open, so close it
                db.close((err) => {
                    if (err) {
                        log(`Warning: Error closing database: ${err.message}`, 0);
                        // Don't reject here, just log and continue
                        resolve();
                        return;
                    }
                    log('Database connection closed.', 2);
                    resolve();
                });
            });
        } catch (e) {
            // If any other error occurs, log and continue
            log(`Warning: Error checking database state: ${e.message}`, 0);
            resolve();
        }
    });
}

// Helper function to wait for a specified time to avoid rate limits
async function sleep(ms = 1000) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Load progress from file
function loadProgress() {
    if (fs.existsSync(PROGRESS_FILE)) {
        try {
            return JSON.parse(fs.readFileSync(PROGRESS_FILE, 'utf8'));
        } catch (e) {
            log(`Error reading progress file: ${e.message}`, 0);
            return { 
                lastProcessedIndex: 0, 
                processedPoliticians: {}, // Changed from array to object with metadata
                lastRunTimestamp: null,
                apiCallsInLastHour: 0,
                completedCount: 0,
                runs: [] // Track each run
            };
        }
    }
    return { 
        lastProcessedIndex: 0, 
        processedPoliticians: {}, // Changed from array to object with metadata
        lastRunTimestamp: null,
        apiCallsInLastHour: 0,
        completedCount: 0,
        runs: []
    };
}

// Save progress to file
function saveProgress(progress) {
    try {
        fs.writeFileSync(PROGRESS_FILE, JSON.stringify(progress, null, 2));
    } catch (e) {
        log(`Error saving progress file: ${e.message}`, 0);
    }
}

// Get all politicians from our database
async function getAllPoliticians() {
    return new Promise((resolve, reject) => {
        const query = `
            SELECT 
                id,
                bioguide_id, 
                name,
                state, 
                district,
                party,
                chamber
            FROM 
                politicians 
            WHERE 
                bioguide_id IS NOT NULL 
            ORDER BY 
                name
            ${MAX_POLITICIANS > 0 ? `LIMIT ${MAX_POLITICIANS}` : ''}
        `;
        
        db.all(query, [], (err, rows) => {
            if (err) {
                reject(new Error(`Error fetching politicians: ${err.message}`));
                return;
            }
            log(`Retrieved ${rows.length} politicians from database`);
            resolve(rows);
        });
    });
}

// Check if a politician already has financial data in the database
async function hasFinancialDataInDb(bioguideId) {
    return new Promise((resolve, reject) => {
        const query = `
            SELECT COUNT(*) as count 
            FROM assets 
            WHERE politician_bioguide_id = ?
        `;
        
        db.get(query, [bioguideId], (err, row) => {
            if (err) {
                reject(new Error(`Error checking assets: ${err.message}`));
                return;
            }
            resolve(row.count > 0);
        });
    });
}

// Fetch candidate data from FEC API by name
async function fetchCandidateByName(firstName, lastName, state = null) {
    // Construct filename for cache
    const cacheKey = `candidate_${lastName}_${firstName}${state ? `_${state}` : ''}`;
    const cacheFile = path.join(CACHE_DIR, `${cacheKey}.json`);
    
    // Check cache first
    if (fs.existsSync(cacheFile)) {
        try {
            const cachedData = JSON.parse(fs.readFileSync(cacheFile, 'utf8'));
            log(`Using cached candidate data for ${firstName} ${lastName}`, 2);
            return { data: cachedData, fromCache: true };
        } catch (e) {
            log(`Error reading cache: ${e.message}`, 0);
        }
    }
    
    // Construct URL for API request
    let url = `${FEC_API_BASE}/candidates/search/?api_key=${FEC_API_KEY}&name=${lastName}`;
    if (state) {
        url += `&state=${state}`;
    }
    
    try {
        log(`Fetching candidate data for ${firstName} ${lastName}`, 2);
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`FEC API Error (${response.status}): ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // Filter results to match first name (API only searches by last name)
        const filteredResults = data.results.filter(candidate => 
            candidate.name.toLowerCase().includes(firstName.toLowerCase())
        );
        
        // Create a filtered response object
        const filteredData = {
            ...data,
            results: filteredResults
        };
        
        // Cache the response
        fs.writeFileSync(cacheFile, JSON.stringify(filteredData, null, 2));
        
        // Add delay to respect rate limits
        await sleep(1200); // About 50 requests per minute to stay well below limit
        
        return { data: filteredData, fromCache: false };
    } catch (error) {
        log(`Error fetching candidate data: ${error.message}`, 0);
        return { data: { results: [] }, fromCache: false };
    }
}

// Fetch financial data for a candidate by FEC ID
async function fetchCandidateFinancialData(fecId, electionYear = '2024') {
    // Construct filename for cache
    const cacheFile = path.join(CACHE_DIR, `financial_${fecId}_${electionYear}.json`);
    
    // Check cache first
    if (fs.existsSync(cacheFile)) {
        try {
            const cachedData = JSON.parse(fs.readFileSync(cacheFile, 'utf8'));
            log(`Using cached financial data for candidate ID ${fecId} (${electionYear})`, 2);
            return { data: cachedData, fromCache: true };
        } catch (e) {
            log(`Error reading cache: ${e.message}`, 0);
        }
    }
    
    try {
        log(`Fetching financial data for candidate ID ${fecId} (${electionYear})`, 2);
        const response = await fetch(
            `${FEC_API_BASE}/candidate/${fecId}/totals/?api_key=${FEC_API_KEY}&election_year=${electionYear}`
        );
        
        if (!response.ok) {
            throw new Error(`FEC API Error (${response.status}): ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // Cache the response
        fs.writeFileSync(cacheFile, JSON.stringify(data, null, 2));
        
        // Add delay to respect rate limits
        await sleep(1200); // About 50 requests per minute to stay well below limit
        
        return { data, fromCache: false };
    } catch (error) {
        log(`Error fetching financial data: ${error.message}`, 0);
        return { data: { results: [] }, fromCache: false };
    }
}

// Fetch top donors for a candidate's committees
async function fetchCommitteeDonors(committeeId, twoYearPeriod = '2024') {
    // Construct filename for cache
    const cacheFile = path.join(CACHE_DIR, `donors_${committeeId}_${twoYearPeriod}.json`);
    
    // Check cache first
    if (fs.existsSync(cacheFile)) {
        try {
            const cachedData = JSON.parse(fs.readFileSync(cacheFile, 'utf8'));
            log(`Using cached donor data for committee ID ${committeeId} (${twoYearPeriod})`, 2);
            return { data: cachedData, fromCache: true };
        } catch (e) {
            log(`Error reading cache: ${e.message}`, 0);
        }
    }
    
    try {
        log(`Fetching donor data for committee ID ${committeeId} (${twoYearPeriod})`, 2);
        const response = await fetch(
            `${FEC_API_BASE}/schedules/schedule_a/?api_key=${FEC_API_KEY}&committee_id=${committeeId}&two_year_transaction_period=${twoYearPeriod}&sort=-contribution_receipt_amount&per_page=100`
        );
        
        if (!response.ok) {
            throw new Error(`FEC API Error (${response.status}): ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // Cache the response
        fs.writeFileSync(cacheFile, JSON.stringify(data, null, 2));
        
        // Add delay to respect rate limits
        await sleep(1200); // About 50 requests per minute to stay well below limit
        
        return { data, fromCache: false };
    } catch (error) {
        log(`Error fetching donor data: ${error.message}`, 0);
        return { data: { results: [] }, fromCache: false };
    }
}

// Insert financial data into database
async function insertFinancialData(data, bioguideId) {
    if (!data || !data.results || data.results.length === 0) {
        return 0;
    }
    
    const insertSql = `
        INSERT OR IGNORE INTO assets (
            politician_bioguide_id, asset_name, asset_type, 
            value_range_min, value_range_max, 
            income_range_min, income_range_max, 
            report_year, source_document
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    `;

    return new Promise((resolve, reject) => {
        db.serialize(() => {
            db.run('BEGIN TRANSACTION;');
            const stmt = db.prepare(insertSql);
            let insertedCount = 0;
            
            // Add a summary asset record from the FEC data
            for (const result of data.results) {
                stmt.run([
                    bioguideId,
                    'Campaign Finances - Total Receipts',
                    'Campaign',
                    result.receipts || 0,
                    result.receipts || 0,
                    null,
                    null,
                    result.cycle || new Date().getFullYear(),
                    'FEC Campaign Finance Data'
                ], function(err) {
                    if (err) {
                        log(`Error inserting asset: ${err.message}`, 0);
                    } else if (this.changes > 0) {
                        insertedCount++;
                    }
                });
                
                // Add a second record for disbursements (spending)
                stmt.run([
                    bioguideId,
                    'Campaign Finances - Total Disbursements',
                    'Campaign',
                    result.disbursements || 0,
                    result.disbursements || 0,
                    null,
                    null,
                    result.cycle || new Date().getFullYear(),
                    'FEC Campaign Finance Data'
                ], function(err) {
                    if (err) {
                        log(`Error inserting asset: ${err.message}`, 0);
                    } else if (this.changes > 0) {
                        insertedCount++;
                    }
                });
                
                // Add a third record for cash on hand
                stmt.run([
                    bioguideId,
                    'Campaign Finances - Cash on Hand',
                    'Campaign',
                    result.cash_on_hand_end_period || 0,
                    result.cash_on_hand_end_period || 0,
                    null,
                    null,
                    result.cycle || new Date().getFullYear(),
                    'FEC Campaign Finance Data'
                ], function(err) {
                    if (err) {
                        log(`Error inserting asset: ${err.message}`, 0);
                    } else if (this.changes > 0) {
                        insertedCount++;
                    }
                });
            }
            
            stmt.finalize((err) => {
                if (err) {
                    log(`Error finalizing statement: ${err.message}`, 0);
                    db.run('ROLLBACK;');
                    reject(err);
                } else {
                    db.run('COMMIT;', (commitErr) => {
                        if (commitErr) {
                            log(`Error committing transaction: ${commitErr.message}`, 0);
                            reject(commitErr);
                        } else {
                            resolve(insertedCount);
                        }
                    });
                }
            });
        });
    });
}

// Insert donation data into database
async function insertDonationData(data, bioguideId) {
    if (!data || !data.results || data.results.length === 0) {
        return 0;
    }
    
    const insertSql = `
        INSERT OR IGNORE INTO donations (
            politician_bioguide_id, donor_name, donor_type, donor_employer, donor_occupation,
            donor_address, amount, election_cycle, source_url
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    `;

    return new Promise((resolve, reject) => {
        db.serialize(() => {
            db.run('BEGIN TRANSACTION;');
            const stmt = db.prepare(insertSql);
            let insertedCount = 0;
            
            data.results.forEach(donation => {
                const donorType = donation.contributor_type || (
                    donation.committee_id ? 'Committee' : 
                    donation.entity_type === 'organization' ? 'Organization' : 'Individual'
                );
                
                stmt.run([
                    bioguideId,
                    donation.contributor_name || 'Unknown',
                    donorType,
                    donation.contributor_employer || '',
                    donation.contributor_occupation || '',
                    `${donation.contributor_city || ''}, ${donation.contributor_state || ''}`,
                    donation.contribution_receipt_amount || 0,
                    donation.two_year_transaction_period || new Date().getFullYear(),
                    `https://www.fec.gov/data/receipts/?committee_id=${donation.committee_id}`
                ], function(err) {
                    if (err) {
                        log(`Error inserting donation: ${err.message}`, 0);
                    } else if (this.changes > 0) {
                        insertedCount++;
                    }
                });
            });
            
            stmt.finalize((err) => {
                if (err) {
                    log(`Error finalizing donation statement: ${err.message}`, 0);
                    db.run('ROLLBACK;');
                    reject(err);
                } else {
                    db.run('COMMIT;', (commitErr) => {
                        if (commitErr) {
                            log(`Error committing donation transaction: ${commitErr.message}`, 0);
                            reject(commitErr);
                        } else {
                            resolve(insertedCount);
                        }
                    });
                }
            });
        });
    });
}

// Identify politicians with missing or incomplete data from previous runs
async function identifyPoliticiansWithMissingData() {
    // Load progress
    const progress = loadProgress();
    if (!progress.processedPoliticians) {
        return [];
    }
    
    const incomplete = [];
    
    // Loop through all processed politicians
    for (const [bioguideId, politician] of Object.entries(progress.processedPoliticians)) {
        // Look for politicians with specific issues
        if (politician.status === 'processed') {
            // Check if we have any election years that were not processed
            // or if we have fewer than expected financial records
            const hasAllYears = politician.allElectionYears.every(year => 
                politician.processedElectionYears.includes(year));
                
            if (!hasAllYears || politician.committeesProcessed.length === 0) {
                incomplete.push({
                    bioguideId,
                    name: politician.name,
                    state: politician.state,
                    district: politician.district,
                    chamber: politician.chamber,
                    priority: 1, // Higher priority
                    reason: !hasAllYears ? 'missing_election_years' : 'missing_committees'
                });
            }
        }
        // Look for politicians with no data
        else if (['no_candidate_data', 'no_recent_candidacy'].includes(politician.status)) {
            incomplete.push({
                bioguideId,
                name: politician.name,
                state: politician.state,
                district: politician.district,
                chamber: politician.chamber,
                priority: 2, // Medium priority
                reason: politician.status
            });
        }
    }
    
    // Sort by priority
    incomplete.sort((a, b) => a.priority - b.priority);
    
    return incomplete;
}

// Main execution function that supports hourly runs
async function fetchAndStoreFecData(recoverMode = false) {
    let dbInitialized = false;
    
    try {
        // Load progress from previous runs
        const progress = loadProgress();
        
        // Initialize or ensure processedPoliticians is an object
        if (!progress.processedPoliticians) {
            progress.processedPoliticians = {};
        }
        
        // Track this run
        const runId = Date.now().toString();
        const runInfo = {
            id: runId,
            startTime: new Date().toISOString(),
            apiCalls: 0,
            politiciansProcessed: 0,
            recoveryMode: recoverMode,
            endTime: null
        };
        
        if (!progress.runs) progress.runs = [];
        progress.runs.push(runInfo);
        
        // Check if it's been less than an hour since the last run
        const now = new Date();
        const lastRunTime = progress.lastRunTimestamp ? new Date(progress.lastRunTimestamp) : null;
        let apiCallsRemaining = API_CALLS_PER_HOUR;
        
        if (lastRunTime && (now - lastRunTime) < 3600000) { // 3600000 ms = 1 hour
            // Calculate time passed since last run in minutes
            const minutesPassed = Math.floor((now - lastRunTime) / 60000);
            log(`Last run was ${minutesPassed} minutes ago`, 1);
            
            // If it's been less than an hour, reduce available API calls
            if (progress.apiCallsInLastHour > 0) {
                // Estimate how many calls we can make based on time passed
                const estimatedRegeneratedCalls = Math.floor((minutesPassed / 60) * API_CALLS_PER_HOUR);
                apiCallsRemaining = Math.min(API_CALLS_PER_HOUR, 
                    estimatedRegeneratedCalls + (API_CALLS_PER_HOUR - progress.apiCallsInLastHour));
                
                log(`API calls available for this run: ${apiCallsRemaining}`, 1);
                
                // If very few calls are available, wait until more time passes
                if (apiCallsRemaining < 10) {
                    const waitMinutes = Math.ceil(60 - minutesPassed);
                    log(`Too few API calls available (${apiCallsRemaining}). Consider waiting ${waitMinutes} more minutes.`, 0);
                }
            }
        } else {
            // Reset call count if it's been more than an hour
            log(`It's been more than an hour since the last run or this is the first run`, 1);
        }
        
        log(`Starting FEC data acquisition process${recoverMode ? ' in RECOVERY mode' : ''}`);
        log(`Previous run processed ${progress.completedCount || 0} politicians`);
        
        // Initialize database
        await initDb();
        dbInitialized = true;
        
        // Retrieve politicians from our DB
        const allPoliticians = await getAllPoliticians();
        log(`Retrieved ${allPoliticians.length} politicians from database`);
        
        let pendingPoliticians = [];
        
        // In recovery mode, prioritize politicians with missing data
        if (recoverMode) {
            log('Recovery mode active: Identifying politicians with missing data');
            const incompleteData = await identifyPoliticiansWithMissingData();
            
            if (incompleteData.length > 0) {
                log(`Found ${incompleteData.length} politicians with incomplete data`);
                
                // Map incomplete data back to full politician records
                pendingPoliticians = incompleteData.map(incomplete => {
                    const politician = allPoliticians.find(p => p.bioguide_id === incomplete.bioguideId);
                    if (politician) {
                        // Add recovery info to help with processing
                        politician.recoveryReason = incomplete.reason;
                        politician.recoveryPriority = incomplete.priority;
                        return politician;
                    }
                    return null;
                }).filter(Boolean);
                
                log(`Will attempt to recover data for ${pendingPoliticians.length} politicians`);
                
                // Remove these politicians from progress tracking so we can reprocess
                pendingPoliticians.forEach(politician => {
                    delete progress.processedPoliticians[politician.bioguide_id];
                });
                
                saveProgress(progress);
            } else {
                log('No politicians with incomplete data found, proceeding with normal processing');
                // Fall back to normal processing if no recovery needed
                pendingPoliticians = allPoliticians.filter(
                    p => !progress.processedPoliticians[p.bioguide_id]
                );
            }
        } else {
            // Normal mode - filter out already processed politicians
            pendingPoliticians = allPoliticians.filter(
                p => !progress.processedPoliticians[p.bioguide_id]
            );
        }
        
        log(`${pendingPoliticians.length} politicians remain to be processed`);
        
        if (pendingPoliticians.length === 0) {
            log('All politicians have been processed! Nothing to do.');
            return;
        }
        
        // Track API calls for this run
        let apiCallsCount = 0;
        
        // Process in batches to manage memory usage
        const startIndex = recoverMode ? 0 : (progress.lastProcessedIndex || 0);
        const endIndex = Math.min(startIndex + apiCallsRemaining / 3, pendingPoliticians.length);
        
        log(`Processing politicians from index ${startIndex} to ${endIndex - 1}`);
        
        for (let i = startIndex; i < endIndex && apiCallsCount < apiCallsRemaining; i++) {
            const politician = pendingPoliticians[i];
            
            // Add recovery info to log if in recovery mode
            if (recoverMode && politician.recoveryReason) {
                log(`Processing ${politician.name} (${politician.state}${politician.chamber === 'house' ? `-${politician.district}` : ''}) [${i + 1}/${pendingPoliticians.length}] - Recovery reason: ${politician.recoveryReason}`);
            } else {
                log(`Processing ${politician.name} (${politician.state}${politician.chamber === 'house' ? `-${politician.district}` : ''}) [${i + 1}/${pendingPoliticians.length}]`);
            }
            
            // Check if already has financial data
            const hasData = await hasFinancialDataInDb(politician.bioguide_id);
            if (hasData) {
                log(`Skipping ${politician.name}: Already has financial data in database`);
                // Mark as processed with metadata
                progress.processedPoliticians[politician.bioguide_id] = {
                    name: politician.name,
                    state: politician.state,
                    district: politician.district,
                    chamber: politician.chamber,
                    party: politician.party,
                    processedAt: new Date().toISOString(),
                    dataInDb: true,
                    runId: runId,
                    electionYears: [],
                    status: 'skipped_has_data'
                };
                progress.completedCount = (progress.completedCount || 0) + 1;
                continue;
            }
            
            // Break up name into components
            const nameParts = politician.name.split(' ');
            const firstName = nameParts[0];
            const lastName = nameParts[nameParts.length - 1];
            
            // Search for candidate in FEC data
            const candidateResponse = await fetchCandidateByName(firstName, lastName, politician.state);
            if (!candidateResponse.fromCache) apiCallsCount++;
            const candidateData = candidateResponse.data;
            
            if (!candidateData.results || candidateData.results.length === 0) {
                log(`No FEC candidate data found for ${politician.name}`);
                // Mark as processed with metadata
                progress.processedPoliticians[politician.bioguide_id] = {
                    name: politician.name,
                    state: politician.state,
                    district: politician.district,
                    chamber: politician.chamber,
                    party: politician.party,
                    processedAt: new Date().toISOString(),
                    dataInDb: false,
                    runId: runId,
                    electionYears: [],
                    status: 'no_candidate_data'
                };
                progress.completedCount = (progress.completedCount || 0) + 1;
                continue;
            }
            
            // Track all available election years for this candidate
            const allElectionYears = [];
            candidateData.results.forEach(candidate => {
                if (candidate.election_years && Array.isArray(candidate.election_years)) {
                    candidate.election_years.forEach(year => {
                        if (!allElectionYears.includes(parseInt(year, 10))) {
                            allElectionYears.push(parseInt(year, 10));
                        }
                    });
                }
            });
            
            // Find the most recent candidate record
            let recentCandidate = null;
            let mostRecentElection = 0;
            
            for (const candidate of candidateData.results) {
                const electionYears = candidate.election_years || [];
                const mostRecent = Math.max(...electionYears.map(y => parseInt(y, 10)), 0);
                
                if (mostRecent > mostRecentElection) {
                    mostRecentElection = mostRecent;
                    recentCandidate = candidate;
                }
            }
            
            if (!recentCandidate) {
                log(`Couldn't determine most recent candidacy for ${politician.name}`);
                // Mark as processed with metadata
                progress.processedPoliticians[politician.bioguide_id] = {
                    name: politician.name,
                    state: politician.state,
                    district: politician.district,
                    chamber: politician.chamber,
                    party: politician.party,
                    processedAt: new Date().toISOString(),
                    dataInDb: false,
                    runId: runId,
                    electionYears: allElectionYears,
                    status: 'no_recent_candidacy'
                };
                progress.completedCount = (progress.completedCount || 0) + 1;
                continue;
            }
            
            log(`Found FEC candidate ID ${recentCandidate.candidate_id} for ${politician.name}`);
            
            // Fetch financial data for the candidate
            const financialResponse = await fetchCandidateFinancialData(recentCandidate.candidate_id, mostRecentElection.toString());
            if (!financialResponse.fromCache) apiCallsCount++;
            const financialData = financialResponse.data;
            
            let processedElectionYears = [];
            if (financialData.results && financialData.results.length > 0) {
                // Track processed election years
                financialData.results.forEach(result => {
                    if (result.cycle) {
                        processedElectionYears.push(parseInt(result.cycle, 10));
                    }
                });
                
                // Insert the financial data
                const insertedCount = await insertFinancialData(financialData, politician.bioguide_id);
                log(`Inserted ${insertedCount} financial records for ${politician.name}`);
                
                // If candidate has committees, fetch top donors for the principal committee
                if (financialData.results[0].committee_id) {
                    const committeeId = financialData.results[0].committee_id;
                    log(`Fetching donor data for committee ${committeeId}`);
                    
                    const donorResponse = await fetchCommitteeDonors(committeeId, mostRecentElection.toString());
                    if (!donorResponse.fromCache) apiCallsCount++;
                    const donorData = donorResponse.data;
                    
                    if (donorData.results && donorData.results.length > 0) {
                        const insertedDonations = await insertDonationData(donorData, politician.bioguide_id);
                        log(`Inserted ${insertedDonations} donation records for ${politician.name}`);
                    } else {
                        log(`No donor data found for ${politician.name}`);
                    }
                }
            } else {
                log(`No financial data found for ${politician.name}`);
            }
            
            // Mark as processed with comprehensive metadata
            progress.processedPoliticians[politician.bioguide_id] = {
                name: politician.name,
                state: politician.state,
                district: politician.district,
                chamber: politician.chamber,
                party: politician.party,
                processedAt: new Date().toISOString(),
                dataInDb: true,
                runId: runId,
                candidateId: recentCandidate.candidate_id,
                allElectionYears: allElectionYears,
                processedElectionYears: processedElectionYears,
                mostRecentElection: mostRecentElection,
                committeesProcessed: financialData.results && financialData.results.length > 0 
                    ? financialData.results.map(r => r.committee_id).filter(Boolean) 
                    : [],
                status: 'processed'
            };
            
            progress.completedCount = (progress.completedCount || 0) + 1;
            runInfo.politiciansProcessed++;
            
            // Update progress after each politician
            progress.lastProcessedIndex = i;
            progress.apiCallsInLastHour = apiCallsCount;
            progress.lastRunTimestamp = now.toISOString();
            saveProgress(progress);
            
            // Add a delay between politicians to respect rate limits
            await sleep(3000);
            
            // Check if we're approaching API call limit
            if (apiCallsCount >= apiCallsRemaining - 3) {
                log(`Approaching API call limit (${apiCallsCount}/${apiCallsRemaining}). Stopping to be safe.`, 0);
                break;
            }
        }
        
        // Update run information
        runInfo.apiCalls = apiCallsCount;
        runInfo.endTime = new Date().toISOString();
        
        // Calculate progress statistics
        const processedCount = Object.keys(progress.processedPoliticians).length;
        const withDataCount = Object.values(progress.processedPoliticians)
            .filter(p => p.dataInDb).length;
        const withoutDataCount = processedCount - withDataCount;
        const pendingCount = allPoliticians.length - processedCount;
        
        // Final progress update
        progress.apiCallsInLastHour = apiCallsCount;
        progress.lastRunTimestamp = now.toISOString();
        saveProgress(progress);
        
        log(`=== FEC Data Acquisition Run Complete ===`);
        log(`API calls made: ${apiCallsCount}`);
        log(`Run duration: ${Math.round((new Date() - new Date(runInfo.startTime)) / 1000 / 60)} minutes`);
        log(`Politicians processed in this run: ${runInfo.politiciansProcessed}`);
        log(`Total politicians processed: ${processedCount}/${allPoliticians.length} (${Math.round(processedCount / allPoliticians.length * 100)}%)`);
        log(`Politicians with data: ${withDataCount}`);
        log(`Politicians without data: ${withoutDataCount}`);
        log(`Politicians remaining: ${pendingCount}`);
        
        if (pendingCount === 0) {
            log(`All politicians have been processed! Data acquisition complete.`);
        } else {
            log(`Run the script again to process more politicians.`);
        }
        
    } catch (error) {
        log(`Fatal error: ${error.message}`, 0);
        if (error.stack) {
            log(error.stack, 0);
        }
    } finally {
        await closeDb();
    }
}

// Execute with proper error handling
fetchAndStoreFecData().catch(err => {
    log(`Unhandled error: ${err.message}`, 0);
    if (err.stack) {
        log(err.stack, 0);
    }
    closeDb().catch(() => {});
});

module.exports = {
    fetchAndStoreFecData
}; 