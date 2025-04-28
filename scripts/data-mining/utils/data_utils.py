#!/usr/bin/env python3
"""
Common utilities for data processing operations
"""
import os
import sys
import json
import csv
import pickle
import hashlib
import re
from datetime import datetime, timedelta
import sqlite3

# Add parent directory to path for relative imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config import DB_PATH, CACHE_DIR, CACHE_EXPIRY
from utils.logger import get_logger

# Initialize logger
logger = get_logger("data_utils")

def connect_db():
    """
    Create a connection to the SQLite database
    
    Returns:
        sqlite3.Connection: Database connection object
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        raise

def generate_cache_key(source, params):
    """
    Generate a unique cache key based on source and parameters
    
    Args:
        source (str): The data source name
        params (dict): Dictionary of parameters
        
    Returns:
        str: A unique cache key
    """
    # Convert params to sorted string representation to ensure consistency
    param_str = json.dumps(params, sort_keys=True)
    key = f"{source}:{param_str}"
    return hashlib.md5(key.encode()).hexdigest()

def get_cache_path(source, cache_key):
    """
    Get the full path to a cache file
    
    Args:
        source (str): The data source name
        cache_key (str): The cache key
        
    Returns:
        str: Full path to the cache file
    """
    source_dir = os.path.join(CACHE_DIR, source)
    os.makedirs(source_dir, exist_ok=True)
    return os.path.join(source_dir, f"{cache_key}.pkl")

def cache_get(source, params):
    """
    Get data from cache if available and not expired
    
    Args:
        source (str): The data source name
        params (dict): Dictionary of parameters
        
    Returns:
        object: Cached data or None if not found or expired
    """
    cache_key = generate_cache_key(source, params)
    cache_path = get_cache_path(source, cache_key)
    
    # Check if cache file exists
    if not os.path.exists(cache_path):
        return None
    
    # Get cache expiry time for this source
    expiry_time = CACHE_EXPIRY.get(source, CACHE_EXPIRY['default'])
    
    # Check if cache is expired
    file_mod_time = os.path.getmtime(cache_path)
    if datetime.now().timestamp() - file_mod_time > expiry_time:
        logger.debug(f"Cache expired for {source} with key {cache_key}")
        return None
    
    # Load cache data
    try:
        with open(cache_path, 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        logger.warning(f"Failed to load cache for {source}: {e}")
        return None

def cache_set(source, params, data):
    """
    Save data to cache
    
    Args:
        source (str): The data source name
        params (dict): Dictionary of parameters
        data (object): Data to cache
        
    Returns:
        bool: True if successful, False otherwise
    """
    cache_key = generate_cache_key(source, params)
    cache_path = get_cache_path(source, cache_key)
    
    try:
        with open(cache_path, 'wb') as f:
            pickle.dump(data, f)
        return True
    except Exception as e:
        logger.warning(f"Failed to save cache for {source}: {e}")
        return False

def clean_text(text):
    """
    Clean text by removing extra whitespace, HTML, etc.
    
    Args:
        text (str): Text to clean
        
    Returns:
        str: Cleaned text
    """
    if not text:
        return ""
        
    # Convert to string if not already
    text = str(text)
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    
    # Replace multiple spaces, newlines, tabs with a single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text

def parse_date(date_str, formats=None):
    """
    Parse a date string into a datetime object
    
    Args:
        date_str (str): Date string to parse
        formats (list): List of formats to try
        
    Returns:
        datetime: Parsed datetime or None if parsing fails
    """
    if not date_str:
        return None
        
    if formats is None:
        formats = [
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%m/%d/%Y',
            '%d/%m/%Y',
            '%Y-%m-%d %H:%M:%S',
            '%Y/%m/%d %H:%M:%S',
            '%m/%d/%Y %H:%M:%S',
            '%d/%m/%Y %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%dT%H:%M:%S.%fZ',
            '%b %d, %Y',
            '%B %d, %Y',
            '%d %b %Y',
            '%d %B %Y'
        ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    logger.warning(f"Could not parse date: {date_str}")
    return None

def normalize_name(name):
    """
    Normalize a person's name for matching
    
    Args:
        name (str): Name to normalize
        
    Returns:
        str: Normalized name
    """
    if not name:
        return ""
    
    # Convert to lowercase
    name = name.lower()
    
    # Remove titles, suffixes, etc.
    titles = ['mr', 'mrs', 'ms', 'miss', 'dr', 'prof', 'representative', 'rep', 'senator', 'sen']
    suffixes = ['jr', 'sr', 'ii', 'iii', 'iv', 'phd', 'md', 'esq']
    
    # Replace commas and periods with spaces
    name = name.replace(',', ' ').replace('.', ' ')
    
    # Split into words
    parts = name.split()
    
    # Remove titles and suffixes
    parts = [p for p in parts if p not in titles and p not in suffixes]
    
    # Rejoin
    return ' '.join(parts)

def export_to_csv(data, filepath, headers=None):
    """
    Export data to CSV
    
    Args:
        data (list): List of dictionaries or lists
        filepath (str): Path to output file
        headers (list): Optional list of column headers
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            if data and isinstance(data[0], dict):
                if not headers:
                    headers = data[0].keys()
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(data)
            else:
                writer = csv.writer(f)
                if headers:
                    writer.writerow(headers)
                writer.writerows(data)
        return True
    except Exception as e:
        logger.error(f"Failed to export to CSV: {e}")
        return False

def calculate_similarity(text1, text2):
    """
    Calculate similarity between two text strings
    
    Args:
        text1 (str): First text
        text2 (str): Second text
        
    Returns:
        float: Similarity score 0-1
    """
    if not text1 or not text2:
        return 0.0
    
    # Convert to lowercase
    text1 = text1.lower()
    text2 = text2.lower()
    
    # Tokenize
    tokens1 = set(re.findall(r'\w+', text1))
    tokens2 = set(re.findall(r'\w+', text2))
    
    # Calculate Jaccard similarity
    intersection = len(tokens1.intersection(tokens2))
    union = len(tokens1.union(tokens2))
    
    if union == 0:
        return 0.0
    
    return intersection / union

def levenshtein_distance(s1, s2):
    """
    Calculate the Levenshtein distance between two strings
    
    Args:
        s1 (str): First string
        s2 (str): Second string
        
    Returns:
        int: Edit distance
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]

def calculate_name_similarity(name1, name2):
    """
    Calculate similarity between two person names
    
    Args:
        name1 (str): First name
        name2 (str): Second name
        
    Returns:
        float: Similarity score 0-1
    """
    norm1 = normalize_name(name1)
    norm2 = normalize_name(name2)
    
    if not norm1 or not norm2:
        return 0.0
    
    # Check for exact match
    if norm1 == norm2:
        return 1.0
    
    # Check for name containment
    if norm1 in norm2 or norm2 in norm1:
        return 0.9
    
    # Calculate edit distance
    max_len = max(len(norm1), len(norm2))
    if max_len == 0:
        return 0.0
    
    distance = levenshtein_distance(norm1, norm2)
    similarity = 1.0 - (distance / max_len)
    
    return max(0.0, similarity)

if __name__ == "__main__":
    # Test functions
    print("Testing data utilities...")
    
    # Test DB connection
    conn = connect_db()
    print(f"Database connection successful: {conn is not None}")
    if conn:
        conn.close()
    
    # Test text cleaning
    test_text = "  <p>This is a <b>test</b> with\nmultiple   spaces</p>  "
    cleaned = clean_text(test_text)
    print(f"Cleaned text: '{cleaned}'")
    
    # Test date parsing
    test_date = "2023-05-15T14:30:45Z"
    parsed = parse_date(test_date)
    print(f"Parsed date: {parsed}")
    
    # Test name normalization
    test_name = "Dr. John A. Smith, Jr."
    normalized = normalize_name(test_name)
    print(f"Normalized name: '{normalized}'")
    
    # Test similarity calculation
    text1 = "The quick brown fox jumps over the lazy dog"
    text2 = "A quick brown fox jumped over a lazy dog"
    sim = calculate_similarity(text1, text2)
    print(f"Text similarity: {sim:.2f}")
    
    # Test name similarity
    name1 = "John Robert Smith"
    name2 = "Smith, John R."
    name_sim = calculate_name_similarity(name1, name2)
    print(f"Name similarity: {name_sim:.2f}")
    
    print("Data utilities testing complete.") 