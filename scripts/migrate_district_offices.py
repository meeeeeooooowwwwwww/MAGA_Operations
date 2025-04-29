#!/usr/bin/env python3
"""
Migration script to add district office data from YAML files to the database.
"""
import os
import sys
import yaml
import sqlite3
import logging
import atexit
import json
from datetime import datetime

# Set up logging
log_file = "district_offices_migration_log.txt"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Clean exit handler
def exit_handler():
    logger.info("Migration script completed and exiting cleanly.")
    
atexit.register(exit_handler)

def connect_to_db():
    """Connect to the SQLite database."""
    try:
        conn = sqlite3.connect('maga_ops.db')
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        sys.exit(1)

def load_yaml_file(file_path):
    """Load and parse YAML file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
        logger.info(f"Successfully loaded YAML file: {file_path}")
        return data
    except Exception as e:
        logger.error(f"Error loading YAML file {file_path}: {e}")
        return None

def verify_table_exists(cursor, table_name):
    """Check if a table exists in the database."""
    cursor.execute(f"""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='{table_name}'
    """)
    return cursor.fetchone() is not None

def create_offices_table_if_not_exists(cursor):
    """Create district_offices table if it doesn't exist."""
    if not verify_table_exists(cursor, 'district_offices'):
        logger.info("Creating district_offices table...")
        cursor.execute("""
            CREATE TABLE district_offices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                politician_id INTEGER,
                office_name TEXT,
                address TEXT,
                suite TEXT,
                building TEXT,
                city TEXT,
                state TEXT,
                zip TEXT,
                phone TEXT,
                fax TEXT,
                latitude REAL,
                longitude REAL,
                is_main_office INTEGER DEFAULT 0,
                office_type TEXT DEFAULT 'district',
                metadata TEXT,
                FOREIGN KEY (politician_id) REFERENCES politicians (entity_id)
            )
        """)
        return True
    return False

def verify_politician_exists(cursor, bioguide_id):
    """Verify if a politician with the given bioguide_id exists."""
    cursor.execute("SELECT entity_id FROM politicians WHERE bioguide_id = ?", (bioguide_id,))
    return cursor.fetchone()

def migrate_district_offices():
    """Migrate district offices data from YAML files."""
    conn = connect_to_db()
    cursor = conn.cursor()
    
    # Load district offices data
    district_offices = load_yaml_file('backups/migrated_data_files/legislators-district-offices.yaml')
    
    if not district_offices:
        logger.error("No district offices data found. Migration aborted.")
        return
    
    total_records = 0
    updated_records = 0
    new_records = 0
    skipped_records = 0
    
    # Process each legislator's offices
    for legislator in district_offices:
        bioguide_id = legislator.get('id', {}).get('bioguide', '')
        if not bioguide_id:
            logger.warning(f"Legislator missing bioguide ID. Skipping.")
            continue
        
        # Find the politician
        politician = verify_politician_exists(cursor, bioguide_id)
        if not politician:
            logger.warning(f"No politician found with bioguide_id {bioguide_id}. Skipping.")
            continue
        
        politician_id = politician['entity_id']
        
        # Process each office
        offices = legislator.get('offices', [])
        if not offices:
            logger.debug(f"No offices found for {bioguide_id}")
            continue
        
        for office in offices:
            total_records += 1
            
            office_id = office.get('id', '')
            if not office_id:
                logger.warning(f"Office missing ID for politician {bioguide_id}. Skipping.")
                skipped_records += 1
                continue
            
            # Check if the office already exists
            cursor.execute(
                "SELECT id FROM district_offices WHERE office_name = ? AND politician_id = ?", 
                (office_id, politician_id)
            )
            existing = cursor.fetchone()
            
            # Prepare office data
            office_data = {
                'politician_id': politician_id,
                'office_name': office_id,
                'address': office.get('address', ''),
                'suite': office.get('suite', ''),
                'building': office.get('building', ''),
                'city': office.get('city', ''),
                'state': office.get('state', ''),
                'zip': office.get('zip', ''),
                'phone': office.get('phone', ''),
                'fax': office.get('fax', ''),
                'latitude': office.get('latitude', 0.0),
                'longitude': office.get('longitude', 0.0),
                'is_main_office': 1 if office_id.lower().endswith('main') else 0,
                'office_type': 'district',
                'metadata': json.dumps({
                    'hours': office.get('hours', ''),
                    'id': office_id
                })
            }
            
            if existing:
                # Update existing office
                set_clause = ", ".join([f"{key} = ?" for key in office_data.keys()])
                values = list(office_data.values())
                values.append(existing['id'])
                
                cursor.execute(
                    f"UPDATE district_offices SET {set_clause} WHERE id = ?",
                    values
                )
                updated_records += 1
                logger.debug(f"Updated office: {office_id} for {bioguide_id}")
            else:
                # Insert new office
                columns = ", ".join(office_data.keys())
                placeholders = ", ".join(["?"] * len(office_data))
                values = list(office_data.values())
                
                cursor.execute(
                    f"INSERT INTO district_offices ({columns}) VALUES ({placeholders})",
                    values
                )
                new_records += 1
                logger.debug(f"Added new office: {office_id} for {bioguide_id}")
    
    # Commit changes
    conn.commit()
    
    # Generate migration summary
    logger.info(f"\nDistrict Offices Migration Summary:")
    logger.info(f"Total records processed: {total_records}")
    logger.info(f"Records updated: {updated_records}")
    logger.info(f"New records added: {new_records}")
    logger.info(f"Records skipped: {skipped_records}")
    
    conn.close()

if __name__ == "__main__":
    logger.info("Starting district offices data migration...")
    
    # Create a backup of the database
    backup_filename = f"maga_ops_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    try:
        import shutil
        shutil.copy2("maga_ops.db", backup_filename)
        logger.info(f"Database backed up to {backup_filename}")
    except Exception as e:
        logger.error(f"Failed to backup database: {e}")
        sys.exit(1)
    
    # Run migrations
    migrate_district_offices()
    
    logger.info("District offices data migration completed successfully!") 