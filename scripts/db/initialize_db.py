#!/usr/bin/env python3
"""
Database Initialization Script

This script:
1. Creates the database tables using schema.sql
2. Populates initial category types and categories
3. Checks if data needs to be migrated from old schema
"""
import os
import sys
import sqlite3
import logging
import subprocess
from pathlib import Path
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', 'db_initialization.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, 'scripts')
DB_DIR = os.path.join(SCRIPTS_DIR, 'db')
DB_PATH = os.path.join(PROJECT_ROOT, 'maga_ops.db')
SCHEMA_PATH = os.path.join(DB_DIR, 'schema.sql')
MIGRATE_SCRIPT = os.path.join(DB_DIR, 'migrate_data.py')

def check_dependencies():
    """Check if required files exist."""
    if not os.path.exists(SCHEMA_PATH):
        logger.error(f"Schema file not found at {SCHEMA_PATH}")
        return False
    
    if not os.path.exists(MIGRATE_SCRIPT):
        logger.warning(f"Migration script not found at {MIGRATE_SCRIPT}, data migration will be skipped")
    
    return True

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
        except sqlite3.Error as e:
            logger.error(f"Error executing SQL: {statement[:100]}...")
            logger.error(f"Error details: {str(e)}")
            raise
    
    conn.commit()
    logger.info("Schema SQL executed successfully")

def migrate_existing_data():
    """Run the data migration script if available."""
    if not os.path.exists(MIGRATE_SCRIPT):
        logger.warning("Migration script not found, skipping data migration")
        return
    
    logger.info("Running data migration script...")
    
    try:
        result = subprocess.run(
            [sys.executable, MIGRATE_SCRIPT],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info("Migration script executed successfully")
        logger.info(f"Migration output: {result.stdout}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Migration script failed with error code {e.returncode}")
        logger.error(f"Error output: {e.stderr}")
    except Exception as e:
        logger.error(f"Error running migration script: {str(e)}")

def insert_initial_categories(conn):
    """Insert initial category types if the table is empty."""
    cursor = conn.cursor()
    
    # Check if data already exists
    cursor.execute("SELECT COUNT(*) FROM category_types")
    if cursor.fetchone()[0] > 0:
        logger.info("Category types already populated, skipping initialization")
        return
    
    # Insert standard category types if table is empty
    category_types = [
        ('entity_type', 'General entity classification', 0),
        ('entity_subtype', 'Specific role or position', 0),
        ('party', 'Political party affiliation', 0),
        ('ideology', 'Political ideology or worldview', 1),
        ('trump_stance', 'Position toward Donald Trump', 0),
    ]
    
    try:
        for name, description, is_multiple in category_types:
            cursor.execute(
                "INSERT INTO category_types (name, description, is_multiple) VALUES (?, ?, ?)",
                (name, description, is_multiple)
            )
        
        conn.commit()
        logger.info(f"Inserted {len(category_types)} category types")
        
    except sqlite3.Error as e:
        logger.error(f"Error inserting category types: {str(e)}")
        conn.rollback()

def main():
    """Main function to initialize the database."""
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    logger.info("Starting database initialization")
    
    # Check dependencies
    if not check_dependencies():
        logger.error("Dependency check failed, exiting")
        return
    
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
        # Check if core tables already exist
        core_tables = ['entities', 'politicians', 'influencers', 'categories', 'category_types']
        existing_tables = check_tables_exist(conn, core_tables)
        
        if len(existing_tables) == len(core_tables):
            logger.info("All core tables already exist, skipping schema creation")
        else:
            missing_tables = set(core_tables) - existing_tables
            logger.info(f"Creating missing tables: {', '.join(missing_tables)}")
            
            # Execute schema SQL
            execute_schema_sql(conn, schema_sql)
            
            # Insert initial category types
            insert_initial_categories(conn)
            
            logger.info("Database schema initialized successfully")
        
        # Only migrate data if this is not a complete set of tables
        if len(existing_tables) > 0 and len(existing_tables) < len(core_tables):
            logger.warning("Partial set of tables found. This might cause issues with migration.")
        
        # Migrate existing data if needed
        migrate_existing_data()
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
    finally:
        if conn:
            conn.close()
    
    logger.info("Database initialization completed")

if __name__ == "__main__":
    main() 