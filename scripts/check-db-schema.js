// Script to check database schema
const sqlite3 = require('sqlite3').verbose();
const path = require('path');

const dbPath = path.resolve(__dirname, '../data/politicians.db');

const db = new sqlite3.Database(dbPath, sqlite3.OPEN_READWRITE, (err) => {
    if (err) {
        console.error('Error opening database:', err.message);
        process.exit(1);
    }
    console.log(`Connected to the SQLite database: ${dbPath}`);
});

// Get list of all tables
db.all(`SELECT name FROM sqlite_master WHERE type='table' ORDER BY name`, [], (err, tables) => {
    if (err) {
        console.error('Error querying tables:', err.message);
        db.close();
        process.exit(1);
    }
    
    console.log('=== Database Tables ===');
    tables.forEach(table => {
        console.log(table.name);
    });
    
    // For each table, get its schema
    let completed = 0;
    tables.forEach(table => {
        db.all(`PRAGMA table_info(${table.name})`, [], (err, columns) => {
            if (err) {
                console.error(`Error getting schema for ${table.name}:`, err.message);
            } else {
                console.log(`\n=== Table: ${table.name} ===`);
                columns.forEach(col => {
                    console.log(`${col.name} (${col.type})${col.pk ? ' PRIMARY KEY' : ''}${col.notnull ? ' NOT NULL' : ''}`);
                });
            }
            
            completed++;
            if (completed === tables.length) {
                db.close(() => {
                    console.log('\nDatabase connection closed.');
                });
            }
        });
    });
});