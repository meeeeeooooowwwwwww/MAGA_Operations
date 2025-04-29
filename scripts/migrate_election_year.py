#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Data Migration Script for Election Year Data
This script migrates election year data from legislators YAML files to the politicians table
"""

import os
import sys
import sqlite3
import yaml
import pickle
import logging
from datetime import datetime
import atexit

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("election_year_migration_log.txt"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("election_year_migration")

# Project paths
PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, 'maga_ops.db')
BACKUPS_DIR = os.path.join(PROJECT_ROOT, 'backups')
MIGRATED_FILES_DIR = os.path.join(BACKUPS_DIR, 'migrated_data_files')

# Track stats
total_records = 0
updated_records = 0
missing_records = 0

# Register exit handler to ensure clean termination
def exit_handler():
    print("
Script completed. No input required.")
    # Don't call sys.exit() from an atexit handler

atexit.register(exit_handler)

def get_connection():
    """Create and return a database connection."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"Error connecting to database: {e}")
        raise

def load_yaml_file(file_path):
    """Load a YAML file, handling pickle format if needed."""
    try:
        # Check if it's a pickle file
        if file_path.endswith('.pickle'):
            with open(file_path, 'rb') as f:
                return pickle.load(f)
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading YAML file {file_path}: {e}")
        return None

def verify_politician_exists(cursor, bioguide_id):
    """Verify that a politician exists with the given bioguide_id."""
    cursor.execute("""
        SELECT e.name, p.state 
        FROM politicians p
        JOIN entities e ON p.entity_id = e.id
        WHERE p.bioguide_id = ?
    """, (bioguide_id,))
    return cursor.fetchone()

def extract_election_year(terms):
    """Extract the most recent election year from terms."""
    if not terms:
        return None
    
    # Get the most recent term
    current_term = terms[-1]
    
    # Try to extract the start year (first election)
    start_date = current_term.get('start')
    if start_date and len(start_date) >= 4:
        return int(start_date[:4])
    
    return None

def migrate_election_year_data(file_path):
    """Migrate election year data from legislators YAML file."""
    global total_records, updated_records, missing_records
    
    logger.info(f"Migrating election year data from {file_path}")
    
    data = load_yaml_file(file_path)
    if not data:
        logger.error(f"Failed to load legislators data from {file_path}")
        return False
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        for legislator in data:
            total_records += 1
            
            # Get bioguide id for unique identification
            ids = legislator.get('id', {})
            bioguide_id = ids.get('bioguide')
            
            if not bioguide_id:
                logger.warning(f"Legislator missing bioguide ID, skipping")
                missing_records += 1
                continue
            
            # Get terms information
            terms = legislator.get('terms', [])
            election_year = extract_election_year(terms)
            
            if not election_year:
                logger.debug(f"Could not extract election year for {bioguide_id}, skipping")
                missing_records += 1
                continue
                
            # Verify this politician exists
            politician = verify_politician_exists(cursor, bioguide_id)
            
            if not politician:
                logger.warning(f"No politician found with bioguide_id: {bioguide_id}")
                missing_records += 1
                continue
            
            politician_name = politician['name']
            
            # Update the politicians table
            cursor.execute("""
                UPDATE politicians SET
                election_year = ?
                WHERE bioguide_id = ?
            """, (election_year, bioguide_id))
            
            # Check if any row was affected
            if cursor.rowcount > 0:
                updated_records += 1
                logger.info(f"Updated election year for {politician_name} with bioguide_id: {bioguide_id} to {election_year}")
            else:
                logger.warning(f"Failed to update election year for {politician_name}")
                missing_records += 1
        
        conn.commit()
        logger.info(f"Successfully migrated election year data from {file_path}")
        return True
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Error migrating election year data from {file_path}: {e}")
        return False
    
    finally:
        conn.close()

def main():
    """Main execution function."""
    global total_records, updated_records, missing_records
    
    logger.info("Starting election year data migration")
    
    # List of legislators YAML files
    legislators_files = [
        os.path.join(MIGRATED_FILES_DIR, 'legislators-current.yaml'),
        os.path.join(PROJECT_ROOT, 'legislators-historical.yaml')
    ]
    
    for file_path in legislators_files:
        if os.path.exists(file_path):
            migrate_election_year_data(file_path)
    
    # Print summary
    logger.info("=== ELECTION YEAR DATA MIGRATION SUMMARY ===")
    logger.info(f"Total records processed: {total_records}")
    logger.info(f"Records updated: {updated_records}")
    logger.info(f"Records missing or not found: {missing_records}")
    
    # Also print to console
    print("\n=== ELECTION YEAR DATA MIGRATION SUMMARY ===")
    print(f"Total records processed: {total_records}")
    print(f"Records updated: {updated_records}")
    print(f"Records missing or not found: {missing_records}")
    
    logger.info("Election year data migration complete")

if __name__ == "__main__":
    main() 