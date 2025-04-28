#!/usr/bin/env python3
"""
FEC Contributions Data Mining Script.

This script downloads and processes contribution data from the FEC API.
It focuses on Schedule A (individual contributions) filtered by committee ID.
"""
import os
import sys
import json
import time
import datetime
import argparse
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

# Add project root to path for relative imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import utilities
from scripts.utils.config import get, get_config
from scripts.utils.logger import get_logger

# Initialize logger
logger = get_logger("data_mining.fec_contributions")

class FECContributionDownloader:
    """FEC API client for downloading contribution data."""
    
    def __init__(self, api_key: Optional[str] = None, cache_dir: Optional[str] = None):
        """
        Initialize FEC API client.
        
        Args:
            api_key (str, optional): FEC API key
            cache_dir (str, optional): Directory for caching results
        """
        # Get API key from config if not provided
        self.api_key = api_key or get("sources.fec.api_key")
        if not self.api_key:
            raise ValueError("FEC API key is required. Set it in config or provide it as an argument.")
        
        # Get base URL from config
        self.base_url = get("sources.fec.base_url", "https://api.open.fec.gov/v1")
        
        # Get cache directory from config if not provided
        self.cache_dir = cache_dir or get("general.cache_dir", "cache")
        self.cache_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), self.cache_dir, "fec")
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Set rate limit (requests per minute)
        self.rate_limit = get("sources.fec.rate_limit", 120)
        self.request_delay = 60 / self.rate_limit if self.rate_limit > 0 else 0
        
        # Set cache TTL
        self.cache_ttl = get("sources.fec.cache_ttl", 86400)  # 24 hours in seconds
        
        logger.info(f"Initialized FEC API client with base URL: {self.base_url}")
    
    def get_schedule_a(self, committee_id: str, **params) -> List[Dict[str, Any]]:
        """
        Get Schedule A (individual contributions) for a committee.
        
        Args:
            committee_id (str): Committee ID
            **params: Additional query parameters
            
        Returns:
            list: List of contributions
        """
        # Construct endpoint
        endpoint = f"{get('sources.fec.endpoints.schedules.schedule_a', '/schedules/schedule_a')}"
        
        # Set default parameters
        default_params = {
            "committee_id": committee_id,
            "sort": "-contribution_receipt_date",
            "sort_hide_null": True,
            "per_page": 100,
        }
        
        # Merge default parameters with provided parameters
        params = {**default_params, **params}
        
        # Get all pages
        return self._get_all_pages(endpoint, params)
    
    def get_committee(self, committee_id: str) -> Dict[str, Any]:
        """
        Get committee details.
        
        Args:
            committee_id (str): Committee ID
            
        Returns:
            dict: Committee details
        """
        # Construct endpoint
        endpoint = f"{get('sources.fec.endpoints.committees', '/committees')}/{committee_id}"
        
        # Get committee details
        return self._make_request(endpoint)
    
    def get_candidate(self, candidate_id: str) -> Dict[str, Any]:
        """
        Get candidate details.
        
        Args:
            candidate_id (str): Candidate ID
            
        Returns:
            dict: Candidate details
        """
        # Construct endpoint
        endpoint = f"{get('sources.fec.endpoints.candidates', '/candidates')}/{candidate_id}"
        
        # Get candidate details
        return self._make_request(endpoint)
    
    def _get_all_pages(self, endpoint: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get all pages for an endpoint.
        
        Args:
            endpoint (str): API endpoint
            params (dict): Query parameters
            
        Returns:
            list: All results from all pages
        """
        results = []
        page = 1
        has_more = True
        
        while has_more:
            # Update page number
            params["page"] = page
            
            # Make request
            response = self._make_request(endpoint, params)
            
            # Add results
            if "results" in response:
                results.extend(response["results"])
            
            # Check if there are more pages
            if "pagination" in response:
                has_more = response["pagination"].get("hasMore", False)
                page += 1
            else:
                has_more = False
            
            # Log progress
            logger.info(f"Downloaded page {page - 1} with {len(response.get('results', []))} results")
            
            # Respect rate limit
            if has_more and self.request_delay > 0:
                time.sleep(self.request_delay)
        
        return results
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Make a request to the FEC API.
        
        Args:
            endpoint (str): API endpoint
            params (dict, optional): Query parameters
            
        Returns:
            dict: API response
        """
        # Initialize parameters
        params = params or {}
        
        # Add API key
        params["api_key"] = self.api_key
        
        # Construct URL
        url = f"{self.base_url}{endpoint}"
        
        # Check cache
        cache_file = self._get_cache_file(endpoint, params)
        if self._is_cache_valid(cache_file):
            logger.debug(f"Using cached response for {url}")
            return self._load_from_cache(cache_file)
        
        # Make request
        logger.debug(f"Making request to {url}")
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            
            # Cache response
            self._save_to_cache(cache_file, data)
            
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request to {url}: {e}")
            
            # Try to use cache even if expired
            if os.path.exists(cache_file):
                logger.warning(f"Using expired cache for {url}")
                return self._load_from_cache(cache_file)
            
            raise
    
    def _get_cache_file(self, endpoint: str, params: Dict[str, Any]) -> str:
        """
        Get cache file path for a request.
        
        Args:
            endpoint (str): API endpoint
            params (dict): Query parameters
            
        Returns:
            str: Cache file path
        """
        # Remove API key from params for cache file name
        cache_params = params.copy()
        cache_params.pop("api_key", None)
        
        # Create cache file name
        endpoint_clean = endpoint.replace("/", "_").strip("_")
        params_str = "_".join(f"{k}_{v}" for k, v in sorted(cache_params.items()) if k != "api_key")
        cache_file = f"{endpoint_clean}_{params_str}.json" if params_str else f"{endpoint_clean}.json"
        
        # Replace invalid characters
        cache_file = "".join(c if c.isalnum() or c == "_" or c == "." else "_" for c in cache_file)
        
        # Return cache file path
        return os.path.join(self.cache_dir, cache_file)
    
    def _is_cache_valid(self, cache_file: str) -> bool:
        """
        Check if cache is valid.
        
        Args:
            cache_file (str): Cache file path
            
        Returns:
            bool: True if cache is valid, False otherwise
        """
        if not os.path.exists(cache_file):
            return False
        
        # Get file modification time
        mtime = os.path.getmtime(cache_file)
        
        # Check if file is older than cache TTL
        return time.time() - mtime < self.cache_ttl
    
    def _load_from_cache(self, cache_file: str) -> Dict[str, Any]:
        """
        Load response from cache.
        
        Args:
            cache_file (str): Cache file path
            
        Returns:
            dict: Cached response
        """
        with open(cache_file, "r") as f:
            return json.load(f)
    
    def _save_to_cache(self, cache_file: str, data: Dict[str, Any]) -> None:
        """
        Save response to cache.
        
        Args:
            cache_file (str): Cache file path
            data (dict): Response data
        """
        with open(cache_file, "w") as f:
            json.dump(data, f, indent=2)


def download_committee_contributions(committee_id: str, output_dir: str, start_date: str = None, end_date: str = None) -> str:
    """
    Download contributions for a committee.
    
    Args:
        committee_id (str): Committee ID
        output_dir (str): Output directory for results
        start_date (str, optional): Start date (YYYY-MM-DD)
        end_date (str, optional): End date (YYYY-MM-DD)
        
    Returns:
        str: Path to output file
    """
    # Initialize downloader
    downloader = FECContributionDownloader()
    
    # Construct parameters
    params = {}
    
    if start_date:
        params["min_date"] = start_date
    
    if end_date:
        params["max_date"] = end_date
    
    # Get committee details
    logger.info(f"Getting details for committee {committee_id}")
    committee = downloader.get_committee(committee_id)
    
    # Get committee contributions
    logger.info(f"Downloading contributions for committee {committee_id}")
    contributions = downloader.get_schedule_a(committee_id, **params)
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Create output file name
    committee_name = committee.get("results", [{}])[0].get("name", "unknown")
    committee_name = "".join(c if c.isalnum() or c == "_" or c == "-" or c == " " else "_" for c in committee_name)
    
    date_range = ""
    if start_date and end_date:
        date_range = f"_{start_date}_to_{end_date}"
    elif start_date:
        date_range = f"_from_{start_date}"
    elif end_date:
        date_range = f"_to_{end_date}"
    
    output_file = os.path.join(output_dir, f"{committee_id}_{committee_name}{date_range}.json")
    
    # Save data
    with open(output_file, "w") as f:
        json.dump({
            "committee": committee.get("results", [{}])[0],
            "contributions": contributions,
            "metadata": {
                "committee_id": committee_id,
                "start_date": start_date,
                "end_date": end_date,
                "download_date": datetime.datetime.now().isoformat(),
                "count": len(contributions)
            }
        }, f, indent=2)
    
    logger.info(f"Downloaded {len(contributions)} contributions for committee {committee_id}")
    logger.info(f"Results saved to {output_file}")
    
    return output_file


def main():
    """Main entry point."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Download FEC contributions data for committees")
    parser.add_argument("committee_id", help="Committee ID to download contributions for")
    parser.add_argument("--output-dir", "-o", default="data/fec", help="Output directory for results")
    parser.add_argument("--start-date", "-s", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", "-e", help="End date (YYYY-MM-DD)")
    parser.add_argument("--config", "-c", help="Path to configuration file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set log level
    if args.verbose:
        get_logger("data_mining").setLevel("debug")
    
    # Load configuration if provided
    if args.config:
        from scripts.utils.config import load_config
        load_config(args.config)
    
    # Download contributions
    try:
        output_file = download_committee_contributions(
            args.committee_id,
            args.output_dir,
            args.start_date,
            args.end_date
        )
        
        logger.info(f"Results saved to {output_file}")
        return 0
    except Exception as e:
        logger.error(f"Error downloading contributions: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main()) 