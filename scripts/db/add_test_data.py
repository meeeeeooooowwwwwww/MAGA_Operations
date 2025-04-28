#!/usr/bin/env python3
"""
Add Test Data to Database

This script adds sample entities to the database for testing purposes.
"""
import os
import sys
import logging
from datetime import datetime

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

def add_test_categories(db):
    """Add test categories to the database."""
    categories_by_type = {
        'party': [
            ('GOP', 'Republican', 'Republican Party'),
            ('DEM', 'Democrat', 'Democratic Party'),
            ('LIB', 'Libertarian', 'Libertarian Party'),
            ('GRN', 'Green', 'Green Party'),
        ],
        'ideology': [
            ('CONS', 'Conservative', 'Right-leaning political ideology'),
            ('LIB', 'Liberal', 'Left-leaning political ideology'),
            ('PROG', 'Progressive', 'Far-left political ideology'),
            ('MOD', 'Moderate', 'Centrist political ideology'),
            ('POP', 'Populist', 'Anti-establishment ideology'),
            ('NAT', 'Nationalist', 'Prioritizes national interests'),
            ('MAGA', 'MAGA', 'Make America Great Again movement'),
            ('FR', 'Far-right', 'Extreme right-wing ideology'),
            ('RW', 'Right-wing', 'General right-wing ideology'),
        ],
        'trump_stance': [
            ('STR_SUP', 'Strong supporter', 'Strongly supports Trump'),
            ('SUP', 'Supporter', 'Generally supports Trump'),
            ('MSUP', 'Mostly supportive', 'Usually supports Trump with reservations'),
            ('MIX', 'Mixed', 'Mixed support for Trump'),
            ('CRIT', 'Critical', 'Critical of Trump but not opposed'),
            ('OPP', 'Opposed', 'Opposed to Trump'),
        ]
    }
    
    for category_type, categories in categories_by_type.items():
        for code, name, description in categories:
            db.add_category(category_type, code, name, description)
            logger.info(f"Added category: {name} (type: {category_type})")
    
def add_test_politicians(db):
    """Add test politician entities."""
    politician_data = [
        {
            'name': 'Donald Trump',
            'bio': 'Former President of the United States (2017-2021)',
            'twitter_handle': 'realDonaldTrump',
            'website_url': 'https://www.donaldjtrump.com/',
            'office': 'President',
            'state': 'N/A',
            'district': 'N/A',
            'election_year': '2024',
            'bioguide_id': 'T000001',
            'categories': {
                'party': 'Republican',
                'ideology': ['Populist', 'Nationalist', 'Conservative']
            }
        },
        {
            'name': 'Joe Biden',
            'bio': 'Current President of the United States (2021-present)',
            'twitter_handle': 'JoeBiden',
            'website_url': 'https://www.whitehouse.gov/',
            'office': 'President',
            'state': 'N/A',
            'district': 'N/A',
            'election_year': '2020',
            'bioguide_id': 'B000001',
            'categories': {
                'party': 'Democrat',
                'ideology': ['Liberal', 'Moderate'],
                'trump_stance': 'Opposed'
            }
        },
        {
            'name': 'Marjorie Taylor Greene',
            'bio': 'U.S. Representative for Georgia\'s 14th congressional district',
            'twitter_handle': 'mtgreenee',
            'website_url': 'https://greene.house.gov/',
            'office': 'House Representative',
            'state': 'GA',
            'district': '14',
            'election_year': '2022',
            'bioguide_id': 'G000001',
            'categories': {
                'party': 'Republican',
                'ideology': ['MAGA', 'Far-right', 'Conservative'],
                'trump_stance': 'Strong supporter'
            }
        }
    ]
    
    politician_ids = []
    
    for politician in politician_data:
        # Extract categories
        categories = politician.pop('categories', {})
        
        # Add the politician
        entity_id = add_entity(db, 'politician', politician)
        
        if entity_id:
            politician_ids.append(entity_id)
            
            # Add categories
            for category_type, category_values in categories.items():
                if isinstance(category_values, list):
                    for value in category_values:
                        db.update_entity_field('politician', entity_id, f'category_{category_type}', value)
                else:
                    db.update_entity_field('politician', entity_id, f'category_{category_type}', category_values)
    
    return politician_ids

def add_test_influencers(db):
    """Add test influencer entities."""
    influencer_data = [
        {
            'name': 'Ben Shapiro',
            'bio': 'Conservative political commentator, author, and host of The Ben Shapiro Show',
            'twitter_handle': 'benshapiro',
            'website_url': 'https://www.dailywire.com/',
            'platform': 'YouTube/Podcast',
            'audience_size': 3000000,
            'content_focus': 'Conservative news and commentary',
            'influence_score': 0.85,
            'categories': {
                'ideology': ['Conservative', 'Right-wing'],
                'trump_stance': 'Mixed'
            }
        },
        {
            'name': 'Tucker Carlson',
            'bio': 'Political commentator and former Fox News host',
            'twitter_handle': 'TuckerCarlson',
            'platform': 'TV/Podcast',
            'audience_size': 4500000,
            'content_focus': 'Conservative news commentary',
            'influence_score': 0.90,
            'categories': {
                'ideology': ['Conservative', 'Populist', 'Nationalist'],
                'trump_stance': 'Supporter'
            }
        }
    ]
    
    influencer_ids = []
    
    for influencer in influencer_data:
        # Extract categories
        categories = influencer.pop('categories', {})
        
        # Add the influencer
        entity_id = add_entity(db, 'influencer', influencer)
        
        if entity_id:
            influencer_ids.append(entity_id)
            
            # Add categories
            for category_type, category_values in categories.items():
                if isinstance(category_values, list):
                    for value in category_values:
                        db.update_entity_field('influencer', entity_id, f'category_{category_type}', value)
                else:
                    db.update_entity_field('influencer', entity_id, f'category_{category_type}', category_values)
    
    return influencer_ids

def add_test_organizations(db):
    """Add test organization entities."""
    organization_data = [
        {
            'name': 'Fox News',
            'bio': 'Conservative news network',
            'twitter_handle': 'FoxNews',
            'website_url': 'https://www.foxnews.com/',
            'categories': {
                'ideology': ['Conservative', 'Right-wing'],
                'trump_stance': 'Mostly supportive'
            }
        },
        {
            'name': 'MAGA Patriots Coalition',
            'bio': 'Grassroots organization supporting Donald Trump and MAGA policies',
            'website_url': 'https://www.example-maga-patriots.org/',
            'facebook_url': 'https://www.facebook.com/magapatriots',
            'categories': {
                'ideology': ['MAGA', 'Nationalist', 'Conservative'],
                'trump_stance': 'Strong supporter'
            }
        }
    ]
    
    organization_ids = []
    
    for organization in organization_data:
        # Extract categories
        categories = organization.pop('categories', {})
        
        # Add the organization
        entity_id = add_entity(db, 'organization', organization)
        
        if entity_id:
            organization_ids.append(entity_id)
            
            # Add categories
            for category_type, category_values in categories.items():
                if isinstance(category_values, list):
                    for value in category_values:
                        db.update_entity_field('organization', entity_id, f'category_{category_type}', value)
                else:
                    db.update_entity_field('organization', entity_id, f'category_{category_type}', category_values)
    
    return organization_ids

def add_test_connections(db, entity_ids):
    """Add test connections between entities."""
    # Only add connections if we have enough entities
    if (len(entity_ids['politician']) >= 2 and 
        len(entity_ids['influencer']) >= 1 and 
        len(entity_ids['organization']) >= 1):
        
        connections = [
            # Trump with Biden
            (entity_ids['politician'][0], entity_ids['politician'][1], 'opponent', 0.95),
        ]
        
        # Add more connections only if we have enough entities
        if len(entity_ids['politician']) >= 3:
            connections.append(
                (entity_ids['politician'][0], entity_ids['politician'][2], 'ally', 0.9)
            )
        
        # Politicians with influencers
        if len(entity_ids['influencer']) >= 2:
            connections.extend([
                (entity_ids['politician'][0], entity_ids['influencer'][1], 'supported by', 0.85),
            ])
            
            if len(entity_ids['politician']) >= 3:
                connections.append(
                    (entity_ids['politician'][2], entity_ids['influencer'][0], 'supported by', 0.75)
                )
        
        # Politicians with organizations
        if len(entity_ids['organization']) >= 2:
            connections.extend([
                (entity_ids['politician'][0], entity_ids['organization'][0], 'covered by', 0.8),
                (entity_ids['politician'][0], entity_ids['organization'][1], 'supported by', 0.95),
            ])
        
        # Influencers with organizations
        if len(entity_ids['influencer']) >= 2 and len(entity_ids['organization']) >= 1:
            connections.append(
                (entity_ids['influencer'][1], entity_ids['organization'][0], 'affiliated with', 0.9)
            )
        
        for entity1_id, entity2_id, connection_type, strength in connections:
            try:
                # Execute direct SQL for adding connections since there's no direct method
                # in the DatabaseManager class
                conn = db._get_connection()
                cursor = conn.cursor()
                
                sql = """
                INSERT INTO entity_connections 
                (entity1_id, entity2_id, connection_type, strength, first_detected, last_updated)
                VALUES (?, ?, ?, ?, ?, ?)
                """
                now = datetime.now().isoformat()
                cursor.execute(sql, (
                    entity1_id, entity2_id, connection_type, strength, now, now
                ))
                
                conn.commit()
                logger.info(f"Added connection: {entity1_id} -> {entity2_id} ({connection_type})")
                
            except Exception as e:
                logger.error(f"Error adding connection: {str(e)}")
            finally:
                if conn:
                    conn.close()
    else:
        logger.warning("Not enough entities to create connections")

def add_entity(db, entity_type, data):
    """Add an entity to the database."""
    try:
        conn = db._get_connection()
        cursor = conn.cursor()
        
        # Extract basic entity data
        entity_fields = {
            'name': data.get('name', ''),
            'normalized_name': data.get('name', '').lower(),
            'bio': data.get('bio', ''),
            'twitter_handle': data.get('twitter_handle', None),
            'instagram_handle': data.get('instagram_handle', None),
            'facebook_url': data.get('facebook_url', None),
            'website_url': data.get('website_url', None),
            'entity_type': entity_type,
            'relevance_score': 1.0,  # Default to 1.0 for test data
            'last_updated': datetime.now().isoformat()
        }
        
        # Insert entity record
        fields = ', '.join(entity_fields.keys())
        placeholders = ', '.join(['?' for _ in entity_fields])
        
        sql = f"INSERT INTO entities ({fields}) VALUES ({placeholders})"
        cursor.execute(sql, tuple(entity_fields.values()))
        
        entity_id = cursor.lastrowid
        logger.info(f"Added {entity_type}: {data['name']} (ID: {entity_id})")
        
        # Add type-specific data
        if entity_type == 'politician':
            politician_fields = {
                'entity_id': entity_id,
                'office': data.get('office', ''),
                'state': data.get('state', ''),
                'district': data.get('district', ''),
                'election_year': data.get('election_year', ''),
                'bioguide_id': data.get('bioguide_id', '')
            }
            
            fields = ', '.join(politician_fields.keys())
            placeholders = ', '.join(['?' for _ in politician_fields])
            
            sql = f"INSERT INTO politicians ({fields}) VALUES ({placeholders})"
            cursor.execute(sql, tuple(politician_fields.values()))
            
        elif entity_type == 'influencer':
            influencer_fields = {
                'entity_id': entity_id,
                'platform': data.get('platform', ''),
                'audience_size': data.get('audience_size', 0),
                'content_focus': data.get('content_focus', ''),
                'influence_score': data.get('influence_score', 0.0)
            }
            
            fields = ', '.join(influencer_fields.keys())
            placeholders = ', '.join(['?' for _ in influencer_fields])
            
            sql = f"INSERT INTO influencers ({fields}) VALUES ({placeholders})"
            cursor.execute(sql, tuple(influencer_fields.values()))
        
        conn.commit()
        return entity_id
        
    except Exception as e:
        logger.error(f"Error adding {entity_type} {data.get('name', '')}: {str(e)}")
        if conn:
            conn.rollback()
        return None
    finally:
        if conn:
            conn.close()

def main():
    """Main function."""
    db = DatabaseManager()
    logger.info("Adding test data to the database...")
    
    # Clear existing data for testing
    conn = None
    try:
        conn = db._get_connection()
        cursor = conn.cursor()
        
        tables = ['entity_connections', 'entity_categories', 'social_posts', 
                 'voting_records', 'search_history', 'influencers', 'politicians', 'entities']
        
        for table in tables:
            cursor.execute(f"DELETE FROM {table}")
        
        conn.commit()
        logger.info("Cleared existing data")
    except Exception as e:
        logger.error(f"Error clearing data: {str(e)}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
    
    # Add test categories first (so we can use them for entities)
    add_test_categories(db)
    
    # Add test entities
    politician_ids = add_test_politicians(db)
    influencer_ids = add_test_influencers(db)
    organization_ids = add_test_organizations(db)
    
    # Store entity IDs by type
    entity_ids = {
        'politician': politician_ids,
        'influencer': influencer_ids,
        'organization': organization_ids
    }
    
    # Add connections between entities
    add_test_connections(db, entity_ids)
    
    logger.info("Test data added successfully!")

if __name__ == "__main__":
    main() 