const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const TARGET_URL = 'https://warroom.org/content-feed/';
const OUTPUT_FILE = path.join(__dirname, '..', 'data', 'warroom-headings.json');
const LOAD_MORE_SELECTOR = 'a:has-text("Load More")'; // Selector for the button
const MAX_CLICKS = 20; // Safety limit to prevent infinite loops

async function scrapeWarRoomHeadings() {
    console.log(`Starting heading scrape of ${TARGET_URL}...`);
    const browser = await chromium.launch();
    const page = await browser.newPage();

    try {
        console.log(`Navigating to ${TARGET_URL}...`);
        await page.goto(TARGET_URL, { waitUntil: 'load', timeout: 120000 });
        console.log('Initial page loaded.');

        // --- Click "Load More" loop ---
        let clicks = 0;
        while (clicks < MAX_CLICKS) {
            const loadMoreButton = page.locator(LOAD_MORE_SELECTOR);
            
            try {
                // Check if button exists and is visible
                await loadMoreButton.waitFor({ state: 'visible', timeout: 5000 }); // Wait up to 5s
                console.log(`"Load More" button found. Clicking... (Click ${clicks + 1})`);
                await loadMoreButton.click();
                // Wait a bit for content to load after click
                await page.waitForTimeout(3000); // Wait 3 seconds - adjust if needed
                clicks++;
            } catch (error) {
                // If button not found or visible after timeout, assume we're done
                console.log('"Load More" button not found or finished loading.');
                break; // Exit the loop
            }
        }
        if (clicks === MAX_CLICKS) {
            console.warn('Reached maximum click limit. There might be more content.');
        }
        // ---------------------------

        console.log('Finished loading content. Extracting headings...');
        // Selectors for the heading elements we want to extract
        const selectors = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'];
        
        const extractedHeadings = await page.evaluate((selectors) => {
            const results = [];
            document.querySelectorAll(selectors.join(', ')).forEach(element => {
                const text = element.textContent.trim();
                if (text && text.length > 1) { // Only add non-empty text, ignore single characters
                    results.push({
                        tag: element.tagName.toLowerCase(),
                        text: text
                    });
                }
            });
            return results;
        }, selectors);

        console.log(`Extracted ${extractedHeadings.length} total heading elements.`);
        
        // Filter out potential duplicates or navigation elements often in headers/footers
        const uniqueHeadings = extractedHeadings.filter((item, index, self) => 
            index === self.findIndex((t) => t.text === item.text)
        );
        console.log(`Filtered down to ${uniqueHeadings.length} unique heading elements.`);

        // Save the extracted headings to a JSON file
        fs.writeFileSync(OUTPUT_FILE, JSON.stringify(uniqueHeadings, null, 2), 'utf-8');
        console.log(`Successfully saved scraped headings to ${OUTPUT_FILE}`);

    } catch (error) {
        console.error(`Error during scraping: ${error.message}`);
        // Log more details if available
        if (error.stack) {
            console.error(error.stack);
        }
    } finally {
        await browser.close();
        console.log('Browser closed.');
    }
}

if (require.main === module) {
    scrapeWarRoomHeadings();
}

module.exports = { scrapeWarRoomHeadings }; 