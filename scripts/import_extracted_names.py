#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Import Extracted Names into AI-Optimized Database
--------------------------------------------------
This script processes the names extracted from Benny Johnson's YouTube videos
and imports them into our AI-optimized database structure.
"""

import os
import json
import sqlite3
import datetime
import re
from pathlib import Path

# Configuration
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DB_PATH = os.path.join(DATA_DIR, "influencers_ai.db")
NAMES_JSON = None  # Will be set to the most recent names JSON file

# Political figures categorization data
KNOWN_POLITICIANS = {
    "Trump": {
        "full_name": "Donald Trump",
        "category": "Federal Politician",
        "affiliations": ["Republican", "MAGA"],
        "bio": "45th President of the United States",
        "twitter_handle": "@realDonaldTrump"
    },
    "Biden": {
        "full_name": "Joe Biden",
        "category": "Federal Politician",
        "affiliations": ["Democrat"],
        "bio": "46th President of the United States",
        "twitter_handle": "@JoeBiden"
    },
    "DeSantis": {
        "full_name": "Ron DeSantis",
        "category": "Federal Politician", 
        "affiliations": ["Republican"],
        "bio": "Governor of Florida",
        "twitter_handle": "@GovRonDeSantis"
    },
    "Kristi Noem": {
        "full_name": "Kristi Noem",
        "category": "State Politician",
        "affiliations": ["Republican", "Trump Supporter"],
        "bio": "Governor of South Dakota",
        "twitter_handle": "@KristiNoem"
    },
    "Elon Musk": {
        "full_name": "Elon Musk",
        "category": "Business Leader",
        "affiliations": ["Independent", "Trump Supporter"],
        "bio": "CEO of Tesla, SpaceX, and owner of Twitter/X",
        "twitter_handle": "@elonmusk"
    },
    "Musk": {
        "full_name": "Elon Musk",
        "category": "Business Leader",
        "affiliations": ["Independent", "Trump Supporter"],
        "bio": "CEO of Tesla, SpaceX, and owner of Twitter/X",
        "twitter_handle": "@elonmusk" 
    },
    "Kamala": {
        "full_name": "Kamala Harris",
        "category": "Federal Politician",
        "affiliations": ["Democrat"],
        "bio": "Vice President of the United States",
        "twitter_handle": "@VP"
    },
    "Harris": {
        "full_name": "Kamala Harris",
        "category": "Federal Politician",
        "affiliations": ["Democrat"],
        "bio": "Vice President of the United States",
        "twitter_handle": "@VP"
    },
    "John Rich": {
        "full_name": "John Rich",
        "category": "Influencer",
        "affiliations": ["Republican", "Trump Supporter"],
        "bio": "Country music star and political commentator",
        "twitter_handle": "@johnrich"
    },
    "Jeffrey Epstein": {
        "full_name": "Jeffrey Epstein",
        "category": "Business Leader",
        "affiliations": ["Independent"],
        "bio": "Financier and convicted sex offender",
        "twitter_handle": ""
    },
    "Kash Patel": {
        "full_name": "Kash Patel",
        "category": "Federal Politician",
        "affiliations": ["Republican", "Trump Supporter"],
        "bio": "Former Chief of Staff to the Secretary of Defense",
        "twitter_handle": "@Kash"
    },
    "Dan Bongino": {
        "full_name": "Dan Bongino",
        "category": "Conservative Media Personality",
        "affiliations": ["Republican", "MAGA"],
        "bio": "Conservative political commentator and radio show host",
        "twitter_handle": "@dbongino"
    },
    "Mike Davis": {
        "full_name": "Mike Davis",
        "category": "Conservative Media Personality",
        "affiliations": ["Republican", "MAGA"],
        "bio": "Lawyer and political commentator",
        "twitter_handle": "@mrddmia"
    }
}

# Noise terms to filter out (not real political figures)
NOISE_TERMS = [
    "Fake Space", "Ticket Sales", "Multiple Shows", "Hysterical New", "White Male",
    "Blue Suit", "To The", "Her Face", "In Denial", "Big Peace", "These Answers",
    "Dark Truth", "Not Real", "The Final", "After Getting", "Worse Than",
    "Calls For", "Asked Spring"
]

def find_most_recent_names_file():
    """Find the most recent Benny Johnson names JSON file."""
    name_files = []
    for file in os.listdir(DATA_DIR):
        if file.startswith("benny_johnson_names_") and file.endswith(".json"):
            name_files.append(os.path.join(DATA_DIR, file))
    
    if not name_files:
        return None
    
    # Sort by modification time, newest first
    name_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return name_files[0]

def initialize_database():
    """Initialize the database with our AI-optimized schema."""
    if os.path.exists(DB_PATH):
        print(f"Database already exists at {DB_PATH}")
        return
    
    print(f"Creating new database at {DB_PATH}")
    
    # Read the SQL schema file
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ai_optimized_schema.sql")
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
    
    # Create the database and execute the schema
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(schema_sql)
    conn.commit()
    conn.close()
    
    print("Database initialized successfully")

def normalize_name(name):
    """Normalize a name for better matching."""
    # Convert to lowercase
    normalized = name.lower()
    # Remove special characters and extra spaces
    normalized = re.sub(r'[^\w\s]', '', normalized)
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized

def is_likely_person(name):
    """Check if this is likely a real person's name."""
    # Filter out noise terms
    if name in NOISE_TERMS or any(term.lower() in name.lower() for term in NOISE_TERMS):
        return False
    
    # Check for known political figures
    if name in KNOWN_POLITICIANS:
        return True
    
    # Title case words (proper names) that aren't extremely short
    if ' ' in name and len(name) > 5 and all(w[0].isupper() for w in name.split() if len(w) > 1):
        return True
    
    # Known name patterns: First Last, single names like "Trump"
    name_pattern = r'^[A-Z][a-z]+ [A-Z][a-z]+$'
    single_name_pattern = r'^[A-Z][a-z]{2,}$'
    
    if re.match(name_pattern, name) or re.match(single_name_pattern, name):
        return True
    
    return False

def get_or_create_category(conn, category_name):
    """Get the ID for a category, creating it if it doesn't exist."""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM categories WHERE name = ?", (category_name,))
    result = cursor.fetchone()
    
    if result:
        return result[0]
    
    # Category doesn't exist, so create parent category if needed
    if category_name in ["Federal Politician", "State Politician"]:
        parent_id = get_or_create_category(conn, "Politician")
        level = 2
    elif category_name in ["Conservative Media Personality", "Progressive Media Personality"]:
        parent_id = get_or_create_category(conn, "Media Personality")
        level = 2
    else:
        parent_id = None
        level = 1
    
    if parent_id:
        cursor.execute(
            "INSERT INTO categories (name, parent_category_id, taxonomy_level) VALUES (?, ?, ?)",
            (category_name, parent_id, level)
        )
    else:
        cursor.execute(
            "INSERT INTO categories (name, taxonomy_level) VALUES (?, ?)",
            (category_name, level)
        )
    
    conn.commit()
    return cursor.lastrowid

def get_or_create_affiliation(conn, affiliation_name):
    """Get the ID for an affiliation, creating it if it doesn't exist."""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM affiliations WHERE name = ?", (affiliation_name,))
    result = cursor.fetchone()
    
    if result:
        return result[0]
    
    # Just insert with basic data if not found
    cursor.execute(
        "INSERT INTO affiliations (name) VALUES (?)",
        (affiliation_name,)
    )
    
    conn.commit()
    return cursor.lastrowid

def import_names_to_database():
    """Import the extracted names into the database."""
    if not NAMES_JSON or not os.path.exists(NAMES_JSON):
        print("No names JSON file found")
        return
    
    print(f"Importing names from {NAMES_JSON}")
    
    # Load the names data
    with open(NAMES_JSON, 'r', encoding='utf-8') as f:
        names_data = json.load(f)
    
    # Connect to the database
    conn = sqlite3.connect(DB_PATH)
    
    # Get the current date for tracking
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Process each name
    total_names = len(names_data)
    imported_count = 0
    skipped_count = 0
    
    for i, item in enumerate(names_data):
        name = item["name"]
        mentions = item["mentions"]
        
        # Skip if not likely a person
        if not is_likely_person(name):
            print(f"Skipping '{name}' as it doesn't appear to be a person")
            skipped_count += 1
            continue
        
        # Check if this is a known political figure
        if name in KNOWN_POLITICIANS:
            info = KNOWN_POLITICIANS[name]
            full_name = info["full_name"]
            category = info["category"]
            affiliations = info["affiliations"]
            bio = info["bio"]
            twitter_handle = info["twitter_handle"]
        else:
            # For unknown names, use what we have and guess the rest
            full_name = name
            # Guess category based on context
            if "Judge" in name or "Senator" in name or "Governor" in name or "Rep." in name:
                category = "Politician"
            else:
                category = "Influencer"  # Default category
            
            affiliations = []  # We don't know affiliations
            bio = f"Mentioned in Benny Johnson's YouTube videos {mentions} times"
            twitter_handle = "@" + normalize_name(name).replace(" ", "")
        
        # Get or create the category
        category_id = get_or_create_category(conn, category)
        
        # Normalize the name
        normalized_name = normalize_name(full_name)
        
        # Check if the influencer already exists
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM influencers WHERE normalized_name = ?", (normalized_name,))
        existing_id = cursor.fetchone()
        
        if existing_id:
            influencer_id = existing_id[0]
            # Update the existing record
            cursor.execute("""
                UPDATE influencers 
                SET relevance_score = relevance_score + ?,
                    last_updated = ?
                WHERE id = ?
            """, (mentions / 10.0, current_date, influencer_id))
            print(f"Updated existing influencer: {full_name}")
        else:
            # Insert new influencer
            cursor.execute("""
                INSERT INTO influencers (
                    name, normalized_name, category_id, bio, twitter_handle,
                    first_appearance_date, last_updated, relevance_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                full_name, normalized_name, category_id, bio, twitter_handle,
                current_date, current_date, mentions / 10.0
            ))
            influencer_id = cursor.lastrowid
            print(f"Added new influencer: {full_name}")
        
        # Add name variation if different from full name
        if name != full_name:
            cursor.execute("""
                INSERT OR IGNORE INTO name_variations (
                    influencer_id, variation, source, frequency
                ) VALUES (?, ?, ?, ?)
            """, (
                influencer_id, name, "Benny Johnson YouTube", mentions
            ))
        
        # Add affiliations
        for affiliation in affiliations:
            affiliation_id = get_or_create_affiliation(conn, affiliation)
            cursor.execute("""
                INSERT OR IGNORE INTO influencer_affiliations (
                    influencer_id, affiliation_id, source_count
                ) VALUES (?, ?, ?)
            """, (influencer_id, affiliation_id, 1))
        
        # Commit after each influencer to avoid losing all work if there's an error
        conn.commit()
        imported_count += 1
        
        # Show progress periodically
        if (i + 1) % 10 == 0 or i == total_names - 1:
            print(f"Processed {i + 1}/{total_names} names")
    
    # Close the database connection
    conn.close()
    
    print("\nImport Summary:")
    print(f"- Total names processed: {total_names}")
    print(f"- Names imported: {imported_count}")
    print(f"- Names skipped: {skipped_count}")
    print(f"- Database saved to: {DB_PATH}")

def main():
    """Main function."""
    global NAMES_JSON
    
    print("Import Extracted Names into AI-Optimized Database")
    print("--------------------------------------------------")
    
    # Find the most recent names JSON file
    NAMES_JSON = find_most_recent_names_file()
    if not NAMES_JSON:
        print("No Benny Johnson names JSON file found in the data directory")
        return
    
    print(f"Found names file: {os.path.basename(NAMES_JSON)}")
    
    # Initialize the database
    initialize_database()
    
    # Import the names
    import_names_to_database()
    
    print("\nProcess completed!")

if __name__ == "__main__":
    main() 