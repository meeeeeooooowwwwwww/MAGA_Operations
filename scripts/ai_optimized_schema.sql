-- AI-Optimized Influencers and Politicians Database Schema
-- Enhanced for machine learning, vector search, and intelligent querying

-- Main Categories table with AI-friendly fields
CREATE TABLE categories (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    parent_category_id INTEGER,
    taxonomy_level INTEGER DEFAULT 1,
    FOREIGN KEY (parent_category_id) REFERENCES categories(id)
);

-- Insert standard categories with detailed descriptions
INSERT INTO categories (name, description, taxonomy_level) VALUES 
    ('Politician', 'Elected officials or candidates for office at any level of government', 1),
    ('Media Personality', 'Public figures primarily known for media appearances and commentary', 1),
    ('Journalist', 'Professional reporters, writers, or news analysts', 1),
    ('Activist', 'Individuals primarily engaged in advocacy and social movements', 1),
    ('Influencer', 'Social media personalities with significant following and influence', 1),
    ('Business Leader', 'Executives, entrepreneurs, and corporate decision-makers', 1);

-- Add subcategories for more precise AI classification
INSERT INTO categories (name, description, parent_category_id, taxonomy_level) VALUES
    ('Federal Politician', 'Officials at the national government level', 1, 2),
    ('State Politician', 'Officials at the state government level', 1, 2),
    ('Conservative Media Personality', 'Right-leaning commentators and hosts', 2, 2),
    ('Progressive Media Personality', 'Left-leaning commentators and hosts', 2, 2),
    ('Independent Media Personality', 'Non-partisan or third-party aligned commentators', 2, 2);

-- Political affiliations with ideological spectrum positioning
CREATE TABLE affiliations (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    ideology_spectrum_position REAL, -- -1.0 (far left) to 1.0 (far right), 0 is center
    primary_color TEXT -- For UI representation
);

-- Insert standard affiliations with spectrum positions
INSERT INTO affiliations (name, description, ideology_spectrum_position, primary_color) VALUES
    ('Republican', 'Member of the Republican Party', 0.6, '#E91D0E'),
    ('Democrat', 'Member of the Democratic Party', -0.6, '#0015BC'),
    ('MAGA', 'Make America Great Again movement supporter', 0.8, '#E91D0E'),
    ('America First', 'Adherent to America First policy perspective', 0.7, '#E91D0E'),
    ('Trump Supporter', 'Supporter of Donald Trump', 0.7, '#E91D0E'),
    ('Trump Critic', 'Critical of Donald Trump', -0.5, '#0015BC'),
    ('Independent', 'Not affiliated with major political parties', 0.0, '#PURPLE'),
    ('Libertarian', 'Advocating for minimal government intervention', 0.3, '#FED105'),
    ('Progressive', 'Supporting progressive social and economic policies', -0.8, '#0015BC');

-- Media outlets with additional metadata for AI context
CREATE TABLE media_outlets (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    type TEXT, -- e.g., TV, Online, Print, etc.
    description TEXT,
    audience_size_estimate INTEGER,
    ideology_spectrum_position REAL, -- -1.0 (far left) to 1.0 (far right), 0 is center
    founded_year INTEGER,
    parent_company TEXT
);

-- Enhanced main influencers table with AI-friendly fields
CREATE TABLE influencers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    normalized_name TEXT NOT NULL, -- Lowercase, no special chars for better matching
    category_id INTEGER,
    bio TEXT,
    summary TEXT, -- AI-generated summary
    twitter_handle TEXT,
    instagram_handle TEXT,
    facebook_url TEXT,
    website_url TEXT,
    birth_year INTEGER,
    home_state TEXT,
    notes TEXT,
    first_appearance_date TEXT, -- When they first appeared in our dataset
    last_updated TEXT, -- Timestamp for when record was last updated
    ai_embedding_updated TEXT, -- Timestamp for when AI embedding was last updated
    relevance_score REAL DEFAULT 0, -- Computed relevance based on mentions, recency
    popularity_trend TEXT, -- JSON string storing trend data
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

-- Create a table for name variations to improve entity resolution
CREATE TABLE name_variations (
    id INTEGER PRIMARY KEY,
    influencer_id INTEGER NOT NULL,
    variation TEXT NOT NULL,
    source TEXT, -- where this variation was found
    frequency INTEGER DEFAULT 1, -- how often this variation appears
    FOREIGN KEY (influencer_id) REFERENCES influencers(id)
);

-- Many-to-many relationships (enhanced)
CREATE TABLE influencer_affiliations (
    influencer_id INTEGER,
    affiliation_id INTEGER,
    confidence_score REAL DEFAULT 1.0, -- AI confidence in this association (0-1)
    source_count INTEGER DEFAULT 1, -- Number of sources confirming this
    PRIMARY KEY (influencer_id, affiliation_id),
    FOREIGN KEY (influencer_id) REFERENCES influencers(id),
    FOREIGN KEY (affiliation_id) REFERENCES affiliations(id)
);

-- Topics and themes for AI-driven content analysis
CREATE TABLE topics (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    parent_topic_id INTEGER,
    FOREIGN KEY (parent_topic_id) REFERENCES topics(id)
);

INSERT INTO topics (name, description) VALUES
    ('Immigration', 'Border security, immigration policy, and related issues'),
    ('Economy', 'Economic policies, jobs, inflation, and financial matters'),
    ('Foreign Policy', 'International relations, diplomacy, and global affairs'),
    ('Social Issues', 'Cultural debates, social justice, and societal concerns'),
    ('Election Integrity', 'Voting systems, electoral processes, and related controversies');

-- Link influencers to topics they discuss
CREATE TABLE influencer_topics (
    influencer_id INTEGER,
    topic_id INTEGER,
    stance REAL, -- -1.0 (strongly opposed) to 1.0 (strongly supportive)
    confidence_score REAL DEFAULT 1.0,
    sources_count INTEGER DEFAULT 1,
    PRIMARY KEY (influencer_id, topic_id),
    FOREIGN KEY (influencer_id) REFERENCES influencers(id),
    FOREIGN KEY (topic_id) REFERENCES topics(id)
);

-- Source tracking with enhanced metadata
CREATE TABLE sources (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    url TEXT,
    type TEXT, -- e.g., YouTube video, tweet, article, etc.
    published_date TEXT,
    date_accessed TEXT,
    content_summary TEXT,
    reliability_score REAL DEFAULT 1.0
);

-- AI-specific tables for machine learning and search
CREATE TABLE ai_embeddings (
    id INTEGER PRIMARY KEY,
    influencer_id INTEGER NOT NULL,
    embedding_data TEXT, -- JSON string of vector representation
    embedding_model TEXT, -- Model used to generate the embedding
    created_at TEXT NOT NULL,
    FOREIGN KEY (influencer_id) REFERENCES influencers(id)
);

-- Track connections between influencers for network analysis
CREATE TABLE influencer_connections (
    id INTEGER PRIMARY KEY,
    influencer1_id INTEGER NOT NULL,
    influencer2_id INTEGER NOT NULL,
    connection_type TEXT, -- e.g., Colleague, Friend, Adversary, etc.
    strength REAL, -- 0.0 to 1.0 indicating connection strength
    FOREIGN KEY (influencer1_id) REFERENCES influencers(id),
    FOREIGN KEY (influencer2_id) REFERENCES influencers(id)
);

-- Table for tracking search queries and results
CREATE TABLE search_queries (
    id INTEGER PRIMARY KEY,
    query_text TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    results_count INTEGER
);

-- Create indexes for faster AI-driven lookups
CREATE INDEX idx_influencer_name ON influencers(name);
CREATE INDEX idx_influencer_normalized_name ON influencers(normalized_name);
CREATE INDEX idx_influencer_category ON influencers(category_id);
CREATE INDEX idx_influencer_relevance ON influencers(relevance_score DESC);
CREATE INDEX idx_name_variations ON name_variations(variation);
CREATE INDEX idx_topics_name ON topics(name);

-- Create a view for easy AI querying of complete influencer profiles
CREATE VIEW ai_influencer_profiles AS
SELECT 
    i.id, i.name, i.normalized_name, i.bio, i.summary, 
    c.name as category,
    i.relevance_score,
    i.twitter_handle,
    i.last_updated
FROM 
    influencers i
LEFT JOIN 
    categories c ON i.category_id = c.id; 