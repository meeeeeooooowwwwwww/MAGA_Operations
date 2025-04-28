const sqlite3 = require('sqlite3').verbose();
const path = require('path');

// Define the path to the database file relative to the project root
const dbPath = path.resolve(__dirname, '../../data/politicians.db');
const db = new sqlite3.Database(dbPath, (err) => {
    if (err) {
        console.error('Error opening database:', err.message);
    } else {
        console.log('Connected to the SQLite database for migration.');
    }
});

// Function to run migration
const runMigration = () => {
    db.serialize(() => {
        console.log('Running migration: 002-add-financial-tables');

        // --- Donations Table ---
        // Stores campaign finance contribution data, likely sourced from FEC.
        db.run(`
            CREATE TABLE IF NOT EXISTS donations (
                donation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                politician_bioguide_id TEXT,                  -- Link to the politician
                donor_name TEXT,                             -- Name of the individual or committee donating
                donor_type TEXT,                             -- e.g., Individual, PAC, Corporation (if applicable)
                donor_employer TEXT,                         -- Often included in FEC data
                donor_occupation TEXT,                       -- Often included in FEC data
                donor_address TEXT,                          -- Address of the donor
                amount REAL,                                 -- Donation amount
                date TEXT,                                   -- Date of the donation
                election_cycle TEXT,                         -- e.g., '2024'
                transaction_id TEXT UNIQUE,                  -- FEC transaction ID or similar unique identifier
                source_url TEXT,                             -- URL where the data was obtained, if applicable
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- When this record was added/updated
                FOREIGN KEY (politician_bioguide_id) REFERENCES politicians (bioguide_id) ON DELETE CASCADE
            );
        `, (err) => {
            if (err) console.error("Error creating donations table:", err.message);
            else console.log("Donations table created or already exists.");
        });
        db.run(`CREATE INDEX IF NOT EXISTS idx_donations_politician ON donations (politician_bioguide_id);`);
        db.run(`CREATE INDEX IF NOT EXISTS idx_donations_donor ON donations (donor_name);`);
        db.run(`CREATE INDEX IF NOT EXISTS idx_donations_date ON donations (date);`);

        // --- Assets Table ---
        // Stores information about assets held by politicians, from financial disclosures.
        db.run(`
            CREATE TABLE IF NOT EXISTS assets (
                asset_id INTEGER PRIMARY KEY AUTOINCREMENT,
                politician_bioguide_id TEXT,                  -- Link to the politician
                asset_name TEXT,                             -- Description of the asset (e.g., "Stock in Apple Inc.")
                asset_type TEXT,                             -- e.g., Stock, Bond, Real Estate, Mutual Fund
                value_range_min REAL,                        -- Minimum value estimate (often reported in ranges)
                value_range_max REAL,                        -- Maximum value estimate
                income_range_min REAL,                       -- Minimum income generated (if applicable)
                income_range_max REAL,                       -- Maximum income generated
                report_year INTEGER,                         -- The year the disclosure report covers
                source_document TEXT,                        -- Identifier for the disclosure document (e.g., filename, URL)
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (politician_bioguide_id) REFERENCES politicians (bioguide_id) ON DELETE CASCADE
            );
        `, (err) => {
            if (err) console.error("Error creating assets table:", err.message);
            else console.log("Assets table created or already exists.");
        });
        db.run(`CREATE INDEX IF NOT EXISTS idx_assets_politician ON assets (politician_bioguide_id);`);
        db.run(`CREATE INDEX IF NOT EXISTS idx_assets_name ON assets (asset_name);`);
        db.run(`CREATE INDEX IF NOT EXISTS idx_assets_year ON assets (report_year);`);

        // --- Transactions Table ---
        // Stores financial transactions (buy/sell) reported in disclosures.
        db.run(`
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_record_id INTEGER PRIMARY KEY AUTOINCREMENT, -- Renamed from transaction_id to avoid conflict
                politician_bioguide_id TEXT,                  -- Link to the politician
                transaction_type TEXT,                       -- e.g., 'Purchase', 'Sale', 'Exchange'
                transaction_date TEXT,                       -- Date of the transaction
                asset_name TEXT,                             -- Description of the asset involved
                asset_type TEXT,                             -- Type of asset
                value_range_min REAL,                        -- Minimum transaction value estimate
                value_range_max REAL,                        -- Maximum transaction value estimate
                report_year INTEGER,                         -- The year the disclosure report covers
                source_document TEXT,                        -- Identifier for the disclosure document
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (politician_bioguide_id) REFERENCES politicians (bioguide_id) ON DELETE CASCADE
            );
        `, (err) => {
            if (err) console.error("Error creating transactions table:", err.message);
            else console.log("Transactions table created or already exists.");
        });
        db.run(`CREATE INDEX IF NOT EXISTS idx_transactions_politician ON transactions (politician_bioguide_id);`);
        db.run(`CREATE INDEX IF NOT EXISTS idx_transactions_asset ON transactions (asset_name);`);
        db.run(`CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions (transaction_date);`);
        db.run(`CREATE INDEX IF NOT EXISTS idx_transactions_year ON transactions (report_year);`);


        // --- Company Associations Table ---
        // Stores affiliations with companies (e.g., board memberships, executive roles). Often harder to source reliably.
        db.run(`
            CREATE TABLE IF NOT EXISTS company_associations (
                association_id INTEGER PRIMARY KEY AUTOINCREMENT,
                politician_bioguide_id TEXT,                  -- Link to the politician
                company_name TEXT,                           -- Name of the company/organization
                role TEXT,                                   -- Position held (e.g., Board Member, Consultant)
                start_date TEXT,                             -- Start date of the association (may be approximate)
                end_date TEXT,                               -- End date (if applicable)
                compensation_details TEXT,                   -- Notes on compensation if available
                source TEXT,                                 -- How this information was sourced (e.g., Financial Disclosure, News Article)
                source_url TEXT,                             -- URL of the source, if applicable
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (politician_bioguide_id) REFERENCES politicians (bioguide_id) ON DELETE CASCADE
            );
        `, (err) => {
            if (err) console.error("Error creating company_associations table:", err.message);
            else console.log("Company Associations table created or already exists.");
        });
        db.run(`CREATE INDEX IF NOT EXISTS idx_associations_politician ON company_associations (politician_bioguide_id);`);
        db.run(`CREATE INDEX IF NOT EXISTS idx_associations_company ON company_associations (company_name);`);


        console.log('Migration 002 finished.');
    });

    // Close the database connection
    db.close((err) => {
        if (err) {
            console.error('Error closing database connection:', err.message);
        } else {
            console.log('Database connection closed.');
        }
    });
};

// Execute the migration function
runMigration();

module.exports = { runMigration }; // Export if needed elsewhere, though likely run directly 