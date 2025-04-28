const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');
const sqlite3 = require('sqlite3').verbose();
const tweetService = require('../services/tweetService.js');
const { spawn } = require('child_process');
// const { getStandardizedName } = require('../utils/name-utils');

// --- BEGIN CONSOLE LOG REDIRECTION ---
const logFilePath = path.join(__dirname, '..', '..', 'console.log.txt');
let logStream; // Define logStream here to be accessible by IPC listener
try {
    logStream = fs.createWriteStream(logFilePath, { flags: 'w', encoding: 'utf8' });

    // Store original write methods
    const originalStdoutWrite = process.stdout.write.bind(process.stdout);
    const originalStderrWrite = process.stderr.write.bind(process.stderr);

    // Override stdout.write
    process.stdout.write = (chunk, encoding, callback) => {
        if (typeof chunk === 'string') {
            logStream.write(chunk, encoding);
        }
        return originalStdoutWrite(chunk, encoding, callback);
    };

    // Override stderr.write
    process.stderr.write = (chunk, encoding, callback) => {
        if (typeof chunk === 'string') {
            logStream.write(`[STDERR] ${chunk}`, encoding); // Prefix stderr messages
        }
        return originalStderrWrite(chunk, encoding, callback);
    };

    // Log unhandled rejections and uncaught exceptions to the file too
    process.on('uncaughtException', (error, origin) => {
        logStream.write(`\n[UNCAUGHT EXCEPTION] Origin: ${origin}\n${error.stack || error}\n`);
        // Optional: also log to original stderr before potentially exiting
        originalStderrWrite(`\n[UNCAUGHT EXCEPTION] Origin: ${origin}\n${error.stack || error}\n`);
        // Consider exiting the app depending on the error severity
        // process.exit(1); 
    });

    process.on('unhandledRejection', (reason, promise) => {
        logStream.write(`\n[UNHANDLED REJECTION] Promise: ${promise}\nReason: ${reason.stack || reason}\n`);
        originalStderrWrite(`\n[UNHANDLED REJECTION] Reason: ${reason.stack || reason}\n`);
    });

    console.log(`--- Console logging redirected to ${logFilePath} ---`);

} catch (error) {
    console.error('Failed to set up file logging:', error);
}
// --- END CONSOLE LOG REDIRECTION ---

// Keep a global reference of the window object
let mainWindow;
// Remove global db variable - connections managed by services or direct handlers
// let db; 

// Initialize the Twitter service
// const twitterService = new TwitterService();

// Create the browser window
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      // nodeIntegration: true, // Setting this to false is recommended with contextIsolation: true
      contextIsolation: true, // Enable contextIsolation for security
      preload: path.join(__dirname, '../preload.js')
    },
    icon: path.join(__dirname, '../assets/logo.png')
  });

  // Load the landing.html file initially
  mainWindow.loadFile(path.join(__dirname, '../renderer/landing.html'));

  // Open DevTools in development mode
  if (process.env.NODE_ENV === 'development') {
    mainWindow.webContents.openDevTools();
  }

  // Handle window being closed
  mainWindow.on('closed', function () {
    mainWindow = null;
  });
}

// Initialize the database connection
function initDatabase() {
  // Path to the database file created by setup-db.js
  const dbPath = path.join(__dirname, '..', '..', 'data', 'politicians.db'); 

  // Check if the database file exists
  if (!fs.existsSync(dbPath)) {
      console.error(`\n*** ERROR: Database file not found at expected location: ${dbPath}`);
      console.error("*** Please run 'npm run setup-db' first to create and populate the database.");
      // Option 1: Exit the app immediately
      app.quit(); 
      // Option 2: Reject the promise to prevent window creation (might show empty window briefly)
      // return Promise.reject(new Error(`Database not found at ${dbPath}`)); 
      // Option 3: Allow app to open but show an error dialog (more complex)
  }
  
  return new Promise((resolve, reject) => {
    console.log(`Attempting to connect to database at: ${dbPath}`);
    db = new sqlite3.Database(dbPath, sqlite3.OPEN_READWRITE, (err) => { // Specify READWRITE
      if (err) {
        console.error('Database connection error:', err.message);
        // Also quit if connection fails
        app.quit();
        reject(err);
        return;
      }
      console.log('Connected to the politicians database successfully.');
      
      // No need to create tables here, setup-db.js handles that
      resolve();
    });
  });
}

// Initialize the database connection (Only checks existence now, service manages connections)
function checkDatabaseExists() {
    const dbPath = path.join(__dirname, '..', '..', 'data', 'politicians.db');
    if (!fs.existsSync(dbPath)) {
        console.error(`\n*** ERROR: Database file not found: ${dbPath}`);
        console.error("*** Please run 'npm run setup-db' first.");
        app.quit();
        return false;
    }
    console.log(`Database file found at: ${dbPath}`);
    return true;
}

// This method will be called when Electron has finished initialization
app.whenReady().then(async () => {
    if (!checkDatabaseExists()) {
        return; // Quit if DB doesn't exist
    }

    try {
        // Initialize our tweet service (which connects DB, Twitter, AI)
        await tweetService.initializeService(); // Wait for init

        createWindow();

        app.on('activate', function () {
            if (BrowserWindow.getAllWindows().length === 0) createWindow();
        });

    } catch (err) {
        console.error('Failed to initialize services or create window:', err);
        app.quit();
    }
});

// Quit when all windows are closed, except on macOS
app.on('window-all-closed', function () {
    // Close service connections before quitting
    tweetService.closeDbConnection(); 
    if (process.platform !== 'darwin') app.quit();
});

// Added handler for graceful shutdown on other signals
app.on('will-quit', () => {
    console.log('App is quitting, closing service connections...');
    tweetService.closeDbConnection();
});

// IPC handlers for communication with the renderer process

// Helper for direct read-only DB access for politician/office handlers
let directDbConnection = null;
function getDirectDb() {
    if (!directDbConnection || !directDbConnection.open) { // Check if open
        const dbPath = path.join(__dirname, '..', '..', 'data', 'politicians.db');
        try {
            directDbConnection = new sqlite3.Database(dbPath, sqlite3.OPEN_READONLY, (err) => {
                if (err) {
                    console.error('Direct DB Connection Error:', err.message);
                    directDbConnection = null; // Reset on error
                } else {
                    console.log('Direct DB connection established (read-only).');
                }
            });
        } catch (err) {
             console.error('Direct DB Instantiation Error:', err.message);
             directDbConnection = null;
        }
    }
    return directDbConnection;
}

// Ensure direct connection is closed on quit
app.on('will-quit', () => {
    if (directDbConnection && directDbConnection.open) {
        directDbConnection.close((err) => {
             if (err) console.error('Error closing direct DB:', err.message);
             else console.log('Direct DB connection closed.');
             directDbConnection = null;
        });
    }
    // tweetService connection closed by its own handler added previously
    console.log('App is quitting, closing service connections...'); // Moved logging here for clarity
    tweetService.closeDbConnection(); // Ensure this is called
});

// Get all politicians (Use getDirectDb)
ipcMain.handle('get-politicians', async () => {
    console.log('Received IPC request: get-politicians');
    return new Promise((resolve, reject) => {
        const db = getDirectDb(); // Use the helper
        if (!db) {
            console.error('Direct DB connection failed for get-politicians');
            return reject(new Error('Direct DB connection failed for get-politicians'));
        }
        
        console.log('DB connection successful, executing politicians query...');
        
        const sql = `
          SELECT 
            p.*, 
            json_group_array(
              json_object('id', o.id, 'type', o.type, 'address', o.address, 'city', o.city, 'state', o.state, 'zip', o.zip, 'phone', o.phone, 'fax', o.fax)
            ) AS offices
          FROM politicians p
          LEFT JOIN offices o ON p.id = o.politician_id
          GROUP BY p.id
        `;
        
        db.all(sql, (err, rows) => {
            if (err) {
                console.error('Error fetching politicians:', err.message);
                reject(err);
                return;
            }
            
            console.log(`[get-politicians] Query successful, retrieved ${rows.length} politicians`);
            
            try {
                const politicians = rows.map(row => {
                    try {
                        // Parse the offices JSON string and filter out null entries
                        const offices = JSON.parse(row.offices);
                        row.offices = offices.filter(o => o.id !== null);
                    } catch (e) {
                        console.warn(`Failed to parse offices for politician ${row.id}: ${e.message}`);
                        row.offices = [];
                    }
                    return row;
                });
                
                console.log(`[get-politicians] Successfully processed ${politicians.length} politician records`);
                resolve(politicians);
            } catch (processingError) {
                console.error(`[get-politicians] Failed to process results: ${processingError.message}`);
                reject(processingError);
            }
        });
    });
});

// Get a politician by ID (Use getDirectDb)
ipcMain.handle('get-politician', async (event, id) => {
    return new Promise((resolve, reject) => {
        const db = getDirectDb(); // Use the helper
        if (!db) {
             return reject(new Error('Direct DB connection failed for get-politician'));
        }
        const sql = `
          SELECT 
            p.*,
            json_group_array(
              json_object('id', o.id, 'type', o.type, 'address', o.address, 'city', o.city, 'state', o.state, 'zip', o.zip, 'phone', o.phone, 'fax', o.fax)
            ) AS offices
          FROM politicians p
          LEFT JOIN offices o ON p.id = o.politician_id
          WHERE p.id = ?
          GROUP BY p.id
        `;
        db.get(sql, [id], (err, row) => {
            if (err) {
                console.error('Error fetching politician:', err.message);
                reject(err);
                return;
            }
            
            if (!row) {
                resolve(null);
                return;
            }
            
            try {
                 const offices = JSON.parse(row.offices);
                 row.offices = offices.filter(o => o.id !== null);
             } catch (e) { row.offices = []; }
            resolve(row);
        });
    });
});

// Search politicians (Use getDirectDb)
ipcMain.handle('search-politicians', async (event, params) => {
    return new Promise((resolve, reject) => {
        const db = getDirectDb(); // Use the helper
        if (!db) {
             return reject(new Error('Direct DB connection failed for search-politicians'));
        }
        
        // Extract searchTerm from params object and ensure it's a string
        const searchTerm = params?.searchTerm || '';
        
        const normalizedTerm = searchTerm.trim().toLowerCase();
        const pattern = `%${normalizedTerm}%`;
        const sql = `
          SELECT 
            p.*,
            json_group_array(
              json_object('id', o.id, 'type', o.type, 'address', o.address, 'city', o.city, 'state', o.state, 'zip', o.zip, 'phone', o.phone, 'fax', o.fax)
            ) AS offices
          FROM politicians p
          LEFT JOIN offices o ON p.id = o.politician_id
          WHERE LOWER(p.name) LIKE ? OR LOWER(p.state) LIKE ? OR LOWER(p.district) LIKE ? OR LOWER(p.party) LIKE ?
          GROUP BY p.id
        `;
        db.all(sql, [pattern, pattern, pattern, pattern], (err, rows) => {
            if (err) {
                console.error('Error searching politicians:', err.message);
                reject(err);
                return;
            }
            
            console.log(`[search-politicians] Found ${rows.length} results for term: "${normalizedTerm}"`);
            
            const politicians = rows.map(row => {
                try {
                    const offices = JSON.parse(row.offices);
                    row.offices = offices.filter(o => o.id !== null);
                } catch (e) { row.offices = []; }
                return row;
            });
            
            resolve(politicians);
        });
    });
});

// Get the latest tweet for a politician
ipcMain.handle('get-latest-tweet', async (event, politicianPK) => {
    console.log(`[IPC] Received get-latest-tweet for PK: ${politicianPK}`);
    try {
        const tweet = await tweetService.getLatestTweet(politicianPK);
        // The service now returns the tweet object directly or null
        return tweet; 
    } catch (error) {
        console.error(`[IPC] Error in get-latest-tweet for PK ${politicianPK}:`, error);
        // Propagate error to renderer to display message
        throw error; 
    }
});

// Analyze tweets for a politician
ipcMain.handle('analyze-tweets', async (event, politicianPK) => {
    console.warn(`[IPC] Received legacy analyze-tweets call for PK: ${politicianPK}. Forwarding to analyzeTweet service.`);
    try {
        // Just call the single tweet analysis for now
        const analysisResult = await tweetService.analyzeTweet(politicianPK);
        // We need to adapt the result format slightly if renderer.js expects metrics/summary directly
        return {
            summary: analysisResult.ai_analysis?.raw_response || "AI analysis failed or not available.",
            metrics: { /* Add dummy metrics or extract from analysis if needed */ }
        }; 
    } catch (error) {
        console.error(`[IPC] Error in legacy analyze-tweets for PK ${politicianPK}:`, error);
        throw error;
    }
});

// Analyze tweet using the service
ipcMain.handle('analyze-tweet', async (event, politicianPK) => {
    console.log(`[IPC] Received analyze-tweet for PK: ${politicianPK}`);
    try {
        const analysisResult = await tweetService.analyzeTweet(politicianPK);
        // Returns object: { tweet, financial_context, ai_analysis: { raw_response } }
        return analysisResult;
    } catch (error) {
        console.error(`[IPC] Error in analyze-tweet for PK ${politicianPK}:`, error);
        throw error; // Propagate error to renderer
    }
});

// --- BEGIN RENDERER LOG LISTENER ---
ipcMain.on('log-message', (event, logEntry) => {
    const { timestamp, level, message } = logEntry;
    const formattedMessage = `[Renderer][${level.toUpperCase()}] ${timestamp}: ${message}\n`;
    
    // Write to the log file stream if it's available
    if (logStream) {
        logStream.write(formattedMessage);
    } else {
        // Fallback if file stream failed
        console.log(`(Log Stream Error) ${formattedMessage}`);
    }
});
// --- END RENDERER LOG LISTENER ---

// --- BEGIN NEW PYTHON BRIDGE HANDLER ---
ipcMain.handle('python-bridge', async (event, command, ...args) => {
    console.log(`[IPC] Received python-bridge command: ${command}`, args);
    
    // Construct the absolute path to the Python script
    const scriptPath = path.join(__dirname, '..', '..', 'scripts', 'api_bridge.py');
    
    // Check if script exists
    if (!fs.existsSync(scriptPath)) {
        console.error(`[IPC Python Bridge] Error: Script not found at ${scriptPath}`);
        return JSON.stringify({
            timestamp: new Date().toISOString(),
            success: false,
            error: `Python bridge script not found at ${scriptPath}`
        });
    }
    
    // Arguments for the Python script: script path, command, then other args
    const processArgs = [scriptPath, command, ...args.map(String)]; // Ensure all args are strings
    
    console.log(`[IPC Python Bridge] Executing: python ${processArgs.join(' ')}`);
    
    return new Promise((resolve, reject) => {
        // Spawn the Python process
        const pythonProcess = spawn('python', processArgs);
        
        let stdoutData = '';
        let stderrData = '';
        
        // Collect stdout
        pythonProcess.stdout.on('data', (data) => {
            stdoutData += data.toString();
        });
        
        // Collect stderr
        pythonProcess.stderr.on('data', (data) => {
            stderrData += data.toString();
            console.error(`[IPC Python Bridge] stderr: ${data}`); // Log stderr immediately
        });
        
        // Handle process exit
        pythonProcess.on('close', (code) => {
            console.log(`[IPC Python Bridge] Python script exited with code ${code}`);
            
            if (code === 0) {
                console.log(`[IPC Python Bridge] stdout:
${stdoutData}`);
                // Attempt to parse stdout as JSON, but return raw if it fails
                try {
                    // The python script should already be formatting as JSON string
                    // We resolve with the raw string as the renderer expects JSON *string*
                    resolve(stdoutData.trim()); 
                } catch (parseError) {
                    console.error('[IPC Python Bridge] Error parsing stdout JSON:', parseError);
                    console.error('[IPC Python Bridge] Raw stdout:', stdoutData);
                    // Resolve with an error structure if parsing failed
                    resolve(JSON.stringify({
                        timestamp: new Date().toISOString(),
                        success: false,
                        error: 'Failed to parse Python script output.',
                        raw_output: stdoutData.trim()
                    }));
                }
            } else {
                console.error(`[IPC Python Bridge] Error executing script (code ${code}): ${stderrData}`);
                // Resolve with an error structure if the script failed
                resolve(JSON.stringify({
                    timestamp: new Date().toISOString(),
                    success: false,
                    error: `Python script failed with code ${code}.`,
                    stderr: stderrData.trim()
                }));
            }
        });
        
        // Handle spawn errors (e.g., python command not found)
        pythonProcess.on('error', (error) => {
            console.error('[IPC Python Bridge] Spawn error:', error);
            resolve(JSON.stringify({
                timestamp: new Date().toISOString(),
                success: false,
                error: `Failed to start Python script: ${error.message}`
            }));
        });
    });
});
// --- END NEW PYTHON BRIDGE HANDLER ---

// Add a simple diagnostic IPC handler for troubleshooting
ipcMain.handle('app:diagnostics', async (event, request) => {
    console.log(`[IPC] Received diagnostics request: ${JSON.stringify(request)}`);
    
    // Build diagnostic info
    const diagnosticInfo = {
        timestamp: new Date().toISOString(),
        electronVersion: process.versions.electron,
        nodeVersion: process.versions.node,
        platform: process.platform,
        arch: process.arch,
        request: request,
        dbConnectionAvailable: !!getDirectDb(),
        ipcChannels: ['get-politicians', 'get-politician', 'search-politicians', 'get-latest-tweet', 'analyze-tweet', 'app:diagnostics'],
    };
    
    // If requested, test database access
    if (request?.testDb) {
        try {
            const db = getDirectDb();
            if (db) {
                const testPromise = new Promise((resolve, reject) => {
                    db.get("SELECT COUNT(*) as count FROM politicians", (err, row) => {
                        if (err) {
                            diagnosticInfo.dbTest = { success: false, error: err.message };
                            reject(err);
                        } else {
                            diagnosticInfo.dbTest = { success: true, count: row.count };
                            resolve(row.count);
                        }
                    });
                });
                
                await testPromise;
            } else {
                diagnosticInfo.dbTest = { success: false, error: "Database connection not available" };
            }
        } catch (e) {
            diagnosticInfo.dbTest = { success: false, error: e.message };
        }
    }
    
    console.log(`[IPC] Diagnostic results: ${JSON.stringify(diagnosticInfo)}`);
    return diagnosticInfo;
});

// Helper for direct influencers DB access
function getInfluencersDb() {
    const dbPath = path.join(__dirname, '..', '..', 'data', 'influencers.db');
    try {
        const db = new sqlite3.Database(dbPath, sqlite3.OPEN_READONLY, (err) => {
            if (err) console.error('Direct DB Connection Error for influencers:', err.message);
            else console.log('Direct Influencers DB connection established (read-only).');
        });
        return db;
    } catch (e) {
        console.error('Error opening influencers DB:', e.message);
        return null;
    }
}

// Search influencers
ipcMain.handle('search-influencers', async (event, params) => {
    return new Promise((resolve, reject) => {
        const db = getInfluencersDb();
        if (!db) return reject(new Error('Direct DB connection failed for search-influencers'));
        const searchTerm = params?.searchTerm || '';
        const normalized = searchTerm.trim().toLowerCase();
        const pattern = `%${normalized}%`;
        const sql = `
          SELECT * FROM influencers
          WHERE LOWER(name) LIKE ?
             OR LOWER(platform) LIKE ?
             OR LOWER(outlet) LIKE ?
        `;
        db.all(sql, [pattern, pattern, pattern], (err, rows) => {
            if (err) {
                console.error('Error searching influencers:', err.message);
                reject(err);
                return;
            }
            resolve(rows);
        });
    });
}); 