#!/usr/bin/env python3
"""
Update Entities Table

Adds new columns to the entities table.
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

def check_column_exists(conn, table, column):
    """Check if a column exists in a table."""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row['name'] for row in cursor.fetchall()]
    return column in columns

def update_entities_table(conn):
    """Add new columns to the entities table."""
    cursor = conn.cursor()
    
    # New columns to add
    new_columns = [
        ('image_url', 'TEXT'),
        ('official_positions', 'TEXT'),
        ('known_affiliations', 'TEXT'),
        ('location', 'TEXT'),
        ('recent_activity', 'TEXT')
    ]
    
    # Add each column if it doesn't exist
    for column, type in new_columns:
        if not check_column_exists(conn, 'entities', column):
            try:
                sql = f"ALTER TABLE entities ADD COLUMN {column} {type}"
                cursor.execute(sql)
                logger.info(f"Added column '{column}' to entities table")
            except sqlite3.Error as e:
                logger.error(f"Error adding column '{column}': {str(e)}")
    
    conn.commit()
    logger.info("Entities table update completed")

def main():
    """Main function."""
    logger.info("Starting entities table update")
    
    # Get database connection
    try:
        conn = get_connection()
        logger.info(f"Connected to database at {DB_PATH}")
    except Exception as e:
        logger.error(f"Failed to connect to database: {str(e)}")
        return
    
    try:
        # Update entities table
        update_entities_table(conn)
    except Exception as e:
        logger.error(f"Entities table update failed: {str(e)}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main() 