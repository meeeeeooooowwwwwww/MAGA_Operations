#!/usr/bin/env python3
"""
Migration script to add committee data from YAML files to the database.
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
    filename='committee_migration_log.txt',
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

def create_committees_table_if_not_exists(cursor):
    """Create committees table if it doesn't exist."""
    if not verify_table_exists(cursor, 'committees'):
        logging.info("Creating committees table...")
        cursor.execute("""
            CREATE TABLE committees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                committee_id TEXT UNIQUE,
                name TEXT,
                type TEXT,
                jurisdiction TEXT,
                url TEXT,
                address TEXT,
                phone TEXT,
                chamber TEXT,
                parent_id TEXT,
                active INTEGER DEFAULT 1,
                metadata TEXT
            )
        """)
        return True
    return False

def create_committee_memberships_table_if_not_exists(cursor):
    """Create committee_memberships table if it doesn't exist."""
    if not verify_table_exists(cursor, 'committee_memberships'):
        logging.info("Creating committee_memberships table...")
        cursor.execute("""
            CREATE TABLE committee_memberships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                committee_id TEXT,
                politician_id INTEGER,
                title TEXT,
                rank INTEGER,
                start_date TEXT,
                end_date TEXT,
                FOREIGN KEY (politician_id) REFERENCES politicians (entity_id),
                FOREIGN KEY (committee_id) REFERENCES committees (committee_id)
            )
        """)
        return True
    return False

def verify_politician_exists(cursor, bioguide_id):
    """Check if a politician with the given bioguide_id exists in the database."""
    cursor.execute("""
        SELECT p.entity_id, e.name
        FROM politicians p
        JOIN entities e ON p.entity_id = e.id
        WHERE p.bioguide_id = ?
    """, (bioguide_id,))
    return cursor.fetchone()

def migrate_committees(cursor, committees_data, is_current=True):
    """Migrate committee data from YAML to database."""
    total_processed = 0
    total_added = 0
    total_updated = 0
    
    for committee in committees_data:
        total_processed += 1
        
        if 'thomas_id' not in committee and 'id' not in committee:
            logging.warning(f"Committee missing ID, skipping: {committee.get('name', 'Unknown')}")
            continue
        
        # Get committee ID from thomas_id or id
        committee_id = committee.get('thomas_id') or committee.get('id', {}).get('thomas')
        if not committee_id:
            logging.warning(f"No valid committee ID found for: {committee.get('name', 'Unknown')}")
            continue
        
        # Check if committee already exists
        cursor.execute("SELECT id FROM committees WHERE committee_id = ?", (committee_id,))
        existing = cursor.fetchone()
        
        metadata = {
            'source': 'legislators-yaml',
            'imported_date': datetime.now().isoformat(),
            'is_current': is_current
        }
        
        # Add any additional fields to metadata
        for key, value in committee.items():
            if key not in ['name', 'type', 'url', 'address', 'phone', 'chamber', 'parent', 'thomas_id']:
                if isinstance(value, dict) and 'thomas' in value:
                    metadata[key] = value['thomas']
                else:
                    metadata[key] = value
        
        # Prepare committee data
        committee_data = {
            'committee_id': committee_id,
            'name': committee.get('name'),
            'type': committee.get('type'),
            'jurisdiction': committee.get('jurisdiction'),
            'url': committee.get('url'),
            'address': committee.get('address'),
            'phone': committee.get('phone'),
            'chamber': committee.get('chamber'),
            'parent_id': committee.get('parent', {}).get('thomas') if isinstance(committee.get('parent'), dict) else committee.get('parent'),
            'active': 1 if is_current else 0,
            'metadata': json.dumps(metadata)
        }
        
        if existing:
            # Update existing committee
            set_clause = ", ".join([f"{key} = ?" for key in committee_data.keys()])
            values = list(committee_data.values())
            values.append(existing['id'])
            
            cursor.execute(f"""
                UPDATE committees 
                SET {set_clause}
                WHERE id = ?
            """, values)
            
            total_updated += 1
            logging.info(f"Updated committee: {committee_data['name']} (ID: {committee_id})")
        else:
            # Insert new committee
            columns = ", ".join(committee_data.keys())
            placeholders = ", ".join(["?"] * len(committee_data))
            values = list(committee_data.values())
            
            cursor.execute(f"""
                INSERT INTO committees ({columns})
                VALUES ({placeholders})
            """, values)
            
            total_added += 1
            logging.info(f"Added committee: {committee_data['name']} (ID: {committee_id})")
    
    return total_processed, total_added, total_updated

def migrate_committee_memberships(cursor, membership_data):
    """Migrate committee membership data from YAML to database."""
    total_processed = 0
    total_added = 0
    total_updated = 0
    total_missing_politician = 0
    
    # The membership data is organized as a dictionary where the key is the committee ID
    # and the value is a list of members
    for committee_id, members in membership_data.items():
        # Check if committee exists in database
        cursor.execute("SELECT id FROM committees WHERE committee_id = ?", (committee_id,))
        committee = cursor.fetchone()
        
        if not committee:
            logging.warning(f"Committee with ID {committee_id} not found in database, skipping")
            continue
            
        # Process each member
        for member in members:
            total_processed += 1
            
            if 'bioguide' not in member:
                logging.warning(f"Member missing bioguide ID for committee {committee_id}, skipping")
                continue
            
            bioguide_id = member['bioguide']
            
            # Verify politician exists
            politician = verify_politician_exists(cursor, bioguide_id)
            if not politician:
                logging.warning(f"No politician found with bioguide_id {bioguide_id}, skipping")
                total_missing_politician += 1
                continue
            
            politician_id = politician['entity_id']
            
            # Prepare membership data
            membership_data = {
                'committee_id': committee_id,
                'politician_id': politician_id,
                'title': member.get('title'),
                'rank': member.get('rank'),
                'start_date': None,  # Not provided in current data
                'end_date': None     # Not provided in current data
            }
            
            # Check if membership already exists
            cursor.execute("""
                SELECT id FROM committee_memberships 
                WHERE committee_id = ? AND politician_id = ?
            """, (committee_id, politician_id))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing membership
                set_clause = ", ".join([f"{key} = ?" for key in membership_data.keys()])
                values = list(membership_data.values())
                values.append(existing['id'])
                
                cursor.execute(f"""
                    UPDATE committee_memberships 
                    SET {set_clause}
                    WHERE id = ?
                """, values)
                
                total_updated += 1
                logging.info(f"Updated membership: {politician['name']} in committee {committee_id}")
            else:
                # Insert new membership
                columns = ", ".join(membership_data.keys())
                placeholders = ", ".join(["?"] * len(membership_data))
                values = list(membership_data.values())
                
                cursor.execute(f"""
                    INSERT INTO committee_memberships ({columns})
                    VALUES ({placeholders})
                """, values)
                
                total_added += 1
                logging.info(f"Added membership: {politician['name']} in committee {committee_id}")
    
    return total_processed, total_added, total_updated, total_missing_politician

def migrate_all_committee_data():
    """Main function to migrate all committee data."""
    conn = connect_to_db()
    cursor = conn.cursor()
    
    try:
        # Create tables if they don't exist
        tables_created = False
        tables_created = create_committees_table_if_not_exists(cursor) or tables_created
        tables_created = create_committee_memberships_table_if_not_exists(cursor) or tables_created
        
        if tables_created:
            logging.info("Created new tables for committee data")
        
        # Migrate current committees
        current_committees_file = 'backups/migrated_data_files/committees-current.yaml'
        current_committees = load_yaml_file(current_committees_file)
        
        if not current_committees:
            logging.error("No data found in current committees YAML file")
        else:
            processed, added, updated = migrate_committees(cursor, current_committees, is_current=True)
            logging.info(f"Current Committees: Processed {processed}, Added {added}, Updated {updated}")
        
        # Migrate historical committees
        historical_committees_file = 'backups/migrated_data_files/committees-historical.yaml'
        historical_committees = load_yaml_file(historical_committees_file)
        
        if not historical_committees:
            logging.error("No data found in historical committees YAML file")
        else:
            processed, added, updated = migrate_committees(cursor, historical_committees, is_current=False)
            logging.info(f"Historical Committees: Processed {processed}, Added {added}, Updated {updated}")
        
        # Migrate committee memberships
        memberships_file = 'backups/migrated_data_files/committee-membership-current.yaml'
        memberships = load_yaml_file(memberships_file)
        
        if not memberships:
            logging.error("No data found in committee memberships YAML file")
        else:
            processed, added, updated, missing = migrate_committee_memberships(cursor, memberships)
            logging.info(f"Committee Memberships: Processed {processed}, Added {added}, Updated {updated}, Missing politicians {missing}")
        
        # Commit the changes
        conn.commit()
        logging.info("Committee data migration completed successfully")
        
    except Exception as e:
        conn.rollback()
        logging.error(f"Error during committee data migration: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    logging.info("Starting committee data migration")
    migrate_all_committee_data()
    logging.info("Committee data migration completed") 