#!/usr/bin/env python3
"""
Base Scraper Module

Provides a foundation for all scrapers with common functionality:
- Rate limiting
- Error handling and retries
- Caching
- Logging
- Screenshot capture
- Trust scoring
- User agent management
"""
import os
import sys
import json
import time
import random
import hashlib
import requests
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse
import sqlite3

# Add parent directory to path for relative imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import get_logger
from utils.config import (
    CACHE_ROOT, 
    SCRAPE_RATE_LIMIT, 
    CRAWLER_USER_AGENT,
    RAW_DATA_STORAGE
)
from utils.source_trust import calculate_trust_score, is_trusted_source

class BaseScraper:
    """Base class for all scrapers providing common functionality."""
    
    def __init__(self, source_name, cache_dir=None, rate_limit=None, user_agent=None):
        """
        Initialize the base scraper.
        
        Args:
            source_name: Name of the data source
            cache_dir: Directory to store cached data (default: CACHE_ROOT/source_name)
            rate_limit: Rate limit in seconds between requests (default: from config)
            user_agent: User agent for HTTP requests (default: from config)
        """
        self.source_name = source_name
        self.logger = get_logger(f"scraper.{source_name}")
        
        # Set up caching
        self.cache_dir = cache_dir or os.path.join(CACHE_ROOT, source_name)
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Set up request parameters
        self.rate_limit = rate_limit or SCRAPE_RATE_LIMIT
        self.user_agent = user_agent or CRAWLER_USER_AGENT
        self.session = self._init_session()
        self.last_request_time = 0
        
        # Stats
        self.stats = {
            'requests': 0,
            'cache_hits': 0,
            'retries': 0,
            'errors': 0,
            'start_time': datetime.now(),
        }
        
        self.logger.info(f"Initialized {source_name} scraper")
    
    def _init_session(self):
        """Initialize a requests session with appropriate headers."""
        session = requests.Session()
        session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',  # Do Not Track
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        return session
    
    def _rate_limit(self):
        """Apply rate limiting between requests."""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        if elapsed < self.rate_limit:
            sleep_time = self.rate_limit - elapsed
            
            # Add small jitter (±10%) to avoid detection
            jitter = sleep_time * 0.1 * random.choice([-1, 1])
            sleep_time += jitter
            
            # Ensure non-negative
            sleep_time = max(0, sleep_time)
            
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _get_cache_path(self, url, params=None):
        """
        Generate a cache path for a URL.
        
        Args:
            url: The URL to cache
            params: Optional dict of query parameters
            
        Returns:
            Path to the cache file
        """
        # Create a hash of the URL and params
        cache_key = url
        if params:
            cache_key += str(sorted(params.items()))
        
        hash_key = hashlib.md5(cache_key.encode()).hexdigest()
        
        # Get domain for organization
        domain = urlparse(url).netloc
        domain = domain.replace('.', '_')
        
        # Create cache path
        return os.path.join(self.cache_dir, f"{domain}_{hash_key}.json")
    
    def _load_from_cache(self, url, params=None, max_age_days=7):
        """
        Load data from cache if available and not expired.
        
        Args:
            url: The URL to load from cache
            params: Optional dict of query parameters
            max_age_days: Maximum age of cache in days
            
        Returns:
            Cached data if available and valid, None otherwise
        """
        cache_path = self._get_cache_path(url, params)
        
        if not os.path.exists(cache_path):
            return None
        
        # Check cache age
        file_time = os.path.getmtime(cache_path)
        file_age = datetime.now() - datetime.fromtimestamp(file_time)
        
        if file_age > timedelta(days=max_age_days):
            self.logger.debug(f"Cache expired for {url}")
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.stats['cache_hits'] += 1
                return data
        except Exception as e:
            self.logger.warning(f"Failed to load from cache: {str(e)}")
            return None
    
    def _save_to_cache(self, url, data, params=None):
        """
        Save data to cache.
        
        Args:
            url: The URL that was requested
            data: The data to cache
            params: Optional dict of query parameters
        """
        cache_path = self._get_cache_path(url, params)
        
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.warning(f"Failed to save to cache: {str(e)}")
    
    def _save_raw_data(self, url, data, data_type='html'):
        """
        Save raw data to the raw data storage.
        
        Args:
            url: The URL that was requested
            data: The raw data to save
            data_type: The type of data (html, json, etc.)
        """
        if not os.path.exists(RAW_DATA_STORAGE):
            os.makedirs(RAW_DATA_STORAGE, exist_ok=True)
        
        # Create a hash of the URL for the filename
        url_hash = hashlib.md5(url.encode()).hexdigest()
        
        # Get domain and timestamp for organization
        domain = urlparse(url).netloc
        domain = domain.replace('.', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create filename
        filename = f"{domain}_{timestamp}_{url_hash}.{data_type}"
        path = os.path.join(RAW_DATA_STORAGE, filename)
        
        try:
            with open(path, 'w', encoding='utf-8') as f:
                if data_type == 'json':
                    json.dump(data, f, indent=2)
                else:
                    f.write(data)
            
            self.logger.debug(f"Saved raw data to {path}")
            return path
        except Exception as e:
            self.logger.warning(f"Failed to save raw data: {str(e)}")
            return None
    
    def capture_screenshot(self, url, force=False):
        """
        Capture a screenshot of a webpage.
        
        Args:
            url: The URL to capture
            force: Whether to capture even if a screenshot already exists
            
        Returns:
            Path to the screenshot if successful, None otherwise
        """
        screenshots_dir = os.path.join(CACHE_ROOT, 'screenshots')
        os.makedirs(screenshots_dir, exist_ok=True)
        
        # Generate screenshot filename
        url_hash = hashlib.md5(url.encode()).hexdigest()
        domain = urlparse(url).netloc.replace('.', '_')
        screenshot_path = os.path.join(screenshots_dir, f"{domain}_{url_hash}.png")
        
        # Check if screenshot already exists
        if os.path.exists(screenshot_path) and not force:
            self.logger.debug(f"Screenshot already exists for {url}")
            return screenshot_path
        
        try:
            # Try using Playwright if available
            from playwright.sync_api import sync_playwright
            
            self.logger.info(f"Capturing screenshot for {url}")
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, wait_until='networkidle')
                page.screenshot(path=screenshot_path)
                browser.close()
            
            self.logger.info(f"Screenshot saved to {screenshot_path}")
            return screenshot_path
            
        except ImportError:
            self.logger.warning("Playwright not installed. Install with: pip install playwright")
            
            try:
                # Try using Selenium as fallback
                from selenium import webdriver
                from selenium.webdriver.chrome.options import Options
                
                chrome_options = Options()
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument(f"user-agent={self.user_agent}")
                
                driver = webdriver.Chrome(options=chrome_options)
                driver.get(url)
                time.sleep(5)  # Wait for page to load
                driver.save_screenshot(screenshot_path)
                driver.quit()
                
                self.logger.info(f"Screenshot saved to {screenshot_path} (using Selenium)")
                return screenshot_path
                
            except ImportError:
                self.logger.warning("Selenium not installed. Install with: pip install selenium")
                return None
            except Exception as e:
                self.logger.error(f"Failed to capture screenshot with Selenium: {str(e)}")
                return None
        
        except Exception as e:
            self.logger.error(f"Failed to capture screenshot: {str(e)}")
            return None
    
    def get(self, url, params=None, headers=None, use_cache=True, max_age_days=7, max_retries=3, save_raw=True):
        """
        Make a GET request with caching, rate limiting, and retries.
        
        Args:
            url: The URL to request
            params: Optional dict of query parameters
            headers: Optional dict of headers to add to the request
            use_cache: Whether to use cache
            max_age_days: Maximum age of cache in days
            max_retries: Maximum number of retries on failure
            save_raw: Whether to save the raw response
            
        Returns:
            Response object or data dict if cached
        """
        # Check if URL is from a trusted source
        trust_score = calculate_trust_score(url)
        trusted = is_trusted_source(url)
        self.logger.info(f"Request URL: {url} (Trust score: {trust_score}, Trusted: {trusted})")
        
        # Check cache if enabled
        if use_cache:
            cached_data = self._load_from_cache(url, params, max_age_days)
            if cached_data:
                self.logger.debug(f"Using cached data for {url}")
                return cached_data
        
        # Apply rate limiting
        self._rate_limit()
        
        # Add custom headers
        request_headers = {}
        if headers:
            request_headers.update(headers)
        
        # Make the request with retries
        retries = 0
        while retries <= max_retries:
            try:
                self.stats['requests'] += 1
                
                response = self.session.get(url, params=params, headers=request_headers, timeout=30)
                
                # Log response status
                self.logger.debug(f"Response status: {response.status_code} for {url}")
                
                # Check for successful response
                response.raise_for_status()
                
                # Save raw data if enabled
                if save_raw:
                    content_type = response.headers.get('Content-Type', '')
                    data_type = 'json' if 'application/json' in content_type else 'html'
                    self._save_raw_data(url, response.text, data_type)
                
                # Try to parse as JSON if content type is application/json
                if 'application/json' in response.headers.get('Content-Type', ''):
                    data = response.json()
                    
                    # Cache the response if enabled
                    if use_cache:
                        self._save_to_cache(url, data, params)
                    
                    return data
                
                # Otherwise return the response object
                return response
            
            except requests.RequestException as e:
                retries += 1
                self.stats['retries'] += 1
                
                if retries > max_retries:
                    self.logger.error(f"Failed to get {url} after {max_retries} retries: {str(e)}")
                    self.stats['errors'] += 1
                    raise
                
                # Exponential backoff
                sleep_time = 2 ** retries
                self.logger.warning(f"Request failed, retrying in {sleep_time}s: {str(e)}")
                time.sleep(sleep_time)
    
    def post(self, url, data=None, json=None, headers=None, max_retries=3):
        """
        Make a POST request with rate limiting and retries.
        
        Args:
            url: The URL to request
            data: Form data to send
            json: JSON data to send
            headers: Optional dict of headers to add to the request
            max_retries: Maximum number of retries on failure
            
        Returns:
            Response object
        """
        # Apply rate limiting
        self._rate_limit()
        
        # Add custom headers
        request_headers = {}
        if headers:
            request_headers.update(headers)
        
        # Make the request with retries
        retries = 0
        while retries <= max_retries:
            try:
                self.stats['requests'] += 1
                
                response = self.session.post(
                    url, 
                    data=data, 
                    json=json, 
                    headers=request_headers, 
                    timeout=30
                )
                
                # Log response status
                self.logger.debug(f"Response status: {response.status_code} for {url}")
                
                # Check for successful response
                response.raise_for_status()
                
                # Try to parse as JSON if content type is application/json
                if 'application/json' in response.headers.get('Content-Type', ''):
                    return response.json()
                
                # Otherwise return the response object
                return response
            
            except requests.RequestException as e:
                retries += 1
                self.stats['retries'] += 1
                
                if retries > max_retries:
                    self.logger.error(f"Failed to post to {url} after {max_retries} retries: {str(e)}")
                    self.stats['errors'] += 1
                    raise
                
                # Exponential backoff
                sleep_time = 2 ** retries
                self.logger.warning(f"Request failed, retrying in {sleep_time}s: {str(e)}")
                time.sleep(sleep_time)
    
    def print_stats(self):
        """Print statistics about the scraper's operation."""
        duration = datetime.now() - self.stats['start_time']
        duration_seconds = duration.total_seconds()
        
        print(f"\n=== {self.source_name} Scraper Statistics ===")
        print(f"Duration: {duration}")
        print(f"Requests: {self.stats['requests']}")
        print(f"Cache hits: {self.stats['cache_hits']}")
        print(f"Retries: {self.stats['retries']}")
        print(f"Errors: {self.stats['errors']}")
        
        if duration_seconds > 0 and self.stats['requests'] > 0:
            req_per_second = self.stats['requests'] / duration_seconds
            print(f"Requests per second: {req_per_second:.2f}")
        
        return self.stats
    
    def close(self):
        """Clean up resources."""
        if self.session:
            self.session.close()
        
        self.logger.info(f"Closed {self.source_name} scraper")
        self.print_stats()

if __name__ == "__main__":
    # Test the base scraper
    scraper = BaseScraper("test")
    
    try:
        # Test GitHub API (JSON response)
        response = scraper.get("https://api.github.com/users/octocat")
        print(f"GitHub API response type: {type(response)}")
        if isinstance(response, dict):
            print(f"Username: {response.get('login')}")
        
        # Test HTML page
        response = scraper.get("https://example.com")
        print(f"Example.com response type: {type(response)}")
        if hasattr(response, 'text'):
            print(f"Example.com content length: {len(response.text)}")
        
        # Print scraper stats
        scraper.print_stats()
    
    finally:
        scraper.close() 