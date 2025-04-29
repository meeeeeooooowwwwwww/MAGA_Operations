import os
import sqlite3
import yaml
import json
import logging
import sys
import atexit
from datetime import datetime

# Set up logging
log_file = "executive_migration_log.txt"
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

def check_entity_exists(cursor, name, create_if_not=True):
    """Check if an entity exists with the given name, create it if not exists."""
    cursor.execute("SELECT id FROM entities WHERE name = ?", (name,))
    entity = cursor.fetchone()
    
    if entity:
        return entity['id']
    
    if create_if_not:
        # Create new entity
        normalized_name = name.lower()
        now = datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute("""
            INSERT INTO entities (
                name, normalized_name, entity_type, 
                first_appearance_date, last_updated
            ) VALUES (?, ?, ?, ?, ?)
        """, (name, normalized_name, 'politician', now, now))
        
        return cursor.lastrowid
    
    return None

def migrate_executive_officials():
    """Migrate executive branch officials data from YAML files."""
    conn = connect_to_db()
    cursor = conn.cursor()
    
    # Load executive data
    executive_data = load_yaml_file('backups/migrated_data_files/executive.yaml')
    
    if not executive_data:
        logger.error("No executive officials data found. Migration aborted.")
        return
    
    total_records = 0
    updated_records = 0
    new_records = 0
    skipped_records = 0
    
    # Process each executive official
    for official in executive_data:
        total_records += 1
        
        # Get bioguide_id if available
        bioguide_id = official.get('id', {}).get('bioguide', '')
        
        # Get name
        if 'name' not in official:
            logger.warning(f"Official missing name. Skipping.")
            skipped_records += 1
            continue
        
        first_name = official['name'].get('first', '')
        last_name = official['name'].get('last', '')
        full_name = official['name'].get('official_full', f"{first_name} {last_name}")
        
        if not full_name:
            logger.warning(f"Official missing name. Skipping.")
            skipped_records += 1
            continue
        
        # Check if we already have this person
        if bioguide_id:
            cursor.execute("SELECT entity_id FROM politicians WHERE bioguide_id = ?", (bioguide_id,))
            politician = cursor.fetchone()
            if politician:
                entity_id = politician['entity_id']
                logger.debug(f"Found existing politician record for {full_name} (bioguide: {bioguide_id})")
            else:
                entity_id = check_entity_exists(cursor, full_name)
                
                # Create politician record
                cursor.execute("""
                    INSERT INTO politicians (entity_id, bioguide_id)
                    VALUES (?, ?)
                """, (entity_id, bioguide_id))
        else:
            entity_id = check_entity_exists(cursor, full_name)
        
        # Process each term
        terms = official.get('terms', [])
        if not terms:
            logger.debug(f"No terms found for {full_name}")
            continue
        
        for term in terms:
            if term.get('type') not in ['prez', 'viceprez']:
                continue
                
            # Prepare executive office data
            position = 'President' if term.get('type') == 'prez' else 'Vice President'
            start_date = term.get('start', '')
            end_date = term.get('end', '')
            is_current = 1 if end_date > datetime.now().strftime('%Y-%m-%d') else 0
            
            # Check if record already exists
            cursor.execute("""
                SELECT id FROM executive_officials 
                WHERE entity_id = ? AND position = ? AND start_date = ?
            """, (entity_id, position, start_date))
            existing = cursor.fetchone()
            
            executive_data = {
                'entity_id': entity_id,
                'position': position,
                'start_date': start_date,
                'end_date': end_date,
                'department': 'Executive Branch',
                'branch': 'Executive',
                'is_current': is_current,
                'metadata': json.dumps({
                    'party': term.get('party', ''),
                    'how': term.get('how', ''),
                    'bioguide_id': bioguide_id
                })
            }
            
            if existing:
                # Update existing record
                set_clause = ", ".join([f"{key} = ?" for key in executive_data.keys()])
                values = list(executive_data.values())
                values.append(existing['id'])
                
                cursor.execute(
                    f"UPDATE executive_officials SET {set_clause} WHERE id = ?",
                    values
                )
                updated_records += 1
                logger.debug(f"Updated {position} record for {full_name} ({start_date} to {end_date})")
            else:
                # Insert new record
                columns = ", ".join(executive_data.keys())
                placeholders = ", ".join(["?"] * len(executive_data))
                values = list(executive_data.values())
                
                cursor.execute(
                    f"INSERT INTO executive_officials ({columns}) VALUES ({placeholders})",
                    values
                )
                new_records += 1
                logger.debug(f"Added new {position} record for {full_name} ({start_date} to {end_date})")
    
    # Commit changes
    conn.commit()
    
    # Generate migration summary
    logger.info(f"\nExecutive Officials Migration Summary:")
    logger.info(f"Total records processed: {total_records}")
    logger.info(f"Records updated: {updated_records}")
    logger.info(f"New records added: {new_records}")
    logger.info(f"Records skipped: {skipped_records}")
    
    conn.close()

if __name__ == "__main__":
    logger.info("Starting executive officials data migration...")
    
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
    migrate_executive_officials()
    
    logger.info("Executive officials data migration completed successfully!") 