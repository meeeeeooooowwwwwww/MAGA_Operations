#!/usr/bin/env python3
"""
Entity schema definitions for the MAGA_Ops database.

This module defines:
1. Constants for entity categorization (types, parties, ideologies, etc.)
2. Database schema for the entities table
3. Functions to initialize and access the database
"""
import os
import sqlite3
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
DB_PATH = os.path.join(PROJECT_ROOT, 'maga_ops.db')

# Entity Type Constants
ENTITY_TYPES = {
    "UNKNOWN": "Unknown type",
    "POLITICIAN": "Government official or candidate",
    "JOURNALIST": "News reporter or editor",
    "MEDIA_PERSONALITY": "TV, radio, or podcast host",
    "INFLUENCER": "Social media personality",
    "ORGANIZATION": "Political or social organization",
    "GOVERNMENT_AGENCY": "Federal, state, or local agency",
    "ACTIVIST": "Political or social activist",
    "THINK_TANK": "Research or policy organization",
    "PUNDIT": "Political commentator",
    "BUSINESS_LEADER": "CEO, entrepreneur, or executive",
    "CELEBRITY": "Famous person (actor, musician, etc.)",
    "ACADEMIC": "Professor, researcher, or scholar",
    "LEGAL_PROFESSIONAL": "Lawyer, judge, or legal expert",
    "RELIGIOUS_LEADER": "Pastor, priest, imam, etc."
}

# Entity Subtypes - More granular classifications
ENTITY_SUBTYPES = {
    # Political subtypes
    "PRESIDENT": "President of the United States",
    "VICE_PRESIDENT": "Vice President of the United States",
    "SENATOR": "U.S. Senator",
    "REPRESENTATIVE": "U.S. Representative",
    "GOVERNOR": "State Governor",
    "CABINET_MEMBER": "Cabinet Secretary or equivalent",
    "MAYOR": "Mayor of a city",
    "CANDIDATE": "Political candidate",
    "WHITE_HOUSE_STAFF": "White House staff member",
    "PARTY_OFFICIAL": "Political party official",
    
    # Media subtypes
    "NEWS_ANCHOR": "Television news anchor",
    "REPORTER": "News reporter",
    "EDITOR": "News editor",
    "COLUMNIST": "Opinion columnist",
    "RADIO_HOST": "Radio show host",
    "PODCAST_HOST": "Podcast host",
    "COMMENTATOR": "Political commentator",
    "BLOGGER": "Blog writer",
    "CONTENT_CREATOR": "Video or content creator",
    
    # Organization subtypes
    "POLITICAL_PARTY": "Political party",
    "ADVOCACY_GROUP": "Advocacy organization",
    "LOBBYING_FIRM": "Lobbying organization",
    "MEDIA_OUTLET": "News or media organization",
    "PAC": "Political Action Committee",
    "SUPER_PAC": "Super PAC",
    "NON_PROFIT": "Non-profit organization",
    "RESEARCH_INSTITUTE": "Research-focused organization",
    
    # Other professional subtypes
    "PROFESSOR": "University professor",
    "AUTHOR": "Book author",
    "CONSULTANT": "Political consultant",
    "STRATEGIST": "Political strategist",
    "LAWYER": "Attorney",
    "JUDGE": "Judge or justice",
    "CEO": "Chief Executive Officer",
    "ENTREPRENEUR": "Business founder",
    "RELIGIOUS_FIGURE": "Religious leader or figure",
    
    # Catch-all
    "OTHER": "Other specific role",
    "UNKNOWN": "Unknown role"
}

# Party Affiliations
PARTY_AFFILIATIONS = {
    "UNKNOWN": "Unknown party affiliation",
    "REPUBLICAN": "Republican Party",
    "DEMOCRAT": "Democratic Party",
    "LIBERTARIAN": "Libertarian Party",
    "GREEN": "Green Party",
    "CONSTITUTION": "Constitution Party",
    "INDEPENDENT": "Independent (no party)",
    "OTHER": "Other political party"
}

# Political Ideologies
POLITICAL_IDEOLOGIES = {
    "UNKNOWN": "Unknown ideology",
    # Conservative spectrum
    "TRADITIONAL_CONSERVATIVE": "Traditional conservative values",
    "FISCAL_CONSERVATIVE": "Fiscally conservative",
    "SOCIAL_CONSERVATIVE": "Socially conservative",
    "AMERICA_FIRST": "America First",
    "MAGA": "Make America Great Again",
    "RELIGIOUS_RIGHT": "Religious right",
    "LIBERTARIAN_RIGHT": "Libertarian-leaning right",
    "MODERATE_REPUBLICAN": "Moderate Republican",
    "NEO_CONSERVATIVE": "Neo-conservative",
    
    # Liberal/Progressive spectrum
    "PROGRESSIVE": "Progressive",
    "LIBERAL": "Liberal",
    "DEMOCRATIC_SOCIALIST": "Democratic socialist",
    "SOCIAL_DEMOCRAT": "Social democrat",
    "MODERATE_DEMOCRAT": "Moderate Democrat",
    "BLUE_DOG_DEMOCRAT": "Blue Dog Democrat",
    
    # Other
    "CENTRIST": "Centrist or moderate",
    "POPULIST": "Populist",
    "LIBERTARIAN": "Libertarian",
    "NATIONALIST": "Nationalist",
    "OTHER": "Other ideology"
}

# Trump Stance
TRUMP_STANCE = {
    "UNKNOWN": "Unknown stance",
    "TRUMP_LOYALIST": "Strong Trump supporter/ally",
    "TRUMP_SUPPORTER": "Supports Trump",
    "TRUMP_ALIGNED": "Generally aligned with Trump",
    "TRUMP_CRITICAL_SUPPORTER": "Supports but sometimes critical",
    "NEUTRAL": "Neutral on Trump",
    "MIXED": "Mixed or changing views on Trump",
    "TRUMP_SKEPTIC": "Skeptical of Trump",
    "TRUMP_CRITIC": "Critical of Trump",
    "NEVER_TRUMPER": "Strongly opposed to Trump",
    "FORMER_SUPPORTER": "Former supporter, now critical",
    "FORMER_CRITIC": "Former critic, now supportive"
}

# SQL to create the entities table
CREATE_ENTITIES_TABLE = """
CREATE TABLE IF NOT EXISTS entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    normalized_name TEXT NOT NULL,
    entity_type TEXT,
    entity_subtype TEXT,
    party_affiliation TEXT,
    political_ideology TEXT,
    trump_stance TEXT,
    bio TEXT,
    twitter_handle TEXT,
    instagram_handle TEXT,
    facebook_url TEXT,
    website_url TEXT,
    first_appearance_date TEXT,
    last_updated TEXT,
    UNIQUE(normalized_name)
)
"""

# SQL to create index on normalized name
CREATE_NAME_INDEX = """
CREATE INDEX IF NOT EXISTS idx_normalized_name ON entities(normalized_name)
"""

def get_db_connection():
    """Get a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize the database schema."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create entities table
        cursor.execute(CREATE_ENTITIES_TABLE)
        
        # Create index on normalized_name
        cursor.execute(CREATE_NAME_INDEX)
        
        # Commit changes
        conn.commit()
        logger.info(f"Database initialized at {DB_PATH}")
        
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

def insert_entity(entity_data):
    """Insert a new entity into the database."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if entity already exists
        cursor.execute(
            "SELECT id FROM entities WHERE normalized_name = ?",
            (entity_data.get('normalized_name', '').lower(),)
        )
        existing = cursor.fetchone()
        
        if existing:
            # Update existing entity
            entity_id = existing[0]
            cursor.execute("""
                UPDATE entities SET
                entity_type = ?,
                entity_subtype = ?,
                party_affiliation = ?,
                political_ideology = ?,
                trump_stance = ?,
                bio = ?,
                twitter_handle = ?,
                instagram_handle = ?,
                facebook_url = ?,
                website_url = ?,
                last_updated = ?
                WHERE id = ?
            """, (
                entity_data.get('entity_type'),
                entity_data.get('entity_subtype'),
                entity_data.get('party_affiliation'),
                entity_data.get('political_ideology'),
                entity_data.get('trump_stance'),
                entity_data.get('bio'),
                entity_data.get('twitter_handle'),
                entity_data.get('instagram_handle'),
                entity_data.get('facebook_url'),
                entity_data.get('website_url'),
                datetime.now().isoformat(),
                entity_id
            ))
            logger.info(f"Updated entity: {entity_data.get('name')}")
        else:
            # Insert new entity
            cursor.execute("""
                INSERT INTO entities (
                    name, normalized_name, entity_type, entity_subtype,
                    party_affiliation, political_ideology, trump_stance,
                    bio, twitter_handle, instagram_handle, facebook_url,
                    website_url, first_appearance_date, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entity_data.get('name'),
                entity_data.get('normalized_name', '').lower(),
                entity_data.get('entity_type'),
                entity_data.get('entity_subtype'),
                entity_data.get('party_affiliation'),
                entity_data.get('political_ideology'),
                entity_data.get('trump_stance'),
                entity_data.get('bio'),
                entity_data.get('twitter_handle'),
                entity_data.get('instagram_handle'),
                entity_data.get('facebook_url'),
                entity_data.get('website_url'),
                entity_data.get('first_appearance_date', datetime.now().isoformat()),
                datetime.now().isoformat()
            ))
            logger.info(f"Inserted new entity: {entity_data.get('name')}")
        
        conn.commit()
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def get_entity(normalized_name):
    """Get an entity by its normalized name."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM entities WHERE normalized_name = ?",
            (normalized_name.lower(),)
        )
        entity = cursor.fetchone()
        
        if entity:
            return dict(entity)
        return None
        
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_all_entities():
    """Get all entities from the database."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM entities ORDER BY name")
        entities = cursor.fetchall()
        
        return [dict(entity) for entity in entities]
        
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_entities_by_type(entity_type):
    """Get entities filtered by type."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM entities WHERE entity_type = ? ORDER BY name",
            (entity_type,)
        )
        entities = cursor.fetchall()
        
        return [dict(entity) for entity in entities]
        
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        return []
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # Initialize database when run directly
    init_database()
    print(f"Entity database schema initialized at {DB_PATH}")
    print(f"Entity types defined: {len(ENTITY_TYPES)}")
    print(f"Entity subtypes defined: {len(ENTITY_SUBTYPES)}")
    print(f"Party affiliations defined: {len(PARTY_AFFILIATIONS)}")
    print(f"Political ideologies defined: {len(POLITICAL_IDEOLOGIES)}")
    print(f"Trump stances defined: {len(TRUMP_STANCE)}") 