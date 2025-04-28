#!/usr/bin/env python3
"""
Add Test AI Metadata

This script adds sample AI metadata to the database for testing purposes.
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

def add_ai_metadata(db):
    """Add test AI metadata to entities."""
    # Donald Trump (entity ID 13)
    metadata = [
        # Trump
        (13, 'ideology_analysis', 'Primarily populist with nationalist tendencies, shows conservative economic policy inclinations with populist messaging.', 0.85, 'Claude-3.5'),
        (13, 'political_strategy', 'Relies heavily on direct voter engagement, uses social media extensively, focuses on immigration and economic messaging.', 0.78, 'News Analysis Pipeline'),
        (13, 'voter_demographics', 'Strong support among non-college educated white voters, rural communities, and evangelical Christians.', 0.92, 'Electoral Data Analysis'),
        
        # Biden
        (14, 'ideology_analysis', 'Center-left politician with pragmatic policy positions, focuses on institutional stability and bipartisan appeal when possible.', 0.81, 'Claude-3.5'),
        (14, 'political_strategy', 'Emphasizes experience and stability, targets suburban voters and coalition-building across Democratic party factions.', 0.76, 'News Analysis Pipeline'),
        
        # MTG
        (15, 'ideology_analysis', 'Far-right populist with strong America-first nationalist positions, frequently employs controversial rhetoric.', 0.88, 'Claude-3.5'),
        
        # Shapiro
        (16, 'audience_analysis', 'Primarily appeals to conservative college-educated males 18-34, with secondary audience of politically engaged high school students.', 0.79, 'Audience Metrics v2'),
        (16, 'content_topics', 'Focus on campus politics, cultural issues, free speech, and criticism of progressive policies.', 0.91, 'Content Analysis Tool'),
        
        # Carlson
        (17, 'audience_analysis', 'Broad appeal to conservative viewers 45+, especially strong with populist right and America-first demographics.', 0.84, 'Audience Metrics v2'),
        (17, 'content_topics', 'Immigration, national sovereignty, elite criticism, economic nationalism, and traditional values.', 0.87, 'Content Analysis Tool'),
        
        # Fox News
        (18, 'media_bias', 'Right-leaning news organization with opinion programming that skews further right than news division.', 0.76, 'Media Bias Assessment'),
        
        # MAGA Patriots
        (19, 'organization_effectiveness', 'Small but active grassroots organization with limited funding but high engagement metrics among followers.', 0.67, 'Org Analysis Framework')
    ]
    
    for entity_id, field_name, field_value, confidence, source in metadata:
        db.add_ai_metadata(entity_id, field_name, field_value, confidence, source)
        logger.info(f"Added AI metadata '{field_name}' for entity ID {entity_id}")
    
    # Mark some as verified
    verified_metadata = [
        (13, 'ideology_analysis'), 
        (14, 'ideology_analysis'),
        (16, 'audience_analysis')
    ]
    
    for entity_id, field_name in verified_metadata:
        metadata = db.get_ai_metadata(entity_id, field_name)
        if metadata:
            db.mark_ai_metadata_verified(metadata[0]['id'], True)
            logger.info(f"Marked '{field_name}' metadata as verified for entity ID {entity_id}")

def add_connection_evidence(db):
    """Add evidence for entity connections."""
    # First get some connections to add evidence for
    connections = []
    conn = db._get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, entity1_id, entity2_id, connection_type FROM entity_connections LIMIT 5")
        connections = [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error fetching connections: {str(e)}")
    finally:
        if conn:
            conn.close()
    
    # Evidence data: (connection_id, evidence_type, description, source_url, confidence)
    evidence_data = []
    
    for conn in connections:
        # Only add evidence for some connections
        if conn['connection_type'] == 'ally':
            evidence_data.append((
                conn['id'],
                'social_post',
                f"Entity {conn['entity1_id']} posted strong support for {conn['entity2_id']} on Twitter",
                "https://twitter.com/example/status/12345",
                0.85
            ))
            evidence_data.append((
                conn['id'],
                'news_article',
                f"News coverage of {conn['entity1_id']} endorsing {conn['entity2_id']} at a campaign rally",
                "https://example-news.com/article/54321",
                0.95
            ))
        elif conn['connection_type'] == 'opponent':
            evidence_data.append((
                conn['id'],
                'debate_transcript',
                f"Heated debate exchange between {conn['entity1_id']} and {conn['entity2_id']} showing clear opposition",
                "https://debates.org/transcript/98765",
                0.92
            ))
        elif conn['connection_type'] == 'supported by':
            evidence_data.append((
                conn['id'],
                'video_content',
                f"{conn['entity2_id']} created multiple videos supporting positions of {conn['entity1_id']}",
                "https://youtube.com/watch?v=abcdef",
                0.83
            ))
    
    # Add evidence
    for connection_id, evidence_type, description, source_url, confidence in evidence_data:
        db.add_connection_evidence(connection_id, evidence_type, description, source_url, confidence)
        logger.info(f"Added evidence type '{evidence_type}' for connection ID {connection_id}")

def add_donation_records(db):
    """Add test donation records."""
    # Sample donation data: (donor_id, recipient_id, amount, date, type, source)
    donations = [
        # Donors to Trump
        (16, 13, 1000.00, '2023-06-15', 'individual', 'https://www.fec.gov/data/receipts/?data_type=processed'),
        (18, 13, 50000.00, '2023-08-22', 'corporate', 'https://www.fec.gov/data/receipts/?data_type=processed'),
        (19, 13, 25000.00, '2023-09-30', 'pac', 'https://www.fec.gov/data/receipts/?data_type=processed'),
        
        # Donors to Biden
        (17, 14, 2500.00, '2023-05-10', 'individual', 'https://www.fec.gov/data/receipts/?data_type=processed'),
        
        # Donors to MTG
        (19, 15, 15000.00, '2023-07-05', 'pac', 'https://www.fec.gov/data/receipts/?data_type=processed'),
        
        # Trump as donor
        (13, 19, 10000.00, '2023-11-20', 'individual', 'https://www.fec.gov/data/receipts/?data_type=processed'),
    ]
    
    for donor_id, recipient_id, amount, date, donation_type, source in donations:
        db.add_donation_record(donor_id, recipient_id, amount, date, donation_type, source)
        logger.info(f"Added donation of ${amount} from entity {donor_id} to entity {recipient_id}")

def main():
    """Main function."""
    db = DatabaseManager()
    logger.info("Adding test data to the AI metadata tables...")
    
    # Clear existing metadata for testing
    conn = None
    try:
        conn = db._get_connection()
        cursor = conn.cursor()
        
        # Delete existing data
        tables_to_clear = ['ai_metadata', 'connection_evidence', 'donation_records']
        for table in tables_to_clear:
            cursor.execute(f"DELETE FROM {table}")
        
        conn.commit()
        logger.info("Cleared existing metadata")
    except Exception as e:
        logger.error(f"Error clearing data: {str(e)}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
    
    # Add test metadata
    add_ai_metadata(db)
    add_connection_evidence(db)
    add_donation_records(db)
    
    logger.info("Test metadata added successfully!")

if __name__ == "__main__":
    main() 