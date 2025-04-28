// Placeholder script for fetching Senate financial disclosures
// Data source: https://www.disclosure.senate.gov/ (Public Disclosure section)

const sqlite3 = require('sqlite3').verbose();
const path = require('path');
// Potentially use node-fetch, axios, cheerio, pdf-parse, or Playwright/Puppeteer

const dbPath = path.resolve(__dirname, '../data/database.sqlite');
let db;

async function fetchAndStoreSenateDisclosures() {
    console.log('Connecting to database...');
    db = new sqlite3.Database(dbPath, sqlite3.OPEN_READWRITE, (err) => {
        if (err) {
            console.error('Error opening database:', err.message);
            return;
        }
        console.log('Connected to the SQLite database.');
    });

    console.log('Fetching data from Senate Public Disclosures (Implementation needed)...');
    // TODO: Implement logic similar to the House script:
    // 1. Identify target senators.
    // 2. Navigate the eFD portal (often requires searching/filtering).
    // 3. Download disclosure documents (often PDFs, sometimes structured data?).
    // 4. Parse documents for Assets, Transactions, Liabilities, Agreements, Gifts, Travel.
    // 5. Convert value ranges.
    // 6. Format data for 'assets', 'transactions', 'company_associations' tables.

    const sampleAssets = [
        // { politician_bioguide_id: 'M001111', asset_name: 'US Treasury Note', asset_type: 'Bond', value_range_min: 15001, value_range_max: 50000, report_year: 2023, source_document: 'Murray_Patty_2023_eFD.pdf' },
    ];
    const sampleTransactions = [
        // { politician_bioguide_id: 'S000148', transaction_type: 'Sale', transaction_date: '2023-08-01', asset_name: 'Tech Stock Fund', value_range_min: 100001, value_range_max: 250000, report_year: 2023, source_document: 'Schumer_Charles_2023_eFD.pdf' },
    ];

    if (sampleAssets.length > 0) {
        await insertData(sampleAssets, 'assets');
    }
    if (sampleTransactions.length > 0) {
        await insertData(sampleTransactions, 'transactions');
    }

    console.log('Closing database connection.');
    db.close((err) => {
        if (err) {
            console.error('Error closing database:', err.message);
        }
    });
}

// Reusing the generic insert function from the House script (or duplicate/import it)
// For brevity, assuming 'insertData' is available here.
// If running standalone, copy the insertData function here.
async function insertData(records, tableName) {
    // Determine columns based on table name
    let columns, placeholders, valuesFn;
    if (tableName === 'assets') {
        columns = '(politician_bioguide_id, asset_name, asset_type, value_range_min, value_range_max, income_range_min, income_range_max, report_year, source_document)';
        placeholders = '(?, ?, ?, ?, ?, ?, ?, ?, ?)';
        valuesFn = r => [r.politician_bioguide_id, r.asset_name, r.asset_type, r.value_range_min, r.value_range_max, r.income_range_min, r.income_range_max, r.report_year, r.source_document];
    } else if (tableName === 'transactions') {
        columns = '(politician_bioguide_id, transaction_type, transaction_date, asset_name, asset_type, value_range_min, value_range_max, report_year, source_document)';
        placeholders = '(?, ?, ?, ?, ?, ?, ?, ?, ?)';
        valuesFn = r => [r.politician_bioguide_id, r.transaction_type, r.transaction_date, r.asset_name, r.asset_type, r.value_range_min, r.value_range_max, r.report_year, r.source_document];
    } else {
        console.error(`Unsupported table name for insertion: ${tableName}`);
        return;
    }

    const insertSql = `INSERT OR IGNORE INTO ${tableName} ${columns} VALUES ${placeholders}`;

    return new Promise((resolve, reject) => {
        db.serialize(() => {
            db.run('BEGIN TRANSACTION;');
            const stmt = db.prepare(insertSql);
            let insertedCount = 0;
            records.forEach(record => {
                stmt.run(valuesFn(record), function(err) {
                    if (err) {
                        console.error(`Error inserting into ${tableName}:`, err.message);
                    } else if (this.changes > 0) {
                        insertedCount++;
                    }
                });
            });
            stmt.finalize((err) => {
                if (err) {
                    console.error(`Error finalizing ${tableName} statement:`, err.message);
                    db.run('ROLLBACK;');
                    reject(err);
                } else {
                    db.run('COMMIT;', (commitErr) => {
                        if (commitErr) {
                            console.error(`Error committing ${tableName} transaction:`, commitErr.message);
                            reject(commitErr);
                        } else {
                            console.log(`Successfully inserted ${insertedCount} new records into ${tableName}.`);
                            resolve();
                        }
                    });
                }
            });
        });
    });
}


// Run the main function
fetchAndStoreSenateDisclosures().catch(err => {
    console.error('Error during Senate disclosure processing:', err);
    if (db) {
        db.close();
    }
}); 