// OpenSecrets API Data Acquisition Script
// Data source: https://www.opensecrets.org/
// API Docs: https://www.opensecrets.org/api/
// Note: OpenSecrets API requires a key: https://www.opensecrets.org/api/admin/index.php?function=signup

const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const fetch = require('node-fetch');
const fs = require('fs');
const parse = require('csv-parse/sync').parse;

// Load environment variables (OPENSECRETS_API_KEY)
try {
    require('dotenv').config();
} catch (e) {
    console.log('dotenv not found, using process.env or defaults');
}

// Configuration
const dbPath = path.resolve(__dirname, '../data/politicians.db');
let db;

// API key from env or default (get your key at https://www.opensecrets.org/api/admin/index.php?function=signup)
const OPENSECRETS_API_KEY = process.env.OPENSECRETS_API_KEY || 'YOUR_API_KEY_HERE';
const OPENSECRETS_API_BASE = 'https://www.opensecrets.org/api';
const DEBUG_LEVEL = parseInt(process.env.DEBUG_LEVEL || '1', 10);

// Cache directory for mapping files and API responses
const CACHE_DIR = path.resolve(__dirname, '../cache/opensecrets');
if (!fs.existsSync(CACHE_DIR)) {
    fs.mkdirSync(CACHE_DIR, { recursive: true });
}

// Mapping file for bioguide to OpenSecrets CID
const MAPPING_FILE = path.join(CACHE_DIR, 'bioguide-to-opensecrets-map.json');

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
        db.close((err) => {
            if (err) {
                reject(new Error(`Error closing database: ${err.message}`));
                return;
            }
            log('Database connection closed.');
            resolve();
        });
    });
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
                party
            FROM 
                politicians 
            WHERE 
                bioguide_id IS NOT NULL 
            ORDER BY 
                name
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

// Check if a politician already has donations in the database
async function hasDonationsInDb(bioguidId) {
    return new Promise((resolve, reject) => {
        const query = `
            SELECT COUNT(*) as count 
            FROM donations 
            WHERE politician_bioguide_id = ?
        `;
        
        db.get(query, [bioguidId], (err, row) => {
            if (err) {
                reject(new Error(`Error checking donations: ${err.message}`));
                return;
            }
            resolve(row.count > 0);
        });
    });
}

// Check if a politician already has assets in the database
async function hasAssetsInDb(bioguidId) {
    return new Promise((resolve, reject) => {
        const query = `
            SELECT COUNT(*) as count 
            FROM assets 
            WHERE politician_bioguide_id = ?
        `;
        
        db.get(query, [bioguidId], (err, row) => {
            if (err) {
                reject(new Error(`Error checking assets: ${err.message}`));
                return;
            }
            resolve(row.count > 0);
        });
    });
}

// Load or create bioguide_id to OpenSecrets CID mapping
async function loadOrCreateMapping(politicians) {
    let mapping = {};
    
    // Try to load from file first
    if (fs.existsSync(MAPPING_FILE)) {
        try {
            mapping = JSON.parse(fs.readFileSync(MAPPING_FILE, 'utf8'));
            log(`Loaded ${Object.keys(mapping).length} bioguide->CID mappings from cache`);
        } catch (e) {
            log(`Error loading mapping file: ${e.message}`, 0);
        }
    }
    
    // Find politicians without mapping and try to identify their CID
    // Note: OpenSecrets doesn't have a direct API to look up CIDs by name
    // We'll need to use a predefined list, or manual lookups
    
    // For this template, we're using a simplified approach with a known CID list
    // In a real implementation, you might manually build this mapping or use web scraping
    const unmappedPoliticians = politicians.filter(p => !mapping[p.bioguide_id]);
    if (unmappedPoliticians.length > 0) {
        log(`Need to map ${unmappedPoliticians.length} politicians to OpenSecrets CIDs`);
        log(`This typically requires manual mapping or additional data sources`);
        
        // Example manual mapping for a few known politicians:
        const knownCidMap = {
            // Using a small sample of known mappings
            'P000197': 'N00007360', // Nancy Pelosi
            'S000148': 'N00001093', // Chuck Schumer
            'M000355': 'N00035368', // Kevin McCarthy
            'M001196': 'N00044521', // Mitch McConnell
            'O000172': 'N00001372', // Alexandria Ocasio-Cortez
            'C001084': 'N00041303', // Ted Cruz
            'S001197': 'N00043412', // Bernie Sanders
            'W000187': 'N00026686', // Elizabeth Warren
        };
        
        // Apply any known mappings from our sample list
        unmappedPoliticians.forEach(politician => {
            if (knownCidMap[politician.bioguide_id]) {
                mapping[politician.bioguide_id] = knownCidMap[politician.bioguide_id];
                log(`Mapped ${politician.name} (${politician.bioguide_id}) to CID: ${knownCidMap[politician.bioguide_id]}`, 2);
            }
        });
        
        // Save the updated mapping
        fs.writeFileSync(MAPPING_FILE, JSON.stringify(mapping, null, 2));
        log(`Saved mapping file with ${Object.keys(mapping).length} entries`);
    }
    
    return mapping;
}

// Fetch candidates personal finances (assets)
async function fetchCandidateFinances(cid, year = '2022') {
    const apiUrl = `${OPENSECRETS_API_BASE}?method=memPFDprofile&year=${year}&cid=${cid}&apikey=${OPENSECRETS_API_KEY}&output=json`;
    const cacheFile = path.join(CACHE_DIR, `finances_${cid}_${year}.json`);
    
    // Check cache first
    if (fs.existsSync(cacheFile)) {
        try {
            const cachedData = JSON.parse(fs.readFileSync(cacheFile, 'utf8'));
            log(`Using cached finance data for CID ${cid} (${year})`, 2);
            return cachedData;
        } catch (e) {
            log(`Error reading cache: ${e.message}`, 0);
        }
    }
    
    try {
        log(`Fetching finance data for CID ${cid} (${year})...`, 2);
        const response = await fetch(apiUrl);
        if (!response.ok) {
            throw new Error(`OpenSecrets API Error (${response.status}): ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // Cache the response
        fs.writeFileSync(cacheFile, JSON.stringify(data, null, 2));
        
        return data;
    } catch (error) {
        log(`Error fetching finance data: ${error.message}`, 0);
        return null;
    }
}

// Fetch top donors
async function fetchTopDonors(cid, cycle = '2022') {
    const apiUrl = `${OPENSECRETS_API_BASE}?method=candContrib&cid=${cid}&cycle=${cycle}&apikey=${OPENSECRETS_API_KEY}&output=json`;
    const cacheFile = path.join(CACHE_DIR, `donors_${cid}_${cycle}.json`);
    
    // Check cache first
    if (fs.existsSync(cacheFile)) {
        try {
            const cachedData = JSON.parse(fs.readFileSync(cacheFile, 'utf8'));
            log(`Using cached donor data for CID ${cid} (${cycle})`, 2);
            return cachedData;
        } catch (e) {
            log(`Error reading cache: ${e.message}`, 0);
        }
    }
    
    try {
        log(`Fetching top donors for CID ${cid} (${cycle})...`, 2);
        const response = await fetch(apiUrl);
        if (!response.ok) {
            throw new Error(`OpenSecrets API Error (${response.status}): ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // Cache the response
        fs.writeFileSync(cacheFile, JSON.stringify(data, null, 2));
        
        return data;
    } catch (error) {
        log(`Error fetching donor data: ${error.message}`, 0);
        return null;
    }
}

// Insert assets into database
async function insertAssets(assets, bioguidId) {
    if (!assets || assets.length === 0) {
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
            
            assets.forEach(asset => {
                stmt.run([
                    bioguidId,
                    asset.asset_name,
                    asset.asset_type,
                    asset.value_range_min,
                    asset.value_range_max,
                    asset.income_range_min || null,
                    asset.income_range_max || null,
                    asset.report_year,
                    asset.source_document
                ], function(err) {
                    if (err) {
                        log(`Error inserting asset: ${err.message}`, 0);
                    } else if (this.changes > 0) {
                        insertedCount++;
                    }
                });
            });
            
            stmt.finalize((err) => {
                if (err) {
                    log(`Error finalizing asset statement: ${err.message}`, 0);
                    db.run('ROLLBACK;');
                    reject(err);
                } else {
                    db.run('COMMIT;', (commitErr) => {
                        if (commitErr) {
                            log(`Error committing asset transaction: ${commitErr.message}`, 0);
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

// Insert donations into database
async function insertDonations(donations, bioguidId) {
    if (!donations || donations.length === 0) {
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
            
            donations.forEach(donation => {
                stmt.run([
                    bioguidId,
                    donation.donor_name,
                    donation.donor_type,
                    donation.donor_employer,
                    donation.donor_occupation,
                    donation.donor_address || '',
                    donation.amount,
                    donation.election_cycle,
                    donation.source_url
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

// Process OpenSecrets API donor response
function processTopDonors(donorData, bioguidId, cycle) {
    if (!donorData || !donorData.response || !donorData.response.contributors || !donorData.response.contributors.contributor) {
        return [];
    }
    
    const contributors = Array.isArray(donorData.response.contributors.contributor) 
        ? donorData.response.contributors.contributor 
        : [donorData.response.contributors.contributor];
    
    return contributors.map(contributor => ({
        politician_bioguide_id: bioguidId,
        donor_name: contributor['@attributes'].org_name,
        donor_type: 'Organization',
        donor_employer: contributor['@attributes'].org_name,
        donor_occupation: null,
        amount: parseFloat(contributor['@attributes'].total) || 0,
        election_cycle: cycle,
        source_url: `https://www.opensecrets.org/members-of-congress/summary?cid=${donorData.response.contributors['@attributes'].cid}`
    }));
}

// Process personal financial data
function processFinancialData(financeData, bioguidId, year) {
    if (!financeData || !financeData.response || !financeData.response.member_profile) {
        return [];
    }
    
    const profile = financeData.response.member_profile['@attributes'] || {};
    
    // Parse ranges like "$1,001 to $15,000" to min/max values
    function parseValueRange(rangeStr) {
        if (!rangeStr || typeof rangeStr !== 'string') return { min: null, max: null };
        
        // Handle special case "Over $50,000,000"
        if (rangeStr.toLowerCase().includes('over')) {
            const match = rangeStr.match(/\$([0-9,]+)/);
            return match ? { min: parseFloat(match[1].replace(/,/g, '')), max: null } : { min: null, max: null };
        }
        
        const parts = rangeStr.split('to').map(p => p.trim());
        const min = parts[0] ? parseFloat(parts[0].replace(/[^0-9.]/g, '')) : null;
        const max = parts.length > 1 ? parseFloat(parts[1].replace(/[^0-9.]/g, '')) : null;
        
        return { min, max };
    }
    
    // Build simplified assets list from available data
    const assets = [];
    
    // Net worth estimate
    if (profile.net_low && profile.net_high) {
        const netWorthMin = parseFloat(profile.net_low.replace(/[^0-9.]/g, ''));
        const netWorthMax = parseFloat(profile.net_high.replace(/[^0-9.]/g, ''));
        
        assets.push({
            asset_name: 'Net Worth Estimate',
            asset_type: 'Aggregate',
            value_range_min: netWorthMin,
            value_range_max: netWorthMax,
            income_range_min: null,
            income_range_max: null,
            report_year: parseInt(year, 10),
            source_document: `OpenSecrets Financial Disclosure ${year}`
        });
    }
    
    // Top assets (if available)
    if (profile.assets_low && profile.assets_high) {
        const assetsMin = parseFloat(profile.assets_low.replace(/[^0-9.]/g, ''));
        const assetsMax = parseFloat(profile.assets_high.replace(/[^0-9.]/g, ''));
        
        assets.push({
            asset_name: 'Total Reported Assets',
            asset_type: 'Aggregate',
            value_range_min: assetsMin,
            value_range_max: assetsMax,
            income_range_min: null,
            income_range_max: null,
            report_year: parseInt(year, 10),
            source_document: `OpenSecrets Financial Disclosure ${year}`
        });
    }
    
    return assets;
}

// Main execution function
async function fetchAndStoreOpenSecretsData() {
    try {
        log('Starting OpenSecrets data acquisition process');
        
        // 1. Initialize database
        await initDb();
        
        // 2. Retrieve politicians from our DB
        const politicians = await getAllPoliticians();
        log(`Retrieved ${politicians.length} politicians to process`);
        
        // 3. Load/create bioguide to OpenSecrets CID mapping
        const bioguideToOsCidMap = await loadOrCreateMapping(politicians);
        
        // 4. Process each politician
        let totalPoliticiansProcessed = 0;
        let totalDonations = 0;
        let totalAssets = 0;
        
        // Track API calls to avoid hitting rate limits
        let apiCallsCount = 0;
        const MAX_API_CALLS = 200; // Adjust based on your API key limits
        
        // Process in batches to manage memory usage
        const batchSize = 5;
        for (let i = 0; i < politicians.length && apiCallsCount < MAX_API_CALLS; i += batchSize) {
            const batch = politicians.slice(i, i + batchSize);
            
            for (const politician of batch) {
                const cid = bioguideToOsCidMap[politician.bioguide_id];
                if (!cid) {
                    log(`Skipping ${politician.name}: No OpenSecrets CID mapping found`);
                    continue;
                }
                
                log(`Processing ${politician.name} with OpenSecrets CID: ${cid}`);
                
                // Process donations
                const hasDonations = await hasDonationsInDb(politician.bioguide_id);
                if (!hasDonations) {
                    const cycles = ['2022', '2020', '2018']; // Election cycles to check
                    let donationsAdded = 0;
                    
                    for (const cycle of cycles) {
                        if (apiCallsCount >= MAX_API_CALLS) break;
                        
                        const donorData = await fetchTopDonors(cid, cycle);
                        apiCallsCount++;
                        
                        if (donorData) {
                            const donations = processTopDonors(donorData, politician.bioguide_id, cycle);
                            if (donations.length > 0) {
                                const insertedCount = await insertDonations(donations, politician.bioguide_id);
                                log(`Inserted ${insertedCount} donation records for ${politician.name} (cycle ${cycle})`);
                                donationsAdded += insertedCount;
                                totalDonations += insertedCount;
                            }
                        }
                        
                        // Brief pause between API calls
                        await new Promise(resolve => setTimeout(resolve, 500));
                    }
                    
                    if (donationsAdded > 0) {
                        log(`Added ${donationsAdded} total donations for ${politician.name}`);
                    } else {
                        log(`No donation data found for ${politician.name}`);
                    }
                } else {
                    log(`Skipping donations for ${politician.name}: Already has records in DB`);
                }
                
                // Process assets/personal finances
                const hasAssets = await hasAssetsInDb(politician.bioguide_id);
                if (!hasAssets) {
                    const years = ['2022', '2020', '2018']; // Years to check
                    let assetsAdded = 0;
                    
                    for (const year of years) {
                        if (apiCallsCount >= MAX_API_CALLS) break;
                        
                        const financeData = await fetchCandidateFinances(cid, year);
                        apiCallsCount++;
                        
                        if (financeData) {
                            const assets = processFinancialData(financeData, politician.bioguide_id, year);
                            if (assets.length > 0) {
                                const insertedCount = await insertAssets(assets, politician.bioguide_id);
                                log(`Inserted ${insertedCount} asset records for ${politician.name} (year ${year})`);
                                assetsAdded += insertedCount;
                                totalAssets += insertedCount;
                            }
                        }
                        
                        // Brief pause between API calls
                        await new Promise(resolve => setTimeout(resolve, 500));
                    }
                    
                    if (assetsAdded > 0) {
                        log(`Added ${assetsAdded} total assets for ${politician.name}`);
                    } else {
                        log(`No asset data found for ${politician.name}`);
                    }
                } else {
                    log(`Skipping assets for ${politician.name}: Already has records in DB`);
                }
                
                if (apiCallsCount >= MAX_API_CALLS) {
                    log(`Reached API call limit (${MAX_API_CALLS}). Stopping to avoid rate limits.`, 0);
                    break;
                }
                
                totalPoliticiansProcessed++;
                
                // Small pause between politicians
                await new Promise(resolve => setTimeout(resolve, 1000));
            }
            
            log(`Progress: ${Math.min(i + batchSize, politicians.length)} / ${politicians.length} politicians processed`);
            
            // Longer pause between batches
            if (i + batchSize < politicians.length && apiCallsCount < MAX_API_CALLS) {
                log('Pausing between batches...');
                await new Promise(resolve => setTimeout(resolve, 3000));
            }
        }
        
        log(`=== OpenSecrets Data Acquisition Complete ===`);
        log(`API calls made: ${apiCallsCount}`);
        log(`Politicians processed: ${totalPoliticiansProcessed}`);
        log(`Total donations inserted: ${totalDonations}`);
        log(`Total assets inserted: ${totalAssets}`);
        
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
fetchAndStoreOpenSecretsData().catch(err => {
    log(`Unhandled error: ${err.message}`, 0);
    if (err.stack) {
        log(err.stack, 0);
    }
    closeDb().catch(() => {});
}); 