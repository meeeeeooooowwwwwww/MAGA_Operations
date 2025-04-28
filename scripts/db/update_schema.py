#!/usr/bin/env python3
"""
Database Schema Update Script

Updates the database schema with new tables and views from schema.sql
"""
import os
import sys
import sqlite3
import logging
from pathlib import Path

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
SCHEMA_PATH = os.path.join(PROJECT_ROOT, 'scripts', 'db', 'schema.sql')

def read_schema_sql():
    """Read the schema SQL file."""
    with open(SCHEMA_PATH, 'r') as f:
        return f.read()

def get_connection():
    """Get a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def check_table_exists(conn, table_name):
    """Check if a table exists in the database."""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    return cursor.fetchone() is not None

def check_view_exists(conn, view_name):
    """Check if a view exists in the database."""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='view' AND name=?", (view_name,))
    return cursor.fetchone() is not None

def extract_table_statements(schema_sql):
    """Extract CREATE TABLE statements from schema SQL."""
    tables = {}
    current_table = None
    lines = schema_sql.split('\n')
    
    for line in lines:
        line = line.strip()
        if line.startswith('CREATE TABLE '):
            # Extract table name
            table_name = line.split('CREATE TABLE ')[1].split('(')[0].strip()
            current_table = table_name
            tables[current_table] = [line]
        elif line.startswith('CREATE VIEW '):
            # Extract view name
            view_name = line.split('CREATE VIEW ')[1].split(' ')[0].strip()
            current_table = view_name
            tables[current_table] = [line]
        elif current_table is not None:
            tables[current_table].append(line)
            if line.endswith(';'):
                # End of statement
                tables[current_table] = '\n'.join(tables[current_table])
                current_table = None
    
    return tables

def update_database_schema(conn, schema_sql):
    """Update database schema with new tables and views."""
    cursor = conn.cursor()
    
    # Extract CREATE TABLE statements
    table_statements = extract_table_statements(schema_sql)
    
    for name, statement in table_statements.items():
        # Skip if statement doesn't end properly
        if not statement.strip().endswith(';'):
            continue
            
        # Check if it's a table or view
        is_view = statement.strip().upper().startswith('CREATE VIEW')
        
        # Check if table/view exists
        if is_view:
            exists = check_view_exists(conn, name)
        else:
            exists = check_table_exists(conn, name)
        
        if not exists:
            try:
                cursor.execute(statement)
                if is_view:
                    logger.info(f"Created view: {name}")
                else:
                    logger.info(f"Created table: {name}")
            except sqlite3.Error as e:
                logger.error(f"Error creating {name}: {str(e)}")
                logger.error(f"Statement: {statement[:100]}...")
    
    # Get index statements
    index_statements = []
    for line in schema_sql.split('\n'):
        line = line.strip()
        if line.startswith('CREATE INDEX ') and line.endswith(';'):
            index_statements.append(line)
    
    # Create indices
    for statement in index_statements:
        try:
            # Extract index name
            index_name = statement.split('CREATE INDEX ')[1].split(' ')[0].strip()
            
            # Check if index exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name=?", (index_name,))
            if cursor.fetchone() is None:
                cursor.execute(statement)
                logger.info(f"Created index: {index_name}")
        except sqlite3.Error as e:
            logger.error(f"Error creating index: {str(e)}")
            logger.error(f"Statement: {statement}")
    
    conn.commit()
    logger.info("Database schema update completed")

def main():
    """Main function to run the schema update."""
    logger.info("Starting database schema update")
    
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
        # Update database schema
        update_database_schema(conn, schema_sql)
    except Exception as e:
        logger.error(f"Schema update failed: {str(e)}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main() 