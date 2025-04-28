#!/usr/bin/env python3
"""
Entity Relationship Finder

This script analyzes entities in the database to find and record relationships:
1. Uses AI to analyze social posts for mentions of other entities
2. Examines voting patterns and committee memberships
3. Analyzes public statements for endorsements/criticisms
4. Identifies connections based on shared organizations/events

Records these relationships in the entity_connections table.
"""
import os
import sys
import json
import time
import logging
import argparse
import requests
from datetime import datetime
from dotenv import load_dotenv
from tqdm import tqdm

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
        logging.FileHandler(os.path.join(PROJECT_ROOT, 'logs', 'relationship_finder.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

# API key for OpenAI
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Define relationship types
RELATIONSHIP_TYPES = [
    'mentions',        # Simply mentions the other entity
    'endorses',        # Explicitly supports/endorses
    'criticizes',      # Explicitly criticizes/opposes
    'collaborates',    # Works with/collaborates with
    'affiliated',      # Has organizational affiliation
    'influenced_by',   # Is influenced by/follows
    'family',          # Family relationship
    'co_sponsors',     # Co-sponsors legislation (politicians)
    'interviewed',     # Interviewed or featured
    'donates_to',      # Financially supports
    'reports_on'       # Reports on/covers (media)
]

def check_api_key():
    """Check if API key is set."""
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY not set. Cannot analyze relationships.")
        sys.exit(1)
    
    logger.info("API key verified.")

def get_all_entities(db):
    """Get all entities from the database."""
    entities = db.execute_query("SELECT id, name, entity_type FROM entities")
    return {entity['id']: entity for entity in entities}

def analyze_social_posts(db, entity_id, entity_name, all_entities):
    """Analyze social posts from an entity for mentions of other entities."""
    # Get recent social posts
    posts = db.get_social_posts(entity_id, limit=20)
    
    if not posts:
        logger.info(f"No social posts found for entity {entity_id} ({entity_name})")
        return []
    
    logger.info(f"Analyzing {len(posts)} social posts for entity {entity_id} ({entity_name})")
    
    # Combine posts for analysis
    combined_text = f"Posts by {entity_name}:\n\n"
    for post in posts:
        combined_text += f"Post ID {post['id']}: {post['content']}\n\n"
    
    # Create a list of entity names to look for
    entity_names = [e['name'] for e in all_entities.values() if e['id'] != entity_id]
    
    # Use AI to identify mentioned entities
    mentioned_entities = detect_entity_mentions(combined_text, entity_names)
    
    # Map mentioned entity names back to IDs and create relationship data
    relationships = []
    for mention in mentioned_entities:
        # Find entity ID by name
        mentioned_entity_id = None
        relationship_type = mention['type']
        strength = mention['strength']
        
        for e_id, e_data in all_entities.items():
            if e_data['name'].lower() == mention['entity_name'].lower():
                mentioned_entity_id = e_id
                break
        
        if mentioned_entity_id:
            relationships.append({
                'entity1_id': entity_id,
                'entity2_id': mentioned_entity_id,
                'connection_type': relationship_type,
                'strength': strength,
                'source': f"Social post analysis ({len(posts)} posts)"
            })
    
    return relationships

def detect_entity_mentions(text, entity_names):
    """Use AI to detect mentions of other entities in text and analyze relationship type."""
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY not set. Cannot analyze mentions.")
        return []
    
    # Prepare entity names list for the prompt (limit to avoid token issues)
    if len(entity_names) > 100:
        logger.warning(f"Too many entity names ({len(entity_names)}), limiting to 100")
        entity_names = entity_names[:100]
    
    entity_names_str = "\n".join([f"- {name}" for name in entity_names])
    
    prompt = f"""
Analyze the following text and identify any mentions of entities from the provided list.
For each mentioned entity, determine the type of relationship implied and the strength of that relationship (0.0 to 1.0).

Relationship types:
- mentions: Simply mentions the other entity
- endorses: Explicitly supports/endorses
- criticizes: Explicitly criticizes/opposes
- collaborates: Works with/collaborates with
- affiliated: Has organizational affiliation
- influenced_by: Is influenced by/follows
- family: Family relationship
- co_sponsors: Co-sponsors legislation
- interviewed: Interviewed or featured
- donates_to: Financially supports
- reports_on: Reports on/covers

TEXT TO ANALYZE:
{text}

LIST OF ENTITIES TO LOOK FOR:
{entity_names_str}

Return a JSON array of objects with the following format:
[
  {{
    "entity_name": "Name of mentioned entity",
    "type": "relationship_type",
    "strength": 0.8,
    "context": "Brief explanation of why this relationship was identified"
  }}
]

Only include entities that are actually mentioned in the text. Return an empty array if no entities are mentioned.
"""
    
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        
        data = {
            "model": "gpt-4-turbo",
            "messages": [
                {"role": "system", "content": "You are a political relationship analyzer."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data
        )
        response.raise_for_status()
        
        # Extract the response text
        response_data = response.json()
        if "choices" in response_data and len(response_data["choices"]) > 0:
            ai_response = response_data["choices"][0]["message"]["content"].strip()
            
            # Try to parse JSON from the response
            try:
                # First, try to extract JSON if it's wrapped in markdown code blocks
                if "```json" in ai_response:
                    json_str = ai_response.split("```json")[1].split("```")[0].strip()
                    mentions = json.loads(json_str)
                elif "```" in ai_response:
                    json_str = ai_response.split("```")[1].strip()
                    mentions = json.loads(json_str)
                else:
                    mentions = json.loads(ai_response)
                
                return mentions
            except json.JSONDecodeError:
                logger.error(f"Failed to parse AI response as JSON")
                logger.debug(f"AI response: {ai_response}")
                return []
        else:
            logger.error(f"Unexpected AI response format")
            return []
            
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error during entity mention detection: {str(e)}")
        return []

def save_relationships(db, relationships):
    """Save new relationships to the database."""
    conn = None
    try:
        conn = db._get_connection()
        cursor = conn.cursor()
        
        for rel in relationships:
            # Check if this relationship already exists
            cursor.execute("""
                SELECT id, strength FROM entity_connections 
                WHERE entity1_id = ? AND entity2_id = ? AND connection_type = ?
            """, (
                rel['entity1_id'], 
                rel['entity2_id'], 
                rel['connection_type']
            ))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing relationship if new strength is higher
                existing_id = existing['id']
                existing_strength = existing['strength']
                
                if rel['strength'] > existing_strength:
                    cursor.execute("""
                        UPDATE entity_connections
                        SET strength = ?, source = ?, last_updated = ?
                        WHERE id = ?
                    """, (
                        rel['strength'],
                        rel['source'],
                        datetime.now().isoformat(),
                        existing_id
                    ))
                    logger.debug(f"Updated relationship {existing_id} with higher strength {rel['strength']}")
            else:
                # Insert new relationship
                cursor.execute("""
                    INSERT INTO entity_connections (
                        entity1_id, entity2_id, connection_type, 
                        strength, source, first_detected, last_updated
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    rel['entity1_id'],
                    rel['entity2_id'],
                    rel['connection_type'],
                    rel['strength'],
                    rel['source'],
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                logger.debug(f"Inserted new relationship between {rel['entity1_id']} and {rel['entity2_id']}")
        
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error saving relationships: {str(e)}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def find_voting_relationships(db, politician_ids):
    """Find relationships based on similar voting patterns."""
    if not politician_ids:
        return []
    
    logger.info("Finding relationships based on voting patterns")
    
    relationships = []
    
    try:
        # For each pair of politicians, calculate voting similarity
        for i, pol1_id in enumerate(politician_ids):
            for pol2_id in politician_ids[i+1:]:
                # Get recent votes for both politicians
                votes1 = db.get_voting_records(pol1_id, limit=50)
                votes2 = db.get_voting_records(pol2_id, limit=50)
                
                # Skip if not enough voting data
                if not votes1 or not votes2:
                    continue
                
                # Find votes they both participated in
                common_vote_ids = set(v['vote_id'] for v in votes1).intersection(
                    set(v['vote_id'] for v in votes2)
                )
                
                if len(common_vote_ids) < 5:
                    # Not enough common votes for meaningful analysis
                    continue
                
                # Create dictionaries for easier lookup
                votes1_dict = {v['vote_id']: v for v in votes1}
                votes2_dict = {v['vote_id']: v for v in votes2}
                
                # Count agreements and disagreements
                agreements = 0
                total = len(common_vote_ids)
                
                for vote_id in common_vote_ids:
                    if votes1_dict[vote_id]['vote_position'] == votes2_dict[vote_id]['vote_position']:
                        agreements += 1
                
                # Calculate similarity score (0 to 1)
                similarity = agreements / total if total > 0 else 0
                
                # Create relationships based on voting similarity
                if similarity > 0.8:
                    # Strong agreement - collaborates
                    relationships.append({
                        'entity1_id': pol1_id,
                        'entity2_id': pol2_id,
                        'connection_type': 'collaborates',
                        'strength': similarity,
                        'source': f"Voting pattern analysis ({agreements}/{total} agreement)"
                    })
                elif similarity < 0.2:
                    # Strong disagreement - criticizes
                    relationships.append({
                        'entity1_id': pol1_id,
                        'entity2_id': pol2_id,
                        'connection_type': 'criticizes',
                        'strength': 1 - similarity,
                        'source': f"Voting pattern analysis ({total-agreements}/{total} disagreement)"
                    })
    except Exception as e:
        logger.error(f"Error analyzing voting relationships: {str(e)}")
    
    return relationships

def process_entity(db, entity_id, entity_name, entity_type, all_entities):
    """Process a single entity to find relationships."""
    logger.info(f"Processing entity {entity_id}: {entity_name} ({entity_type})")
    
    relationships = []
    
    # 1. Analyze social posts for mentions
    social_relationships = analyze_social_posts(db, entity_id, entity_name, all_entities)
    relationships.extend(social_relationships)
    
    # 2. Save discovered relationships
    if relationships:
        saved = save_relationships(db, relationships)
        if saved:
            logger.info(f"Saved {len(relationships)} relationships for entity {entity_id}")
        else:
            logger.error(f"Failed to save relationships for entity {entity_id}")
    else:
        logger.info(f"No relationships found for entity {entity_id}")
    
    return len(relationships)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Find relationships between entities")
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Limit the number of entities to process (default: process all)"
    )
    parser.add_argument(
        "--entity-type", type=str, choices=['politician', 'influencer', 'organization'],
        help="Only process entities of this type"
    )
    parser.add_argument(
        "--id", type=int,
        help="Process a specific entity by ID"
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Reanalyze entities that already have relationships"
    )
    return parser.parse_args()

def main():
    """Main function to find relationships between entities."""
    args = parse_args()
    
    # Ensure log directory exists
    os.makedirs('logs', exist_ok=True)
    
    # Check API key
    check_api_key()
    
    # Initialize database manager
    db = DatabaseManager()
    
    # Get all entities for cross-referencing
    all_entities = get_all_entities(db)
    logger.info(f"Loaded {len(all_entities)} entities from database")
    
    # Get entities to process
    if args.id:
        # Process specific entity
        entity = db.get_entity(args.id)
        if entity:
            entities = [entity]
            logger.info(f"Processing single entity: {entity['name']} (ID: {entity['id']})")
        else:
            logger.error(f"No entity found with ID {args.id}")
            return
    else:
        # Process all entities, optionally filtered by type
        if args.entity_type:
            sql = "SELECT id, name, entity_type FROM entities WHERE entity_type = ?"
            entities = db.execute_query(sql, (args.entity_type,))
            logger.info(f"Processing {len(entities)} entities of type '{args.entity_type}'")
        else:
            sql = "SELECT id, name, entity_type FROM entities"
            entities = db.execute_query(sql)
            logger.info(f"Processing all {len(entities)} entities")
    
    # Apply limit if specified
    if args.limit and args.limit > 0 and len(entities) > args.limit:
        entities = entities[:args.limit]
        logger.info(f"Limited to {len(entities)} entities")
    
    # If we have politicians, process voting relationships first (more efficient to do all at once)
    politician_ids = [e['id'] for e in entities if e['entity_type'] == 'politician']
    if politician_ids:
        voting_relationships = find_voting_relationships(db, politician_ids)
        if voting_relationships:
            saved = save_relationships(db, voting_relationships)
            logger.info(f"Saved {len(voting_relationships)} voting-based relationships")
    
    # Process each entity
    total_relationships = 0
    for entity in tqdm(entities, desc="Processing entities"):
        # Skip entities that already have relationships unless forced
        if not args.force:
            related = db.get_related_entities(entity['id'], limit=1)
            if related:
                logger.info(f"Entity {entity['id']} already has relationships, skipping (use --force to override)")
                continue
        
        # Process entity
        rel_count = process_entity(
            db, entity['id'], entity['name'], entity['entity_type'], all_entities
        )
        total_relationships += rel_count
        
        # Small delay to avoid API rate limits
        time.sleep(1)
    
    logger.info(f"Relationship analysis complete. Found {total_relationships} total relationships.")

if __name__ == "__main__":
    main() 