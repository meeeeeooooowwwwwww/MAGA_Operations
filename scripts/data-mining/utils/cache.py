#!/usr/bin/env python3
"""
Caching utility for data mining operations.
Provides functions to cache and retrieve data from API calls.
"""
import os
import sys
import json
import pickle
import hashlib
import datetime
import time
from pathlib import Path

# Add parent directory to path for relative imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from data_mining.utils.logger import get_logger
from data_mining.utils.config import CACHE_DIR, CACHE_ENABLED, get_cache_expiry

# Initialize logger
logger = get_logger('cache')

def generate_cache_key(url, params=None, headers=None, method='GET'):
    """
    Generate a unique key for caching based on request parameters
    
    Args:
        url (str): The URL to request
        params (dict, optional): Query parameters
        headers (dict, optional): Request headers to include in cache key
        method (str, optional): HTTP method. Defaults to 'GET'.
        
    Returns:
        str: A hash string to use as cache key
    """
    # Create a string representation of the request
    key_parts = [method.upper(), url]
    
    # Add sorted parameters
    if params:
        param_str = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        key_parts.append(param_str)
    
    # Add selected headers that affect the response (e.g., authorization)
    if headers:
        # Only include certain headers that affect caching
        cache_headers = ['authorization', 'api-key', 'x-api-key']
        header_parts = []
        for h in cache_headers:
            if h in headers:
                # Only store the fact that the header exists, not its value
                header_parts.append(f"{h}=present")
        if header_parts:
            key_parts.append("&".join(header_parts))
    
    # Join parts and create hash
    key_string = "|".join(key_parts)
    return hashlib.md5(key_string.encode('utf-8')).hexdigest()

def get_cache_path(cache_key, cache_dir=None, ext='json'):
    """
    Get the file path for a cache item
    
    Args:
        cache_key (str): The cache key
        cache_dir (str, optional): Directory to store cache files
        ext (str, optional): File extension. Defaults to 'json'.
        
    Returns:
        str: Path to cache file
    """
    if cache_dir is None:
        cache_dir = CACHE_DIR
    
    # Create the cache directory if it doesn't exist
    os.makedirs(cache_dir, exist_ok=True)
    
    # Use first few chars as directory to avoid too many files in one dir
    subdir = cache_key[:2]
    subdir_path = os.path.join(cache_dir, subdir)
    os.makedirs(subdir_path, exist_ok=True)
    
    return os.path.join(subdir_path, f"{cache_key}.{ext}")

def is_cache_valid(cache_path, expiry=None):
    """
    Check if a cache file is valid (exists and not expired)
    
    Args:
        cache_path (str): Path to cache file
        expiry (datetime.timedelta, optional): Cache expiry time
        
    Returns:
        bool: True if cache is valid, False otherwise
    """
    if not os.path.exists(cache_path):
        return False
    
    # If no expiry provided, cache is always valid
    if expiry is None:
        return True
    
    # Check file modification time
    mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(cache_path))
    now = datetime.datetime.now()
    
    return (now - mod_time) < expiry

def save_to_cache(data, cache_key, cache_dir=None, metadata=None):
    """
    Save data to cache
    
    Args:
        data: The data to cache
        cache_key (str): Cache key
        cache_dir (str, optional): Directory to store cache files
        metadata (dict, optional): Additional metadata to store with the cache
        
    Returns:
        str: Path to cache file
    """
    if not CACHE_ENABLED:
        return None
    
    # Determine file type based on data
    if isinstance(data, (dict, list)) and not metadata:
        ext = 'json'
    else:
        ext = 'pkl'
    
    cache_path = get_cache_path(cache_key, cache_dir, ext)
    
    try:
        if ext == 'json':
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        else:
            # Store as pickle with metadata
            cache_data = {
                'data': data,
                'metadata': metadata or {},
                'timestamp': datetime.datetime.now().isoformat()
            }
            with open(cache_path, 'wb') as f:
                pickle.dump(cache_data, f)
        
        logger.debug(f"Saved to cache: {cache_path}")
        return cache_path
    except Exception as e:
        logger.error(f"Error saving to cache: {e}")
        # Try to remove the file if it was created
        try:
            if os.path.exists(cache_path):
                os.remove(cache_path)
        except:
            pass
        return None

def load_from_cache(cache_key, cache_dir=None, expiry=None, data_type=None):
    """
    Load data from cache
    
    Args:
        cache_key (str): Cache key
        cache_dir (str, optional): Directory to load cache from
        expiry (datetime.timedelta, optional): Cache expiry time
        data_type (str, optional): Type of data (for determining expiry)
        
    Returns:
        tuple: (data, metadata) or (None, None) if cache is invalid
    """
    if not CACHE_ENABLED:
        return None, None
    
    # Determine expiry if not provided
    if expiry is None and data_type:
        expiry = get_cache_expiry(data_type)
    
    # Try both json and pickle extensions
    for ext in ['json', 'pkl']:
        cache_path = get_cache_path(cache_key, cache_dir, ext)
        
        if is_cache_valid(cache_path, expiry):
            try:
                if ext == 'json':
                    with open(cache_path, 'r', encoding='utf-8') as f:
                        return json.load(f), None
                else:
                    with open(cache_path, 'rb') as f:
                        cache_data = pickle.load(f)
                        return cache_data['data'], cache_data.get('metadata')
            except Exception as e:
                logger.error(f"Error loading from cache: {e}")
                # Remove invalid cache file
                try:
                    os.remove(cache_path)
                except:
                    pass
    
    return None, None

def cache_decorator(expiry=None, data_type=None, cache_dir=None):
    """
    Decorator to cache function results
    
    Args:
        expiry (datetime.timedelta, optional): Cache expiry time
        data_type (str, optional): Type of data (for determining expiry)
        cache_dir (str, optional): Directory to store cache files
        
    Returns:
        function: Decorated function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not CACHE_ENABLED:
                return func(*args, **kwargs)
            
            # Generate a cache key based on function name and arguments
            func_name = func.__name__
            arg_str = str(args) + str(sorted(kwargs.items()))
            cache_key = hashlib.md5(f"{func_name}|{arg_str}".encode('utf-8')).hexdigest()
            
            # Determine appropriate expiry
            _expiry = expiry
            if _expiry is None and data_type:
                _expiry = get_cache_expiry(data_type)
            
            # Try to load from cache
            data, _ = load_from_cache(cache_key, cache_dir, _expiry)
            if data is not None:
                return data
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            save_to_cache(result, cache_key, cache_dir)
            return result
        
        return wrapper
    
    return decorator

def clear_cache(cache_dir=None, age=None):
    """
    Clear expired cache files
    
    Args:
        cache_dir (str, optional): Directory to clear
        age (datetime.timedelta, optional): Age threshold to clear
        
    Returns:
        int: Number of files cleared
    """
    if cache_dir is None:
        cache_dir = CACHE_DIR
    
    if not os.path.exists(cache_dir):
        return 0
    
    count = 0
    now = datetime.datetime.now()
    
    for root, dirs, files in os.walk(cache_dir):
        for file in files:
            if file.endswith('.json') or file.endswith('.pkl'):
                file_path = os.path.join(root, file)
                
                # Check age if specified
                if age is not None:
                    mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                    if (now - mod_time) < age:
                        continue
                
                try:
                    os.remove(file_path)
                    count += 1
                except Exception as e:
                    logger.error(f"Error removing cache file {file_path}: {e}")
    
    return count

def get_cache_stats(cache_dir=None):
    """
    Get statistics about the cache
    
    Args:
        cache_dir (str, optional): Directory to analyze
        
    Returns:
        dict: Cache statistics
    """
    if cache_dir is None:
        cache_dir = CACHE_DIR
    
    if not os.path.exists(cache_dir):
        return {
            'total_files': 0,
            'total_size': 0,
            'oldest_file': None,
            'newest_file': None
        }
    
    total_files = 0
    total_size = 0
    oldest_time = None
    newest_time = None
    oldest_file = None
    newest_file = None
    
    for root, dirs, files in os.walk(cache_dir):
        for file in files:
            if file.endswith('.json') or file.endswith('.pkl'):
                file_path = os.path.join(root, file)
                total_files += 1
                size = os.path.getsize(file_path)
                total_size += size
                
                mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                if oldest_time is None or mod_time < oldest_time:
                    oldest_time = mod_time
                    oldest_file = file_path
                if newest_time is None or mod_time > newest_time:
                    newest_time = mod_time
                    newest_file = file_path
    
    return {
        'total_files': total_files,
        'total_size': total_size,
        'size_mb': round(total_size / (1024 * 1024), 2),
        'oldest_file': {
            'path': oldest_file,
            'time': oldest_time.isoformat() if oldest_time else None
        },
        'newest_file': {
            'path': newest_file,
            'time': newest_time.isoformat() if newest_time else None
        }
    }

if __name__ == "__main__":
    # Test cache functions
    test_cache_dir = os.path.join(CACHE_DIR, 'test')
    os.makedirs(test_cache_dir, exist_ok=True)
    
    test_data = {
        'timestamp': datetime.datetime.now().isoformat(),
        'sample': 'This is a test',
        'numbers': [1, 2, 3, 4, 5]
    }
    
    test_key = generate_cache_key('https://example.com/api', {'param1': 'value1'})
    print(f"Test cache key: {test_key}")
    
    save_to_cache(test_data, test_key, test_cache_dir)
    
    loaded_data, _ = load_from_cache(test_key, test_cache_dir)
    print(f"Loaded data matches: {loaded_data == test_data}")
    
    # Test cache decorator
    @cache_decorator(cache_dir=test_cache_dir)
    def slow_function(a, b):
        print("Running slow function...")
        time.sleep(1)
        return a + b
    
    print("First call (should be slow):")
    result1 = slow_function(5, 7)
    print(f"Result: {result1}")
    
    print("Second call (should be fast):")
    result2 = slow_function(5, 7)
    print(f"Result: {result2}")
    
    print("Call with different args (should be slow):")
    result3 = slow_function(10, 20)
    print(f"Result: {result3}")
    
    # Get cache stats
    stats = get_cache_stats(test_cache_dir)
    print(f"Cache stats: {json.dumps(stats, indent=2)}") 