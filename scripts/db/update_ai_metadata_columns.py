#!/usr/bin/env python3
"""
Update AI Metadata Table

This script updates the ai_metadata table to match column names in the code.
"""
import os
import sys
import sqlite3
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
DB_PATH = os.path.join(PROJECT_ROOT, 'maga_ops.db')

def get_connection():
    """Get a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def update_ai_metadata_table():
    """Update the ai_metadata table to match our code."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # First check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_metadata'")
        if not cursor.fetchone():
            logger.error("ai_metadata table does not exist")
            return False
        
        # Create a new table with the correct column names
        logger.info("Creating temporary table with new column structure")
        cursor.execute("""
        CREATE TABLE ai_metadata_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_id INTEGER NOT NULL,
            field_name TEXT NOT NULL,
            field_value TEXT,
            confidence_score REAL DEFAULT 0.0,
            source TEXT,
            extraction_date TEXT NOT NULL,
            verified BOOLEAN DEFAULT FALSE,
            verified_date TEXT,
            FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE
        )
        """)
        
        # Copy data from old table to new table
        logger.info("Copying data to new table with updated column names")
        cursor.execute("""
        INSERT INTO ai_metadata_new (
            id, entity_id, field_name, field_value, 
            confidence_score, source, extraction_date, verified
        )
        SELECT 
            id, entity_id, field_name, field_value, 
            ai_confidence_score, extraction_source, extraction_date, human_verified
        FROM ai_metadata
        """)
        
        # Drop the old table
        logger.info("Dropping old table")
        cursor.execute("DROP TABLE ai_metadata")
        
        # Rename the new table
        logger.info("Renaming new table to ai_metadata")
        cursor.execute("ALTER TABLE ai_metadata_new RENAME TO ai_metadata")
        
        # Recreate indexes
        logger.info("Recreating indexes")
        cursor.execute("CREATE INDEX idx_ai_metadata_entity ON ai_metadata(entity_id)")
        cursor.execute("CREATE INDEX idx_ai_metadata_field ON ai_metadata(field_name)")
        cursor.execute("CREATE INDEX idx_ai_metadata_verified ON ai_metadata(verified)")
        
        conn.commit()
        logger.info("ai_metadata table successfully updated")
        
        return True
    except sqlite3.Error as e:
        logger.error(f"Database error: {str(e)}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def main():
    """Main function."""
    logger.info("Starting ai_metadata table update")
    success = update_ai_metadata_table()
    if success:
        logger.info("Update completed successfully")
    else:
        logger.error("Update failed")

if __name__ == "__main__":
    main() 