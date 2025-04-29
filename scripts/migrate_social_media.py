#!/usr/bin/env python3
"""
Migration script to add social media handles from YAML files to the database.
"""
import os
import sys
import yaml
import sqlite3
import logging
import atexit
import json

# Set up logging
logging.basicConfig(
    filename='social_media_migration_log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Add console handler
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger('').addHandler(console)

# Setup exit handler to ensure clean termination
def exit_handler():
    logging.info("Script exiting, no input required.")

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
        SELECT p.entity_id, e.name, e.twitter_handle
        FROM politicians p
        JOIN entities e ON p.entity_id = e.id
        WHERE p.bioguide_id = ?
    """, (bioguide_id,))
    return cursor.fetchone()

def update_social_media(cursor, entity_id, social_data, politician_name):
    """Update social media information for a politician entity."""
    updates = {}
    
    # Map social media handles to entity table fields
    if 'twitter' in social_data:
        twitter = social_data['twitter']
        # Add @ if missing
        if twitter and not twitter.startswith('@'):
            twitter = '@' + twitter
        updates['twitter_handle'] = twitter
    
    if 'instagram' in social_data:
        updates['instagram_handle'] = social_data['instagram']
        
    if 'facebook' in social_data:
        if social_data['facebook'] and 'facebook.com' not in social_data['facebook']:
            updates['facebook_url'] = f"https://www.facebook.com/{social_data['facebook']}"
        else:
            updates['facebook_url'] = social_data['facebook']
    
    # If we have youtube or other platforms, store in official_positions as JSON
    other_platforms = {k: v for k, v in social_data.items() 
                      if k not in ('twitter', 'instagram', 'facebook')}
    
    if other_platforms:
        cursor.execute("SELECT official_positions FROM entities WHERE id = ?", (entity_id,))
        result = cursor.fetchone()
        current_data = {}
        
        if result and result[0]:
            try:
                current_data = json.loads(result[0])
            except json.JSONDecodeError:
                current_data = {}
        
        if isinstance(current_data, dict):
            if 'social_media' not in current_data:
                current_data['social_media'] = {}
            
            current_data['social_media'].update(other_platforms)
            updates['official_positions'] = json.dumps(current_data)
    
    if updates:
        set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
        values = list(updates.values())
        values.append(entity_id)
        
        cursor.execute(f"""
            UPDATE entities 
            SET {set_clause}
            WHERE id = ?
        """, values)
        
        # Log what was updated
        for key, value in updates.items():
            if key != 'official_positions':  # Skip logging large JSON
                logging.info(f"Updated {key} to '{value}' for {politician_name}")
        
        return True
    
    return False

def migrate_social_media():
    """Main function to migrate social media data from YAML to database."""
    conn = connect_to_db()
    cursor = conn.cursor()
    
    # Load social media YAML file
    yaml_file = 'backups/migrated_data_files/legislators-social-media.yaml'
    social_media_data = load_yaml_file(yaml_file)
    
    if not social_media_data:
        logging.error("No data found in the social media YAML file")
        return
    
    logging.info(f"Found {len(social_media_data)} social media records in the YAML file")
    
    # Statistics
    total_processed = 0
    total_updated = 0
    total_missing = 0
    no_changes = 0
    
    try:
        # Process each social media record
        for record in social_media_data:
            total_processed += 1
            
            if 'id' not in record or 'bioguide' not in record['id']:
                logging.warning(f"Record {total_processed} is missing bioguide ID, skipping")
                total_missing += 1
                continue
            
            bioguide_id = record['id']['bioguide']
            
            # Verify politician exists
            politician = verify_politician_exists(cursor, bioguide_id)
            if not politician:
                logging.warning(f"No politician found with bioguide_id {bioguide_id}, skipping")
                total_missing += 1
                continue
            
            entity_id = politician['entity_id']
            name = politician['name']
            
            # Check if social media data exists in the record
            if 'social' not in record:
                logging.warning(f"No social media data found for {name} (ID: {entity_id})")
                no_changes += 1
                continue
            
            # Skip if Twitter is already populated
            if politician['twitter_handle'] and 'twitter' in record['social']:
                existing = politician['twitter_handle']
                from_yaml = record['social']['twitter']
                if existing.replace('@', '') == from_yaml.replace('@', ''):
                    logging.info(f"Twitter already set for {name}: {existing}, skipping")
                    no_changes += 1
                    continue
            
            # Update social media information
            if update_social_media(cursor, entity_id, record['social'], name):
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
    logging.info("Starting social media migration")
    migrate_social_media()
    logging.info("Social media migration completed") 