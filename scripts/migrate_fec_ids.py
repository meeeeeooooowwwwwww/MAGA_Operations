#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Data Migration Script for FEC Candidate IDs
This script migrates FEC candidate IDs from legislators YAML files to the politicians table
"""

import os
import sys
import sqlite3
import yaml
import pickle
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fec_migration_log.txt"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("fec_migration")

# Project paths
PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, 'maga_ops.db')
BACKUPS_DIR = os.path.join(PROJECT_ROOT, 'backups')
MIGRATED_FILES_DIR = os.path.join(BACKUPS_DIR, 'migrated_data_files')

# Track stats
total_records = 0
updated_records = 0
missing_records = 0

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

def migrate_fec_ids(file_path):
    """Migrate FEC candidate IDs from legislators YAML file."""
    global total_records, updated_records, missing_records
    
    logger.info(f"Migrating FEC IDs from {file_path}")
    
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
            
            # Get FEC candidate ID(s)
            fec_ids = ids.get('fec', [])
            
            # Skip if no FEC IDs
            if not fec_ids:
                logger.debug(f"No FEC ID for {bioguide_id}, skipping")
                missing_records += 1
                continue
            
            # Use the first FEC ID (most recent)
            fec_candidate_id = fec_ids[0] if isinstance(fec_ids, list) else fec_ids
            
            # Update the politicians table
            cursor.execute("""
                UPDATE politicians SET
                fec_candidate_id = ?
                WHERE bioguide_id = ?
            """, (fec_candidate_id, bioguide_id))
            
            # Check if any row was affected
            if cursor.rowcount > 0:
                updated_records += 1
                logger.info(f"Updated FEC ID for politician with bioguide_id: {bioguide_id} to {fec_candidate_id}")
            else:
                logger.warning(f"No politician found with bioguide_id: {bioguide_id}")
                missing_records += 1
        
        conn.commit()
        logger.info(f"Successfully migrated FEC IDs from {file_path}")
        return True
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Error migrating FEC IDs from {file_path}: {e}")
        return False
    
    finally:
        conn.close()

def main():
    """Main execution function."""
    global total_records, updated_records, missing_records
    
    logger.info("Starting FEC ID migration")
    
    # List of legislators YAML files
    legislators_files = [
        os.path.join(MIGRATED_FILES_DIR, 'legislators-current.yaml'),
        os.path.join(PROJECT_ROOT, 'legislators-historical.yaml')
    ]
    
    for file_path in legislators_files:
        if os.path.exists(file_path):
            migrate_fec_ids(file_path)
    
    # Print summary
    logger.info("=== FEC ID MIGRATION SUMMARY ===")
    logger.info(f"Total records processed: {total_records}")
    logger.info(f"Records updated: {updated_records}")
    logger.info(f"Records missing or not found: {missing_records}")
    
    # Also print to console
    print("\n=== FEC ID MIGRATION SUMMARY ===")
    print(f"Total records processed: {total_records}")
    print(f"Records updated: {updated_records}")
    print(f"Records missing or not found: {missing_records}")
    
    logger.info("FEC ID migration complete")

if __name__ == "__main__":
    main() 