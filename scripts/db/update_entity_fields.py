#!/usr/bin/env python3
"""
Update Entity Fields

This script updates entity fields with additional information to improve completeness.
"""
import os
import sys
import logging
import json

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
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def update_entity(db, entity_id, updates):
    """Update entity fields with provided data."""
    entity = db.get_entity(entity_id)
    if not entity:
        logger.error(f"Entity with ID {entity_id} not found")
        return False
    
    logger.info(f"Updating entity: {entity['name']} (ID: {entity_id})")
    
    success = True
    for field, value in updates.items():
        try:
            # Convert JSON data to strings for storage
            if isinstance(value, (list, dict)):
                value = json.dumps(value)
                
            # Update the field
            result = db.update_entity_field(entity['entity_type'], entity_id, field, value)
            if result:
                logger.info(f"Updated {field} for entity {entity_id}")
            else:
                logger.warning(f"Failed to update {field} for entity {entity_id}")
                success = False
        except Exception as e:
            logger.error(f"Error updating {field} for entity {entity_id}: {str(e)}")
            success = False
    
    return success

def update_maga_patriots(db):
    """Update MAGA Patriots Coalition entity (ID 19)."""
    updates = {
        "image_url": "https://example.com/images/maga_patriots_logo.jpg",
        "official_positions": json.dumps([
            "Grassroots Political Action Committee",
            "America First Advocacy Group"
        ]),
        "known_affiliations": json.dumps([
            "America First Policy Institute",
            "Republican National Committee"
        ]),
        "location": "Multiple chapters across battleground states",
        "recent_activity": "Recently organized rallies in Pennsylvania, Michigan, and Wisconsin supporting candidates for 2024 election."
    }
    
    return update_entity(db, 19, updates)

def update_tucker_carlson(db):
    """Update Tucker Carlson entity (ID 17)."""
    updates = {
        "image_url": "https://example.com/images/tucker_carlson.jpg",
        "official_positions": json.dumps([
            "Former Fox News Host (2016-2023)",
            "Current Independent Media Personality"
        ]),
        "known_affiliations": json.dumps([
            "The Daily Caller (Co-founder)",
            "Tucker Carlson Network"
        ]),
        "location": "Florida",
        "recent_activity": "Launched subscription-based digital platform with exclusive interviews and commentary."
    }
    
    return update_entity(db, 17, updates)

def main():
    """Main function."""
    db = DatabaseManager()
    logger.info("Starting entity updates")
    
    # Update highest priority entities
    update_maga_patriots(db)
    update_tucker_carlson(db)
    
    logger.info("Entity updates completed")

if __name__ == "__main__":
    main() 