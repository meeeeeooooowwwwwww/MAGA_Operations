#!/usr/bin/env python3
"""
Entity Classification Script for MAGA_Ops

Uses AI to classify entities in the database according to various categories:
- Entity type (politician, journalist, etc.)
- Entity subtype (senator, governor, etc.)
- Party affiliation (Republican, Democrat, etc.)
- Political ideology (conservative, progressive, etc.)
- Trump stance (supporter, critic, etc.)

Interacts with the new normalized database schema.
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

# Define the main category types we'll be classifying
CATEGORY_TYPES = ['entity_type', 'entity_subtype', 'party', 'ideology', 'trump_stance']

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

def get_categories_by_type(db):
    """Get all categories organized by type."""
    categories = db.get_categories()
    categories_by_type = {}
    
    for category in categories:
        cat_type = category['category_type']
        if cat_type not in categories_by_type:
            categories_by_type[cat_type] = []
        categories_by_type[cat_type].append({
            'id': category['id'],
            'code': category['code'],
            'name': category['name'],
            'description': category['description']
        })
    
    return categories_by_type

def generate_classification_prompt(entity_name, search_data, categories_by_type):
    """Generate a prompt for AI classification."""
    # Create lists of category options for each type
    category_options = {}
    for cat_type in CATEGORY_TYPES:
        if cat_type in categories_by_type:
            category_options[cat_type] = "\n".join([
                f"- {cat['code']}: {cat['description']}" 
                for cat in categories_by_type[cat_type]
            ])
        else:
            logger.warning(f"No categories found for type '{cat_type}'")
            category_options[cat_type] = "No options available"
    
    # Create prompt
    prompt = f"""
You are an expert in political entity classification. Analyze the following information about "{entity_name}" and classify them according to these categories:

ENTITY TYPE:
{category_options.get('entity_type', 'Not available')}

ENTITY SUBTYPE:
{category_options.get('entity_subtype', 'Not available')}

PARTY AFFILIATION:
{category_options.get('party', 'Not available')}

POLITICAL IDEOLOGY:
{category_options.get('ideology', 'Not available')}

TRUMP STANCE:
{category_options.get('trump_stance', 'Not available')}

INFORMATION ABOUT {entity_name.upper()}:
{search_data}

Based only on the above information, classify "{entity_name}" by providing a JSON object with the following fields:
- entity_type: The entity type code (e.g., "POLITICIAN")
- entity_subtype: The entity subtype code (e.g., "SENATOR")
- party: The party affiliation code (e.g., "REPUBLICAN")
- ideology: The political ideology code (e.g., "TRADITIONAL_CONSERVATIVE")
- trump_stance: The stance toward Trump code (e.g., "TRUMP_SUPPORTER")
- bio: A 1-2 sentence objective biographical summary
- confidence: A confidence score (0-1) for each classification
- sources: List of source statements supporting these classifications

Return only valid JSON without markdown formatting or additional text.
"""
    return prompt

def classify_entity_with_ai(entity_name, search_data, categories_by_type):
    """Classify entity using OpenAI's API based on search results."""
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY not set. Cannot perform AI classification.")
        return {}
    
    # Generate prompt
    prompt = generate_classification_prompt(entity_name, search_data, categories_by_type)
    
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

def update_entity_categories(db, entity_id, classification, categories_by_type):
    """Update an entity's categories based on classification results."""
    success_count = 0
    error_count = 0
    
    for cat_type in CATEGORY_TYPES:
        if cat_type in classification:
            category_code = classification[cat_type]
            
            # Find category ID
            category_id = None
            if cat_type in categories_by_type:
                for category in categories_by_type[cat_type]:
                    if category['code'] == category_code:
                        category_id = category['id']
                        break
            
            if category_id:
                # Get confidence score if available
                confidence = 1.0  # Default confidence
                if 'confidence' in classification and cat_type in classification['confidence']:
                    confidence = float(classification['confidence'][cat_type])
                
                # Use the database manager to update category
                field_name = f"category_{cat_type}"
                result = db.update_entity_field('', entity_id, field_name, category_id)
                
                if result:
                    logger.info(f"Updated category '{cat_type}' to '{category_code}' for entity {entity_id}")
                    success_count += 1
                else:
                    logger.error(f"Failed to update category '{cat_type}' for entity {entity_id}")
                    error_count += 1
            else:
                logger.warning(f"Category code '{category_code}' not found for type '{cat_type}'")
                error_count += 1
    
    # Update bio if available
    if 'bio' in classification and classification['bio']:
        result = db.update_entity_field('', entity_id, 'bio', classification['bio'])
        if result:
            logger.info(f"Updated bio for entity {entity_id}")
            success_count += 1
        else:
            logger.error(f"Failed to update bio for entity {entity_id}")
            error_count += 1
    
    return (success_count, error_count)

def process_entity(db, entity, categories_by_type, force=False):
    """Process a single entity: search, classify, and save."""
    try:
        entity_id = entity['id']
        entity_name = entity['name']
        logger.info(f"Processing entity: {entity_name} (ID: {entity_id})")
        
        # Check if entity already has categories and we're not forcing reclassification
        if not force:
            has_categories = False
            # Use the database manager to get categories
            entity_categories = db.get_entity_field('', entity_id, 'categories')
            
            if entity_categories and len(entity_categories) > 0:
                logger.info(f"Entity '{entity_name}' already has categories, skipping (use --force to override)")
                return {'status': 'skipped', 'reason': 'already_classified'}
        
        # Search for entity information
        search_results = search_entity(entity_name)
        if not search_results:
            logger.warning(f"No search results found for {entity_name}")
            search_data = ""
        else:
            search_data = extract_search_data(search_results)
        
        # Classify entity using AI
        classification = classify_entity_with_ai(entity_name, search_data, categories_by_type)
        if not classification:
            logger.warning(f"Failed to classify {entity_name}")
            return {'status': 'error', 'reason': 'classification_failed'}
        
        # Update entity categories
        success_count, error_count = update_entity_categories(db, entity_id, classification, categories_by_type)
        
        result = {
            'status': 'success' if success_count > 0 else 'error',
            'entity_id': entity_id,
            'entity_name': entity_name,
            'success_count': success_count,
            'error_count': error_count,
            'classification': classification
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing entity {entity.get('name', 'Unknown')}: {str(e)}")
        return {'status': 'error', 'reason': str(e), 'entity_id': entity.get('id')}

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
        "--entity-type", type=str, choices=['politician', 'influencer', 'organization'],
        help="Only process entities of this type"
    )
    parser.add_argument(
        "--id", type=int,
        help="Process a specific entity by ID"
    )
    parser.add_argument(
        "--name", type=str,
        help="Process a specific entity by name"
    )
    parser.add_argument(
        "--output", type=str, default="data/classification_results.json",
        help="Output file path for classification results"
    )
    return parser.parse_args()

def main():
    """Main function to classify entities."""
    args = parse_args()
    
    # Ensure log and data directories exist
    os.makedirs('logs', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    
    # Check API keys
    check_api_keys()
    
    # Initialize database manager
    db = DatabaseManager()
    
    # Get all categories by type
    categories_by_type = get_categories_by_type(db)
    logger.info(f"Loaded categories for {len(categories_by_type)} types")
    
    # Get entities to process
    if args.id:
        # Get specific entity by ID
        entity = db.get_entity(args.id)
        if entity:
            entities = [entity]
            logger.info(f"Found entity with ID {args.id}: {entity['name']}")
        else:
            logger.error(f"No entity found with ID {args.id}")
            return
    elif args.name:
        # Get specific entity by name
        entity = db.get_entity_by_name(args.name)
        if entity:
            entities = [entity]
            logger.info(f"Found entity with name '{args.name}': ID {entity['id']}")
        else:
            logger.error(f"No entity found with name '{args.name}'")
            return
    else:
        # Get all entities, optionally filtered by type
        if args.entity_type:
            sql = f"SELECT id, name, entity_type FROM entities WHERE entity_type = ?"
            entities = db.execute_query(sql, (args.entity_type,))
            logger.info(f"Found {len(entities)} entities of type '{args.entity_type}'")
        else:
            sql = "SELECT id, name, entity_type FROM entities"
            entities = db.execute_query(sql)
            logger.info(f"Found {len(entities)} total entities")
    
    # Apply limit if specified
    if args.limit and args.limit > 0 and len(entities) > args.limit:
        logger.info(f"Limiting to first {args.limit} entities")
        entities = entities[:args.limit]
    
    # Process entities
    results = []
    for entity in tqdm(entities, desc="Classifying entities"):
        result = process_entity(db, entity, categories_by_type, force=args.force)
        results.append(result)
        
        # Save results after each entity (to capture progress in case of failure)
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Add a small delay to avoid rate limits
        time.sleep(1)
    
    # Summarize results
    success_count = sum(1 for r in results if r['status'] == 'success')
    skipped_count = sum(1 for r in results if r['status'] == 'skipped')
    error_count = sum(1 for r in results if r['status'] == 'error')
    
    logger.info(f"Processed {len(results)} entities:")
    logger.info(f"- Success: {success_count}")
    logger.info(f"- Skipped: {skipped_count}")
    logger.info(f"- Errors: {error_count}")
    logger.info(f"Results saved to {args.output}")

if __name__ == "__main__":
    main() 