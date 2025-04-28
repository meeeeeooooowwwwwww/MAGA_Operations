#!/usr/bin/env python3
"""
Entity Import Script for MAGA_Ops

This script imports entities from various sources (CSV, JSON, etc.) into the normalized database.
It:
1. Validates entity data against required schema
2. Normalizes input data (names, categories, etc.)
3. Inserts entities into the database with proper categorization
4. Handles duplicate detection and conflict resolution
"""
import os
import sys
import json
import csv
import logging
import argparse
from datetime import datetime
from pathlib import Path

# Add parent directory to path to import database_manager
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(PROJECT_ROOT)

# Import our database manager
from scripts.db.database_manager import DatabaseManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(PROJECT_ROOT, 'logs', 'entity_import.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def normalize_name(name):
    """Normalize entity name for consistent storage and lookup."""
    return name.lower().strip()

def validate_entity(entity, entity_type):
    """Validate entity data for required fields."""
    required_fields = ['name']
    
    # Additional required fields based on entity type
    if entity_type == 'politician':
        pass  # Could add politician-specific validation
    elif entity_type == 'influencer':
        pass  # Could add influencer-specific validation
    
    # Check required fields
    missing_fields = [field for field in required_fields if field not in entity or not entity[field]]
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"
    
    return True, None

def import_from_json(db, json_file, entity_type):
    """Import entities from a JSON file."""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different possible JSON structures
        if isinstance(data, list):
            entities = data
        elif isinstance(data, dict) and 'entities' in data:
            entities = data['entities']
        else:
            logger.error(f"Unrecognized JSON format in {json_file}")
            return 0, 0
        
        return import_entities(db, entities, entity_type)
        
    except Exception as e:
        logger.error(f"Error importing from JSON file {json_file}: {str(e)}")
        return 0, 0

def import_from_csv(db, csv_file, entity_type):
    """Import entities from a CSV file."""
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            entities = list(reader)
        
        return import_entities(db, entities, entity_type)
        
    except Exception as e:
        logger.error(f"Error importing from CSV file {csv_file}: {str(e)}")
        return 0, 0

def import_entities(db, entities, entity_type):
    """Import a list of entities into the database."""
    successful = 0
    failed = 0
    
    # Get category mappings (for category codes/names in import data)
    categories_by_type = get_categories_by_type(db)
    
    for entity_data in entities:
        try:
            # Validate entity
            valid, error = validate_entity(entity_data, entity_type)
            if not valid:
                logger.warning(f"Invalid entity data: {error}")
                failed += 1
                continue
            
            # Add normalized name if not present
            if 'normalized_name' not in entity_data:
                entity_data['normalized_name'] = normalize_name(entity_data['name'])
            
            # Check if entity already exists
            existing_entity = db.get_entity_by_name(entity_data['normalized_name'])
            
            if existing_entity:
                logger.info(f"Entity '{entity_data['name']}' already exists, updating")
                
                # Update entity with new data
                result = update_existing_entity(db, existing_entity['id'], entity_data, entity_type, categories_by_type)
                if result:
                    successful += 1
                else:
                    failed += 1
            else:
                # Create new entity
                result = create_new_entity(db, entity_data, entity_type, categories_by_type)
                if result:
                    successful += 1
                else:
                    failed += 1
                
        except Exception as e:
            logger.error(f"Error processing entity {entity_data.get('name', 'Unknown')}: {str(e)}")
            failed += 1
    
    return successful, failed

def get_categories_by_type(db):
    """Get all categories organized by type and code."""
    categories = db.get_categories()
    categories_by_type = {}
    
    for category in categories:
        cat_type = category['category_type']
        if cat_type not in categories_by_type:
            categories_by_type[cat_type] = {}
        
        # Map both by code and by name (lowercase for case-insensitive matching)
        categories_by_type[cat_type][category['code']] = category['id']
        categories_by_type[cat_type][category['name'].lower()] = category['id']
    
    return categories_by_type

def map_category_to_id(category_value, category_type, categories_by_type):
    """Map a category value (code or name) to its ID."""
    if not category_value or category_type not in categories_by_type:
        return None
    
    # Try exact match on code
    if category_value in categories_by_type[category_type]:
        return categories_by_type[category_type][category_value]
    
    # Try lowercase match
    category_value_lower = str(category_value).lower()
    if category_value_lower in categories_by_type[category_type]:
        return categories_by_type[category_type][category_value_lower]
    
    return None

def create_new_entity(db, entity_data, entity_type, categories_by_type):
    """Create a new entity in the database."""
    conn = None
    try:
        conn = db._get_connection()
        cursor = conn.cursor()
        
        # Extract base entity fields
        base_fields = {
            'name': entity_data['name'],
            'normalized_name': entity_data['normalized_name'],
            'bio': entity_data.get('bio'),
            'image_url': entity_data.get('image_url'),
            'twitter_handle': entity_data.get('twitter_handle'),
            'instagram_handle': entity_data.get('instagram_handle'),
            'facebook_url': entity_data.get('facebook_url'),
            'website_url': entity_data.get('website_url'),
            'first_appearance_date': entity_data.get('first_appearance_date', datetime.now().isoformat()),
            'last_updated': datetime.now().isoformat(),
            'entity_type': entity_type
        }
        
        # Insert base entity
        cursor.execute("""
            INSERT INTO entities (
                name, normalized_name, bio, image_url, twitter_handle, instagram_handle,
                facebook_url, website_url, first_appearance_date, last_updated, entity_type
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            base_fields['name'],
            base_fields['normalized_name'],
            base_fields['bio'],
            base_fields['image_url'],
            base_fields['twitter_handle'],
            base_fields['instagram_handle'],
            base_fields['facebook_url'],
            base_fields['website_url'],
            base_fields['first_appearance_date'],
            base_fields['last_updated'],
            base_fields['entity_type']
        ))
        
        # Get the new entity ID
        entity_id = cursor.lastrowid
        
        # Insert type-specific data
        if entity_type == 'politician':
            cursor.execute("""
                INSERT INTO politicians (entity_id, office, state, district, election_year, bioguide_id, fec_candidate_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                entity_id,
                entity_data.get('office'),
                entity_data.get('state'),
                entity_data.get('district'),
                entity_data.get('election_year'),
                entity_data.get('bioguide_id'),
                entity_data.get('fec_candidate_id')
            ))
        
        elif entity_type == 'influencer':
            cursor.execute("""
                INSERT INTO influencers (entity_id, platform, audience_size, content_focus, influence_score)
                VALUES (?, ?, ?, ?, ?)
            """, (
                entity_id,
                entity_data.get('platform'),
                entity_data.get('audience_size'),
                entity_data.get('content_focus'),
                entity_data.get('influence_score', 0.0)
            ))
        
        # Handle categories
        category_mappings = [
            ('entity_type', entity_data.get('entity_type')),
            ('entity_subtype', entity_data.get('entity_subtype')),
            ('party', entity_data.get('party')),
            ('ideology', entity_data.get('ideology')),
            ('trump_stance', entity_data.get('trump_stance'))
        ]
        
        for cat_type, cat_value in category_mappings:
            if cat_value:
                cat_id = map_category_to_id(cat_value, cat_type, categories_by_type)
                if cat_id:
                    cursor.execute("""
                        INSERT INTO entity_categories (entity_id, category_id, source)
                        VALUES (?, ?, ?)
                    """, (entity_id, cat_id, 'import'))
        
        conn.commit()
        logger.info(f"Created new {entity_type}: {entity_data['name']} (ID: {entity_id})")
        return True
        
    except Exception as e:
        logger.error(f"Error creating entity {entity_data.get('name')}: {str(e)}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def update_existing_entity(db, entity_id, entity_data, entity_type, categories_by_type):
    """Update an existing entity with new data."""
    conn = None
    try:
        conn = db._get_connection()
        cursor = conn.cursor()
        
        # Update base entity fields (only non-null values)
        update_fields = []
        update_values = []
        
        base_field_mapping = {
            'bio': 'bio',
            'image_url': 'image_url',
            'twitter_handle': 'twitter_handle',
            'instagram_handle': 'instagram_handle',
            'facebook_url': 'facebook_url',
            'website_url': 'website_url'
        }
        
        for db_field, data_field in base_field_mapping.items():
            if data_field in entity_data and entity_data[data_field]:
                update_fields.append(f"{db_field} = ?")
                update_values.append(entity_data[data_field])
        
        # Always update last_updated
        update_fields.append("last_updated = ?")
        update_values.append(datetime.now().isoformat())
        
        # Update base entity if we have fields to update
        if update_fields:
            update_values.append(entity_id)  # For WHERE clause
            sql = f"UPDATE entities SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(sql, update_values)
        
        # Update type-specific data
        if entity_type == 'politician':
            pol_update_fields = []
            pol_update_values = []
            
            pol_field_mapping = {
                'office': 'office',
                'state': 'state',
                'district': 'district',
                'election_year': 'election_year',
                'bioguide_id': 'bioguide_id',
                'fec_candidate_id': 'fec_candidate_id'
            }
            
            for db_field, data_field in pol_field_mapping.items():
                if data_field in entity_data and entity_data[data_field]:
                    pol_update_fields.append(f"{db_field} = ?")
                    pol_update_values.append(entity_data[data_field])
            
            if pol_update_fields:
                pol_update_values.append(entity_id)  # For WHERE clause
                sql = f"UPDATE politicians SET {', '.join(pol_update_fields)} WHERE entity_id = ?"
                cursor.execute(sql, pol_update_values)
        
        elif entity_type == 'influencer':
            inf_update_fields = []
            inf_update_values = []
            
            inf_field_mapping = {
                'platform': 'platform',
                'audience_size': 'audience_size',
                'content_focus': 'content_focus',
                'influence_score': 'influence_score'
            }
            
            for db_field, data_field in inf_field_mapping.items():
                if data_field in entity_data and entity_data[data_field]:
                    inf_update_fields.append(f"{db_field} = ?")
                    inf_update_values.append(entity_data[data_field])
            
            if inf_update_fields:
                inf_update_values.append(entity_id)  # For WHERE clause
                sql = f"UPDATE influencers SET {', '.join(inf_update_fields)} WHERE entity_id = ?"
                cursor.execute(sql, inf_update_values)
        
        # Handle categories (only add, don't remove)
        category_mappings = [
            ('entity_type', entity_data.get('entity_type')),
            ('entity_subtype', entity_data.get('entity_subtype')),
            ('party', entity_data.get('party')),
            ('ideology', entity_data.get('ideology')),
            ('trump_stance', entity_data.get('trump_stance'))
        ]
        
        for cat_type, cat_value in category_mappings:
            if cat_value:
                cat_id = map_category_to_id(cat_value, cat_type, categories_by_type)
                if cat_id:
                    # Check if category already exists
                    cursor.execute("""
                        SELECT 1 FROM entity_categories ec
                        JOIN categories c ON ec.category_id = c.id
                        JOIN category_types ct ON c.category_type_id = ct.id
                        WHERE ec.entity_id = ? AND ct.name = ? AND c.id = ?
                    """, (entity_id, cat_type, cat_id))
                    
                    if not cursor.fetchone():
                        # If this category type is single-value, remove existing
                        cursor.execute("""
                            SELECT is_multiple FROM category_types WHERE name = ?
                        """, (cat_type,))
                        result = cursor.fetchone()
                        
                        if result and not result['is_multiple']:
                            cursor.execute("""
                                DELETE FROM entity_categories 
                                WHERE entity_id = ? AND category_id IN (
                                    SELECT c.id FROM categories c
                                    JOIN category_types ct ON c.category_type_id = ct.id
                                    WHERE ct.name = ?
                                )
                            """, (entity_id, cat_type))
                        
                        # Insert new category
                        cursor.execute("""
                            INSERT INTO entity_categories (entity_id, category_id, source)
                            VALUES (?, ?, ?)
                        """, (entity_id, cat_id, 'import'))
        
        conn.commit()
        logger.info(f"Updated {entity_type}: {entity_data['name']} (ID: {entity_id})")
        return True
        
    except Exception as e:
        logger.error(f"Error updating entity {entity_data.get('name')} (ID: {entity_id}): {str(e)}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Import entities into the MAGA_Ops database")
    parser.add_argument(
        "file",
        help="JSON or CSV file containing entity data"
    )
    parser.add_argument(
        "--type", "-t",
        choices=["politician", "influencer", "organization"],
        required=True,
        help="Type of entities to import"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["json", "csv"],
        help="Format of the input file (detected from extension if not specified)"
    )
    return parser.parse_args()

def main():
    """Main function to import entities."""
    args = parse_args()
    
    # Ensure log directory exists
    os.makedirs('logs', exist_ok=True)
    
    # Validate input file
    if not os.path.exists(args.file):
        logger.error(f"Input file not found: {args.file}")
        return
    
    # Determine file format if not specified
    file_format = args.format
    if not file_format:
        if args.file.lower().endswith('.json'):
            file_format = 'json'
        elif args.file.lower().endswith('.csv'):
            file_format = 'csv'
        else:
            logger.error(f"Could not determine file format for {args.file}, please specify with --format")
            return
    
    # Initialize database manager
    db = DatabaseManager()
    
    # Import entities
    logger.info(f"Importing {args.type}s from {file_format} file: {args.file}")
    
    if file_format == 'json':
        successful, failed = import_from_json(db, args.file, args.type)
    elif file_format == 'csv':
        successful, failed = import_from_csv(db, args.file, args.type)
    
    logger.info(f"Import complete: {successful} successful, {failed} failed")

if __name__ == "__main__":
    main() 