const fs = require('fs');
const path = require('path');
const sqlite3 = require('sqlite3').verbose(); // Added for DB access
const { TwitterApi } = require('twitter-api-v2'); // Added Twitter library
const { GoogleGenerativeAI } = require('@google/generative-ai'); // Added Gemini SDK

// Define PROJECT_ROOT first
const PROJECT_ROOT = path.join(__dirname, '..', '..');

// Load .env variables using the defined PROJECT_ROOT
require('dotenv').config({ path: path.join(PROJECT_ROOT, '.env') });

// Database configuration
const DB_PATH = path.join(PROJECT_ROOT, 'data', 'politicians.db'); // Correct DB path

// Cache configuration (can be kept for analysis results)
const CACHE_DIR = path.join(PROJECT_ROOT, 'cache');
const CACHE_DURATION = 3600000; // 1 hour in milliseconds

// Create cache directory if it doesn't exist
if (!fs.existsSync(CACHE_DIR)) {
    fs.mkdirSync(CACHE_DIR, { recursive: true });
}

// --- Database Helper ---
let readOnlyDb = null; // Renamed for clarity

// --- Twitter API Client ---
let twitterClient = null;

// --- AI Client ---
let genAI = null;
let aiModel = null;

function getDbConnection() {
    if (!readOnlyDb || !readOnlyDb.open) {
        readOnlyDb = new sqlite3.Database(DB_PATH, sqlite3.OPEN_READONLY, (err) => {
            if (err) {
                console.error('Error connecting to read-only database:', err.message);
                readOnlyDb = null; // Ensure it's null on error
                throw new Error('Could not connect to the read-only database.');
            } else {
                console.log('Connected to the SQLite database (read-only).');
            }
        });
    }
    return readOnlyDb;
}

// Function to get a writeable DB connection (opens and closes as needed)
function getWriteDbConnection(callback) {
    const writeDb = new sqlite3.Database(DB_PATH, sqlite3.OPEN_READWRITE, (err) => {
        if (err) {
            console.error('Error connecting to writeable database:', err.message);
            callback(err, null);
        } else {
            console.log('Connected to the SQLite database (read-write).');
            callback(null, writeDb);
        }
    });
    return writeDb; // Returns the db instance for closing later
}

// Close DB connections
function closeDbConnection() {
    if (readOnlyDb && readOnlyDb.open) {
        readOnlyDb.close((err) => {
            if (err) console.error('Error closing read-only database:', err.message);
            else console.log('Read-only database connection closed.');
            readOnlyDb = null;
        });
    }
    // Write connection is opened/closed per transaction in storeTweetInDb
}

// Mock data removed
// const MOCK_HANDLES = { ... };

/**
 * Initialize - Initializes Twitter client, AI Client, and DB connection
 */
function initializeService() {
    // Initialize Twitter Client
    const bearerToken = process.env.TWITTER_BEARER_TOKEN;
    if (!bearerToken) {
        console.warn('*** WARNING: TWITTER_BEARER_TOKEN not found. Tweet fetching disabled. ***');
        twitterClient = null;
    } else {
        try {
            twitterClient = new TwitterApi(bearerToken).readOnly;
            console.log('Twitter API client initialized (read-only).');
        } catch (error) {
            console.error('Error initializing Twitter client:', error);
            twitterClient = null;
        }
    }

    // Initialize Gemini AI Client
    const geminiApiKey = process.env.GEMINI_API_KEY;
    if (!geminiApiKey) {
        console.warn('*** WARNING: GEMINI_API_KEY not found. AI analysis disabled. ***');
        genAI = null;
    } else {
        try {
            genAI = new GoogleGenerativeAI(geminiApiKey);
            aiModel = genAI.getGenerativeModel({ model: "gemini-pro"}); // Using gemini-pro
            console.log('Gemini AI client initialized (model: gemini-pro).');
        } catch (error) {
            console.error('Error initializing Gemini AI client:', error);
            genAI = null;
            aiModel = null;
        }
    }

    // Initialize DB Connection
    try {
        getDbConnection();
    } catch (dbError) {
        console.error('Failed to establish initial DB connection:', dbError);
    }

    console.log('Tweet Service Initialized.');
}

/**
 * Get Twitter handle for politician from the database using primary key ID.
 * @param {number} politicianPK - The primary key ID of the politician in the DB.
 * @returns {Promise<string|null>} - Twitter handle or null if not found
 */
async function getTwitterHandle(politicianPK) {
    return new Promise((resolve, reject) => {
        const dbConn = getDbConnection();
        // Query by primary key 'id' instead of 'bioguide_id'
        const sql = `SELECT twitter, bioguide_id FROM politicians WHERE id = ?`;

        dbConn.get(sql, [politicianPK], (err, row) => {
            if (err) {
                console.error(`Error fetching Twitter handle from DB for ID ${politicianPK}:`, err.message);
                reject(new Error('Database error fetching Twitter handle.'));
            } else {
                if (row && row.twitter) {
                    console.log(`Found handle for ID ${politicianPK}: ${row.twitter}`);
                    // Return both handle and bioguide_id for potential use later
                    resolve({ handle: row.twitter, bioguide_id: row.bioguide_id });
                } else {
                    console.log(`No Twitter handle found in DB for ID ${politicianPK}`);
                    resolve(null); // Resolve with null if not found
                }
            }
        });
    });
}

/**
 * Get the latest tweet for a politician using their primary key ID.
 * @param {number} politicianPK - The primary key ID of the politician.
 * @returns {Promise<Object|null>} - Tweet data object or null on error/not found
 */
async function getLatestTweet(politicianPK) {
    console.log(`Attempting to get latest tweet for politician ID: ${politicianPK}...`);
    const handleInfo = await getTwitterHandle(politicianPK);

    if (!handleInfo || !handleInfo.handle) {
        console.error(`No Twitter handle found for politician ID ${politicianPK}. Cannot fetch tweet.`);
        return null;
    }
    const twitterHandle = handleInfo.handle;
    const bioguideId = handleInfo.bioguide_id; // Keep bioguide_id for storage

    if (!twitterClient) {
        console.error('Twitter client not initialized (check TWITTER_BEARER_TOKEN). Cannot fetch tweet.');
        // Optionally fall back to mock data or throw an error
        // return getMockTweet(twitterHandle); 
        return null;
    }

    // --- Implement Live Twitter Fetching ---
    let fetchedTweetData = null;
    try {
        console.log(`Fetching latest tweet for handle: @${twitterHandle}`);
        // Get user ID from handle first (needed for timeline endpoint)
        const user = await twitterClient.v2.userByUsername(twitterHandle);
        if (!user || !user.data) {
            console.error(`Could not find Twitter user with handle: @${twitterHandle}`);
            return null;
        }
        const userId = user.data.id;
        console.log(`Found user ID for @${twitterHandle}: ${userId}`);

        // Fetch the most recent tweet(s) from the user's timeline
        // Exclude replies and retweets, get basic metrics
        const timeline = await twitterClient.v2.userTimeline(userId, {
            max_results: 5, // Fetch a few in case the absolute latest is a reply/RT
            exclude: ['replies', 'retweets'],
            'tweet.fields': ['created_at', 'public_metrics', 'entities']
        });

        if (!timeline || !timeline.data || timeline.data.data.length === 0) {
            console.log(`No recent original tweets found for @${twitterHandle} (ID: ${userId}).`);
            return null;
        }

        // The first tweet in the response is the latest eligible one
        fetchedTweetData = timeline.data.data[0];
        console.log(`Successfully fetched tweet ID: ${fetchedTweetData.id}`);

        // Map the V2 data structure slightly for consistency if needed downstream
        // (e.g., add a user object similar to mock/v1)
        fetchedTweetData.user = { screen_name: twitterHandle }; // Add handle back for convenience
        fetchedTweetData.metrics = fetchedTweetData.public_metrics; // Standardize metrics field name

    } catch (error) {
        console.error(`Error fetching tweet from Twitter API for @${twitterHandle}:`, error);
        // Handle specific errors (rate limits, suspended accounts, etc.) if needed
        // For now, just return null on error
        return null;
    }

    if (fetchedTweetData) {
        // Pass politicianPK AND bioguideId to storage function
        console.log(`Tweet fetched: ${fetchedTweetData.id}. Storing in DB...`);
        await storeTweetInDb(politicianPK, bioguideId, fetchedTweetData);

        // --- TODO: Implement Caching (Optional) ---
        // const cacheFile = path.join(CACHE_DIR, `tweet_${politicianPK}.json`);
        // fs.writeFileSync(cacheFile, JSON.stringify(fetchedTweetData));

        return fetchedTweetData;
    } else {
        console.error(`Failed to fetch tweet for handle: ${twitterHandle}`);
        return null;
    }
}

/**
 * Stores a fetched tweet in the database.
 * Uses politician primary key and bioguide_id.
 * @param {number} politicianPK - The primary key ID of the politician.
 * @param {string} bioguideId - The bioguide ID of the politician.
 * @param {Object} tweetData - The fetched tweet object from Twitter API v2.
 * @returns {Promise<void>}
 */
async function storeTweetInDb(politicianPK, bioguideId, tweetData) {
    console.log(`Attempting to store tweet ${tweetData.id} for Politician ID: ${politicianPK} (Bioguide: ${bioguideId}) in DB.`);

    // 1. Map V2 tweet object to DB schema
    const tweetId = tweetData.id;
    const text = tweetData.text;
    const createdAt = new Date(tweetData.created_at).toISOString();
    const retweetCount = tweetData.public_metrics?.retweet_count ?? 0;
    const favoriteCount = tweetData.public_metrics?.like_count ?? 0;
    const hashtags = JSON.stringify(tweetData.entities?.hashtags?.map(h => h.tag) || []);
    const mentions = JSON.stringify(tweetData.entities?.mentions?.map(m => m.username) || []);

    return new Promise((resolve, reject) => {
        getWriteDbConnection(async (err, writeDb) => {
            if (err) {
                return reject(new Error('Failed to get writeable DB connection for storing tweet.'));
            }
            try {
                // 2. Prepare INSERT OR IGNORE statement (Politician ID is now passed directly)
                const sql = `
                    INSERT OR IGNORE INTO tweets
                    (politician_id, bioguide_id, tweet_id, text, created_at, retweet_count, favorite_count, hashtags, mentions)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                `;
                const params = [
                    politicianPK, // Use the passed primary key
                    bioguideId,   // Store bioguide_id as well
                    tweetId, text, createdAt,
                    retweetCount, favoriteCount, hashtags, mentions
                ];

                // 3. Execute statement
                await new Promise((resolveInsert, rejectInsert) => {
                    writeDb.run(sql, params, function(insertErr) {
                        if (insertErr) {
                            rejectInsert(new Error(`DB error inserting tweet ${tweetId}: ${insertErr.message}`));
                        } else {
                            if (this.changes > 0) {
                                console.log(`Successfully inserted tweet ${tweetId} for Politician ID: ${politicianPK}.`);
                            } else {
                                console.log(`Tweet ${tweetId} for Politician ID: ${politicianPK} already exists.`);
                            }
                            resolveInsert();
                        }
                    });
                });

                // 4. Close the writeable connection
                writeDb.close((closeErr) => {
                    if (closeErr) console.error('Error closing writeable database:', closeErr.message);
                    else console.log('Writeable database connection closed (after tweet store).');
                });
                resolve();
            } catch (error) {
                console.error('Error during storeTweetInDb:', error);
                // Ensure DB is closed even if an error occurred mid-process
                if (writeDb && writeDb.open) {
                    writeDb.close((closeErr) => {
                        if (closeErr) console.error('Error closing writeable database after error:', closeErr.message);
                    });
                }
                reject(error); // Propagate the error
            }
        });
    });
}

/**
 * Analyze a tweet for a politician using AI
 * @param {number} politicianPK - The primary key ID of the politician.
 * @returns {Promise<Object>} - Analysis data including AI response
 */
async function analyzeTweet(politicianPK) {
    console.log(`Analyzing tweet for Politician ID: ${politicianPK}`);
    if (!aiModel) { // Check if AI client is initialized
        throw new Error('AI Client not initialized. Cannot perform analysis. Check GEMINI_API_KEY.');
    }
    try {
        // --- Caching --- (can remain based on PK)
        const cacheFile = path.join(CACHE_DIR, `analysis_${politicianPK}.json`);
        if (fs.existsSync(cacheFile)) {
            const stats = fs.statSync(cacheFile);
            const age = Date.now() - stats.mtimeMs;
            if (age < CACHE_DURATION) {
                console.log(`Using cached analysis for ${politicianPK}`);
                const cachedAnalysis = JSON.parse(fs.readFileSync(cacheFile, 'utf-8'));
                return cachedAnalysis;
            }
        }

        // 1. Get the latest tweet
        const tweet = await getLatestTweet(politicianPK);
        if (!tweet) {
            throw new Error('Could not retrieve tweet for analysis.');
        }

        // 2. Fetch Financial Data
        const financialData = await getFinancialData(politicianPK);

        // 3. Generate AI Analysis
        console.log(`Generating AI analysis for tweet ID: ${tweet.id}`);
        const analysisResult = await generateAiAnalysis(tweet, financialData);

        const finalResult = {
            tweet: tweet,
            financial_context: financialData, // Keep full context for potential UI display
            ai_analysis: analysisResult // Contains the AI response text
        };

        // Cache the final AI analysis result
        fs.writeFileSync(cacheFile, JSON.stringify(finalResult, null, 2));
        console.log(`Cached new analysis for ${politicianPK}`);

        return finalResult;

    } catch (error) {
        console.error(`Error analyzing tweet for Politician ID ${politicianPK}:`, error);
        // Add more specific error handling if needed (e.g., AI API errors)
        if (error.message.includes('AI Client')) { // Propagate AI init error
             throw error;
        }
        // Consider returning a structured error for other issues
        throw new Error(`Failed to analyze tweet: ${error.message}`); 
    }
}

/**
 * Fetches financial data (donations, assets, transactions, associations) 
 * from DB for a given politician using their primary key ID.
 * @param {number} politicianPK - The primary key ID of the politician.
 * @returns {Promise<Object>} - Object containing arrays of data for each category.
 */
async function getFinancialData(politicianPK) {
    console.log(`Fetching financial data for Politician ID: ${politicianPK}.`);
    let bioguide_id;

    try {
        // 1. Get bioguide_id from politician primary key
        const politicianRow = await new Promise((resolve, reject) => {
            const dbConn = getDbConnection();
            dbConn.get('SELECT bioguide_id FROM politicians WHERE id = ?', [politicianPK], (err, row) => {
                if (err) reject(new Error(`DB error fetching bioguide_id for PK ${politicianPK}: ${err.message}`));
                else if (!row) reject(new Error(`Politician not found for PK ${politicianPK}`));
                else resolve(row);
            });
        });
        bioguide_id = politicianRow.bioguide_id;
        console.log(`(Financial Data) Found bioguide_id: ${bioguide_id} for PK: ${politicianPK}`);

        // 2. Fetch data from financial tables using bioguide_id
        const dbConn = getDbConnection(); // Use the shared read-only connection

        const fetchData = (table, id) => {
            return new Promise((resolve, reject) => {
                // Basic query - consider adding LIMIT or date ranges for performance
                // Also consider selecting specific columns instead of *
                const sql = `SELECT * FROM ${table} WHERE politician_bioguide_id = ? ORDER BY date DESC, report_year DESC, scraped_at DESC`;
                dbConn.all(sql, [id], (err, rows) => {
                    if (err) {
                        console.error(`Error fetching data from ${table} for ${id}:`, err.message);
                        // Resolve with empty array on error for robustness, or reject
                        resolve([]); 
                    } else {
                        console.log(`Fetched ${rows.length} rows from ${table} for ${id}`);
                        resolve(rows);
                    }
                });
            });
        };

        // Fetch all financial data concurrently
        const [donations, assets, transactions, company_associations] = await Promise.all([
            fetchData('donations', bioguide_id),
            fetchData('assets', bioguide_id),
            fetchData('transactions', bioguide_id),
            fetchData('company_associations', bioguide_id)
        ]);

        return {
            donations: donations || [],
            assets: assets || [],
            transactions: transactions || [],
            company_associations: company_associations || []
        };

    } catch (error) {
        console.error(`Error fetching financial data for Politician ID ${politicianPK}:`, error);
        // Return empty structure on error
        return { donations: [], assets: [], transactions: [], company_associations: [] };
    }
}

/**
 * Generates analysis using the Gemini AI model.
 * @param {Object} tweet - The tweet object.
 * @param {Object} financialData - Object containing donations, assets, etc.
 * @returns {Promise<Object>} - Object containing the AI response text.
 */
async function generateAiAnalysis(tweet, financialData) {
    if (!aiModel) {
        throw new Error('AI model not available for analysis.');
    }

    // --- Construct the Prompt --- 
    const prompt = `
        Analyze the following tweet from a politician:
        Tweet Text: "${tweet.text}"
        Date: ${new Date(tweet.created_at).toLocaleDateString()}

        Contextual Financial Information (Summarized - Top 3 Recent):
        - Donations (${financialData.donations?.length ?? 0} total): ${summarizeFinancials(financialData.donations, 'donation')}
        - Assets (${financialData.assets?.length ?? 0} total): ${summarizeFinancials(financialData.assets, 'asset')}
        - Transactions (${financialData.transactions?.length ?? 0} total): ${summarizeFinancials(financialData.transactions, 'transaction')}
        - Associations (${financialData.company_associations?.length ?? 0} total): ${summarizeFinancials(financialData.company_associations, 'association')}

        Task:
        1.  **Classification:** Classify the tweet\'s primary statement as either an \'Opinion\' or a \'Claim/Fact\'.
        2.  **Summary:** Briefly summarize the main point of the tweet.
        3.  **Evaluation:** Evaluate the tweet\'s message. Is it generally positive, negative, or neutral in tone? Briefly comment on its substance (e.g., is it specific, vague, emotional?).
        4.  **Financial Connection:** Based *only* on the provided financial context, identify any potential connections, conflicts of interest, or supporting/contradictory financial activities related to the tweet\'s topic. State clearly if no connections are apparent from the provided data.
        5.  **Legal Relevance (If Classification is Claim/Fact):** If the tweet was classified as a Claim/Fact, briefly state whether the claim relates to legal, legislative, or regulatory matters based on its content.
        6.  **Supportive Response:** Generate one brief, professional response (1-2 sentences) suitable for social media that generally supports or agrees with the tweet\'s sentiment or premise.
        7.  **Critical Response:** Generate one brief, professional but critical response (1-2 sentences) suitable for social media that questions or challenges the tweet\'s sentiment or premise. **If potential financial connections/conflicts or relevant legal context were identified in steps 4 or 5, incorporate that specific context into this critical response.**

        Format the output clearly using Markdown headings for each section exactly as follows:
        ### Classification
        [Your Classification: Opinion or Claim/Fact]
        ### Summary
        [Your Summary]
        ### Evaluation
        [Your Evaluation]
        ### Financial Connection
        [Your Analysis of Financial Connections]
        ### Legal Relevance
        [Your Analysis of Legal Relevance - include only if classified as Claim/Fact]
        ### Supportive Response
        [Your Supportive Response]
        ### Critical Response
        [Your Critical Response]
    `;

    try {
        console.log('Sending refined prompt to Gemini API...');
        // console.log('Prompt:', prompt); // Uncomment for debugging
        const result = await aiModel.generateContent(prompt);
        const response = await result.response;
        const aiText = response.text();
        console.log('Received structured response from Gemini API.');
        // console.log('AI Response:', aiText); // Uncomment for debugging

        return {
            raw_response: aiText // Return the full text response with Markdown headings
        };
    } catch (error) {
        console.error('Error calling Gemini API:', error);
        // Handle specific API errors if possible
        let errorMessage = `AI analysis failed: ${error.message}`;
        if (error.response && error.response.promptFeedback) {
             errorMessage += ` (Prompt Feedback: ${JSON.stringify(error.response.promptFeedback)})`;
        }
        throw new Error(errorMessage);
    }
}

/** Helper function to summarize financial data for the prompt */
function summarizeFinancials(items, type) {
    if (!items || items.length === 0) return "None reported.";
    // Take top 2-3 recent items for brevity
    const recentItems = items.slice(0, 3);
    switch (type) {
        case 'donation':
            return recentItems.map(d => `$${d.amount} from ${d.donor_name || 'N/A'} (${d.date})`).join('; ');
        case 'asset':
            return recentItems.map(a => `${a.asset_name} (Value: $${a.value_range_min}-$${a.value_range_max}, Reported: ${a.report_year})`).join('; ');
        case 'transaction':
            return recentItems.map(t => `${t.transaction_type} ${t.asset_name} (Value: $${t.value_range_min}-$${t.value_range_max}, Date: ${t.transaction_date})`).join('; ');
        case 'association':
            return recentItems.map(c => `${c.role} at ${c.company_name} (Since: ${c.start_date || 'N/A'})`).join('; ');
        default:
            return `${items.length} items.`;
    }
}

// Export the key functions for the Electron app to use
module.exports = {
    initializeService,
    getTwitterHandle,
    getLatestTweet,
    analyzeTweet,
    getFinancialData,
    closeDbConnection
};

// Example of how to initialize (e.g., in main.js or renderer setup)
// initializeService();

// Example of how to close connection (e.g., on app 'will-quit' event)
// closeDbConnection();