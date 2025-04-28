// Placeholder script for fetching House financial disclosures
// Data source: https://disclosures-clerk.house.gov/FinancialDisclosure

const sqlite3 = require('sqlite3').verbose();
const path = require('path');
// Potentially use node-fetch, axios, cheerio, pdf-parse, or Playwright/Puppeteer

const dbPath = path.resolve(__dirname, '../data/database.sqlite');
let db;

async function fetchAndStoreHouseDisclosures() {
    console.log('Connecting to database...');
    db = new sqlite3.Database(dbPath, sqlite3.OPEN_READWRITE, (err) => {
        if (err) {
            console.error('Error opening database:', err.message);
            return;
        }
        console.log('Connected to the SQLite database.');
    });

    console.log('Fetching data from House Clerk Disclosures (Implementation needed)...');
    // TODO: Implement logic:
    // 1. Identify target representatives (e.g., from our politicians table).
    // 2. Navigate the disclosure website (may involve searching by name/year).
    // 3. Download disclosure documents (often PDFs).
    // 4. Parse PDFs to extract:
    //    - Assets (Schedule A/I)
    //    - Transactions (Schedule B/II)
    //    - Liabilities (Schedule C/IV)
    //    - Agreements/Arrangements (Schedule D/V)
    //    - Gifts (Schedule F/VII)
    //    - Travel Reimbursements (Schedule G/VIII)
    // 5. Standardize data (e.g., convert value ranges like "$1,001 - $15,000" to min/max numbers).
    // 6. Format data for insertion into 'assets', 'transactions', and potentially 'company_associations' tables.

    // Example data structure after parsing (replace with actual parsed data)
    const sampleAssets = [
        // { politician_bioguide_id: 'P000197', asset_name: 'Microsoft Corp Stock', asset_type: 'Stock', value_range_min: 15001, value_range_max: 50000, income_range_min: 0, income_range_max: 200, report_year: 2023, source_document: 'Pelosi_Nancy_2023_FD.pdf' },
        // { politician_bioguide_id: 'M000355', asset_name: 'Rental Property Anytown USA', asset_type: 'Real Estate', value_range_min: 1000001, value_range_max: 5000000, income_range_min: 15001, income_range_max: 50000, report_year: 2023, source_document: 'McCarthy_Kevin_2023_FD.pdf' }
    ];
    const sampleTransactions = [
        // { politician_bioguide_id: 'P000197', transaction_type: 'Purchase', transaction_date: '2023-05-10', asset_name: 'Apple Inc Call Options', asset_type: 'Stock Option', value_range_min: 100001, value_range_max: 250000, report_year: 2023, source_document: 'Pelosi_Nancy_2023_PTR.pdf' }
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

// Generic function to insert records into specified table
async function insertData(records, tableName) {
    // Determine columns based on table name
    let columns, placeholders, valuesFn;
    if (tableName === 'assets') {
        columns = '(politician_bioguide_id, asset_name, asset_type, value_range_min, value_range_max, income_range_min, income_range_max, report_year, source_document)';
        placeholders = '(?, ?, ?, ?, ?, ?, ?, ?, ?)';
        valuesFn = r => [r.politician_bioguide_id, r.asset_name, r.asset_type, r.value_range_min, r.value_range_max, r.income_range_min || null, r.income_range_max || null, r.report_year, r.source_document];
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
fetchAndStoreHouseDisclosures().catch(err => {
    console.error('Error during House disclosure processing:', err);
    if (db) {
        db.close();
    }
}); 