#!/usr/bin/env python3
"""
HTTP client utility for data mining scripts with caching, rate limiting, and error handling
"""
import os
import sys
import time
import json
import random
import hashlib
import sqlite3
import requests
from urllib.parse import urlparse
from datetime import datetime, timedelta

# Add parent directory to path for relative imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.data_mining.utils.config import (
    HTTP_TIMEOUT, HTTP_HEADERS, RATE_LIMITS, CACHE_DIR, CACHE_EXPIRY, 
    PROXY_ENABLED, PROXY_URL, USER_AGENTS
)
from scripts.data_mining.utils.logger import get_logger

logger = get_logger('http_client')

class RateLimiter:
    """Rate limiter to control request frequency"""
    
    def __init__(self):
        self.last_request_time = {}
        
    def wait(self, domain, rate=None):
        """
        Wait if needed to respect rate limits
        
        Args:
            domain (str): Domain to rate limit
            rate (float, optional): Requests per second. If None, uses domain-specific or default rate.
        """
        now = time.time()
        domain_key = domain.lower()
        
        # Determine rate to use
        if rate is None:
            # Check for domain-specific rate
            for domain_pattern, domain_rate in RATE_LIMITS.items():
                if domain_pattern in domain_key:
                    rate = domain_rate
                    break
            else:
                # Use default rate
                rate = RATE_LIMITS.get('default', 1.0)
        
        # Calculate wait time
        if domain_key in self.last_request_time:
            elapsed = now - self.last_request_time[domain_key]
            min_interval = 1.0 / rate
            
            if elapsed < min_interval:
                wait_time = min_interval - elapsed
                logger.debug(f"Rate limiting: waiting {wait_time:.2f}s for {domain}")
                time.sleep(wait_time)
        
        # Update last request time
        self.last_request_time[domain_key] = time.time()

class CacheManager:
    """Manage HTTP response caching"""
    
    def __init__(self, cache_dir=None):
        """
        Initialize cache manager
        
        Args:
            cache_dir (str, optional): Directory to store cache. If None, uses default.
        """
        self.cache_dir = cache_dir or os.path.join(CACHE_DIR, 'http')
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Initialize SQLite cache database
        self.db_path = os.path.join(self.cache_dir, 'cache.db')
        self._init_db()
    
    def _init_db(self):
        """Initialize cache database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create cache table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cache (
                url_hash TEXT PRIMARY KEY,
                url TEXT,
                method TEXT,
                status_code INTEGER,
                headers TEXT,
                content BLOB,
                timestamp REAL,
                expiry REAL
            )
        ''')
        
        # Create index on timestamp for expiration cleanup
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_expiry ON cache (expiry)')
        
        conn.commit()
        conn.close()
    
    def _get_cache_key(self, url, method, params=None, data=None):
        """Generate a unique cache key for a request"""
        # Create a string with all request data
        key_parts = [url.lower(), method.upper()]
        
        if params:
            # Sort params to ensure consistent keys regardless of order
            key_parts.append(json.dumps(params, sort_keys=True))
        
        if data:
            if isinstance(data, dict):
                key_parts.append(json.dumps(data, sort_keys=True))
            else:
                key_parts.append(str(data))
        
        # Join parts and create hash
        key_string = '|'.join(key_parts)
        return hashlib.sha256(key_string.encode('utf-8')).hexdigest()
    
    def get(self, url, method='GET', params=None, data=None):
        """
        Get cached response if available and not expired
        
        Args:
            url (str): URL
            method (str): HTTP method
            params (dict, optional): URL parameters
            data (dict or str, optional): Request body
            
        Returns:
            tuple: (is_cached, response_dict) or (False, None) if not cached
        """
        cache_key = self._get_cache_key(url, method, params, data)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT status_code, headers, content, expiry FROM cache WHERE url_hash = ? AND expiry > ?',
                (cache_key, time.time())
            )
            result = cursor.fetchone()
            
            if result:
                status_code, headers_json, content, expiry = result
                headers = json.loads(headers_json)
                
                # Create a response-like dict
                cached_response = {
                    'status_code': status_code,
                    'headers': headers,
                    'content': content,
                    'from_cache': True,
                    'expiry': expiry
                }
                
                logger.debug(f"Cache hit for {url} (expires in {(expiry - time.time()) / 60:.1f} min)")
                return True, cached_response
            
            return False, None
            
        except Exception as e:
            logger.warning(f"Cache get error for {url}: {e}")
            return False, None
        finally:
            if 'conn' in locals():
                conn.close()
    
    def set(self, url, method, params, data, response, source_type='default'):
        """
        Cache a response
        
        Args:
            url (str): URL
            method (str): HTTP method
            params (dict, optional): URL parameters
            data (dict or str, optional): Request body
            response (requests.Response): Response to cache
            source_type (str): Source type for determining cache expiry
        """
        cache_key = self._get_cache_key(url, method, params, data)
        
        try:
            # Determine cache expiry
            domain = urlparse(url).netloc
            
            # Find most specific expiry time
            expiry_time = None
            for source, expiry in CACHE_EXPIRY.items():
                if source in domain or source in source_type:
                    expiry_time = expiry
                    break
            
            # Use default if no specific expiry found
            if expiry_time is None:
                expiry_time = CACHE_EXPIRY.get('default', 86400)
            
            # Calculate expiry timestamp
            expiry = time.time() + expiry_time
            
            # Save to cache
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                '''
                INSERT OR REPLACE INTO cache 
                (url_hash, url, method, status_code, headers, content, timestamp, expiry)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    cache_key,
                    url,
                    method,
                    response.status_code,
                    json.dumps(dict(response.headers)),
                    response.content,
                    time.time(),
                    expiry
                )
            )
            
            conn.commit()
            logger.debug(f"Cached response for {url} (expires in {expiry_time / 3600:.1f} hours)")
            
        except Exception as e:
            logger.warning(f"Cache set error for {url}: {e}")
        finally:
            if 'conn' in locals():
                conn.close()
    
    def clear_expired(self):
        """Remove expired cache entries"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Delete expired entries
            now = time.time()
            cursor.execute('DELETE FROM cache WHERE expiry < ?', (now,))
            deleted_count = cursor.rowcount
            
            conn.commit()
            if deleted_count > 0:
                logger.info(f"Cleared {deleted_count} expired cache entries")
            
        except Exception as e:
            logger.warning(f"Error clearing expired cache: {e}")
        finally:
            if 'conn' in locals():
                conn.close()
    
    def clear_all(self):
        """Clear all cache entries"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM cache')
            deleted_count = cursor.rowcount
            
            conn.commit()
            logger.info(f"Cleared all {deleted_count} cache entries")
            
        except Exception as e:
            logger.warning(f"Error clearing cache: {e}")
        finally:
            if 'conn' in locals():
                conn.close()

class HttpClient:
    """HTTP client with caching, rate limiting, and error handling"""
    
    def __init__(self, cache_enabled=True, rate_limit_enabled=True):
        """
        Initialize HTTP client
        
        Args:
            cache_enabled (bool): Whether to enable caching
            rate_limit_enabled (bool): Whether to enable rate limiting
        """
        self.cache = CacheManager() if cache_enabled else None
        self.rate_limiter = RateLimiter() if rate_limit_enabled else None
        self.session = requests.Session()
        self.default_headers = HTTP_HEADERS.copy()
        
        # Configure proxies if enabled
        if PROXY_ENABLED and PROXY_URL:
            self.session.proxies = {
                'http': PROXY_URL,
                'https': PROXY_URL
            }
    
    def _rotate_user_agent(self):
        """Rotate user agent to avoid detection"""
        if USER_AGENTS:
            self.default_headers['User-Agent'] = random.choice(USER_AGENTS)
    
    def request(self, method, url, params=None, data=None, json_data=None, headers=None, 
                timeout=None, verify=True, allow_redirects=True, stream=False,
                cache=True, rate_limit=True, source_type=None, retries=3):
        """
        Make an HTTP request with caching and rate limiting
        
        Args:
            method (str): HTTP method
            url (str): URL
            params (dict, optional): URL parameters
            data (dict or str, optional): Form data
            json_data (dict, optional): JSON data
            headers (dict, optional): HTTP headers (will be merged with default headers)
            timeout (int, optional): Request timeout in seconds
            verify (bool): Whether to verify SSL certificates
            allow_redirects (bool): Whether to follow redirects
            stream (bool): Whether to stream the response
            cache (bool): Whether to use cache for this request
            rate_limit (bool): Whether to apply rate limiting for this request
            source_type (str, optional): Source type for cache expiry
            retries (int): Number of retries on failure
            
        Returns:
            requests.Response: Response object
        """
        # Rotate user agent
        self._rotate_user_agent()
        
        # Merge headers
        request_headers = self.default_headers.copy()
        if headers:
            request_headers.update(headers)
        
        # Use default timeout if not specified
        if timeout is None:
            timeout = HTTP_TIMEOUT
        
        # Parse domain for rate limiting
        domain = urlparse(url).netloc
        
        # Check cache if enabled
        if cache and self.cache:
            is_cached, cached_response = self.cache.get(url, method, params, data)
            if is_cached:
                # Create a Response-like object from cached data
                response = requests.Response()
                response.status_code = cached_response['status_code']
                response.headers = cached_response['headers']
                response._content = cached_response['content']
                response.url = url
                response.request = requests.Request(
                    method=method, url=url, headers=request_headers, 
                    params=params, data=data
                ).prepare()
                
                # Add cache metadata
                response.from_cache = True
                response.cache_expiry = cached_response['expiry']
                
                return response
        
        # Apply rate limiting if enabled
        if rate_limit and self.rate_limiter:
            self.rate_limiter.wait(domain)
        
        # Make the request with retries
        for attempt in range(retries):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    data=data,
                    json=json_data,
                    headers=request_headers,
                    timeout=timeout,
                    verify=verify,
                    allow_redirects=allow_redirects,
                    stream=stream
                )
                
                # Add metadata
                response.from_cache = False
                
                # Cache successful responses
                if cache and self.cache and response.status_code < 400:
                    self.cache.set(url, method, params, data, response, source_type)
                
                return response
                
            except (requests.RequestException, requests.ConnectionError, 
                    requests.Timeout, requests.TooManyRedirects) as e:
                
                wait_time = 2 ** attempt  # Exponential backoff
                
                if attempt < retries - 1:
                    logger.warning(
                        f"Request failed ({e.__class__.__name__}): {url}, "
                        f"retrying in {wait_time} seconds (attempt {attempt+1}/{retries})"
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"Request failed after {retries} attempts: {url} - {str(e)}")
                    raise
    
    def get(self, url, **kwargs):
        """
        Make a GET request
        
        Args:
            url (str): URL
            **kwargs: Additional arguments for request()
            
        Returns:
            requests.Response: Response object
        """
        return self.request('GET', url, **kwargs)
    
    def post(self, url, **kwargs):
        """
        Make a POST request
        
        Args:
            url (str): URL
            **kwargs: Additional arguments for request()
            
        Returns:
            requests.Response: Response object
        """
        return self.request('POST', url, **kwargs)
    
    def put(self, url, **kwargs):
        """
        Make a PUT request
        
        Args:
            url (str): URL
            **kwargs: Additional arguments for request()
            
        Returns:
            requests.Response: Response object
        """
        return self.request('PUT', url, **kwargs)
    
    def delete(self, url, **kwargs):
        """
        Make a DELETE request
        
        Args:
            url (str): URL
            **kwargs: Additional arguments for request()
            
        Returns:
            requests.Response: Response object
        """
        return self.request('DELETE', url, **kwargs)
    
    def head(self, url, **kwargs):
        """
        Make a HEAD request
        
        Args:
            url (str): URL
            **kwargs: Additional arguments for request()
            
        Returns:
            requests.Response: Response object
        """
        return self.request('HEAD', url, **kwargs)
    
    def options(self, url, **kwargs):
        """
        Make an OPTIONS request
        
        Args:
            url (str): URL
            **kwargs: Additional arguments for request()
            
        Returns:
            requests.Response: Response object
        """
        return self.request('OPTIONS', url, **kwargs)
    
    def clear_cache(self):
        """Clear all cache entries"""
        if self.cache:
            self.cache.clear_all()
    
    def clear_expired_cache(self):
        """Clear expired cache entries"""
        if self.cache:
            self.cache.clear_expired()

# Create a singleton instance
http_client = HttpClient()

if __name__ == "__main__":
    # Test the HTTP client
    client = HttpClient()
    
    # Test a GET request
    response = client.get('https://httpbin.org/get', params={'test': 'value'})
    print(f"Status: {response.status_code}")
    print(f"From cache: {getattr(response, 'from_cache', False)}")
    print(f"Response: {response.text[:100]}...")
    
    # Test cache
    response = client.get('https://httpbin.org/get', params={'test': 'value'})
    print(f"\nSecond request:")
    print(f"Status: {response.status_code}")
    print(f"From cache: {getattr(response, 'from_cache', False)}")
    
    # Test POST request
    response = client.post('https://httpbin.org/post', data={'test': 'value'})
    print(f"\nPOST request:")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:100]}...") 