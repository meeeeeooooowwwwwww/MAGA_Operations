#!/usr/bin/env python3
"""
Migration script to add image URLs for politicians from external sources.
"""
import os
import sys
import yaml
import sqlite3
import logging
import atexit
import json
import re

# Set up logging
logging.basicConfig(
    filename='image_migration_log.txt',
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
        SELECT p.entity_id, e.name, e.image_url
        FROM politicians p
        JOIN entities e ON p.entity_id = e.id
        WHERE p.bioguide_id = ?
    """, (bioguide_id,))
    return cursor.fetchone()

def generate_image_url(bioguide_id, name):
    """Generate image URL based on known patterns.
    We'll use a few official sources for images.
    """
    # Congressional Pictorial Directory
    congress_url = f"https://bioguide.congress.gov/bioguide/photo/{bioguide_id[0]}/{bioguide_id}.jpg"
    
    # Alternate sources if needed
    house_url = None
    senate_url = None
    
    # For testing, determine if it's a representative or senator based on name patterns
    if "Rep" in name or "Representative" in name:
        # House of Representatives URL pattern
        last_name = name.split()[-1].lower()
        house_url = f"https://clerk.house.gov/images/members/{bioguide_id}.jpg"
    
    if "Sen" in name or "Senator" in name:
        # Senate URL pattern
        last_name = name.split()[-1].lower()
        senate_url = f"https://www.senate.gov/senators/images/{last_name}_{bioguide_id}.jpg"
    
    # Return all potential URLs
    urls = {
        "congress_url": congress_url,
        "house_url": house_url,
        "senate_url": senate_url
    }
    
    # Filter out None values
    return {k: v for k, v in urls.items() if v is not None}

def update_image_url(cursor, entity_id, image_urls, politician_name):
    """Update image URL for a politician entity."""
    # For our database, we'll use the congressional pictorial directory as primary source
    primary_url = image_urls.get("congress_url")
    
    if not primary_url:
        logging.warning(f"No primary image URL available for {politician_name}")
        return False
    
    # Store alternatives in the official_positions field
    cursor.execute("SELECT official_positions FROM entities WHERE id = ?", (entity_id,))
    result = cursor.fetchone()
    current_data = {}
    
    if result and result[0]:
        try:
            current_data = json.loads(result[0])
        except json.JSONDecodeError:
            current_data = {}
    
    if isinstance(current_data, dict):
        if 'image_urls' not in current_data:
            current_data['image_urls'] = {}
        
        current_data['image_urls'].update(image_urls)
        
        # Update both fields
        cursor.execute("""
            UPDATE entities 
            SET image_url = ?, official_positions = ?
            WHERE id = ?
        """, (primary_url, json.dumps(current_data), entity_id))
        
        logging.info(f"Updated image URL for {politician_name} to {primary_url}")
        return True
    
    return False

def migrate_image_urls():
    """Main function to add image URLs to politician records."""
    conn = connect_to_db()
    cursor = conn.cursor()
    
    # Load legislators file to get bioguide IDs
    yaml_file = 'backups/migrated_data_files/legislators-current.yaml'
    legislators_data = load_yaml_file(yaml_file)
    
    if not legislators_data:
        logging.error("No data found in the legislators YAML file")
        return
    
    logging.info(f"Found {len(legislators_data)} legislator records in the YAML file")
    
    # Statistics
    total_processed = 0
    total_updated = 0
    total_missing = 0
    no_changes = 0
    
    try:
        # Query all politicians from the database
        cursor.execute("""
            SELECT p.bioguide_id, p.entity_id, e.name, e.image_url
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
            current_image = politician['image_url']
            
            # Skip if image is already populated
            if current_image:
                logging.info(f"Image already set for {name}: {current_image}, skipping")
                no_changes += 1
                continue
            
            # Generate image URLs
            image_urls = generate_image_url(bioguide_id, name)
            
            # Update image URL
            if update_image_url(cursor, entity_id, image_urls, name):
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
    logging.info("Starting image URL migration")
    migrate_image_urls()
    logging.info("Image URL migration completed") 