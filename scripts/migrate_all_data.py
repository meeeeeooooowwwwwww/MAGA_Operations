#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Data Migration Script for MAGA_Ops

This script migrates data from various sources into the maga_ops.db SQLite database.
It handles YAML files, JSON files, and SQLite databases.
"""

import os
import sys
import json
import sqlite3
import yaml
import shutil
import pickle
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("migration_log.txt"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("data_migration")

# Project paths
PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, 'maga_ops.db')
BACKUP_DB_PATH = os.path.join(PROJECT_ROOT, f'maga_ops_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')

# Data source paths
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
BACKUPS_DIR = os.path.join(PROJECT_ROOT, 'backups')
MIGRATED_FILES_DIR = os.path.join(BACKUPS_DIR, 'migrated_data_files')
OLD_DATABASES_DIR = os.path.join(BACKUPS_DIR, 'old_databases')

# Migration tracking
migrated_files = []
failed_files = []

def backup_database():
    """Create a backup of the current database before migration."""
    try:
        if os.path.exists(DB_PATH):
            shutil.copy2(DB_PATH, BACKUP_DB_PATH)
            logger.info(f"Created database backup at {BACKUP_DB_PATH}")
            return True
        else:
            logger.warning(f"Database file not found at {DB_PATH}. No backup created.")
            return False
    except Exception as e:
        logger.error(f"Error creating database backup: {e}")
        return False

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

def load_json_file(file_path):
    """Load a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading JSON file {file_path}: {e}")
        return None

def migrate_influencers_json(file_path):
    """Migrate influencers data from JSON file."""
    logger.info(f"Migrating influencers from {file_path}")
    
    data = load_json_file(file_path)
    if not data:
        logger.error(f"Failed to load influencers data from {file_path}")
        failed_files.append(file_path)
        return False
    
    conn = get_connection()
    cursor = conn.cursor()
    migrated_count = 0
    
    try:
        for influencer in data:
            # Check if entity already exists
            cursor.execute("SELECT id FROM entities WHERE normalized_name = ? AND entity_type = 'influencer'", 
                          (influencer.get('normalized_name'),))
            entity = cursor.fetchone()
            
            if entity:
                # Update existing entity
                entity_id = entity['id']
                logger.info(f"Updating existing influencer: {influencer.get('name')} (ID: {entity_id})")
                
                # Update entities table
                cursor.execute("""
                    UPDATE entities SET 
                    name = ?,
                    bio = ?,
                    twitter_handle = ?,
                    instagram_handle = ?,
                    facebook_url = ?,
                    website_url = ?,
                    first_appearance_date = ?,
                    last_updated = ?,
                    relevance_score = ?
                    WHERE id = ?
                """, (
                    influencer.get('name'),
                    influencer.get('bio'),
                    influencer.get('twitter_handle'),
                    influencer.get('instagram_handle'),
                    influencer.get('facebook_url'),
                    influencer.get('website_url'),
                    influencer.get('first_appearance_date'),
                    influencer.get('last_updated') or datetime.now().strftime('%Y-%m-%d'),
                    influencer.get('relevance_score') or 0.0,
                    entity_id
                ))
                
                # Handle influencers-specific data
                cursor.execute("""
                    UPDATE influencers SET
                    platform = ?,
                    audience_size = ?,
                    content_focus = ?,
                    influence_score = ?
                    WHERE entity_id = ?
                """, (
                    influencer.get('category'),
                    None,  # We don't have audience_size in the source data
                    None,  # We don't have content_focus in the source data
                    influencer.get('relevance_score') or 0.0,
                    entity_id
                ))
            else:
                # Insert new entity
                logger.info(f"Adding new influencer: {influencer.get('name')}")
                
                # Insert into entities table
                cursor.execute("""
                    INSERT INTO entities (
                    name, normalized_name, bio, twitter_handle, instagram_handle, 
                    facebook_url, website_url, first_appearance_date, last_updated,
                    relevance_score, entity_type
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'influencer')
                """, (
                    influencer.get('name'),
                    influencer.get('normalized_name'),
                    influencer.get('bio'),
                    influencer.get('twitter_handle'),
                    influencer.get('instagram_handle'),
                    influencer.get('facebook_url'),
                    influencer.get('website_url'),
                    influencer.get('first_appearance_date'),
                    influencer.get('last_updated') or datetime.now().strftime('%Y-%m-%d'),
                    influencer.get('relevance_score') or 0.0
                ))
                
                entity_id = cursor.lastrowid
                
                # Insert into influencers table
                cursor.execute("""
                    INSERT INTO influencers (
                    entity_id, platform, audience_size, content_focus, influence_score
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    entity_id,
                    influencer.get('category'),
                    None,  # We don't have audience_size in the source data
                    None,  # We don't have content_focus in the source data
                    influencer.get('relevance_score') or 0.0
                ))
            
            migrated_count += 1
        
        conn.commit()
        logger.info(f"Successfully migrated {migrated_count} influencers from {file_path}")
        migrated_files.append(file_path)
        return True
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Error migrating influencers from {file_path}: {e}")
        failed_files.append(file_path)
        return False
    
    finally:
        conn.close()

def migrate_legislators_yaml(file_path):
    """Migrate legislators data from YAML file."""
    logger.info(f"Migrating legislators from {file_path}")
    
    data = load_yaml_file(file_path)
    if not data:
        logger.error(f"Failed to load legislators data from {file_path}")
        failed_files.append(file_path)
        return False
    
    conn = get_connection()
    cursor = conn.cursor()
    migrated_count = 0
    
    try:
        for legislator in data:
            # Extract basic information
            name_data = legislator.get('name', {})
            full_name = name_data.get('official_full')
            if not full_name:
                # Fallback to constructing from first/last
                first = name_data.get('first', '')
                middle = name_data.get('middle', '')
                last = name_data.get('last', '')
                full_name = f"{first} {middle} {last}".strip().replace('  ', ' ')
            
            normalized_name = full_name.lower()
            
            bio_data = legislator.get('bio', {})
            gender = bio_data.get('gender')
            birthday = bio_data.get('birthday')
            
            # Get bioguide id for unique identification
            ids = legislator.get('id', {})
            bioguide_id = ids.get('bioguide')
            fec_candidate_id = ids.get('fec')
            
            # Get most recent term
            terms = legislator.get('terms', [])
            current_term = terms[-1] if terms else {}
            
            state = current_term.get('state')
            district = current_term.get('district')
            party = current_term.get('party')
            office = current_term.get('type', '').upper()  # 'sen' or 'rep'
            if office == 'SEN':
                office = 'Senator'
            elif office == 'REP':
                office = 'Representative'
            
            # Format known_affiliations to include party
            known_affiliations = f"Party: {party}" if party else None
            
            # Check if entity already exists
            cursor.execute("""
                SELECT entities.id FROM entities 
                JOIN politicians ON entities.id = politicians.entity_id
                WHERE politicians.bioguide_id = ?
            """, (bioguide_id,))
            entity = cursor.fetchone()
            
            if entity:
                # Update existing entity
                entity_id = entity['id']
                logger.info(f"Updating existing politician: {full_name} (ID: {entity_id})")
                
                # Update entities table
                cursor.execute("""
                    UPDATE entities SET 
                    name = ?,
                    normalized_name = ?,
                    bio = ?,
                    twitter_handle = ?,
                    last_updated = ?,
                    known_affiliations = ?
                    WHERE id = ?
                """, (
                    full_name,
                    normalized_name,
                    f"{office} from {state}. {gender}",
                    None,  # twitter_handle will be updated in social media migration
                    datetime.now().strftime('%Y-%m-%d'),
                    known_affiliations,
                    entity_id
                ))
                
                # Update politicians table
                cursor.execute("""
                    UPDATE politicians SET
                    office = ?,
                    state = ?,
                    district = ?,
                    bioguide_id = ?,
                    fec_candidate_id = ?
                    WHERE entity_id = ?
                """, (
                    office,
                    state,
                    district,
                    bioguide_id,
                    fec_candidate_id,
                    entity_id
                ))
            else:
                # Insert new entity
                logger.info(f"Adding new politician: {full_name}")
                
                # Insert into entities table
                cursor.execute("""
                    INSERT INTO entities (
                    name, normalized_name, bio, twitter_handle, 
                    first_appearance_date, last_updated, entity_type, known_affiliations
                    ) VALUES (?, ?, ?, ?, ?, ?, 'politician', ?)
                """, (
                    full_name,
                    normalized_name,
                    f"{office} from {state}. {gender}",
                    None,  # twitter_handle will be updated in social media migration
                    datetime.now().strftime('%Y-%m-%d'),
                    datetime.now().strftime('%Y-%m-%d'),
                    known_affiliations
                ))
                
                entity_id = cursor.lastrowid
                
                # Insert into politicians table
                cursor.execute("""
                    INSERT INTO politicians (
                    entity_id, office, state, district, bioguide_id, fec_candidate_id
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    entity_id,
                    office,
                    state,
                    district,
                    bioguide_id,
                    fec_candidate_id
                ))
            
            migrated_count += 1
        
        conn.commit()
        logger.info(f"Successfully migrated {migrated_count} legislators from {file_path}")
        migrated_files.append(file_path)
        return True
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Error migrating legislators from {file_path}: {e}")
        failed_files.append(file_path)
        return False
    
    finally:
        conn.close()

def migrate_legislators_social_media(file_path):
    """Migrate social media data for legislators."""
    logger.info(f"Migrating legislators social media from {file_path}")
    
    data = load_yaml_file(file_path)
    if not data:
        logger.error(f"Failed to load social media data from {file_path}")
        failed_files.append(file_path)
        return False
    
    conn = get_connection()
    cursor = conn.cursor()
    updated_count = 0
    
    try:
        for person in data:
            # Get bioguide ID
            ids = person.get('id', {})
            bioguide_id = ids.get('bioguide')
            
            if not bioguide_id:
                continue
            
            # Get social media data
            social = person.get('social', {})
            twitter = social.get('twitter')
            instagram = social.get('instagram')
            facebook = social.get('facebook')
            youtube = social.get('youtube')
            
            if not (twitter or instagram or facebook or youtube):
                continue
            
            # Find the entity
            cursor.execute("""
                SELECT entities.id FROM entities 
                JOIN politicians ON entities.id = politicians.entity_id
                WHERE politicians.bioguide_id = ?
            """, (bioguide_id,))
            entity = cursor.fetchone()
            
            if entity:
                entity_id = entity['id']
                logger.info(f"Updating social media for politician with bioguide_id: {bioguide_id}")
                
                # Update entities table with social media handles
                cursor.execute("""
                    UPDATE entities SET 
                    twitter_handle = ?,
                    instagram_handle = ?,
                    facebook_url = ?,
                    last_updated = ?
                    WHERE id = ?
                """, (
                    twitter,
                    instagram,
                    facebook,
                    datetime.now().strftime('%Y-%m-%d'),
                    entity_id
                ))
                
                updated_count += 1
        
        conn.commit()
        logger.info(f"Successfully updated social media for {updated_count} legislators from {file_path}")
        migrated_files.append(file_path)
        return True
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Error migrating social media from {file_path}: {e}")
        failed_files.append(file_path)
        return False
    
    finally:
        conn.close()

def migrate_old_sqlite_db(db_path, db_type):
    """Migrate data from old SQLite databases."""
    logger.info(f"Migrating data from old SQLite database: {db_path}")
    
    try:
        # Connect to old database
        old_conn = sqlite3.connect(db_path)
        old_conn.row_factory = sqlite3.Row
        old_cursor = old_conn.cursor()
        
        # Connect to new database
        new_conn = get_connection()
        new_cursor = new_conn.cursor()
        
        if db_type == 'politicians':
            # Get table structure
            old_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row['name'] for row in old_cursor.fetchall()]
            
            if 'politicians' in tables:
                # Get politicians data
                old_cursor.execute("SELECT * FROM politicians")
                politicians = old_cursor.fetchall()
                
                migrated_count = 0
                
                for politician in politicians:
                    # Convert to dict for easier handling
                    p_dict = dict(politician)
                    
                    # Prepare normalized name
                    normalized_name = p_dict.get('name', '').lower() if p_dict.get('name') else ''
                    
                    # Prepare party as known_affiliations
                    party = p_dict.get('party')
                    known_affiliations = f"Party: {party}" if party else None
                    
                    # Check if entity already exists
                    new_cursor.execute("SELECT id FROM entities WHERE normalized_name = ? AND entity_type = 'politician'", 
                                      (normalized_name,))
                    entity = new_cursor.fetchone()
                    
                    if entity:
                        # Update existing entity
                        entity_id = entity['id']
                        logger.info(f"Updating existing politician from old DB: {p_dict.get('name')} (ID: {entity_id})")
                        
                        # Update entities table
                        new_cursor.execute("""
                            UPDATE entities SET 
                            name = ?,
                            bio = ?,
                            twitter_handle = ?,
                            last_updated = ?,
                            known_affiliations = ?
                            WHERE id = ?
                        """, (
                            p_dict.get('name'),
                            p_dict.get('bio'),
                            p_dict.get('twitter'),
                            datetime.now().strftime('%Y-%m-%d'),
                            known_affiliations,
                            entity_id
                        ))
                        
                        # Update politicians table
                        new_cursor.execute("""
                            UPDATE politicians SET
                            office = ?,
                            state = ?,
                            district = ?,
                            bioguide_id = ?,
                            fec_candidate_id = ?
                            WHERE entity_id = ?
                        """, (
                            p_dict.get('role'),
                            p_dict.get('state'),
                            p_dict.get('district'),
                            p_dict.get('bioguide_id'),
                            p_dict.get('fec_id'),
                            entity_id
                        ))
                    else:
                        # Insert new entity
                        logger.info(f"Adding new politician from old DB: {p_dict.get('name')}")
                        
                        # Insert into entities table
                        new_cursor.execute("""
                            INSERT INTO entities (
                            name, normalized_name, bio, twitter_handle, 
                            first_appearance_date, last_updated, entity_type, known_affiliations
                            ) VALUES (?, ?, ?, ?, ?, ?, 'politician', ?)
                        """, (
                            p_dict.get('name'),
                            normalized_name,
                            p_dict.get('bio'),
                            p_dict.get('twitter'),
                            datetime.now().strftime('%Y-%m-%d'),
                            datetime.now().strftime('%Y-%m-%d'),
                            known_affiliations
                        ))
                        
                        entity_id = new_cursor.lastrowid
                        
                        # Insert into politicians table
                        new_cursor.execute("""
                            INSERT INTO politicians (
                            entity_id, office, state, district, bioguide_id, fec_candidate_id
                            ) VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            entity_id,
                            p_dict.get('role'),
                            p_dict.get('state'),
                            p_dict.get('district'),
                            p_dict.get('bioguide_id'),
                            p_dict.get('fec_id')
                        ))
                    
                    migrated_count += 1
                
                new_conn.commit()
                logger.info(f"Successfully migrated {migrated_count} politicians from old database")
                migrated_files.append(db_path)
                
        elif db_type == 'influencers':
            # Get table structure
            old_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row['name'] for row in old_cursor.fetchall()]
            
            if 'influencers' in tables:
                # Get influencers data
                old_cursor.execute("SELECT * FROM influencers")
                influencers = old_cursor.fetchall()
                
                migrated_count = 0
                
                for influencer in influencers:
                    # Convert to dict for easier handling
                    i_dict = dict(influencer)
                    
                    # Prepare normalized name
                    normalized_name = i_dict.get('name', '').lower() if i_dict.get('name') else ''
                    
                    # Check if entity already exists
                    new_cursor.execute("SELECT id FROM entities WHERE normalized_name = ? AND entity_type = 'influencer'", 
                                      (normalized_name,))
                    entity = new_cursor.fetchone()
                    
                    if entity:
                        # Update existing entity
                        entity_id = entity['id']
                        logger.info(f"Updating existing influencer from old DB: {i_dict.get('name')} (ID: {entity_id})")
                        
                        # Update entities table
                        new_cursor.execute("""
                            UPDATE entities SET 
                            name = ?,
                            bio = ?,
                            twitter_handle = ?,
                            last_updated = ?
                            WHERE id = ?
                        """, (
                            i_dict.get('name'),
                            i_dict.get('bio'),
                            i_dict.get('twitter'),
                            datetime.now().strftime('%Y-%m-%d'),
                            entity_id
                        ))
                        
                        # Update influencers table
                        new_cursor.execute("""
                            UPDATE influencers SET
                            platform = ?,
                            audience_size = ?,
                            content_focus = ?
                            WHERE entity_id = ?
                        """, (
                            i_dict.get('platform'),
                            i_dict.get('followers'),
                            i_dict.get('focus'),
                            entity_id
                        ))
                    else:
                        # Insert new entity
                        logger.info(f"Adding new influencer from old DB: {i_dict.get('name')}")
                        
                        # Insert into entities table
                        new_cursor.execute("""
                            INSERT INTO entities (
                            name, normalized_name, bio, twitter_handle, 
                            first_appearance_date, last_updated, entity_type
                            ) VALUES (?, ?, ?, ?, ?, ?, 'influencer')
                        """, (
                            i_dict.get('name'),
                            normalized_name,
                            i_dict.get('bio'),
                            i_dict.get('twitter'),
                            datetime.now().strftime('%Y-%m-%d'),
                            datetime.now().strftime('%Y-%m-%d')
                        ))
                        
                        entity_id = new_cursor.lastrowid
                        
                        # Insert into influencers table
                        new_cursor.execute("""
                            INSERT INTO influencers (
                            entity_id, platform, audience_size, content_focus
                            ) VALUES (?, ?, ?, ?)
                        """, (
                            entity_id,
                            i_dict.get('platform'),
                            i_dict.get('followers'),
                            i_dict.get('focus')
                        ))
                    
                    migrated_count += 1
                
                new_conn.commit()
                logger.info(f"Successfully migrated {migrated_count} influencers from old database")
                migrated_files.append(db_path)
        
        elif db_type == 'influencers_ai':
            # Try to migrate AI-related data if available
            pass
        
        return True
    
    except Exception as e:
        logger.error(f"Error migrating from old database {db_path}: {e}")
        failed_files.append(db_path)
        return False
    
    finally:
        if 'old_conn' in locals() and old_conn:
            old_conn.close()
        if 'new_conn' in locals() and new_conn:
            new_conn.close()

def generate_migration_report():
    """Generate a report of the migration results."""
    report = {
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "successful_migrations": migrated_files,
        "failed_migrations": failed_files,
        "success_count": len(migrated_files),
        "failure_count": len(failed_files)
    }
    
    # Save report to file
    report_path = os.path.join(PROJECT_ROOT, 'data_migration_report.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Migration report saved to {report_path}")
    logger.info(f"Migration summary: {len(migrated_files)} files migrated successfully, {len(failed_files)} failed")
    
    # Print summary to console
    print("\n\n=== MIGRATION SUMMARY ===")
    print(f"Successfully migrated: {len(migrated_files)} files")
    print(f"Failed migrations: {len(failed_files)} files")
    print(f"Full report saved to: {report_path}")
    
    return report

def main():
    """Main execution function."""
    logger.info("Starting data migration")
    
    # Create a backup of the current database
    if not backup_database():
        if input("Failed to create database backup. Continue anyway? (y/n): ").lower() != 'y':
            logger.info("Migration cancelled by user")
            return
    
    # Migrate legislators data from YAML files
    legislators_files = [
        os.path.join(MIGRATED_FILES_DIR, 'legislators-current.yaml'),
        os.path.join(PROJECT_ROOT, 'legislators-historical.yaml')
    ]
    
    for file_path in legislators_files:
        if os.path.exists(file_path):
            migrate_legislators_yaml(file_path)
    
    # Migrate social media data
    social_media_file = os.path.join(MIGRATED_FILES_DIR, 'legislators-social-media.yaml')
    if os.path.exists(social_media_file):
        migrate_legislators_social_media(social_media_file)
    
    # Migrate influencers data from JSON files
    influencers_file = os.path.join(MIGRATED_FILES_DIR, 'influencers_export_20250428_152510.json')
    if os.path.exists(influencers_file):
        migrate_influencers_json(influencers_file)
    
    # Migrate data from old SQLite databases
    old_db_files = {
        os.path.join(OLD_DATABASES_DIR, 'politicians.db'): 'politicians',
        os.path.join(OLD_DATABASES_DIR, 'influencers.db'): 'influencers',
        os.path.join(OLD_DATABASES_DIR, 'influencers_ai.db'): 'influencers_ai'
    }
    
    for db_path, db_type in old_db_files.items():
        if os.path.exists(db_path):
            migrate_old_sqlite_db(db_path, db_type)
    
    # Generate migration report
    generate_migration_report()
    
    logger.info("Migration complete")

if __name__ == "__main__":
    main() 