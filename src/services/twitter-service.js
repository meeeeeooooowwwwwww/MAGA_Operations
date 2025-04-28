const axios = require('axios');
const crypto = require('crypto');
const oauth1a = require('oauth-1.0a');

// This is a simplified Twitter API service
class TwitterService {
  constructor() {
    // Twitter API credentials would be configured here in a real app
    this.apiKey = process.env.TWITTER_API_KEY || '';
    this.apiSecret = process.env.TWITTER_API_SECRET || '';
    this.accessToken = process.env.TWITTER_ACCESS_TOKEN || '';
    this.accessTokenSecret = process.env.TWITTER_ACCESS_TOKEN_SECRET || '';
    
    // Configure OAuth
    this.oauth = oauth1a({
      consumer: { key: this.apiKey, secret: this.apiSecret },
      signature_method: 'HMAC-SHA1',
      hash_function(base_string, key) {
        return crypto
          .createHmac('sha1', key)
          .update(base_string)
          .digest('base64');
      }
    });
  }

  /**
   * Get authorization header for Twitter API requests
   * @param {string} url - The API endpoint URL
   * @param {string} method - HTTP method (GET, POST, etc.)
   * @returns {Object} Headers for the request
   */
  getAuthHeader(url, method) {
    const token = {
      key: this.accessToken,
      secret: this.accessTokenSecret
    };

    const authHeader = this.oauth.toHeader(
      this.oauth.authorize({
        url,
        method
      }, token)
    );

    return {
      ...authHeader,
      'Content-Type': 'application/json'
    };
  }

  /**
   * Get the latest tweet from a user
   * @param {string} username - Twitter username
   * @returns {Promise<Object>} - Latest tweet object or null
   */
  async getLatestTweet(username) {
    try {
      // Check if API credentials are configured
      if (!this.apiKey || !this.apiSecret) {
        console.warn('Twitter API credentials not configured');
        return this.getMockTweet(username);
      }

      // In a real app, this would use the Twitter API v2 endpoint
      // https://api.twitter.com/2/users/by/username/{username}/tweets
      const url = `https://api.twitter.com/1.1/statuses/user_timeline.json?screen_name=${username}&count=1&tweet_mode=extended`;
      
      const response = await axios.get(url, {
        headers: this.getAuthHeader(url, 'GET')
      });

      if (response.data && response.data.length > 0) {
        return response.data[0];
      }
      
      return null;
    } catch (error) {
      console.error('Error fetching latest tweet:', error.message);
      // If API call fails, return mock data in development
      if (process.env.NODE_ENV === 'development') {
        return this.getMockTweet(username);
      }
      return null;
    }
  }

  /**
   * Get recent tweets from a user
   * @param {string} username - Twitter username
   * @param {number} count - Number of tweets to retrieve
   * @returns {Promise<Array>} - Array of tweet objects
   */
  async getRecentTweets(username, count = 10) {
    try {
      // Check if API credentials are configured
      if (!this.apiKey || !this.apiSecret) {
        console.warn('Twitter API credentials not configured');
        return this.getMockTweets(username, count);
      }

      // In a real app, this would use the Twitter API v2 endpoint
      const url = `https://api.twitter.com/1.1/statuses/user_timeline.json?screen_name=${username}&count=${count}&tweet_mode=extended`;
      
      const response = await axios.get(url, {
        headers: this.getAuthHeader(url, 'GET')
      });

      if (response.data && response.data.length > 0) {
        return response.data;
      }
      
      return [];
    } catch (error) {
      console.error('Error fetching tweets:', error.message);
      // If API call fails, return mock data in development
      if (process.env.NODE_ENV === 'development') {
        return this.getMockTweets(username, count);
      }
      return [];
    }
  }

  /**
   * Generate mock tweet data for development/testing
   * @param {string} username - Twitter username
   * @returns {Object} - Mock tweet object
   */
  getMockTweet(username) {
    const timestamp = new Date().toISOString();
    return {
      id_str: `mock_${Date.now()}`,
      created_at: timestamp,
      text: `This is a mock tweet for ${username}. When in production, actual tweets will be shown here. #MAGA #America`,
      full_text: `This is a mock tweet for ${username}. When in production, actual tweets will be shown here. #MAGA #America`,
      retweet_count: Math.floor(Math.random() * 1000),
      favorite_count: Math.floor(Math.random() * 5000),
      user: {
        screen_name: username,
        name: username,
        profile_image_url: 'https://via.placeholder.com/48'
      },
      entities: {
        hashtags: [
          { text: 'MAGA', indices: [0, 0] },
          { text: 'America', indices: [0, 0] }
        ],
        user_mentions: []
      }
    };
  }

  /**
   * Generate mock tweets for development/testing
   * @param {string} username - Twitter username
   * @param {number} count - Number of tweets to generate
   * @returns {Array} - Array of mock tweet objects
   */
  getMockTweets(username, count) {
    const tweets = [];
    const hashtags = ['MAGA', 'America', 'Freedom', 'USA', 'Patriots', 'Conservative', 'Trump', 'Constitution'];
    const topics = [
      'economy',
      'border security',
      'inflation',
      'energy independence',
      'Second Amendment',
      'national security',
      'jobs',
      'America First',
      'military',
      'veterans'
    ];

    for (let i = 0; i < count; i++) {
      // Select random hashtags for this tweet
      const tweetHashtags = [];
      const numHashtags = Math.floor(Math.random() * 3) + 1;
      for (let j = 0; j < numHashtags; j++) {
        const tag = hashtags[Math.floor(Math.random() * hashtags.length)];
        if (!tweetHashtags.some(h => h.text === tag)) {
          tweetHashtags.push({ text: tag, indices: [0, 0] });
        }
      }

      // Select a random topic
      const topic = topics[Math.floor(Math.random() * topics.length)];

      // Create tweet with somewhat realistic text
      const tweetText = `[Development mock] Working hard on ${topic} issues today. We need to put America first and restore our country's greatness! ${tweetHashtags.map(h => `#${h.text}`).join(' ')}`;

      // Create timestamp between 1 and 30 days ago
      const daysAgo = Math.floor(Math.random() * 30) + 1;
      const hoursAgo = Math.floor(Math.random() * 24);
      const timestamp = new Date();
      timestamp.setDate(timestamp.getDate() - daysAgo);
      timestamp.setHours(timestamp.getHours() - hoursAgo);

      tweets.push({
        id_str: `mock_${Date.now()}_${i}`,
        created_at: timestamp.toISOString(),
        text: tweetText,
        full_text: tweetText,
        retweet_count: Math.floor(Math.random() * 1000),
        favorite_count: Math.floor(Math.random() * 5000),
        user: {
          screen_name: username,
          name: username,
          profile_image_url: 'https://via.placeholder.com/48'
        },
        entities: {
          hashtags: tweetHashtags,
          user_mentions: []
        }
      });
    }

    return tweets;
  }

  /**
   * Analyze tweet content
   * @param {string} tweetText - Tweet text to analyze
   * @returns {Object} - Analysis results including sentiment, key phrases
   */
  analyzeTweetContent(tweetText) {
    // This is a placeholder for more sophisticated NLP processing
    // In a real app, this would use NLP libraries or API services
    
    // Detect sentiment (very basic implementation)
    const positiveWords = ['great', 'good', 'excellent', 'amazing', 'wonderful', 'fantastic', 'success'];
    const negativeWords = ['bad', 'terrible', 'awful', 'fail', 'failure', 'poor', 'wrong'];
    
    const words = tweetText.toLowerCase().split(/\W+/);
    
    let positiveCount = 0;
    let negativeCount = 0;
    
    words.forEach(word => {
      if (positiveWords.includes(word)) positiveCount++;
      if (negativeWords.includes(word)) negativeCount++;
    });
    
    let sentiment = 'neutral';
    if (positiveCount > negativeCount) sentiment = 'positive';
    if (negativeCount > positiveCount) sentiment = 'negative';
    
    // Extract hashtags (basic implementation)
    const hashtags = [];
    const hashtagRegex = /#(\w+)/g;
    let match;
    
    while ((match = hashtagRegex.exec(tweetText)) !== null) {
      hashtags.push(match[1]);
    }
    
    // Topic detection (placeholder implementation)
    const topics = [];
    const topicKeywords = {
      economy: ['economy', 'inflation', 'jobs', 'economic', 'prices', 'cost'],
      immigration: ['border', 'immigration', 'migrant', 'illegal'],
      healthcare: ['healthcare', 'medical', 'doctor', 'hospital', 'medicine'],
      security: ['security', 'military', 'defense', 'troops', 'veterans'],
      energy: ['energy', 'oil', 'gas', 'climate', 'pipeline'],
      education: ['education', 'school', 'student', 'teacher', 'college']
    };
    
    const lowerText = tweetText.toLowerCase();
    
    for (const [topic, keywords] of Object.entries(topicKeywords)) {
      if (keywords.some(keyword => lowerText.includes(keyword))) {
        topics.push(topic);
      }
    }
    
    return {
      sentiment,
      hashtags,
      topics,
      wordCount: words.length
    };
  }
}

module.exports = TwitterService; 