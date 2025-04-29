import os
import sqlite3
import yaml
import json
import logging
import sys
import atexit
import datetime

# Set up logging
log_file = "committee_migration_log.txt"
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

def migrate_committees():
    """Migrate committee data from YAML files."""
    conn = connect_to_db()
    cursor = conn.cursor()
    
    # Load committee data
    committees_current = load_yaml_file('backups/migrated_data_files/committees-current.yaml')
    
    if not committees_current:
        logger.error("No committee data found. Migration aborted.")
        return
    
    total_committees = 0
    updated_committees = 0
    new_committees = 0
    
    # Process each committee
    for committee in committees_current:
        total_committees += 1
        
        # Extract committee_id
        committee_id = committee.get('thomas_id', '')
        if not committee_id:
            logger.warning(f"Committee missing ID: {committee.get('name', 'Unknown')}. Skipping.")
            continue
        
        cursor.execute("SELECT id FROM committees WHERE committee_id = ?", (committee_id,))
        existing = cursor.fetchone()
        
        # Prepare committee data
        committee_data = {
            'committee_id': committee_id,
            'name': committee.get('name', ''),
            'type': committee.get('type', ''),
            'jurisdiction': committee.get('jurisdiction', ''),
            'url': committee.get('url', ''),
            'address': committee.get('address', ''),
            'phone': committee.get('phone', ''),
            'chamber': committee.get('type', ''),
            'active': 1,
            'metadata': json.dumps({
                'subcommittees': committee.get('subcommittees', []),
                'minority_url': committee.get('minority_url', ''),
                'rss_url': committee.get('rss_url', '')
            })
        }
        
        if existing:
            # Update existing committee
            set_clause = ", ".join([f"{key} = ?" for key in committee_data.keys()])
            values = list(committee_data.values())
            values.append(existing['id'])
            
            cursor.execute(
                f"UPDATE committees SET {set_clause} WHERE id = ?",
                values
            )
            updated_committees += 1
        else:
            # Insert new committee
            columns = ", ".join(committee_data.keys())
            placeholders = ", ".join(["?"] * len(committee_data))
            values = list(committee_data.values())
            
            cursor.execute(
                f"INSERT INTO committees ({columns}) VALUES ({placeholders})",
                values
            )
            new_committees += 1
    
    # Commit changes
    conn.commit()
    
    # Generate migration summary
    logger.info(f"\nCommittee Migration Summary:")
    logger.info(f"Total committees processed: {total_committees}")
    logger.info(f"Committees updated: {updated_committees}")
    logger.info(f"New committees added: {new_committees}")
    
    conn.close()

if __name__ == "__main__":
    logger.info("Starting committee data migration...")
    
    # Create a backup of the database
    backup_filename = f"maga_ops_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    try:
        import shutil
        shutil.copy2("maga_ops.db", backup_filename)
        logger.info(f"Database backed up to {backup_filename}")
    except Exception as e:
        logger.error(f"Failed to backup database: {e}")
        sys.exit(1)
    
    # Run migrations
    migrate_committees()
    
    logger.info("Committee data migration completed successfully!") 