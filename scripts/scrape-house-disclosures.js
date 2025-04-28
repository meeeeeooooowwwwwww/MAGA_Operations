// House Financial Disclosures Scraper using Playwright
// Target: https://disclosures-clerk.house.gov/FinancialDisclosure

const { chromium } = require('playwright');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const fs = require('fs');

// Configuration
const dbPath = path.resolve(__dirname, '../data/politicians.db'); 
let db;

// Cache directory for downloaded PDFs
const CACHE_DIR = path.resolve(__dirname, '../cache/house_disclosures');
if (!fs.existsSync(CACHE_DIR)) {
    fs.mkdirSync(CACHE_DIR, { recursive: true });
}

// Settings
const MAX_POLITICIANS = parseInt(process.env.MAX_POLITICIANS || '5', 10); // Limit number of politicians for testing
const DEBUG_LEVEL = parseInt(process.env.DEBUG_LEVEL || '1', 10);
const SEARCH_YEARS = ['2023', '2022', '2021', '2020']; // Years to search for
const DOWNLOAD_REPORTS = true; // Whether to download report PDFs

// Logger function
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

// Helper function to wait for a specified time (randomized to appear more human-like)
async function sleep(minMs = 1000, maxMs = 3000) {
    const sleepTime = Math.floor(Math.random() * (maxMs - minMs + 1)) + minMs;
    log(`Waiting for ${sleepTime}ms...`, 2);
    return new Promise(resolve => setTimeout(resolve, sleepTime));
}

// Get all politicians from House database
async function getHouseRepresentatives() {
    return new Promise((resolve, reject) => {
        const query = `
            SELECT 
                id,
                bioguide_id, 
                name,
                state,
                district,
                chamber
            FROM 
                politicians 
            WHERE 
                bioguide_id IS NOT NULL 
                AND chamber = 'house'
            ORDER BY 
                name
            LIMIT ?
        `;
        
        db.all(query, [MAX_POLITICIANS === 0 ? -1 : MAX_POLITICIANS], (err, rows) => {
            if (err) {
                reject(new Error(`Error fetching politicians: ${err.message}`));
                return;
            }
            log(`Retrieved ${rows.length} House representatives from database`);
            resolve(rows);
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

// Add a document record to the database
async function addDocumentRecord(bioguideId, docType, year, fileUrl, localPath) {
    return new Promise((resolve, reject) => {
        const query = `
            INSERT OR IGNORE INTO company_associations (
                politician_bioguide_id, 
                company_name, 
                role,
                source, 
                source_url
            ) VALUES (?, ?, ?, ?, ?);
        `;
        
        db.run(query, [
            bioguideId,
            `${docType} - ${year}`, // Using this field to store document type
            'Disclosure Document',  // Using role field to indicate document type
            `House Financial Disclosure ${year}`,
            fileUrl
        ], function(err) {
            if (err) {
                reject(new Error(`Error adding document record: ${err.message}`));
                return;
            }
            resolve(this.changes > 0);
        });
    });
}

// Parse financial data from search results and insert into database
async function parseAndStoreFinancialData(politician, documentInfo) {
    // For now, we're just storing document references since parsing PDFs would require additional tools
    let docsAdded = 0;
    
    for (const doc of documentInfo) {
        const added = await addDocumentRecord(
            politician.bioguide_id,
            doc.type,
            doc.year,
            doc.url,
            doc.localPath
        );
        
        if (added) {
            docsAdded++;
        }
    }
    
    return docsAdded;
}

// Scrape House Financial Disclosures website
async function scrapeHouseDisclosures() {
    log('Launching browser...');
    
    const browser = await chromium.launch({
        headless: true,
        slowMo: 50 // Slow down operations by 50ms
    });
    
    try {
        const context = await browser.newContext({
            userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            viewport: { width: 1280, height: 720 }
        });
        
        // Add a realistic delay after each navigation
        context.on('page', page => {
            page.on('response', async response => {
                if (response.status() === 200 && response.url().includes('disclosures-clerk.house.gov')) {
                    await sleep(500, 1500); // Random delay after successful navigation
                }
            });
        });
        
        const page = await context.newPage();
        log('Navigating to House Financial Disclosures website...');
        
        // Navigate to the financial disclosures site
        await page.goto('https://disclosures-clerk.house.gov/FinancialDisclosure', {
            waitUntil: 'networkidle'
        });
        
        // Initialize database
        await initDb();
        
        // Retrieve politicians
        const representatives = await getHouseRepresentatives();
        
        let processedCount = 0;
        let successCount = 0;
        let documentsFound = 0;
        
        // Process each representative
        for (const rep of representatives) {
            log(`Processing ${rep.name} (${rep.state}${rep.district ? '-' + rep.district : ''})...`);
            
            // Check if already has assets
            const hasAssets = await hasAssetsInDb(rep.bioguide_id);
            if (hasAssets) {
                log(`Skipping ${rep.name}: Already has assets in database`);
                processedCount++;
                continue;
            }
            
            // Store document information found for this politician
            const documentInfo = [];
            
            // Search for each year
            for (const year of SEARCH_YEARS) {
                log(`Searching for ${rep.name} financial disclosures in ${year}...`);
                
                try {
                    // Navigate to search form
                    await page.goto('https://disclosures-clerk.house.gov/FinancialDisclosure/ViewMemberSearchResult', {
                        waitUntil: 'networkidle'
                    });
                    
                    // Fill out the search form
                    // Last name
                    const lastName = rep.name.split(' ').pop();
                    await page.locator('#LastName').fill(lastName);
                    
                    // First name (try to extract)
                    const firstName = rep.name.split(' ')[0];
                    await page.locator('#FirstName').fill(firstName);
                    
                    // Select state
                    await page.locator('#FilingYear').selectOption(year);
                    await page.locator('#State').selectOption(rep.state);
                    
                    // Click the search button
                    await Promise.all([
                        page.waitForNavigation({ waitUntil: 'networkidle' }),
                        page.click('input[type="submit"][value="Search"]')
                    ]);
                    
                    // Check for results
                    const noResults = await page.locator('div.results:has-text("No Results")').count();
                    
                    if (noResults > 0) {
                        log(`No results found for ${rep.name} in ${year}`);
                        continue;
                    }
                    
                    // Wait for results to load
                    await page.waitForSelector('table.filedReports');
                    
                    // Extract document information from results
                    const tableRows = await page.locator('table.filedReports tbody tr').count();
                    log(`Found ${tableRows} disclosure documents for ${rep.name} in ${year}`);
                    
                    for (let i = 0; i < tableRows; i++) {
                        const rowSelector = `table.filedReports tbody tr:nth-child(${i + 1})`;
                        
                        // Get document type
                        const docType = await page.locator(`${rowSelector} td:nth-child(2)`).textContent();
                        
                        // Get filing date
                        const filingDate = await page.locator(`${rowSelector} td:nth-child(3)`).textContent();
                        
                        // Get link to PDF
                        const pdfLink = await page.locator(`${rowSelector} td:nth-child(4) a`).getAttribute('href');
                        const pdfUrl = pdfLink ? new URL(pdfLink, page.url()).toString() : null;
                        
                        if (pdfUrl) {
                            // Generate a local path for the PDF
                            const pdfFilename = `${rep.bioguide_id}_${year}_${docType.trim().replace(/\s+/g, '_')}.pdf`;
                            const localPath = path.join(CACHE_DIR, pdfFilename);
                            
                            documentInfo.push({
                                politician: rep.name,
                                bioguideId: rep.bioguide_id,
                                type: docType.trim(),
                                year: year,
                                filingDate: filingDate ? filingDate.trim() : null,
                                url: pdfUrl,
                                localPath: localPath
                            });
                            
                            // Download the PDF if needed
                            if (DOWNLOAD_REPORTS && !fs.existsSync(localPath)) {
                                try {
                                    log(`Downloading PDF: ${pdfUrl}`, 2);
                                    
                                    // Navigate to the PDF in a new page
                                    const pdfPage = await context.newPage();
                                    const downloadPromise = pdfPage.waitForEvent('download');
                                    await pdfPage.goto(pdfUrl, { waitUntil: 'domcontentloaded' });
                                    const download = await downloadPromise;
                                    
                                    // Save the file
                                    await download.saveAs(localPath);
                                    log(`PDF downloaded to ${localPath}`, 2);
                                    
                                    // Close the PDF page
                                    await pdfPage.close();
                                    
                                    // Add a delay to avoid overwhelming the server
                                    await sleep(2000, 4000);
                                } catch (downloadErr) {
                                    log(`Error downloading PDF: ${downloadErr.message}`, 0);
                                }
                            }
                        }
                    }
                    
                    // Wait before proceeding to the next year
                    await sleep(1500, 3000);
                    
                } catch (searchError) {
                    log(`Error searching for ${rep.name} in ${year}: ${searchError.message}`, 0);
                    // Continue to next year despite error
                    continue;
                }
            }
            
            // Store document references in the database
            if (documentInfo.length > 0) {
                const addedCount = await parseAndStoreFinancialData(rep, documentInfo);
                log(`Added ${addedCount} document references for ${rep.name}`);
                documentsFound += addedCount;
                successCount++;
            } else {
                log(`No documents found for ${rep.name}`);
            }
            
            processedCount++;
            
            // Add a longer delay between politicians
            await sleep(3000, 5000);
        }
        
        log(`\n=== House Financial Disclosures Scraping Complete ===`);
        log(`Politicians processed: ${processedCount}/${representatives.length}`);
        log(`Politicians with documents found: ${successCount}`);
        log(`Total documents found: ${documentsFound}`);
        
    } catch (error) {
        log(`Fatal error: ${error.message}`, 0);
        if (error.stack) {
            log(error.stack, 0);
        }
    } finally {
        await closeDb();
        await browser.close();
    }
}

// Main execution
(async () => {
    try {
        await scrapeHouseDisclosures();
    } catch (err) {
        log(`Unhandled error: ${err.message}`, 0);
        if (err.stack) {
            log(err.stack, 0);
        }
        process.exit(1);
    }
})(); 