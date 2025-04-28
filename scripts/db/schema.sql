-- MAGA_Ops Normalized Database Schema
-- Designed for efficient categorization and relationships between
-- Politicians, Influencers, and shared classification types

-- =============================================
-- Core Tables
-- =============================================

-- Base entity table for shared attributes
CREATE TABLE entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    normalized_name TEXT NOT NULL UNIQUE,
    bio TEXT,
    image_url TEXT,
    twitter_handle TEXT,
    instagram_handle TEXT,
    facebook_url TEXT,
    website_url TEXT,
    first_appearance_date TEXT,
    last_updated TEXT,
    relevance_score REAL DEFAULT 0.0, -- Higher value = more important/relevant
    entity_type TEXT NOT NULL, -- 'politician', 'influencer', etc.
    official_positions TEXT, -- JSON array of positions/roles held
    known_affiliations TEXT, -- JSON array of organizations affiliated with
    location TEXT, -- State, city, or region
    recent_activity TEXT, -- Summary of recent notable activity
    CHECK (entity_type IN ('politician', 'influencer', 'organization'))
);

-- Create indexes for common queries
CREATE INDEX idx_entities_normalized_name ON entities(normalized_name);
CREATE INDEX idx_entities_type ON entities(entity_type);
CREATE INDEX idx_entities_relevance ON entities(relevance_score DESC);

-- Politicians table (extends entities)
CREATE TABLE politicians (
    entity_id INTEGER PRIMARY KEY,
    office TEXT, -- Current office held
    state TEXT,
    district TEXT, -- For House representatives
    election_year INTEGER, -- Last election year
    bioguide_id TEXT UNIQUE, -- Official ID for Congress API
    fec_candidate_id TEXT,
    FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE
);

-- Influencers table (extends entities)
CREATE TABLE influencers (
    entity_id INTEGER PRIMARY KEY,
    platform TEXT, -- Primary platform (Twitter, YouTube, etc.)
    audience_size INTEGER, -- Follower count or equivalent
    content_focus TEXT, -- Main topics/issues they focus on
    influence_score REAL DEFAULT 0.0, -- Calculated based on reach/engagement
    FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE
);

-- =============================================
-- Classification/Taxonomy Tables
-- =============================================

-- Category types table (meta-categories)
CREATE TABLE category_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE, -- 'party', 'ideology', 'trump_stance', etc.
    description TEXT,
    is_multiple BOOLEAN DEFAULT FALSE -- Whether an entity can have multiple categories of this type
);

-- Insert standard category types
INSERT INTO category_types (name, description, is_multiple) VALUES
    ('party', 'Political party affiliation', FALSE),
    ('ideology', 'Political ideology or worldview', TRUE),
    ('trump_stance', 'Position toward Donald Trump', FALSE),
    ('entity_type', 'General entity classification', FALSE),
    ('entity_subtype', 'Specific role or position', FALSE);

-- Categories table (all possible values)
CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_type_id INTEGER NOT NULL,
    code TEXT NOT NULL, -- E.g., 'REPUBLICAN', 'DEMOCRAT', 'MAGA', etc.
    name TEXT NOT NULL, -- Human-readable name
    description TEXT,
    display_order INTEGER DEFAULT 0, -- For UI ordering
    parent_category_id INTEGER, -- For hierarchical categories
    UNIQUE (category_type_id, code),
    FOREIGN KEY (category_type_id) REFERENCES category_types(id),
    FOREIGN KEY (parent_category_id) REFERENCES categories(id)
);

-- Create index for category lookups
CREATE INDEX idx_categories_type ON categories(category_type_id);
CREATE INDEX idx_categories_code ON categories(code);

-- Entity-category relationships (many-to-many)
CREATE TABLE entity_categories (
    entity_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    confidence_score REAL DEFAULT 1.0, -- AI confidence in this classification (0-1)
    source TEXT, -- Where this classification came from
    PRIMARY KEY (entity_id, category_id),
    FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

-- Create index for faster lookups
CREATE INDEX idx_entity_categories_entity ON entity_categories(entity_id);
CREATE INDEX idx_entity_categories_category ON entity_categories(category_id);

-- =============================================
-- Relationship Tables
-- =============================================

-- Connections between entities
CREATE TABLE entity_connections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity1_id INTEGER NOT NULL,
    entity2_id INTEGER NOT NULL,
    connection_type TEXT NOT NULL, -- 'mentions', 'endorses', 'opposes', etc.
    strength REAL DEFAULT 0.0, -- 0-1 strength of connection
    source TEXT, -- Evidence for this connection
    first_detected TEXT, -- When this connection was first found
    last_updated TEXT, -- When this connection was last updated
    FOREIGN KEY (entity1_id) REFERENCES entities(id) ON DELETE CASCADE,
    FOREIGN KEY (entity2_id) REFERENCES entities(id) ON DELETE CASCADE
);

CREATE INDEX idx_connections_entity1 ON entity_connections(entity1_id);
CREATE INDEX idx_connections_entity2 ON entity_connections(entity2_id);
CREATE INDEX idx_connections_type ON entity_connections(connection_type);

-- Evidence for entity connections
CREATE TABLE connection_evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    connection_id INTEGER NOT NULL,
    evidence_type TEXT NOT NULL, -- 'news_article', 'social_post', 'official_record', etc.
    description TEXT,
    source_url TEXT,
    confidence_score REAL DEFAULT 0.0, -- 0-1 confidence in this evidence
    extraction_date TEXT NOT NULL,
    FOREIGN KEY (connection_id) REFERENCES entity_connections(id) ON DELETE CASCADE
);

CREATE INDEX idx_evidence_connection ON connection_evidence(connection_id);
CREATE INDEX idx_evidence_type ON connection_evidence(evidence_type);

-- =============================================
-- AI and Analytics Tables
-- =============================================

-- Entity embeddings for vector search
CREATE TABLE entity_embeddings (
    entity_id INTEGER PRIMARY KEY,
    embedding_data TEXT, -- JSON array of embedding vector
    embedding_model TEXT, -- Model used to generate embedding
    created_at TEXT NOT NULL,
    FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE
);

-- Search history for analytics
CREATE TABLE search_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    results_count INTEGER
);

-- =============================================
-- Activity and Content Tables
-- =============================================

-- Social posts from entities
CREATE TABLE social_posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id INTEGER NOT NULL,
    platform TEXT NOT NULL, -- 'twitter', 'facebook', etc.
    post_id TEXT NOT NULL, -- Platform-specific ID
    content TEXT,
    posted_at TEXT,
    engagement_count INTEGER DEFAULT 0, -- Likes, shares, etc.
    sentiment_score REAL, -- -1.0 to 1.0
    ai_analyzed BOOLEAN DEFAULT FALSE,
    analysis_data TEXT, -- JSON with AI analysis
    UNIQUE (platform, post_id),
    FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE
);

CREATE INDEX idx_posts_entity ON social_posts(entity_id);
CREATE INDEX idx_posts_platform ON social_posts(platform, posted_at);

-- Voting records for politicians
CREATE TABLE voting_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    politician_id INTEGER NOT NULL,
    vote_id TEXT NOT NULL, -- Official vote ID
    bill_id TEXT,
    bill_title TEXT,
    vote_date TEXT,
    vote_position TEXT, -- 'Yes', 'No', 'Present', etc.
    congress INTEGER, -- e.g., 117 for 117th Congress
    UNIQUE (politician_id, vote_id),
    FOREIGN KEY (politician_id) REFERENCES politicians(entity_id) ON DELETE CASCADE
);

CREATE INDEX idx_voting_politician ON voting_records(politician_id);
CREATE INDEX idx_voting_date ON voting_records(vote_date);

-- Topics/issues for tracking
CREATE TABLE topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    parent_topic_id INTEGER,
    FOREIGN KEY (parent_topic_id) REFERENCES topics(id)
);

-- Entity-topic relationships
CREATE TABLE entity_topics (
    entity_id INTEGER NOT NULL,
    topic_id INTEGER NOT NULL,
    stance REAL, -- -1.0 (opposed) to 1.0 (supportive)
    importance REAL DEFAULT 0.5, -- How important this topic is to entity
    PRIMARY KEY (entity_id, topic_id),
    FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE,
    FOREIGN KEY (topic_id) REFERENCES topics(id)
);

CREATE INDEX idx_entity_topics_entity ON entity_topics(entity_id);
CREATE INDEX idx_entity_topics_topic ON entity_topics(topic_id);

-- =============================================
-- Funding and Financial Tables (optional expansion)
-- =============================================

CREATE TABLE funding_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    organization_type TEXT
);

CREATE TABLE entity_funding (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id INTEGER NOT NULL,
    source_id INTEGER NOT NULL,
    amount REAL,
    transaction_date TEXT,
    transaction_type TEXT, -- 'donation', 'expenditure', etc.
    transaction_id TEXT, -- Official ID if available
    FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE,
    FOREIGN KEY (source_id) REFERENCES funding_sources(id)
);

CREATE INDEX idx_funding_entity ON entity_funding(entity_id);
CREATE INDEX idx_funding_source ON entity_funding(source_id);
CREATE INDEX idx_funding_date ON entity_funding(transaction_date);

-- =============================================
-- Financial Data Tables
-- =============================================

-- Donation records
CREATE TABLE donation_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    donor_id INTEGER NOT NULL,
    recipient_id INTEGER NOT NULL,
    amount REAL,
    donation_date TEXT,
    donation_type TEXT, -- 'individual', 'pac', 'corporate'
    source_url TEXT, -- Source of this information
    source_id TEXT, -- ID from source database (FEC ID, etc.)
    FOREIGN KEY (donor_id) REFERENCES entities(id) ON DELETE CASCADE,
    FOREIGN KEY (recipient_id) REFERENCES entities(id) ON DELETE CASCADE
);

CREATE INDEX idx_donation_donor ON donation_records(donor_id);
CREATE INDEX idx_donation_recipient ON donation_records(recipient_id);
CREATE INDEX idx_donation_date ON donation_records(donation_date);

-- =============================================
-- Views for Common Queries
-- =============================================

-- Complete entity profile view
CREATE VIEW view_entity_profiles AS
SELECT 
    e.id, 
    e.name,
    e.normalized_name,
    e.bio,
    e.entity_type,
    e.twitter_handle,
    e.relevance_score,
    (SELECT GROUP_CONCAT(c.name, ', ') 
     FROM entity_categories ec 
     JOIN categories c ON ec.category_id = c.id 
     JOIN category_types ct ON c.category_type_id = ct.id 
     WHERE ec.entity_id = e.id AND ct.name = 'party') AS party,
    (SELECT GROUP_CONCAT(c.name, ', ') 
     FROM entity_categories ec 
     JOIN categories c ON ec.category_id = c.id 
     JOIN category_types ct ON c.category_type_id = ct.id 
     WHERE ec.entity_id = e.id AND ct.name = 'ideology') AS ideologies,
    (SELECT c.name 
     FROM entity_categories ec 
     JOIN categories c ON ec.category_id = c.id 
     JOIN category_types ct ON c.category_type_id = ct.id 
     WHERE ec.entity_id = e.id AND ct.name = 'trump_stance' 
     LIMIT 1) AS trump_stance
FROM entities e;

-- Politician-specific view
CREATE VIEW view_politician_profiles AS
SELECT 
    vep.*,
    p.office,
    p.state,
    p.district,
    p.election_year,
    p.bioguide_id
FROM view_entity_profiles vep
JOIN politicians p ON vep.id = p.entity_id
WHERE vep.entity_type = 'politician';

-- Influencer-specific view
CREATE VIEW view_influencer_profiles AS
SELECT 
    vep.*,
    i.platform,
    i.audience_size,
    i.content_focus,
    i.influence_score
FROM view_entity_profiles vep
JOIN influencers i ON vep.id = i.entity_id
WHERE vep.entity_type = 'influencer';

-- =============================================
-- AI Metadata Tables
-- =============================================

-- Track AI-generated metadata and confidence
CREATE TABLE ai_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id INTEGER NOT NULL,
    field_name TEXT NOT NULL, -- The field/attribute this metadata is about
    field_value TEXT, -- The actual value assigned
    confidence_score REAL DEFAULT 0.0, -- 0-1 confidence score
    source TEXT, -- Where this data came from (URL, system name)
    extraction_date TEXT NOT NULL,
    verified BOOLEAN DEFAULT FALSE,
    verified_date TEXT,
    FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE
);

CREATE INDEX idx_ai_metadata_entity ON ai_metadata(entity_id);
CREATE INDEX idx_ai_metadata_field ON ai_metadata(field_name);
CREATE INDEX idx_ai_metadata_verified ON ai_metadata(verified);

-- View for entity data completeness analysis
CREATE VIEW view_entity_gaps AS
SELECT 
    e.id,
    e.name,
    e.entity_type,
    CASE WHEN e.bio IS NULL OR e.bio = '' THEN 1 ELSE 0 END as missing_bio,
    CASE WHEN e.twitter_handle IS NULL THEN 1 ELSE 0 END as missing_twitter,
    CASE WHEN e.website_url IS NULL THEN 1 ELSE 0 END as missing_website,
    CASE WHEN e.image_url IS NULL THEN 1 ELSE 0 END as missing_image,
    CASE WHEN e.official_positions IS NULL THEN 1 ELSE 0 END as missing_positions,
    CASE WHEN e.known_affiliations IS NULL THEN 1 ELSE 0 END as missing_affiliations,
    CASE WHEN e.location IS NULL THEN 1 ELSE 0 END as missing_location,
    (SELECT COUNT(*) FROM entity_categories WHERE entity_id = e.id) as category_count,
    (SELECT COUNT(*) FROM entity_connections WHERE entity1_id = e.id OR entity2_id = e.id) as connection_count,
    (SELECT COUNT(*) FROM voting_records WHERE politician_id = e.id) as vote_count
FROM entities e;

-- View for entities needing enrichment, prioritized
CREATE VIEW view_enrichment_priorities AS
SELECT
    id,
    name,
    entity_type,
    (missing_bio + missing_twitter + missing_website + missing_image + 
     missing_positions + missing_affiliations + missing_location) as missing_field_count,
    category_count,
    connection_count,
    vote_count,
    -- Calculate overall priority score (higher = needs more attention)
    (missing_bio * 2 + missing_twitter + missing_website + missing_image + 
     missing_positions * 1.5 + missing_affiliations * 1.5 + missing_location) -
    (category_count * 0.5 + connection_count * 0.3 + vote_count * 0.2) as priority_score
FROM view_entity_gaps
ORDER BY priority_score DESC; 