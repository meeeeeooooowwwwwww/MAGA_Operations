#!/usr/bin/env python3
"""
Migration script to add detailed biographical information for politicians.
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
    filename='bio_migration_log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Add console handler
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger('').addHandler(console)

# Setup exit handler to ensure clean termination
def exit_handler():
    print("
Script completed. No input required.")
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

def verify_politician_exists(cursor, bioguide_id):
    """Check if a politician with the given bioguide_id exists in the database."""
    cursor.execute("""
        SELECT p.entity_id, e.name, e.bio
        FROM politicians p
        JOIN entities e ON p.entity_id = e.id
        WHERE p.bioguide_id = ?
    """, (bioguide_id,))
    return cursor.fetchone()

def calculate_years_in_office(terms):
    """Calculate total years in office based on terms."""
    if not terms:
        return 0
    
    total_years = 0
    for term in terms:
        if 'start' in term and 'end' in term:
            try:
                start_year = int(term['start'].split('-')[0])
                end_year = int(term['end'].split('-')[0])
                # Add 1 to include both start and end years in the count
                term_years = end_year - start_year
                total_years += term_years
            except (ValueError, IndexError):
                continue
    
    return total_years

def extract_bio_info(legislator):
    """Extract biographical information from legislator data."""
    bio_info = {}
    
    # Extract basic bio information
    if 'bio' in legislator:
        bio_data = legislator['bio']
        
        if 'birthday' in bio_data:
            bio_info['birthday'] = bio_data['birthday']
            
            # Calculate age if birthday is available
            try:
                birth_year = int(bio_data['birthday'].split('-')[0])
                current_year = datetime.now().year
                bio_info['age'] = current_year - birth_year
            except (ValueError, IndexError):
                pass
            
        if 'gender' in bio_data:
            bio_info['gender'] = bio_data['gender']
            
        if 'religion' in bio_data:
            bio_info['religion'] = bio_data['religion']
    
    # Extract terms information
    if 'terms' in legislator:
        terms = legislator['terms']
        
        # Get first and most recent terms
        if terms:
            bio_info['first_term'] = terms[0]
            bio_info['most_recent_term'] = terms[-1]
            bio_info['years_in_office'] = calculate_years_in_office(terms)
            
            # Extract positions held
            positions = set()
            for term in terms:
                if 'type' in term:
                    positions.add(term['type'])
            
            if positions:
                bio_info['positions_held'] = list(positions)
    
    # Extract name information
    if 'name' in legislator:
        name_data = legislator['name']
        
        if 'official_full' in name_data:
            bio_info['official_name'] = name_data['official_full']
            
        # Include other name components if available
        for key in ['first', 'middle', 'last', 'suffix']:
            if key in name_data:
                bio_info[f'name_{key}'] = name_data[key]
    
    return bio_info

def update_bio_info(cursor, entity_id, bio_info, politician_name):
    """Update biographical information for a politician entity."""
    if not bio_info:
        logging.warning(f"No biographical information available for {politician_name}")
        return False
    
    # Create a formatted bio text
    bio_text = format_bio_text(bio_info, politician_name)
    
    # Update both the bio field and add details to official_positions
    cursor.execute("SELECT official_positions FROM entities WHERE id = ?", (entity_id,))
    result = cursor.fetchone()
    current_data = {}
    
    if result and result[0]:
        try:
            current_data = json.loads(result[0])
        except json.JSONDecodeError:
            current_data = {}
    
    if isinstance(current_data, dict):
        if 'biographical_details' not in current_data:
            current_data['biographical_details'] = {}
        
        current_data['biographical_details'].update(bio_info)
        
        # Update both fields
        cursor.execute("""
            UPDATE entities 
            SET bio = ?, official_positions = ?
            WHERE id = ?
        """, (bio_text, json.dumps(current_data), entity_id))
        
        logging.info(f"Updated biographical information for {politician_name}")
        return True
    
    return False

def format_bio_text(bio_info, name):
    """Format biographical info into readable text."""
    bio_parts = []
    
    bio_parts.append(f"{name} ")
    
    if 'gender' in bio_info:
        if bio_info['gender'] == 'M':
            bio_parts.append("is a male ")
        elif bio_info['gender'] == 'F':
            bio_parts.append("is a female ")
        else:
            bio_parts.append("is a ")
    
    # Add position information
    if 'most_recent_term' in bio_info and 'type' in bio_info['most_recent_term']:
        term_type = bio_info['most_recent_term']['type']
        if term_type == 'sen':
            bio_parts.append("Senator ")
        elif term_type == 'rep':
            bio_parts.append("Representative ")
        
        if 'state' in bio_info['most_recent_term']:
            bio_parts.append(f"from {bio_info['most_recent_term']['state']} ")
            
            if term_type == 'rep' and 'district' in bio_info['most_recent_term']:
                bio_parts.append(f"district {bio_info['most_recent_term']['district']} ")
    
    # Add party information
    if 'most_recent_term' in bio_info and 'party' in bio_info['most_recent_term']:
        bio_parts.append(f"who is a member of the {bio_info['most_recent_term']['party']} party. ")
    else:
        bio_parts.append(". ")
    
    # Add age information
    if 'birthday' in bio_info:
        bio_parts.append(f"Born on {bio_info['birthday']}")
        
        if 'age' in bio_info:
            bio_parts.append(f", currently {bio_info['age']} years old. ")
        else:
            bio_parts.append(". ")
    
    # Add experience information
    if 'years_in_office' in bio_info and bio_info['years_in_office'] > 0:
        bio_parts.append(f"Has served approximately {bio_info['years_in_office']} years in office. ")
    
    # Add religious information if available
    if 'religion' in bio_info and bio_info['religion']:
        bio_parts.append(f"Religion: {bio_info['religion']}. ")
    
    return "".join(bio_parts).strip()

def migrate_bio_information():
    """Main function to migrate biographical data to database."""
    conn = connect_to_db()
    cursor = conn.cursor()
    
    # Load legislators file
    yaml_file = 'backups/migrated_data_files/legislators-current.yaml'
    legislators_data = load_yaml_file(yaml_file)
    
    if not legislators_data:
        logging.error("No data found in the legislators YAML file")
        return
    
    logging.info(f"Found {len(legislators_data)} legislator records in the YAML file")
    
    # Build a dictionary of legislators by bioguide ID for quick lookup
    legislators_by_id = {}
    for legislator in legislators_data:
        if 'id' in legislator and 'bioguide' in legislator['id']:
            bioguide_id = legislator['id']['bioguide']
            legislators_by_id[bioguide_id] = legislator
    
    logging.info(f"Indexed {len(legislators_by_id)} legislators by bioguide ID")
    
    # Statistics
    total_processed = 0
    total_updated = 0
    total_missing = 0
    no_changes = 0
    
    try:
        # Query all politicians from the database
        cursor.execute("""
            SELECT p.bioguide_id, p.entity_id, e.name, e.bio
            FROM politicians p
            JOIN entities e ON p.entity_id = e.id
            WHERE p.bioguide_id IS NOT NULL
        """)
        
        politicians = cursor.fetchall()
        logging.info(f"Found {len(politicians)} politicians with bioguide IDs in the database")
        
        # Process each politician
        for politician in politicians:
            total_processed += 1
            
            bioguide_id = politician['bioguide_id']
            entity_id = politician['entity_id']
            name = politician['name']
            
            # Check if we have legislator data for this politician
            if bioguide_id not in legislators_by_id:
                logging.warning(f"No legislator data found for {name} (ID: {bioguide_id})")
                total_missing += 1
                continue
            
            # Skip if bio info is already detailed
            current_bio = politician['bio']
            if current_bio and len(current_bio) > 100:  # Arbitrary threshold for a detailed bio
                logging.info(f"Detailed bio already exists for {name}, skipping")
                no_changes += 1
                continue
            
            # Extract bio information
            legislator = legislators_by_id[bioguide_id]
            bio_info = extract_bio_info(legislator)
            
            # Update bio information
            if update_bio_info(cursor, entity_id, bio_info, name):
                total_updated += 1
            else:
                no_changes += 1
        
        # Commit the changes
        conn.commit()
        
        # Log the summary
        logging.info(f"Migration Summary:")
        logging.info(f"Total records processed: {total_processed}")
        logging.info(f"Total records updated: {total_updated}")
        logging.info(f"Total records with no changes needed: {no_changes}")
        logging.info(f"Total records missing or not found: {total_missing}")
        
    except Exception as e:
        conn.rollback()
        logging.error(f"Error during migration: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    logging.info("Starting biographical information migration")
    migrate_bio_information()
    logging.info("Biographical information migration completed") 