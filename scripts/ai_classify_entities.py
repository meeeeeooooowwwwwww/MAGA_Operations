#!/usr/bin/env python3
"""
AI Entity Classification Script

This script:
1. Extracts entity names from various sources
2. Uses web search to gather information about each entity
3. Classifies entities using AI into categories defined in entity_schema.py
4. Stores the results in the database
"""
import os
import sys
import json
import time
import logging
import sqlite3
import requests
import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from collections import defaultdict
from tqdm import tqdm

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(PROJECT_ROOT)

# Local imports
from scripts.db.entity_schema import (
    get_db_connection, 
    insert_entity, 
    get_entity, 
    ENTITY_TYPES, 
    ENTITY_SUBTYPES,
    PARTY_AFFILIATIONS,
    POLITICAL_IDEOLOGIES,
    TRUMP_STANCE
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(PROJECT_ROOT, 'logs', 'entity_classification.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

# API Keys
SERPER_API_KEY = os.getenv('SERPER_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# File paths
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
ENTITY_CLASSIFICATIONS_FILE = os.path.join(DATA_DIR, 'entity_classifications.json')

def check_api_keys():
    """Check if API keys are set."""
    missing_keys = []
    if not SERPER_API_KEY:
        missing_keys.append('SERPER_API_KEY')
    if not OPENAI_API_KEY:
        missing_keys.append('OPENAI_API_KEY')
    
    if missing_keys:
        logger.error(f"Missing API keys: {', '.join(missing_keys)}. Please add them to your .env file.")
        sys.exit(1)
    
    logger.info("API keys verified.")

def normalize_name(name):
    """Normalize entity name for consistent storage and lookup."""
    return name.lower().strip()

def extract_entities():
    """Extract entity names from sources like database, files, etc."""
    entities = []
    
    # Placeholder for entity extraction logic
    # In a real implementation, you would extract from various data sources
    
    # Example: load from a JSON file if it exists
    try:
        entities_file = os.path.join(DATA_DIR, 'entities.json')
        if os.path.exists(entities_file):
            with open(entities_file, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    entities = data
                elif isinstance(data, dict) and 'entities' in data:
                    entities = data['entities']
            logger.info(f"Loaded {len(entities)} entities from {entities_file}")
        else:
            # Placeholder example entities
            example_entities = [
                "Donald Trump",
                "Joe Biden",
                "Fox News",
                "CNN",
                "Sean Hannity",
                "Rachel Maddow",
                "Republican National Committee",
                "Democratic National Committee",
                "Elon Musk",
                "Ben Shapiro"
            ]
            entities = [{"name": name} for name in example_entities]
            logger.info(f"Using {len(entities)} example entities for testing")
    except Exception as e:
        logger.error(f"Error extracting entities: {str(e)}")
    
    # Process entities
    processed_entities = []
    for entity in entities:
        if isinstance(entity, str):
            processed_entity = {"name": entity, "normalized_name": normalize_name(entity)}
        elif isinstance(entity, dict) and "name" in entity:
            if "normalized_name" not in entity:
                entity["normalized_name"] = normalize_name(entity["name"])
            processed_entity = entity
        else:
            logger.warning(f"Skipping invalid entity format: {entity}")
            continue
        
        processed_entities.append(processed_entity)
    
    return processed_entities

def search_entity(entity_name, max_retries=3, delay=2):
    """Search for entity information using Serper API."""
    if not SERPER_API_KEY:
        logger.error("SERPER_API_KEY not set. Cannot perform web search.")
        return None
    
    url = "https://google.serper.dev/search"
    payload = json.dumps({
        "q": f"{entity_name} political affiliation biography",
        "num": 5
    })
    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json'
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, data=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.warning(f"Search attempt {attempt+1}/{max_retries} failed for {entity_name}: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(delay)
            else:
                logger.error(f"All search attempts failed for {entity_name}")
                return None

def extract_search_data(search_results):
    """Extract relevant information from search results."""
    if not search_results or not isinstance(search_results, dict):
        return ""
    
    search_text = ""
    
    # Extract organic results
    if "organic" in search_results:
        for result in search_results["organic"][:3]:  # Take top 3 results
            if "title" in result:
                search_text += result["title"] + "\n"
            if "snippet" in result:
                search_text += result["snippet"] + "\n\n"
    
    # Extract knowledge graph if available
    if "knowledgeGraph" in search_results:
        kg = search_results["knowledgeGraph"]
        if "title" in kg:
            search_text += "Knowledge Graph: " + kg["title"] + "\n"
        if "type" in kg:
            search_text += "Type: " + kg["type"] + "\n"
        if "description" in kg:
            search_text += "Description: " + kg["description"] + "\n"
        if "attributes" in kg:
            search_text += "Attributes:\n"
            for key, value in kg["attributes"].items():
                search_text += f"- {key}: {value}\n"
    
    return search_text

def classify_entity_with_ai(entity_name, search_data):
    """Classify entity using OpenAI's API based on search results."""
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY not set. Cannot perform AI classification.")
        return {}
    
    # Prepare classification options as strings
    entity_types_str = "\n".join([f"- {key}: {desc}" for key, desc in ENTITY_TYPES.items()])
    entity_subtypes_str = "\n".join([f"- {key}: {desc}" for key, desc in ENTITY_SUBTYPES.items()])
    party_affiliations_str = "\n".join([f"- {key}: {desc}" for key, desc in PARTY_AFFILIATIONS.items()])
    political_ideologies_str = "\n".join([f"- {key}: {desc}" for key, desc in POLITICAL_IDEOLOGIES.items()])
    trump_stance_str = "\n".join([f"- {key}: {desc}" for key, desc in TRUMP_STANCE.items()])
    
    # Create prompt for AI
    prompt = f"""
You are an expert in political entity classification. Analyze the following information about "{entity_name}" and classify them according to these categories:

ENTITY TYPE:
{entity_types_str}

ENTITY SUBTYPE:
{entity_subtypes_str}

PARTY AFFILIATION:
{party_affiliations_str}

POLITICAL IDEOLOGY:
{political_ideologies_str}

TRUMP STANCE:
{trump_stance_str}

INFORMATION ABOUT {entity_name.upper()}:
{search_data}

Based only on the above information, classify "{entity_name}" by providing a JSON object with the following fields:
- entity_type: The entity type code (e.g., "POLITICIAN")
- entity_subtype: The entity subtype code (e.g., "SENATOR")
- party_affiliation: The party affiliation code (e.g., "REPUBLICAN")
- political_ideology: The political ideology code (e.g., "TRADITIONAL_CONSERVATIVE")
- trump_stance: The stance toward Trump code (e.g., "TRUMP_SUPPORTER")
- bio: A 1-2 sentence objective biographical summary
- sources: List of source statements supporting these classifications

Return only valid JSON without markdown formatting or additional text.
"""

    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        
        data = {
            "model": "gpt-4-turbo",
            "messages": [
                {"role": "system", "content": "You are a political entity classification expert."},
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
                classification = json.loads(ai_response)
                return classification
            except json.JSONDecodeError:
                logger.error(f"Failed to parse AI response as JSON for {entity_name}")
                logger.debug(f"AI response: {ai_response}")
                return {}
        else:
            logger.error(f"Unexpected AI response format for {entity_name}")
            return {}
            
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed for {entity_name}: {str(e)}")
        return {}
    except Exception as e:
        logger.error(f"Unexpected error during AI classification for {entity_name}: {str(e)}")
        return {}

def process_entity(entity):
    """Process a single entity: search, classify, and save."""
    try:
        entity_name = entity["name"]
        logger.info(f"Processing entity: {entity_name}")
        
        # Check if entity is already classified in database
        existing_entity = get_entity(entity["normalized_name"])
        if existing_entity and existing_entity.get("entity_type") and existing_entity.get("entity_type") != "UNKNOWN":
            logger.info(f"Entity '{entity_name}' already classified in database, skipping")
            return existing_entity
        
        # Search for entity information
        search_results = search_entity(entity_name)
        if not search_results:
            logger.warning(f"No search results found for {entity_name}")
            search_data = ""
        else:
            search_data = extract_search_data(search_results)
        
        # Classify entity using AI
        classification = classify_entity_with_ai(entity_name, search_data)
        if not classification:
            logger.warning(f"Failed to classify {entity_name}")
            classification = {
                "entity_type": "UNKNOWN",
                "entity_subtype": "UNKNOWN",
                "party_affiliation": "UNKNOWN",
                "political_ideology": "UNKNOWN",
                "trump_stance": "UNKNOWN",
                "bio": f"No information available for {entity_name}"
            }
        
        # Merge classification with entity data
        entity_data = {**entity, **classification}
        
        # Add metadata
        entity_data["last_updated"] = datetime.now().isoformat()
        if not entity_data.get("first_appearance_date"):
            entity_data["first_appearance_date"] = datetime.now().isoformat()
        
        # Save to database
        insert_entity(entity_data)
        
        return entity_data
        
    except Exception as e:
        logger.error(f"Error processing entity {entity.get('name', 'Unknown')}: {str(e)}")
        return entity

def save_classifications(classifications):
    """Save classifications to a JSON file."""
    try:
        # Create parent directories if they don't exist
        os.makedirs(os.path.dirname(ENTITY_CLASSIFICATIONS_FILE), exist_ok=True)
        
        with open(ENTITY_CLASSIFICATIONS_FILE, 'w') as f:
            json.dump(classifications, f, indent=2)
        logger.info(f"Saved {len(classifications)} entity classifications to {ENTITY_CLASSIFICATIONS_FILE}")
    except Exception as e:
        logger.error(f"Error saving classifications to file: {str(e)}")

def generate_statistics(classifications):
    """Generate statistics about the classified entities."""
    stats = {
        "total_entities": len(classifications),
        "entity_types": defaultdict(int),
        "entity_subtypes": defaultdict(int),
        "party_affiliations": defaultdict(int),
        "political_ideologies": defaultdict(int),
        "trump_stance": defaultdict(int)
    }
    
    for entity in classifications:
        stats["entity_types"][entity.get("entity_type", "UNKNOWN")] += 1
        stats["entity_subtypes"][entity.get("entity_subtype", "UNKNOWN")] += 1
        stats["party_affiliations"][entity.get("party_affiliation", "UNKNOWN")] += 1
        stats["political_ideologies"][entity.get("political_ideology", "UNKNOWN")] += 1
        stats["trump_stance"][entity.get("trump_stance", "UNKNOWN")] += 1
    
    return stats

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Classify political entities using AI")
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Limit the number of entities to process (default: process all)"
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Force reclassification of entities that already have a classification"
    )
    parser.add_argument(
        "--output", type=str, default=ENTITY_CLASSIFICATIONS_FILE,
        help=f"Output file path (default: {ENTITY_CLASSIFICATIONS_FILE})"
    )
    return parser.parse_args()

def main():
    """Main function to classify entities."""
    args = parse_args()
    
    # Check API keys
    check_api_keys()
    
    # Extract entities to classify
    entities = extract_entities()
    logger.info(f"Extracted {len(entities)} entities for classification")
    
    # Apply limit if specified
    if args.limit and args.limit > 0:
        entities = entities[:args.limit]
        logger.info(f"Limited to {len(entities)} entities")
    
    # Process each entity
    classified_entities = []
    for entity in tqdm(entities, desc="Classifying entities"):
        classified_entity = process_entity(entity)
        classified_entities.append(classified_entity)
        # Add a small delay to avoid rate limits
        time.sleep(1)
    
    # Save classifications
    save_classifications(classified_entities)
    
    # Generate and display statistics
    stats = generate_statistics(classified_entities)
    print("\nEntity Classification Statistics:")
    print(f"Total Entities: {stats['total_entities']}")
    
    print("\nEntity Types:")
    for k, v in sorted(stats['entity_types'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {k}: {v}")
    
    print("\nTop Entity Subtypes:")
    for k, v in sorted(stats['entity_subtypes'].items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {k}: {v}")
    
    print("\nParty Affiliations:")
    for k, v in sorted(stats['party_affiliations'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {k}: {v}")
    
    print("\nTop Political Ideologies:")
    for k, v in sorted(stats['political_ideologies'].items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {k}: {v}")
    
    print("\nTrump Stance:")
    for k, v in sorted(stats['trump_stance'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {k}: {v}")
    
    print(f"\nClassifications saved to {ENTITY_CLASSIFICATIONS_FILE}")

if __name__ == "__main__":
    main() 