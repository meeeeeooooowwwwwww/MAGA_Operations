#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Data Migration Script for Office Data
This script migrates office data from legislators YAML files to the politicians table
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
        logging.FileHandler("office_migration_log.txt"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("office_migration")

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

def migrate_office_data(file_path):
    """Migrate office data from legislators YAML file."""
    global total_records, updated_records, missing_records
    
    logger.info(f"Migrating office data from {file_path}")
    
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
            
            # Get most recent term
            terms = legislator.get('terms', [])
            if not terms:
                logger.warning(f"No terms found for {bioguide_id}, skipping")
                missing_records += 1
                continue
                
            current_term = terms[-1]  # most recent term
            
            # Format office from type
            office_type = current_term.get('type', '').upper()
            office = None
            if office_type == 'SEN':
                office = 'Senator'
            elif office_type == 'REP':
                office = 'Representative'
            else:
                office = office_type.capitalize()
            
            # Get state information
            state = current_term.get('state')
            district = current_term.get('district')
            
            # Verify this politician exists and has matching state
            politician = verify_politician_exists(cursor, bioguide_id)
            
            if not politician:
                logger.warning(f"No politician found with bioguide_id: {bioguide_id}")
                missing_records += 1
                continue
            
            politician_name = politician['name']
            db_state = politician['state']
            
            # Check if state matches to ensure we're updating the right record
            if state and db_state and state != db_state:
                logger.warning(f"State mismatch for {politician_name}: YAML={state}, DB={db_state}")
                # We'll still update, but with a warning
            
            # Update the politicians table
            cursor.execute("""
                UPDATE politicians SET
                office = ?,
                district = ?
                WHERE bioguide_id = ?
            """, (office, district, bioguide_id))
            
            # Check if any row was affected
            if cursor.rowcount > 0:
                updated_records += 1
                logger.info(f"Updated office for {politician_name} with bioguide_id: {bioguide_id} to {office}")
            else:
                logger.warning(f"Failed to update office for {politician_name}")
                missing_records += 1
        
        conn.commit()
        logger.info(f"Successfully migrated office data from {file_path}")
        return True
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Error migrating office data from {file_path}: {e}")
        return False
    
    finally:
        conn.close()

def main():
    """Main execution function."""
    global total_records, updated_records, missing_records
    
    logger.info("Starting office data migration")
    
    # List of legislators YAML files
    legislators_files = [
        os.path.join(MIGRATED_FILES_DIR, 'legislators-current.yaml'),
        os.path.join(PROJECT_ROOT, 'legislators-historical.yaml')
    ]
    
    for file_path in legislators_files:
        if os.path.exists(file_path):
            migrate_office_data(file_path)
    
    # Print summary
    logger.info("=== OFFICE DATA MIGRATION SUMMARY ===")
    logger.info(f"Total records processed: {total_records}")
    logger.info(f"Records updated: {updated_records}")
    logger.info(f"Records missing or not found: {missing_records}")
    
    # Also print to console
    print("\n=== OFFICE DATA MIGRATION SUMMARY ===")
    print(f"Total records processed: {total_records}")
    print(f"Records updated: {updated_records}")
    print(f"Records missing or not found: {missing_records}")
    
    logger.info("Office data migration complete")

if __name__ == "__main__":
    main() 