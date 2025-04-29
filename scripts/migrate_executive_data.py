#!/usr/bin/env python3
"""
Migration script to add executive branch data from YAML files to the database.
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
logging.basicConfig(
    filename='executive_migration_log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Add console handler
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger('').addHandler(console)

# Setup exit handler to ensure clean termination
def exit_handler():
    print("\nScript completed. No input required.")
    # Don't call sys.exit() from an atexit handler

atexit.register(exit_handler)

def connect_to_db():
    """Connect to the SQLite database."""
    try:
        conn = sqlite3.connect('maga_ops.db')
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logging.error(f"Database connection error: {e}")
        sys.exit(1)

def load_yaml_file(file_path):
    """Load YAML file and return its contents."""
    try:
        logging.info(f"Loading YAML file: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logging.error(f"Error loading YAML file {file_path}: {e}")
        return None

def verify_table_exists(cursor, table_name):
    """Check if a table exists in the database."""
    cursor.execute(f"""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='{table_name}'
    """)
    return cursor.fetchone() is not None

def create_executive_table_if_not_exists(cursor):
    """Create executive_officials table if it doesn't exist."""
    if not verify_table_exists(cursor, 'executive_officials'):
        logging.info("Creating executive_officials table...")
        cursor.execute("""
            CREATE TABLE executive_officials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id INTEGER,
                position TEXT,
                start_date TEXT,
                end_date TEXT,
                department TEXT,
                branch TEXT DEFAULT 'executive',
                is_current INTEGER DEFAULT 1,
                metadata TEXT,
                FOREIGN KEY (entity_id) REFERENCES entities (id)
            )
        """)
        return True
    return False

def ensure_entity_exists(cursor, name, party=None):
    """
    Check if an entity with the given name exists. If not, create it.
    Returns the entity_id.
    """
    # Handle case where name might be a dictionary or other non-string type
    if not isinstance(name, str):
        if isinstance(name, dict) and 'first' in name and 'last' in name:
            # If name is a dictionary with first and last keys, combine them
            name = f"{name['first']} {name['last']}"
        else:
            # Convert to string if it's another type
            name = str(name)
    
    # Clean name and check if entity exists
    name = name.strip()
    cursor.execute("SELECT id FROM entities WHERE name = ?", (name,))
    result = cursor.fetchone()
    
    if result:
        return result['id']
    
    # Entity doesn't exist, create it
    known_affiliations = json.dumps({"party": party}) if party else None
    
    cursor.execute("""
        INSERT INTO entities (name, entity_type, known_affiliations)
        VALUES (?, 'politician', ?)
    """, (name, known_affiliations))
    
    return cursor.lastrowid

def migrate_executive_data(cursor, executive_data):
    """Migrate executive branch data from YAML to database."""
    total_processed = 0
    total_added = 0
    total_updated = 0
    
    logging.info(f"Starting to process {len(executive_data)} executive records")
    
    for person in executive_data:
        total_processed += 1
        
        if 'name' not in person:
            logging.warning(f"Record {total_processed} missing name, skipping")
            continue
        
        name = person['name']
        logging.info(f"Processing executive record {total_processed}: {name}")
        
        # Extract party if available
        party = None
        if 'party' in person:
            party = person['party']
        
        try:
            # Ensure entity exists
            entity_id = ensure_entity_exists(cursor, name, party)
            logging.info(f"Using entity ID {entity_id} for {name}")
            
            # Process each term/position in the executive branch
            if 'terms' not in person or not person['terms']:
                logging.warning(f"No terms found for {name}, skipping")
                continue
            
            for term in person['terms']:
                if 'type' not in term or term['type'] != 'exec':
                    logging.debug(f"Skipping non-executive term for {name}: {term.get('type', 'unknown')}")
                    continue  # Skip non-executive positions
                
                # Get term details
                position = term.get('title', '')
                start_date = term.get('start', '')
                end_date = term.get('end', '')
                department = term.get('department', '')
                
                logging.info(f"Processing position: {position} for {name} ({start_date} - {end_date})")
                
                # Determine if this is a current position
                is_current = 1
                if end_date:
                    # If end date exists and is in the past, not current
                    try:
                        end_year = int(end_date.split('-')[0])
                        current_year = datetime.now().year
                        if end_year < current_year:
                            is_current = 0
                    except (ValueError, IndexError):
                        pass
                
                # Check if this executive position already exists
                cursor.execute("""
                    SELECT id FROM executive_officials 
                    WHERE entity_id = ? AND position = ? AND start_date = ?
                """, (entity_id, position, start_date))
                existing = cursor.fetchone()
                
                # Prepare metadata
                metadata = {
                    'source': 'executive-yaml',
                    'imported_date': datetime.now().isoformat()
                }
                
                # Add any additional fields to metadata
                for key, value in term.items():
                    if key not in ['title', 'start', 'end', 'department', 'type']:
                        metadata[key] = value
                
                # Prepare executive data
                executive_position = {
                    'entity_id': entity_id,
                    'position': position,
                    'start_date': start_date,
                    'end_date': end_date,
                    'department': department,
                    'branch': 'executive',
                    'is_current': is_current,
                    'metadata': json.dumps(metadata)
                }
                
                if existing:
                    # Update existing position
                    set_clause = ", ".join([f"{key} = ?" for key in executive_position.keys()])
                    values = list(executive_position.values())
                    values.append(existing['id'])
                    
                    cursor.execute(f"""
                        UPDATE executive_officials 
                        SET {set_clause}
                        WHERE id = ?
                    """, values)
                    
                    total_updated += 1
                    logging.info(f"Updated executive position: {position} for {name}")
                else:
                    # Insert new position
                    columns = ", ".join(executive_position.keys())
                    placeholders = ", ".join(["?"] * len(executive_position))
                    values = list(executive_position.values())
                    
                    cursor.execute(f"""
                        INSERT INTO executive_officials ({columns})
                        VALUES ({placeholders})
                    """, values)
                    
                    total_added += 1
                    logging.info(f"Added executive position: {position} for {name}")
        except Exception as e:
            logging.error(f"Error processing {name}: {e}")
    
    logging.info(f"Executive migration completed: Processed {total_processed}, Added {total_added}, Updated {total_updated}")
    return total_processed, total_added, total_updated

def migrate_all_executive_data():
    """Main function to migrate executive branch data."""
    conn = connect_to_db()
    cursor = conn.cursor()
    
    try:
        # Create table if it doesn't exist
        if create_executive_table_if_not_exists(cursor):
            logging.info("Created new executive_officials table")
        
        # Load executive YAML file
        executive_file = 'backups/migrated_data_files/executive.yaml'
        executive_data = load_yaml_file(executive_file)
        
        if not executive_data:
            logging.error("No data found in the executive YAML file")
            return
        
        logging.info(f"Found {len(executive_data)} records in the executive YAML file")
        
        # Migrate executive data
        processed, added, updated = migrate_executive_data(cursor, executive_data)
        
        # Log the summary
        logging.info(f"Migration Summary:")
        logging.info(f"Total records processed: {processed}")
        logging.info(f"Total positions added: {added}")
        logging.info(f"Total positions updated: {updated}")
        
        # Commit the changes
        conn.commit()
        logging.info("Executive data migration completed successfully")
        
    except Exception as e:
        conn.rollback()
        logging.error(f"Error during executive data migration: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    logging.info("Starting executive data migration")
    migrate_all_executive_data()
    logging.info("Executive data migration completed") 