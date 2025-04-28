#!/usr/bin/env python3
"""
Data Migration Script for MAGA_Ops

This script migrates data from the old database schema to the new normalized schema.
It performs the following steps:
1. Reads constants from entity_schema.py
2. Creates new schema tables
3. Migrates entities to the new structure
4. Maps old categorizations to the new taxonomy system
5. Logs the migration process
"""
import os
import sys
import sqlite3
import logging
import json
from datetime import datetime
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', 'migration.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
DB_PATH = os.path.join(PROJECT_ROOT, 'maga_ops.db')
SCHEMA_PATH = os.path.join(PROJECT_ROOT, 'scripts', 'db', 'schema.sql')
BACKUP_DB_PATH = os.path.join(PROJECT_ROOT, f'maga_ops_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')

# Import constants from entity_schema.py
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'scripts', 'db'))
try:
    from entity_schema import (
        ENTITY_TYPES, 
        ENTITY_SUBTYPES,
        PARTY_AFFILIATIONS,
        POLITICAL_IDEOLOGIES,
        TRUMP_STANCE
    )
    logger.info("Successfully imported constants from entity_schema.py")
except ImportError:
    logger.error("Failed to import constants from entity_schema.py")
    raise

def backup_database():
    """Create a backup of the current database before migration."""
    if os.path.exists(DB_PATH):
        import shutil
        shutil.copy2(DB_PATH, BACKUP_DB_PATH)
        logger.info(f"Created database backup at {BACKUP_DB_PATH}")
    else:
        logger.warning(f"No existing database found at {DB_PATH}")

def read_schema_sql():
    """Read the schema SQL file."""
    with open(SCHEMA_PATH, 'r') as f:
        return f.read()

def get_connection():
    """Get a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def check_tables_exist(conn, tables):
    """Check if the specified tables exist in the database."""
    cursor = conn.cursor()
    existing_tables = set()
    
    for table in tables:
        try:
            cursor.execute(f"SELECT 1 FROM {table} LIMIT 1")
            existing_tables.add(table)
        except sqlite3.OperationalError:
            pass
            
    return existing_tables

def execute_schema_sql(conn, schema_sql):
    """Execute the schema SQL to create new tables."""
    cursor = conn.cursor()
    
    # Split by semicolon to execute each statement separately
    # Skip empty statements
    statements = [s.strip() for s in schema_sql.split(';') if s.strip()]
    
    for statement in statements:
        try:
            cursor.execute(statement)
            logger.debug(f"Executed: {statement[:60]}...")
        except sqlite3.Error as e:
            logger.error(f"Error executing SQL: {statement[:100]}...")
            logger.error(f"Error details: {str(e)}")
            raise
    
    conn.commit()
    logger.info("Schema SQL executed successfully")

def initialize_category_data(conn):
    """Initialize category data from constants in entity_schema.py."""
    cursor = conn.cursor()
    
    # Check if data already exists to avoid duplicates
    cursor.execute("SELECT COUNT(*) FROM categories")
    if cursor.fetchone()[0] > 0:
        logger.info("Categories already populated, skipping initialization")
        return
    
    # Get category type IDs
    category_types = {
        'entity_type': 0, 
        'entity_subtype': 0, 
        'party': 0, 
        'ideology': 0, 
        'trump_stance': 0
    }
    
    for cat_type in category_types.keys():
        cursor.execute("SELECT id FROM category_types WHERE name = ?", (cat_type,))
        result = cursor.fetchone()
        if result:
            category_types[cat_type] = result[0]
        else:
            logger.error(f"Category type '{cat_type}' not found in database")
            raise ValueError(f"Category type '{cat_type}' not found")
    
    # Insert entity types
    entity_type_id = category_types['entity_type']
    for code, description in ENTITY_TYPES.items():
        cursor.execute(
            "INSERT INTO categories (category_type_id, code, name, description) VALUES (?, ?, ?, ?)",
            (entity_type_id, code, description, description)
        )
    
    # Insert entity subtypes
    entity_subtype_id = category_types['entity_subtype']
    for code, description in ENTITY_SUBTYPES.items():
        cursor.execute(
            "INSERT INTO categories (category_type_id, code, name, description) VALUES (?, ?, ?, ?)",
            (entity_subtype_id, code, description, description)
        )
    
    # Insert party affiliations
    party_id = category_types['party']
    for code, description in PARTY_AFFILIATIONS.items():
        cursor.execute(
            "INSERT INTO categories (category_type_id, code, name, description) VALUES (?, ?, ?, ?)",
            (party_id, code, description, description)
        )
    
    # Insert political ideologies
    ideology_id = category_types['ideology']
    for code, description in POLITICAL_IDEOLOGIES.items():
        cursor.execute(
            "INSERT INTO categories (category_type_id, code, name, description) VALUES (?, ?, ?, ?)",
            (ideology_id, code, description, description)
        )
    
    # Insert Trump stances
    trump_stance_id = category_types['trump_stance']
    for code, description in TRUMP_STANCE.items():
        cursor.execute(
            "INSERT INTO categories (category_type_id, code, name, description) VALUES (?, ?, ?, ?)",
            (trump_stance_id, code, description, description)
        )
    
    conn.commit()
    logger.info("Initialized category data from entity_schema.py constants")

def migrate_entities(conn):
    """Migrate entities from the old schema to the new schema."""
    cursor = conn.cursor()
    
    # Check if the old entities table exists
    old_tables_exist = check_tables_exist(conn, ['entities'])
    
    if 'entities' not in old_tables_exist:
        logger.warning("Old 'entities' table not found, skipping migration")
        return
    
    # Fetch all entities from the old table
    cursor.execute("SELECT * FROM entities")
    old_entities = cursor.fetchall()
    logger.info(f"Found {len(old_entities)} entities in old schema")
    
    # Migration stats
    stats = {
        'total': len(old_entities),
        'migrated': 0,
        'politicians': 0,
        'influencers': 0,
        'organizations': 0,
        'skipped': 0,
        'errors': 0
    }
    
    # Get category IDs for mapping
    category_mapping = {}
    category_types = ['entity_type', 'entity_subtype', 'party', 'ideology', 'trump_stance']
    
    for cat_type in category_types:
        cursor.execute("""
            SELECT c.code, c.id 
            FROM categories c 
            JOIN category_types ct ON c.category_type_id = ct.id 
            WHERE ct.name = ?
        """, (cat_type,))
        category_mapping[cat_type] = {row['code']: row['id'] for row in cursor.fetchall()}
    
    # Process each entity
    for old_entity in old_entities:
        try:
            # Convert to dict for easier access
            entity = dict(old_entity)
            
            # Determine entity type
            if entity['entity_type'] in ['POLITICIAN', 'SENATOR', 'REPRESENTATIVE', 'GOVERNOR']:
                new_type = 'politician'
                stats['politicians'] += 1
            elif entity['entity_type'] in ['INFLUENCER', 'MEDIA_PERSONALITY', 'JOURNALIST', 'PUNDIT']:
                new_type = 'influencer'
                stats['influencers'] += 1
            elif entity['entity_type'] in ['ORGANIZATION', 'GOVERNMENT_AGENCY', 'THINK_TANK']:
                new_type = 'organization'
                stats['organizations'] += 1
            else:
                # Default to influencer for unknown types
                new_type = 'influencer'
                stats['influencers'] += 1
            
            # Insert into new entities table
            cursor.execute("""
                INSERT INTO entities (
                    name, normalized_name, bio, twitter_handle, instagram_handle, 
                    facebook_url, website_url, first_appearance_date, last_updated, entity_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entity['name'],
                entity['normalized_name'],
                entity['bio'],
                entity['twitter_handle'],
                entity['instagram_handle'],
                entity['facebook_url'],
                entity['website_url'],
                entity['first_appearance_date'],
                entity['last_updated'],
                new_type
            ))
            
            # Get the new entity ID
            new_entity_id = cursor.lastrowid
            
            # Insert type-specific data
            if new_type == 'politician':
                cursor.execute("""
                    INSERT INTO politicians (entity_id) VALUES (?)
                """, (new_entity_id,))
                
                # Other politician fields could be populated here if available
            
            elif new_type == 'influencer':
                cursor.execute("""
                    INSERT INTO influencers (entity_id) VALUES (?)
                """, (new_entity_id,))
                
                # Other influencer fields could be populated here if available
            
            # Add entity categorizations
            categories_to_add = []
            
            # Entity type
            if entity['entity_type'] and entity['entity_type'] in category_mapping['entity_type']:
                categories_to_add.append((
                    new_entity_id, 
                    category_mapping['entity_type'][entity['entity_type']]
                ))
            
            # Entity subtype
            if entity['entity_subtype'] and entity['entity_subtype'] in category_mapping['entity_subtype']:
                categories_to_add.append((
                    new_entity_id, 
                    category_mapping['entity_subtype'][entity['entity_subtype']]
                ))
            
            # Party affiliation
            if entity['party_affiliation'] and entity['party_affiliation'] in category_mapping['party']:
                categories_to_add.append((
                    new_entity_id, 
                    category_mapping['party'][entity['party_affiliation']]
                ))
            
            # Political ideology
            if entity['political_ideology'] and entity['political_ideology'] in category_mapping['ideology']:
                categories_to_add.append((
                    new_entity_id, 
                    category_mapping['ideology'][entity['political_ideology']]
                ))
            
            # Trump stance
            if entity['trump_stance'] and entity['trump_stance'] in category_mapping['trump_stance']:
                categories_to_add.append((
                    new_entity_id, 
                    category_mapping['trump_stance'][entity['trump_stance']]
                ))
            
            # Insert all categories
            for entity_id, category_id in categories_to_add:
                try:
                    cursor.execute("""
                        INSERT INTO entity_categories (entity_id, category_id, source)
                        VALUES (?, ?, 'migration')
                    """, (entity_id, category_id))
                except sqlite3.IntegrityError:
                    # Skip duplicates
                    pass
            
            stats['migrated'] += 1
            
        except Exception as e:
            logger.error(f"Error migrating entity {entity.get('name', 'Unknown')}: {str(e)}")
            stats['errors'] += 1
    
    conn.commit()
    logger.info(f"Entity migration complete: {json.dumps(stats)}")

def main():
    """Main function to run the migration."""
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    logger.info("Starting database migration")
    
    # Backup the existing database
    backup_database()
    
    # Read the schema SQL
    try:
        schema_sql = read_schema_sql()
        logger.info(f"Read schema SQL ({len(schema_sql)} characters)")
    except Exception as e:
        logger.error(f"Failed to read schema SQL: {str(e)}")
        return
    
    # Get database connection
    try:
        conn = get_connection()
        logger.info(f"Connected to database at {DB_PATH}")
    except Exception as e:
        logger.error(f"Failed to connect to database: {str(e)}")
        return
    
    try:
        # Check if new tables already exist
        core_tables = ['entities', 'politicians', 'influencers', 'categories', 'category_types']
        existing_tables = check_tables_exist(conn, core_tables)
        
        if len(existing_tables) == len(core_tables):
            logger.info("All core tables already exist, skipping schema creation")
        else:
            missing_tables = set(core_tables) - existing_tables
            logger.info(f"Creating missing tables: {', '.join(missing_tables)}")
            
            # Execute schema SQL
            execute_schema_sql(conn, schema_sql)
        
        # Initialize category data
        initialize_category_data(conn)
        
        # Migrate entities
        migrate_entities(conn)
        
        logger.info("Migration completed successfully")
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main() 