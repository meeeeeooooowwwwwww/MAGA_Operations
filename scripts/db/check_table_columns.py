#!/usr/bin/env python3
"""
Check Table Columns

This script checks the column names in a specified table to help diagnose schema issues.
"""
import os
import sys
import sqlite3
import logging
from tabulate import tabulate

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

def check_table_columns(table_name):
    """Check columns of a specified table."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        if not columns:
            print(f"Table '{table_name}' does not exist in the database.")
            return
        
        column_info = []
        for col in columns:
            column_info.append({
                'cid': col['cid'],
                'name': col['name'],
                'type': col['type'],
                'notnull': col['notnull'],
                'default': col['dflt_value'],
                'primary_key': col['pk']
            })
        
        print(f"\nColumns in table '{table_name}':")
        print(tabulate(column_info, headers="keys", tablefmt="simple"))
        
    except sqlite3.Error as e:
        logger.error(f"Database error: {str(e)}")
    finally:
        if conn:
            conn.close()

def list_all_tables():
    """List all tables in the database."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, type FROM sqlite_master WHERE type='table' OR type='view' ORDER BY type, name")
        tables = cursor.fetchall()
        
        if not tables:
            print("No tables or views found in the database.")
            return
        
        table_info = []
        for table in tables:
            table_info.append({
                'name': table['name'],
                'type': table['type']
            })
        
        print("\nTables and views in the database:")
        print(tabulate(table_info, headers="keys", tablefmt="simple"))
        
    except sqlite3.Error as e:
        logger.error(f"Database error: {str(e)}")
    finally:
        if conn:
            conn.close()

def main():
    """Main function."""
    logger.info("Starting table column check")
    
    if len(sys.argv) > 1:
        table_name = sys.argv[1]
        check_table_columns(table_name)
    else:
        list_all_tables()
        print("\nTo check a specific table's columns, run:")
        print("python scripts/db/check_table_columns.py <table_name>")

if __name__ == "__main__":
    main() 