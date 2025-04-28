// Senate Financial Disclosures Scraper using Playwright
// Target: https://efdsearch.senate.gov/search/

const { chromium } = require('playwright');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const fs = require('fs');

// Configuration
const dbPath = path.resolve(__dirname, '../data/politicians.db'); 
let db;

// Cache directory for downloaded PDFs
const CACHE_DIR = path.resolve(__dirname, '../cache/senate_disclosures');
if (!fs.existsSync(CACHE_DIR)) {
    fs.mkdirSync(CACHE_DIR, { recursive: true });
}

// Settings
const MAX_POLITICIANS = parseInt(process.env.MAX_POLITICIANS || '5', 10); // Limit number of politicians for testing
const DEBUG_LEVEL = parseInt(process.env.DEBUG_LEVEL || '1', 10);
const SEARCH_YEARS = ['2025', '2024', '2023']; // Updated to only search most recent years
const DOWNLOAD_REPORTS = true; // Whether to download report PDFs
const TAKE_SCREENSHOTS = true; // Take screenshots for debugging

// Capture screenshots directory
const SCREENSHOTS_DIR = path.resolve(__dirname, '../cache/screenshots');
if (TAKE_SCREENSHOTS && !fs.existsSync(SCREENSHOTS_DIR)) {
    fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });
}

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

// Take a screenshot
async function screenshot(page, name) {
    if (!TAKE_SCREENSHOTS) return;
    
    const filename = `${Date.now()}_${name.replace(/[^a-z0-9]/gi, '_')}.png`;
    const screenshotPath = path.join(SCREENSHOTS_DIR, filename);
    await page.screenshot({ path: screenshotPath, fullPage: true });
    log(`Screenshot saved: ${screenshotPath}`, 2);
}

// Get all senators from database
async function getSenators() {
    return new Promise((resolve, reject) => {
        const query = `
            SELECT 
                id,
                bioguide_id, 
                name,
                state,
                chamber
            FROM 
                politicians 
            WHERE 
                bioguide_id IS NOT NULL 
                AND chamber = 'senate'
            ORDER BY 
                name
            LIMIT ?
        `;
        
        db.all(query, [MAX_POLITICIANS === 0 ? -1 : MAX_POLITICIANS], (err, rows) => {
            if (err) {
                reject(new Error(`Error fetching politicians: ${err.message}`));
                return;
            }
            log(`Retrieved ${rows.length} senators from database`);
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
            `Senate Financial Disclosure ${year}`,
            fileUrl || `Local file: ${localPath}`
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

// Scrape Senate Financial Disclosures website
async function scrapeSenateDisclosures() {
    log('Launching browser...');
    
    const browser = await chromium.launch({
        headless: false, // Changed to false to make browser visible
        slowMo: 100 // Slow down operations by 100ms (Senate site is more complex)
    });
    
    try {
        const context = await browser.newContext({
            userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            viewport: { width: 1280, height: 720 }
        });
        
        const page = await context.newPage();
        log('Navigating to Senate Financial Disclosures website...');
        
        // Navigate to the financial disclosures site
        await page.goto('https://efdsearch.senate.gov/search/', {
            waitUntil: 'networkidle'
        });
        
        // The Senate site requires agreeing to terms first
        await screenshot(page, 'senate_landing');
        
        try {
            log('Looking for terms agreement checkbox...');
            
            // First take a screenshot to see what we're dealing with
            await screenshot(page, 'before_terms_acceptance');
            
            // Check if we need to agree to terms
            const agreeButton = page.locator('input#agree_statement');
            
            if (await agreeButton.count() > 0) {
                log('Found agreement checkbox. Accepting terms and conditions...');
                
                // First make sure the checkbox is checked
                await page.evaluate(() => {
                    const checkBox = document.querySelector('input#agree_statement');
                    if (checkBox && !checkBox.checked) {
                        checkBox.checked = true;
                        // Trigger any change events
                        checkBox.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                });
                
                // Wait a moment for any JS to process
                await sleep(2000, 3000);
                
                log(`Page URL: ${page.url()}`);
                log(`Page title: ${await page.title()}`);
                
                // Since there's no visible continue button, directly submit the form using JavaScript
                log('No visible continue button detected. Attempting to submit the form directly...');
                
                // First capture screenshot for debugging
                await screenshot(page, 'before_form_submit');
                
                // Submit the form directly
                const formSubmitResult = await page.evaluate(() => {
                    const form = document.getElementById('agreement_form');
                    if (form) {
                        // Try to submit via the form's native submit method
                        form.submit();
                        return 'Form submitted directly';
                    } else {
                        // If can't find the form by ID, try to find any form
                        const forms = document.querySelectorAll('form');
                        if (forms.length > 0) {
                            forms[0].submit();
                            return 'First form submitted directly';
                        }
                        return 'No form found to submit';
                    }
                });
                
                log(`Form submission result: ${formSubmitResult}`);
                
                // Wait for navigation to complete
                try {
                    await page.waitForNavigation({ waitUntil: 'networkidle', timeout: 60000 });
                    log('Navigation after form submission completed');
                } catch (navError) {
                    log(`Navigation error after form submission: ${navError.message}`);
                }
                
                // Wait additional time for any redirects
                await sleep(5000, 5000);
                
                // Take screenshot to see where we ended up
                await screenshot(page, 'after_form_submit');
                
                log(`Current URL after form submission: ${page.url()}`);
                log(`Current page title: ${await page.title()}`);
                
                // If still on the same page, try navigating directly to the search page
                if (page.url().includes('efdsearch.senate.gov/search/home/')) {
                    log('Still on the terms page. Trying to navigate directly to search...');
                    
                    // Try a direct navigation to the search page
                    await page.goto('https://efdsearch.senate.gov/search/search/', {
                        waitUntil: 'networkidle',
                        timeout: 60000
                    });
                    
                    log(`New URL after direct navigation: ${page.url()}`);
                    
                    // Check if redirected back to terms page
                    if (await page.locator('input#agree_statement').count() > 0) {
                        log('Redirected back to terms page. This may require manual intervention.');
                        
                        // Take screenshot of redirect page
                        await screenshot(page, 'redirected_to_terms');
                        
                        // As a last resort, try finding any clickable elements that might help
                        log('Looking for any navigation links or buttons...');
                        const links = await page.locator('a').count();
                        log(`Found ${links} links on the page`);
                        
                        // Try clicking a link that might lead to search
                        const searchLinks = page.locator('a:has-text("Search")');
                        if (await searchLinks.count() > 0) {
                            log('Found a search link. Attempting to click...');
                            await searchLinks.first().click().catch(e => log(`Error clicking search link: ${e.message}`));
                            await sleep(5000, 5000);
                        }
                    }
                }
            } else {
                log('No agreement checkbox found. Might already be on search page or site structure has changed.');
            }
            
            // Take another screenshot to see where we are
            await screenshot(page, 'after_terms_navigation');
            
            // Check if we're actually on the search page
            const onSearchPage = await page.evaluate(() => {
                return {
                    url: window.location.href,
                    hasSearchTab: !!document.getElementById('filedByTab'),
                    hasFirstName: !!document.getElementById('FirstName'),
                    hasLastName: !!document.getElementById('LastName'),
                    pageTitle: document.title
                };
            });
            
            log('Current page state:');
            console.log(JSON.stringify(onSearchPage, null, 2));
            
            // If we need to, proceed to search page explicitly
            if (!onSearchPage.hasSearchTab && !onSearchPage.hasFirstName) {
                log('Not on search page. Trying to navigate directly to search home...');
                
                // Try going directly to the search page
                await page.goto('https://efdsearch.senate.gov/search/home/', {
                    waitUntil: 'networkidle',
                    timeout: 60000
                });
                
                // Check if we're redirected back to agreement page
                const redirectedToAgreement = await page.locator('input#agree_statement').count() > 0;
                
                if (redirectedToAgreement) {
                    log('Redirected back to agreement page. Site requires specific navigation flow.');
                    throw new Error('Unable to navigate past agreement page. Site may have changed or requires manual steps.');
                }
            }
            
            log('Proceeding with search functionality...');
        } catch (navigationError) {
            log(`Error during navigation: ${navigationError.message}`);
            await screenshot(page, 'navigation_error');
            throw navigationError;
        }
        
        // Take a screenshot of where we ended up
        await screenshot(page, 'senate_search');
        
        // Check if we're actually on the search page by looking for expected elements
        const isOnSearchPage = await page.url().includes('efdsearch.senate.gov/search');
        
        if (!isOnSearchPage) {
            log('ERROR: Not on search page after accepting terms. Cannot continue.');
            log('Current URL: ' + await page.url());
            log('Current title: ' + await page.title());
            
            // Let's see what's on the page
            const pageContent = await page.content();
            log('First 500 characters of page content: ' + pageContent.substring(0, 500));
            
            // Give a chance to look at the page manually before exiting
            log('Pausing for 30 seconds for manual observation before exiting...');
            await sleep(30000, 30000);
            
            throw new Error('Failed to navigate to search page after accepting terms');
        }
        
        log('Successfully navigated to search page');
        
        // Initialize database
        await initDb();
        
        // Retrieve senators
        const senators = await getSenators();
        
        let processedCount = 0;
        let successCount = 0;
        let documentsFound = 0;
        
        // Process each senator
        for (const senator of senators) {
            log(`Processing ${senator.name} (${senator.state})...`);
            
            // Check if already has assets
            const hasAssets = await hasAssetsInDb(senator.bioguide_id);
            if (hasAssets) {
                log(`Skipping ${senator.name}: Already has assets in database`);
                processedCount++;
                continue;
            }
            
            // Store document information found for this politician
            const documentInfo = [];
            
            // Search for each year
            for (const year of SEARCH_YEARS) {
                log(`Searching for ${senator.name} financial disclosures in ${year}...`);
                
                try {
                    // Make sure we're on the search form page
                    log('Navigating to search form...');
                    await page.goto('https://efdsearch.senate.gov/search/', {
                        waitUntil: 'networkidle'
                    });
                    
                    // Take screenshot of search page
                    await screenshot(page, `${senator.name}_search_form_initial`);
                    
                    // The search form should be directly accessible without clicking tabs
                    log('Looking for search form elements directly...');
                    
                    // Skip trying to click search tabs which might be causing the issue
                    // Instead directly check for the form fields which should be on the page
                    const lastNameField = page.locator('#LastName, input[name="LastName"], input[placeholder*="Last Name"]');
                    const firstNameField = page.locator('#FirstName, input[name="FirstName"], input[placeholder*="First Name"]');
                    
                    // Check if form fields exist
                    if (await lastNameField.count() === 0 || await firstNameField.count() === 0) {
                        // Try a direct JavaScript evaluation to find the fields
                        log('Using JavaScript to find and identify form fields...');
                        
                        const formElements = await page.evaluate(() => {
                            // Get all input fields
                            const inputs = Array.from(document.querySelectorAll('input[type="text"]'));
                            
                            // Look for likely name fields
                            const lastNameInput = inputs.find(input => 
                                input.id?.toLowerCase().includes('last') || 
                                input.name?.toLowerCase().includes('last') ||
                                input.placeholder?.toLowerCase().includes('last')
                            );
                            
                            const firstNameInput = inputs.find(input => 
                                input.id?.toLowerCase().includes('first') || 
                                input.name?.toLowerCase().includes('first') ||
                                input.placeholder?.toLowerCase().includes('first')
                            );
                            
                            return {
                                foundLastName: lastNameInput ? true : false,
                                lastNameId: lastNameInput?.id || '',
                                lastNameName: lastNameInput?.name || '',
                                
                                foundFirstName: firstNameInput ? true : false,
                                firstNameId: firstNameInput?.id || '',
                                firstNameName: firstNameInput?.name || ''
                            };
                        });
                        
                        log(`Form detection results: ${JSON.stringify(formElements)}`);
                        
                        if (!formElements.foundLastName || !formElements.foundFirstName) {
                            log('ERROR: Name search fields not found. The page structure may have changed.');
                            log('Current URL: ' + await page.url());
                            await screenshot(page, `${senator.name}_search_form_error`);
                            continue; // Skip this year
                        }
                        
                        // Use the detected field IDs/names
                        if (formElements.lastNameId) {
                            log(`Using detected last name field with ID: ${formElements.lastNameId}`);
                            await page.fill(`#${formElements.lastNameId}`, lastName);
                        } else if (formElements.lastNameName) {
                            log(`Using detected last name field with name: ${formElements.lastNameName}`);
                            await page.fill(`input[name="${formElements.lastNameName}"]`, lastName);
                        }
                        
                        if (formElements.firstNameId) {
                            log(`Using detected first name field with ID: ${formElements.firstNameId}`);
                            await page.fill(`#${formElements.firstNameId}`, firstName);
                        } else if (formElements.firstNameName) {
                            log(`Using detected first name field with name: ${formElements.firstNameName}`);
                            await page.fill(`input[name="${formElements.firstNameName}"]`, firstName);
                        }
                    } else {
                        // Fill out the search form
                        log('Filling out search form...');
                        
                        // Get last name
                        const lastName = senator.name.split(' ').pop();
                        await lastNameField.fill(lastName);
                        
                        // First name (try to extract)
                        const firstName = senator.name.split(' ')[0];
                        await firstNameField.fill(firstName);
                    }
                    
                    // Look for date fields and report type
                    const reportTypeField = page.locator('#reportTypeLCDRP, select[name="reportType"], select[id*="report"], select[name*="report"]');
                    if (await reportTypeField.count() > 0) {
                        log('Setting report type to Annual...');
                        await reportTypeField.selectOption('Annual');
                    }
                    
                    // Try to find date fields
                    const fromDateField = page.locator('#fromDate, input[name="fromDate"], input[id*="from"], input[name*="from"]');
                    const toDateField = page.locator('#toDate, input[name="toDate"], input[id*="to"], input[name*="to"]');
                    
                    if (await fromDateField.count() > 0 && await toDateField.count() > 0) {
                        // Enter date range for the search
                        const yearStart = `01/01/${year}`;
                        const yearEnd = `12/31/${year}`;
                        log(`Setting date range: ${yearStart} to ${yearEnd}`);
                        await fromDateField.fill(yearStart);
                        await toDateField.fill(yearEnd);
                    } else {
                        log('Date fields not found. The form may have changed structure.');
                    }
                    
                    await screenshot(page, `${senator.name}_filled_form_${year}`);
                    
                    // Now find and click the search button - use a more specific selector to avoid the "re-search" button
                    log('Looking for search submit button...');
                    const searchButton = page.locator('input[type="submit"][value="Search"]:visible, button[type="submit"]:visible, input.btn-primary[type="submit"]:visible');
                    
                    if (await searchButton.count() > 0) {
                        // Click search using Promise.all for navigation
                        log('Clicking search button...');
                        try {
                            await Promise.all([
                                page.waitForNavigation({ waitUntil: 'networkidle', timeout: 60000 }),
                                searchButton.first().click()
                            ]);
                        } catch (searchClickErr) {
                            log(`Error during search click: ${searchClickErr.message}`);
                            
                            // Try plain click without waiting for navigation
                            log('Trying plain click without navigation...');
                            await searchButton.first().click().catch(e => log(`Error on plain click: ${e.message}`));
                            await sleep(5000, 5000);
                        }
                    } else {
                        // Last resort - try to submit the form directly with JavaScript
                        log('Search button not found. Trying to submit form with JavaScript...');
                        
                        await page.evaluate(() => {
                            const forms = document.querySelectorAll('form');
                            if (forms.length > 0) {
                                // Try to submit the form with the most input fields (likely the search form)
                                let formToSubmit = forms[0];
                                let maxInputs = forms[0].querySelectorAll('input').length;
                                
                                for (let i = 1; i < forms.length; i++) {
                                    const inputCount = forms[i].querySelectorAll('input').length;
                                    if (inputCount > maxInputs) {
                                        formToSubmit = forms[i];
                                        maxInputs = inputCount;
                                    }
                                }
                                
                                formToSubmit.submit();
                                return true;
                            }
                            return false;
                        });
                        
                        // Wait for navigation
                        try {
                            await page.waitForNavigation({ waitUntil: 'networkidle', timeout: 30000 });
                        } catch (navErr) {
                            log(`Navigation error after form submit: ${navErr.message}`);
                        }
                    }
                    
                    await screenshot(page, `${senator.name}_search_results_${year}`);
                    
                    // Check for results - look for search results table
                    const resultsTable = page.locator('table#filedReportsGrid');
                    const hasResults = await resultsTable.count() > 0;
                    
                    if (!hasResults) {
                        log(`No results found for ${senator.name} in ${year}`);
                        continue;
                    }
                    
                    // Count rows in results table (skip header)
                    const rows = await page.locator('table#filedReportsGrid tbody tr').count();
                    log(`Found ${rows} disclosure documents for ${senator.name} in ${year}`);
                    
                    // Process each result row
                    for (let i = 0; i < rows; i++) {
                        const rowSelector = `table#filedReportsGrid tbody tr:nth-child(${i + 1})`;
                        
                        // Get document type from first column
                        const docType = await page.locator(`${rowSelector} td:nth-child(3)`).textContent();
                        
                        // Get filing date from the date column
                        const filingDate = await page.locator(`${rowSelector} td:nth-child(4)`).textContent();
                        
                        // View button is typically in the last column
                        const viewButton = page.locator(`${rowSelector} td:last-child a`);
                        
                        if (await viewButton.count() > 0) {
                            // Get information before clicking
                            const pdfFilename = `${senator.bioguide_id}_${year}_${(docType || 'unknown').trim().replace(/\s+/g, '_')}.pdf`;
                            const localPath = path.join(CACHE_DIR, pdfFilename);
                            
                            // Need to open document in a new page
                            const [popup] = await Promise.all([
                                context.waitForEvent('page'),
                                viewButton.click()
                            ]);
                            
                            // Wait for the document to load
                            await popup.waitForLoadState('networkidle');
                            
                            // Get URL for reference
                            const docUrl = popup.url();
                            
                            // Take screenshot of document page
                            await screenshot(popup, `${senator.name}_document_${year}_${i}`);
                            
                            // Try to download the document if available
                            let downloadSuccessful = false;
                            
                            if (DOWNLOAD_REPORTS && !fs.existsSync(localPath)) {
                                try {
                                    // Look for download links
                                    const downloadLink = popup.locator('a:has-text("View/Download")');
                                    
                                    if (await downloadLink.count() > 0) {
                                        log(`Downloading document for ${senator.name} (${year})`, 2);
                                        
                                        const [download] = await Promise.all([
                                            popup.waitForEvent('download'),
                                            downloadLink.click()
                                        ]);
                                        
                                        await download.saveAs(localPath);
                                        log(`Document saved to ${localPath}`, 2);
                                        downloadSuccessful = true;
                                    } else {
                                        // Fallback: try to take a PDF screenshot if download link not available
                                        log(`Download link not found, taking PDF screenshot for ${senator.name}`, 1);
                                        await popup.pdf({ path: localPath });
                                    }
                                } catch (downloadErr) {
                                    log(`Error downloading document: ${downloadErr.message}`, 0);
                                }
                            }
                            
                            // Add to document info
                            documentInfo.push({
                                politician: senator.name,
                                bioguideId: senator.bioguide_id,
                                type: (docType || 'Unknown Document').trim(),
                                year: year,
                                filingDate: filingDate ? filingDate.trim() : null,
                                url: docUrl,
                                localPath: downloadSuccessful ? localPath : null
                            });
                            
                            // Close the popup
                            await popup.close();
                            
                            // Add a delay to avoid overwhelming the server
                            await sleep(2000, 4000);
                        }
                    }
                    
                    // Wait before proceeding to the next year
                    await sleep(2000, 4000);
                    
                } catch (searchError) {
                    log(`Error searching for ${senator.name} in ${year}: ${searchError.message}`, 0);
                    await screenshot(page, `${senator.name}_error_${year}`);
                    
                    // Continue to next year despite error
                    continue;
                }
            }
            
            // Store document references in the database
            if (documentInfo.length > 0) {
                const addedCount = await parseAndStoreFinancialData(senator, documentInfo);
                log(`Added ${addedCount} document references for ${senator.name}`);
                documentsFound += addedCount;
                successCount++;
            } else {
                log(`No documents found for ${senator.name}`);
            }
            
            processedCount++;
            
            // Add a longer delay between politicians
            await sleep(5000, 8000);
        }
        
        log(`\n=== Senate Financial Disclosures Scraping Complete ===`);
        log(`Senators processed: ${processedCount}/${senators.length}`);
        log(`Senators with documents found: ${successCount}`);
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
        await scrapeSenateDisclosures();
    } catch (err) {
        log(`Unhandled error: ${err.message}`, 0);
        if (err.stack) {
            log(err.stack, 0);
        }
        process.exit(1);
    }
})(); 