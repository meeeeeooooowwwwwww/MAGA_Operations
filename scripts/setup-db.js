const sqlite3 = require('sqlite3').verbose();
const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');

// Paths relative to project root
const PROJECT_ROOT = path.join(__dirname, '..'); 
const DATA_DIR = path.join(PROJECT_ROOT, 'data');
const DB_PATH = path.join(DATA_DIR, 'politicians.db');
const LEGISLATORS_YAML_PATH = path.join(DATA_DIR, 'legislators-current.yaml');
const SOCIAL_MEDIA_YAML_PATH = path.join(DATA_DIR, 'legislators-social-media.yaml');

// --- Main Setup Function ---
function setupDatabase() {
    console.log('Setting up politicians database for frontend...');
    
    // Check for required input file
    if (!fs.existsSync(LEGISLATORS_YAML_PATH)) {
        console.error(`\n*** ERROR: Required input file not found: ${LEGISLATORS_YAML_PATH}`);
        console.error("*** Please ensure 'legislators-current.yaml' exists in the data directory.");
        process.exit(1); // Exit with error
    }
    console.log(`Found required input file: ${LEGISLATORS_YAML_PATH}`);
    
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
            process.exit(1); // Stop if we can't delete the old one
        }
    }
    
    // Connect to/create the database
    const db = new sqlite3.Database(DB_PATH, (err) => {
        if (err) {
            console.error('Error creating/connecting to database:', err);
            process.exit(1);
        }
        console.log(`Connected to/created database: ${DB_PATH}`);
        
        createSchemaAndImportData(db);
    });
}

// --- Schema Creation and Data Import ---
function createSchemaAndImportData(db) {
    db.serialize(() => {
        console.log('Creating tables (frontend schema)...');
        
        // 1. Create Politicians Table
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
            if (err) { logAndClose(db, 'Error creating politicians table', err, true); return; }
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
                if (err) { logAndClose(db, 'Error creating offices table', err, true); return; }
                console.log('Offices table created.');
                
                // 3. Create Tweets Table (Structure only)
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
                     if (err) { logAndClose(db, 'Error creating tweets table', err, true); return; }
                     console.log('Tweets table created.');

                     // 4. Import from YAML
                     console.log('Importing data from YAML files...');
                     importFromYaml(db, (importErr) => { 
                        if (importErr) {
                             // Error logged in import function
                            closeDb(db, true); // Close DB on error
                        } else {
                            console.log('Data import completed successfully.');
                            closeDb(db, false); // Close DB after successful import
                        }
                     });
                }); // End Tweets
            }); // End Offices
        }); // End Politicians
    }); // End db.serialize
}

// --- Data Import from YAML ---
function importFromYaml(db, callback) {
    let hasError = false;
    try {
        const legislatorsFile = fs.readFileSync(LEGISLATORS_YAML_PATH, 'utf8');
        const legislatorsData = yaml.load(legislatorsFile);
        console.log(`Loaded ${legislatorsData.length} records from ${path.basename(LEGISLATORS_YAML_PATH)}.`);

        // Load social media YAML if it exists
        let socialMediaMap = {};
        if (fs.existsSync(SOCIAL_MEDIA_YAML_PATH)) {
            try {
                const socialMediaFile = fs.readFileSync(SOCIAL_MEDIA_YAML_PATH, 'utf8');
                const socialMediaData = yaml.load(socialMediaFile);
                socialMediaData.forEach(entry => {
                    if (entry.id && entry.id.bioguide) {
                        socialMediaMap[entry.id.bioguide] = entry.social || {};
                    }
                });
                console.log(`Loaded social media map for ${Object.keys(socialMediaMap).length} legislators from ${path.basename(SOCIAL_MEDIA_YAML_PATH)}.`);
            } catch (socialErr) {
                console.warn(`\n*** WARNING: Error reading or parsing social media file ${SOCIAL_MEDIA_YAML_PATH}:`, socialErr.message);
                console.warn("*** Proceeding without social media data.");
                socialMediaMap = {}; // Reset map on error
            }
        } else {
            console.warn(`\n*** WARNING: Social media file not found at ${SOCIAL_MEDIA_YAML_PATH}.`);
            console.warn("*** Social media fields will be empty.");
            socialMediaMap = {};
        }
        
        // Prepare statements
        const politicianStmt = db.prepare(`
            INSERT INTO politicians (bioguide_id, name, state, district, party, level, chamber, office, phone, email, website, twitter, facebook, instagram, youtube, linkedin, bio)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        `);
        const officeStmt = db.prepare(`
            INSERT INTO offices (politician_id, bioguide_id, type, address, city, state, zip, phone, fax)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        `);
        
        let politicianInsertCount = 0;
        let officeInsertCount = 0;
        let processedCount = 0;
        const totalToProcess = legislatorsData.length;
        const officesToInsert = []; // Temporary array: { politicianRowId, bioguideId, officeData } 

        // Begin a single transaction for the entire import process
        db.run('BEGIN TRANSACTION', (beginErr) => {
            if (beginErr) {
                console.error("Error beginning transaction:", beginErr.message);
                callback(beginErr);
                return;
            }
            
            console.log('Transaction started. Beginning imports...');
            
            // Stage 1: Insert Politicians and collect office data
            console.log('Starting Stage 1: Inserting politicians...');
            
            legislatorsData.forEach(leg => {
                if (!leg.id || !leg.id.bioguide) {
                    console.warn('Skipping record due to missing bioguide ID:', leg.name);
                    processedCount++;
                    checkStage1Completion();
                    return;
                }
                const bioguideId = leg.id.bioguide;
                const socialData = socialMediaMap[bioguideId] || {}; 
                
                // --- Extract Politician Data ---
                let name = 'Unknown';
                if (leg.name?.official_full) { name = leg.name.official_full; } 
                else if (leg.name?.first && leg.name?.last) { name = `${leg.name.first} ${leg.name.last}`; }
                const currentTerm = leg.terms && leg.terms.length > 0 ? leg.terms[leg.terms.length - 1] : {};
                const state = currentTerm.state || null;
                const party = currentTerm.party || null;
                const type = currentTerm.type || null;
                const level = type === 'sen' ? 'federal_senate' : (type === 'rep' ? 'federal_house' : null);
                const chamber = type === 'sen' ? 'senate' : (type === 'rep' ? 'house' : null);
                const district = type === 'rep' ? String(currentTerm.district ?? '') : null;
                const title = type === 'sen' ? 'Senator' : (type === 'rep' ? 'Representative' : null);
                const phone = currentTerm.phone || null;
                const email = null; 
                const website = currentTerm.url || null;
                const bio = leg.bio ? JSON.stringify(leg.bio) : null;
                const twitter = socialData.twitter || null;
                const facebook = socialData.facebook || null;
                const instagram = socialData.instagram || null;
                const youtube = socialData.youtube || null;
                const linkedin = socialData.linkedin || null;

                politicianStmt.run(
                    bioguideId, name, state, district, party, level, chamber, title, 
                    phone, email, website, twitter, facebook, instagram, youtube, linkedin, bio,
                    function(err) { 
                        if (err) {
                            console.error(`Error inserting politician ${bioguideId} (${name}):`, err.message);
                            hasError = true;
                        } else {
                            const politicianRowId = this.lastID;
                            politicianInsertCount++;
                            // Collect office data for Stage 2
                            if (leg.terms) {
                                leg.terms.forEach(term => {
                                     if (term.address) {
                                        let officeType = term.type || 'unknown'; 
                                        if (term.office && term.office.toLowerCase().includes('district')) { officeType = 'district'; }
                                        if (term.office && term.office.toLowerCase().includes('capitol')) { officeType = 'capitol'; }
                                        
                                        officesToInsert.push({
                                            politicianRowId: politicianRowId,
                                            bioguideId: bioguideId,
                                            type: officeType,
                                            address: term.address || null,
                                            state: term.state || null, 
                                            phone: term.phone || null,
                                            fax: term.fax || null
                                        });
                                    }
                                });
                            }
                        }
                        processedCount++;
                        checkStage1Completion(); 
                    }
                ); // End politicianStmt.run
            }); // End legislatorsData.forEach
        }); // End BEGIN TRANSACTION

        // Function to check completion of Stage 1 (Politician Inserts)
        function checkStage1Completion() {
            if (processedCount === totalToProcess) {
                console.log('Finished Stage 1. Politicians processed/inserted.');
                // Don't commit yet, proceed to Stage 2
                runStage2_InsertOffices();
            }
        }

        // Stage 2: Insert Offices
        function runStage2_InsertOffices() {
            console.log(`Starting Stage 2: Inserting ${officesToInsert.length} collected office records...`);
            let officesAttempted = 0;
            const totalOffices = officesToInsert.length;

            if (totalOffices === 0) {
                 console.log('No offices found to insert.');
                 finalizeImport();
                 return;
            }

            officesToInsert.forEach(o => {
                officeStmt.run(
                    o.politicianRowId, o.bioguideId, o.type, o.address, null, o.state, null, o.phone, o.fax,
                    (officeErr) => {
                        if (officeErr) {
                            console.error(`Error inserting office for ${o.bioguideId} (${o.address}):`, officeErr.message);
                            hasError = true; 
                        } else {
                            officeInsertCount++;
                        }
                        officesAttempted++;
                        if (officesAttempted === totalOffices) {
                             console.log('Finished Stage 2. Offices processed/inserted.');
                             finalizeImport();
                        }
                    }
                );
            });
        }
        
        // Stage 3: Finalize Transaction and Statements
        function finalizeImport() {
            console.log('Finalizing transaction and statements...');
            db.run('COMMIT', (commitErr) => {
                if (commitErr) {
                    console.error("Error committing transaction:", commitErr.message);
                    hasError = true;
                } else {
                    console.log('Transaction committed.')
                }

                politicianStmt.finalize((finErr) => {
                    if(finErr) {
                        console.error("Error finalizing politician statement:", finErr.message);
                        hasError = true;
                    }
                    officeStmt.finalize((finErr2) => {
                        if(finErr2) {
                            console.error("Error finalizing office statement:", finErr2.message);
                            hasError = true;
                        }
                        console.log(`--- Import Summary ---`);
                        console.log(` YAML Records Processed: ${processedCount}`);
                        console.log(` Politicians Inserted: ${politicianInsertCount}`);
                        console.log(` Office Records Inserted: ${officeInsertCount} (out of ${officesToInsert.length} attempted)`);
                        console.log(` Import finished ${hasError ? 'with errors' : 'successfully'}.`);
                        callback(hasError ? new Error("Errors occurred during YAML import.") : null); 
                    });
                });
            });
        }

    } catch (error) {
        console.error('FATAL Error reading or parsing YAML file(s):', error);
        callback(error); // Signal completion with error
    }
}

// --- Utility Functions ---
function closeDb(db, hadError) {
    console.log(`Closing database connection ${hadError ? 'after errors' : 'normally'}...`);
    db.close((err) => {
        if (err) {
            console.error('Error closing database:', err.message);
        } else {
            console.log('Database connection closed.');
        }
    });
}

function logAndClose(db, message, error, exit) {
    console.error(message, error.message);
    closeDb(db, true);
    if (exit) process.exit(1);
}

// --- Run Script ---
if (require.main === module) {
    setupDatabase();
}

module.exports = { setupDatabase }; 