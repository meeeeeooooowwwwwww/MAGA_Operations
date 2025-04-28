const fs = require('fs');
const path = require('path');

// Create cache directory relative to project root
const CACHE_DIR = path.join(__dirname, '..', 'cache');
if (!fs.existsSync(CACHE_DIR)) {
    fs.mkdirSync(CACHE_DIR, { recursive: true });
    console.log('Created cache directory:', CACHE_DIR);
}

// Create mock tweet data for Bernie Sanders
const bernietweetData = {
    id: 'mock_1234567890',
    text: "Just introduced a bill to improve healthcare for all Americans. It's time for Medicare for All.",
    created_at: new Date().toISOString(),
    metrics: {
        retweet_count: 3240,
        like_count: 12520,
        reply_count: 845
    },
    user: {
        screen_name: 'SenSanders'
    }
};

// Create mock analysis data for Bernie Sanders
const bernieAnalysisData = {
    tweet: bernietweetData,
    analysis: {
        sentiment: 'positive',
        topics: ['healthcare', 'legislation'],
        key_points: [
            'Just introduced a bill',
            'Improve healthcare for all Americans',
            'Time for Medicare for All'
        ],
        suggested_response: 'Thank you for your leadership on healthcare. This is important for our community.'
    }
};

// Create mock tweet data for AOC
const aocTweetData = {
    id: 'mock_9876543210',
    text: "Climate change is real, and we need to act now. Just voted for the Green New Deal to protect our environment.",
    created_at: new Date().toISOString(),
    metrics: {
        retweet_count: 5420,
        like_count: 18950,
        reply_count: 1235
    },
    user: {
        screen_name: 'RepAOC'
    }
};

// Create mock analysis data for AOC
const aocAnalysisData = {
    tweet: aocTweetData,
    analysis: {
        sentiment: 'positive',
        topics: ['environment', 'climate', 'legislation'],
        key_points: [
            'Climate change is real',
            'We need to act now',
            'Voted for the Green New Deal',
            'Protect our environment'
        ],
        suggested_response: 'Thank you for your commitment to fighting climate change. This is crucial for our future.'
    }
};

// Write mock data to files
try {
    fs.writeFileSync(path.join(CACHE_DIR, 'tweet_S000148.json'), JSON.stringify(bernietweetData, null, 2));
    fs.writeFileSync(path.join(CACHE_DIR, 'analysis_S000148.json'), JSON.stringify(bernieAnalysisData, null, 2));
    fs.writeFileSync(path.join(CACHE_DIR, 'tweet_O000172.json'), JSON.stringify(aocTweetData, null, 2));
    fs.writeFileSync(path.join(CACHE_DIR, 'analysis_O000172.json'), JSON.stringify(aocAnalysisData, null, 2));

    console.log('Created mock tweet and analysis data for Bernie Sanders (S000148) and AOC (O000172)');
    console.log('Data saved to cache directory:', CACHE_DIR);
} catch (error) {
    console.error('Error writing mock data files:', error);
} 