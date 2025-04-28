#!/usr/bin/env python3
"""
HTTP utility for making API requests with caching support.
Provides functions to make HTTP requests and cache responses.
"""
import os
import sys
import json
import time
import requests
from requests.exceptions import RequestException
from urllib.parse import urljoin

# Add parent directory to path for relative imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from data_mining.utils.logger import get_logger
from data_mining.utils.cache import (
    generate_cache_key, load_from_cache, save_to_cache, is_cache_valid
)
from data_mining.utils.config import CACHE_ENABLED

# Initialize logger
logger = get_logger('http')

# Default headers for all requests
DEFAULT_HEADERS = {
    'User-Agent': 'MAGA-Ops/1.0 Data Mining Tool',
    'Accept': 'application/json'
}

# Request timeout
DEFAULT_TIMEOUT = 30  # seconds

# Retry settings
DEFAULT_RETRIES = 3
DEFAULT_RETRY_DELAY = 2  # seconds
DEFAULT_RETRY_BACKOFF = 2  # exponential backoff factor

def get_session():
    """
    Get a requests session with default settings
    
    Returns:
        requests.Session: Configured session
    """
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    return session

def make_request(url, method='GET', params=None, data=None, headers=None, 
                 auth=None, timeout=DEFAULT_TIMEOUT, retries=DEFAULT_RETRIES,
                 retry_delay=DEFAULT_RETRY_DELAY, retry_backoff=DEFAULT_RETRY_BACKOFF,
                 cache=True, cache_expiry=None, data_type=None, cache_dir=None,
                 stream=False, verify=True, allow_redirects=True):
    """
    Make an HTTP request with caching and retry logic
    
    Args:
        url (str): URL to request
        method (str, optional): HTTP method. Defaults to 'GET'.
        params (dict, optional): Query parameters.
        data (dict, optional): Request body.
        headers (dict, optional): HTTP headers.
        auth (tuple, optional): Authentication credentials.
        timeout (int, optional): Request timeout in seconds.
        retries (int, optional): Number of retries on failure.
        retry_delay (int, optional): Initial delay between retries in seconds.
        retry_backoff (int, optional): Backoff factor.
        cache (bool, optional): Whether to use cache. Defaults to True.
        cache_expiry (datetime.timedelta, optional): Cache expiry time.
        data_type (str, optional): Type of data (for determining cache expiry).
        cache_dir (str, optional): Directory to store cache files.
        stream (bool, optional): Whether to stream the response.
        verify (bool, optional): Whether to verify SSL certificates.
        allow_redirects (bool, optional): Whether to follow redirects.
        
    Returns:
        dict: Response object with the following fields:
            - success (bool): Whether the request was successful
            - status_code (int): HTTP status code
            - headers (dict): Response headers
            - data: Response data (parsed JSON or text)
            - error (str): Error message if request failed
            - cached (bool): Whether the response was from cache
            - url (str): Final URL after redirects
    """
    # Merge headers with defaults
    _headers = DEFAULT_HEADERS.copy()
    if headers:
        _headers.update(headers)
    
    # Prepare response object
    response_obj = {
        'success': False,
        'status_code': None,
        'headers': None,
        'data': None,
        'error': None,
        'cached': False,
        'url': url
    }
    
    # Check cache if enabled and method is GET
    if CACHE_ENABLED and cache and method.upper() == 'GET':
        cache_key = generate_cache_key(url, params, _headers, method)
        cached_data, cached_metadata = load_from_cache(cache_key, cache_dir, cache_expiry, data_type)
        
        if cached_data is not None:
            logger.debug(f"Cache hit for {url}")
            
            # Extract data and metadata from cache
            if isinstance(cached_data, dict) and 'status_code' in cached_data and 'data' in cached_data:
                # This is a cached response object
                response_obj.update(cached_data)
            else:
                # This is just the data
                response_obj['data'] = cached_data
                response_obj['success'] = True
                
                # Try to get additional metadata
                if cached_metadata:
                    if 'status_code' in cached_metadata:
                        response_obj['status_code'] = cached_metadata['status_code']
                    if 'headers' in cached_metadata:
                        response_obj['headers'] = cached_metadata['headers']
            
            response_obj['cached'] = True
            return response_obj
    
    # Make the request with retries
    session = get_session()
    retry_count = 0
    delay = retry_delay
    
    while retry_count <= retries:
        try:
            logger.debug(f"Making {method} request to {url}" + 
                        (f" (retry {retry_count}/{retries})" if retry_count > 0 else ""))
            
            # Make the request
            http_response = session.request(
                method=method,
                url=url,
                params=params,
                json=data if method.upper() in ['POST', 'PUT', 'PATCH'] and data else None,
                data=data if method.upper() in ['POST', 'PUT', 'PATCH'] and isinstance(data, str) else None,
                headers=_headers,
                auth=auth,
                timeout=timeout,
                stream=stream,
                verify=verify,
                allow_redirects=allow_redirects
            )
            
            # Update response object
            response_obj['status_code'] = http_response.status_code
            response_obj['headers'] = dict(http_response.headers)
            response_obj['url'] = http_response.url
            
            # Check if successful
            http_response.raise_for_status()
            
            # Parse response data
            content_type = http_response.headers.get('Content-Type', '')
            if 'application/json' in content_type:
                try:
                    response_obj['data'] = http_response.json()
                except json.JSONDecodeError:
                    response_obj['data'] = http_response.text
            else:
                response_obj['data'] = http_response.text
            
            response_obj['success'] = True
            
            # Cache successful GET responses
            if CACHE_ENABLED and cache and method.upper() == 'GET':
                cache_key = generate_cache_key(url, params, _headers, method)
                
                metadata = {
                    'status_code': http_response.status_code,
                    'headers': dict(http_response.headers),
                    'url': http_response.url,
                    'timestamp': time.time()
                }
                
                save_to_cache(response_obj['data'], cache_key, cache_dir, metadata)
            
            # Return successful response
            return response_obj
            
        except RequestException as e:
            # Update response object with error
            response_obj['error'] = str(e)
            
            # Handle the error based on type
            if hasattr(e, 'response') and e.response is not None:
                response_obj['status_code'] = e.response.status_code
                response_obj['headers'] = dict(e.response.headers)
                
                # Try to parse error response
                try:
                    response_obj['data'] = e.response.json()
                except:
                    try:
                        response_obj['data'] = e.response.text
                    except:
                        pass
            
            # Check if should retry
            retry_count += 1
            if retry_count <= retries:
                # Log retry
                logger.warning(f"Request failed: {e}. Retrying in {delay} seconds...")
                
                # Wait before retrying
                time.sleep(delay)
                
                # Increase delay with backoff
                delay *= retry_backoff
            else:
                # Log final failure
                logger.error(f"Request failed after {retries} retries: {e}")
                return response_obj
        
        except Exception as e:
            # Handle unexpected errors
            response_obj['error'] = f"Unexpected error: {str(e)}"
            logger.error(f"Unexpected error during request: {e}")
            return response_obj
    
    # Should never reach here, but just in case
    return response_obj

def get(url, **kwargs):
    """
    Make a GET request
    
    Args:
        url (str): URL to request
        **kwargs: Additional arguments to pass to make_request
        
    Returns:
        dict: Response object
    """
    return make_request(url, method='GET', **kwargs)

def post(url, data=None, **kwargs):
    """
    Make a POST request
    
    Args:
        url (str): URL to request
        data (dict, optional): Request body
        **kwargs: Additional arguments to pass to make_request
        
    Returns:
        dict: Response object
    """
    return make_request(url, method='POST', data=data, **kwargs)

def put(url, data=None, **kwargs):
    """
    Make a PUT request
    
    Args:
        url (str): URL to request
        data (dict, optional): Request body
        **kwargs: Additional arguments to pass to make_request
        
    Returns:
        dict: Response object
    """
    return make_request(url, method='PUT', data=data, **kwargs)

def delete(url, **kwargs):
    """
    Make a DELETE request
    
    Args:
        url (str): URL to request
        **kwargs: Additional arguments to pass to make_request
        
    Returns:
        dict: Response object
    """
    return make_request(url, method='DELETE', **kwargs)

def build_url(base_url, path=''):
    """
    Build a URL from base URL and path
    
    Args:
        base_url (str): Base URL
        path (str, optional): Path to append
        
    Returns:
        str: Complete URL
    """
    return urljoin(base_url, path)

def handle_pagination(url, params=None, headers=None, auth=None, 
                      page_param='page', limit_param='limit', limit=100,
                      data_key=None, total_key=None, **kwargs):
    """
    Handle paginated requests
    
    Args:
        url (str): URL to request
        params (dict, optional): Query parameters
        headers (dict, optional): HTTP headers
        auth (tuple, optional): Authentication credentials
        page_param (str, optional): Name of pagination parameter
        limit_param (str, optional): Name of limit parameter
        limit (int, optional): Number of items per page
        data_key (str, optional): Key in response that contains data
        total_key (str, optional): Key in response that contains total count
        **kwargs: Additional arguments to pass to make_request
        
    Returns:
        dict: Response object with all data
    """
    # Initialize parameters
    _params = params.copy() if params else {}
    _params[limit_param] = limit
    page = 1
    all_data = []
    has_more = True
    total_count = None
    
    # Set cache to False for pagination sub-requests
    kwargs['cache'] = False
    
    # Generate a cache key for the entire paginated request
    if CACHE_ENABLED and kwargs.get('cache', True):
        cache_key = generate_cache_key(url, _params, headers, 'GET') + '_paginated'
        cache_dir = kwargs.get('cache_dir')
        cache_expiry = kwargs.get('cache_expiry')
        data_type = kwargs.get('data_type')
        
        # Try to load from cache
        cached_data, _ = load_from_cache(cache_key, cache_dir, cache_expiry, data_type)
        if cached_data is not None:
            logger.debug(f"Cache hit for paginated request to {url}")
            
            # Create response object
            response_obj = {
                'success': True,
                'status_code': 200,
                'data': cached_data,
                'cached': True,
                'url': url,
                'paginated': True,
                'total_items': len(cached_data)
            }
            
            return response_obj
    
    while has_more:
        # Update page parameter
        _params[page_param] = page
        
        # Make request
        logger.debug(f"Fetching page {page} from {url}")
        response = make_request(url, params=_params, headers=headers, auth=auth, **kwargs)
        
        # Check for failure
        if not response['success']:
            if page == 1:
                return response
            else:
                # We got some data, so return what we have
                break
        
        # Extract data
        if data_key and isinstance(response['data'], dict):
            page_data = response['data'].get(data_key, [])
            
            # Get total count for logs
            if total_key and total_count is None:
                total_count = response['data'].get(total_key)
        else:
            page_data = response['data']
        
        # If data is a list, extend all_data
        if isinstance(page_data, list):
            all_data.extend(page_data)
        else:
            logger.warning(f"Expected list data but got {type(page_data)}")
            all_data.append(page_data)
        
        # Log progress
        if total_count:
            logger.debug(f"Fetched {len(all_data)}/{total_count} items ({page} pages)")
        else:
            logger.debug(f"Fetched page {page} with {len(page_data)} items")
        
        # Check if there are more pages
        # This logic varies by API, adjust as needed
        if isinstance(page_data, list) and len(page_data) < limit:
            has_more = False
        else:
            page += 1
            
            # Add safety limit
            if page > 100:
                logger.warning("Reached maximum page limit (100)")
                break
    
    # Create response object with all data
    response_obj = {
        'success': True,
        'status_code': 200,
        'data': all_data,
        'cached': False,
        'url': url,
        'paginated': True,
        'total_items': len(all_data)
    }
    
    # Cache the complete result
    if CACHE_ENABLED and kwargs.get('cache', True):
        save_to_cache(all_data, cache_key, kwargs.get('cache_dir'))
    
    return response_obj

if __name__ == "__main__":
    # Test HTTP functions
    test_url = "https://jsonplaceholder.typicode.com/posts"
    
    # Basic GET request
    print("Making GET request...")
    response = get(test_url)
    print(f"Success: {response['success']}")
    print(f"Status: {response['status_code']}")
    print(f"Cached: {response['cached']}")
    print(f"Data count: {len(response['data'])}")
    
    # Make another request to test caching
    print("\nMaking second GET request (should be cached)...")
    response2 = get(test_url)
    print(f"Success: {response2['success']}")
    print(f"Status: {response2['status_code']}")
    print(f"Cached: {response2['cached']}")
    
    # Test POST request
    print("\nMaking POST request...")
    post_data = {"title": "Test Post", "body": "This is a test", "userId": 1}
    post_response = post(test_url, data=post_data)
    print(f"Success: {post_response['success']}")
    print(f"Status: {post_response['status_code']}")
    print(f"Data: {post_response['data']}")
    
    # Test pagination
    print("\nTesting pagination...")
    paginated = handle_pagination(
        test_url, 
        params={}, 
        limit=10,
        limit_param="_limit",
        page_param="_page"
    )
    print(f"Success: {paginated['success']}")
    print(f"Total items: {paginated['total_items']}")
    print(f"Cached: {paginated['cached']}")
    
    # Make the same paginated request again
    print("\nMaking second paginated request (should be cached)...")
    paginated2 = handle_pagination(
        test_url, 
        params={}, 
        limit=10,
        limit_param="_limit",
        page_param="_page"
    )
    print(f"Success: {paginated2['success']}")
    print(f"Total items: {paginated2['total_items']}")
    print(f"Cached: {paginated2['cached']}") 