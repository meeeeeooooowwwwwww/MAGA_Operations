const sqlite3 = require('sqlite3').verbose();
const fs = require('fs');
const path = require('path');

// Database path relative to project root
const PROJECT_ROOT = path.join(__dirname, '..'); 
const DATA_DIR = path.join(PROJECT_ROOT, 'data');
const DB_PATH = path.join(DATA_DIR, 'politicians.db');

// --- Main Setup Function ---
function setupFrontendDatabase() {
    console.log('Setting up frontend politicians database...');
    
    // Ensure data directory exists
    if (!fs.existsSync(DATA_DIR)) {
        fs.mkdirSync(DATA_DIR, { recursive: true });
        console.log(`Created data directory: ${DATA_DIR}`);
    }

    // Delete existing database file if it exists to ensure a clean setup
    if (fs.existsSync(DB_PATH)) {
        console.log(`Deleting existing database at ${DB_PATH}...`);
        try {
            fs.unlinkSync(DB_PATH);
            console.log('Existing database deleted.');
        } catch (err) {
            console.error('Error deleting existing database:', err.message);
            return; // Stop if we can't delete the old one
        }
    }
    
    // Connect to/create the database
    const db = new sqlite3.Database(DB_PATH, (err) => {
        if (err) {
            console.error('Error creating/connecting to database:', err);
            return;
        }
        console.log(`Connected to/created database: ${DB_PATH}`);
        
        createSchemaAndPopulate(db);
    });
}

// --- Schema Creation and Data Population ---
function createSchemaAndPopulate(db) {
    db.serialize(() => {
        console.log('Creating tables...');
        
        // 1. Create Politicians Table (matching main.js schema)
        db.run(`
            CREATE TABLE politicians (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bioguide_id TEXT UNIQUE,
                name TEXT NOT NULL,
                state TEXT,
                district TEXT,
                party TEXT,
                level TEXT,
                chamber TEXT,
                office TEXT,
                phone TEXT,
                email TEXT,
                website TEXT,
                twitter TEXT,
                facebook TEXT,
                instagram TEXT,
                youtube TEXT,
                linkedin TEXT,
                bio TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        `, (err) => {
            if (err) { logAndClose(db, 'Error creating politicians table', err); return; }
            console.log('Politicians table created.');

            // 2. Create Offices Table
            db.run(`
                CREATE TABLE offices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    politician_id INTEGER,
                    bioguide_id TEXT,
                    type TEXT,
                    address TEXT,
                    city TEXT,
                    state TEXT,
                    zip TEXT,
                    phone TEXT,
                    fax TEXT,
                    FOREIGN KEY (politician_id) REFERENCES politicians (id) ON DELETE CASCADE
                )
            `, (err) => {
                if (err) { logAndClose(db, 'Error creating offices table', err); return; }
                console.log('Offices table created.');
                
                // 3. Create Tweets Table
                db.run(`
                    CREATE TABLE tweets (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        politician_id INTEGER,
                        bioguide_id TEXT,
                        tweet_id TEXT,
                        text TEXT,
                        created_at TIMESTAMP,
                        retweet_count INTEGER,
                        favorite_count INTEGER,
                        hashtags TEXT,
                        mentions TEXT,
                        FOREIGN KEY (politician_id) REFERENCES politicians (id) ON DELETE CASCADE
                    )
                `, (err) => {
                     if (err) { logAndClose(db, 'Error creating tweets table', err); return; }
                     console.log('Tweets table created.');

                     // 4. Populate with Sample Data
                     console.log('Populating with sample data...');
                     createSampleData(db, (err) => { // Pass callback to know when done
                        if (err) {
                            // Error already logged in createSampleData
                            closeDb(db); // Still close DB on error
                        } else {
                            console.log('Sample data populated successfully.');
                            closeDb(db); // Close DB after successful population
                        }
                     });
                }); // End Tweets Table callback
            }); // End Offices Table callback
        }); // End Politicians Table callback
    }); // End db.serialize
}

// --- Sample Data Creation ---
function createSampleData(db, callback) { 
    const samplePoliticians = [
        // Sanders Data
        {
            bioguide_id: 'S000148', name: 'Bernard Sanders', state: 'VT', district: null, party: 'Independent', level: 'federal_senate', chamber: 'senate', office: 'Senator', 
            phone: '202-224-5141', email: null, website: 'https://www.sanders.senate.gov', 
            twitter: 'SenSanders', facebook: 'senatorsanders', instagram: null, youtube: 'senatorsanders', linkedin: null, 
            bio: JSON.stringify({ birthday: '1941-09-08', gender: 'M' }),
            offices: [
                { type: 'capitol', address: '332 Dirksen Senate Office Building', city: 'Washington', state: 'DC', zip: '20510', phone: '202-224-5141', fax: '202-228-0776' },
                { type: 'district', address: '1 Church St, 3rd Floor', city: 'Burlington', state: 'VT', zip: '05401', phone: '802-862-0697', fax: '802-860-6370' }
            ]
        },
        // AOC Data
        {
            bioguide_id: 'O000172', name: 'Alexandria Ocasio-Cortez', state: 'NY', district: '14', party: 'Democrat', level: 'federal_house', chamber: 'house', office: 'Representative', 
            phone: '202-225-3965', email: null, website: 'https://ocasio-cortez.house.gov', 
            twitter: 'RepAOC', facebook: 'RepAOC', instagram: 'aoc', youtube: null, linkedin: null, 
            bio: JSON.stringify({ birthday: '1989-10-13', gender: 'F' }),
            offices: [
                 { type: 'capitol', address: '214 Cannon House Office Building', city: 'Washington', state: 'DC', zip: '20515', phone: '202-225-3965', fax: null },
                 { type: 'district', address: '74-09 37th Ave, Ste 305', city: 'Jackson Heights', state: 'NY', zip: '11372', phone: '718-662-5970', fax: null }
            ]
        }
    ];
    
    const politicianStmt = db.prepare(`
        INSERT INTO politicians (bioguide_id, name, state, district, party, level, chamber, office, phone, email, website, twitter, facebook, instagram, youtube, linkedin, bio)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);
    const officeStmt = db.prepare(`
        INSERT INTO offices (politician_id, bioguide_id, type, address, city, state, zip, phone, fax)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);

    let politiciansCompleted = 0;
    const totalPoliticians = samplePoliticians.length;
    let hasError = false;

    db.serialize(() => {
        db.run('BEGIN TRANSACTION');
        
        samplePoliticians.forEach(p => {
            politicianStmt.run(
                p.bioguide_id, p.name, p.state, p.district, p.party, p.level, p.chamber, p.office, 
                p.phone, p.email, p.website, p.twitter, p.facebook, p.instagram, p.youtube, p.linkedin, p.bio,
                function(err) { // Use callback to get ID for office insertion
                    if (err) {
                        console.error(`Error inserting sample politician ${p.bioguide_id}:`, err.message);
                        hasError = true;
                        checkCompletion(); // Check if we should finish even on error
                        return; 
                    }
                    
                    const politicianRowId = this.lastID;
                    
                    // Insert Offices
                    if (p.offices && p.offices.length > 0) {
                        p.offices.forEach(o => {
                            officeStmt.run(
                                politicianRowId, p.bioguide_id, o.type, o.address, o.city, o.state, o.zip, o.phone, o.fax,
                                (officeErr) => {
                                    if (officeErr) {
                                         console.error(`Error inserting office for ${p.bioguide_id}:`, officeErr.message);
                                         hasError = true;
                                         // Don't necessarily stop all inserts on one office error, but flag it
                                    }
                                }
                            );
                        });
                    }
                    
                    politiciansCompleted++;
                    checkCompletion(); // Check if all politicians are processed
                }
            );
        }); // End forEach
        
        // Commit transaction - This runs after the loop *starts* inserts, not after they finish
        // The finalization and callback handle completion.
        db.run('COMMIT', (commitErr) => {
             if (commitErr) {
                 console.error("Error committing transaction:", commitErr.message);
                 hasError = true;
             }
             // Finalize needs to happen *after* all inserts are truly done, handled in checkCompletion
        }); 
    });

    function checkCompletion() {
        if (politiciansCompleted === totalPoliticians) {
            console.log('Finalizing statements...');
            politicianStmt.finalize((finErr) => {
                 if(finErr) console.error("Error finalizing politician statement:", finErr.message); hasError = true; 
                 officeStmt.finalize((finErr2) => {
                     if(finErr2) console.error("Error finalizing office statement:", finErr2.message); hasError = true;
                     console.log(`Sample data processing finished ${hasError ? 'with errors' : 'successfully'}.`);
                     callback(hasError ? new Error("Errors occurred during sample data creation.") : null); // Signal completion
                 });
            });
        }
    }
}


// --- Utility Functions ---
function closeDb(db) {
    console.log('Closing database connection...');
    db.close((err) => {
        if (err) {
            console.error('Error closing database:', err);
        } else {
            console.log('Database connection closed.');
        }
    });
}

function logAndClose(db, message, error) {
    console.error(message, error.message);
    closeDb(db);
}

// --- Run Script ---
if (require.main === module) {
    setupFrontendDatabase();
}

module.exports = { setupFrontendDatabase }; // Export if needed elsewhere 