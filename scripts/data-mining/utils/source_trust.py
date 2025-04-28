#!/usr/bin/env python3
"""
Source Trust Evaluation Module

Evaluates and scores the trustworthiness of data sources based on multiple factors:
- Domain reputation
- Content consistency
- Citation history
- Expert consensus
- Transparency
"""
import os
import sys
import json
import re
from urllib.parse import urlparse
import tldextract
import sqlite3
from datetime import datetime

# Add parent directory to path for relative imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import get_logger
from utils.config import PROJECT_ROOT, TRUST_SCORE_MINIMUM

# Initialize logger
logger = get_logger("source_trust")

# Path to trusted sources list
TRUSTED_SOURCES_PATH = os.path.join(PROJECT_ROOT, "data", "trusted_sources.json")
BLOCKLIST_PATH = os.path.join(PROJECT_ROOT, "data", "blocked_sources.json")

# Default trusted sources if file doesn't exist
DEFAULT_TRUSTED_SOURCES = {
    "government": {
        "domains": [
            "*.gov", "*.mil", "congress.gov", "whitehouse.gov", "senate.gov", "house.gov",
            "supremecourt.gov", "loc.gov", "archives.gov", "cia.gov", "fbi.gov", "dhs.gov"
        ],
        "base_score": 90
    },
    "official_campaign": {
        "domains": ["donaldjtrump.com", "*.donaldjtrump.com"],
        "base_score": 95
    },
    "financial_disclosure": {
        "domains": [
            "opensecrets.org", "fec.gov", "followthemoney.org", "ethics.senate.gov", 
            "disclosures.house.gov"
        ],
        "base_score": 85
    },
    "reputable_news": {
        "domains": [
            "reuters.com", "apnews.com", "c-span.org", "bloomberg.com", "wsj.com",
            "economist.com", "bbc.com", "bbc.co.uk"
        ],
        "base_score": 75
    },
    "right_leaning_news": {
        "domains": [
            "foxnews.com", "nypost.com", "washingtontimes.com", "washingtonexaminer.com",
            "dailycaller.com", "breitbart.com", "oann.com", "newsmax.com"
        ],
        "base_score": 70
    },
    "left_leaning_news": {
        "domains": [
            "nytimes.com", "washingtonpost.com", "cnn.com", "msnbc.com", "vox.com",
            "huffpost.com", "slate.com", "theatlantic.com", "newyorker.com"
        ],
        "base_score": 65
    },
    "fact_checkers": {
        "domains": [
            "factcheck.org", "politifact.com", "snopes.com", "mediabiasfactcheck.com"
        ],
        "base_score": 75
    },
    "research_institutions": {
        "domains": [
            "*.edu", "brookings.edu", "heritage.org", "cato.org", "aei.org", 
            "pewresearch.org", "rand.org"
        ],
        "base_score": 80
    },
    "international_orgs": {
        "domains": [
            "un.org", "who.int", "nato.int", "wto.org", "imf.org", "worldbank.org"
        ],
        "base_score": 75
    },
    "social_media": {
        "domains": [
            "twitter.com", "x.com", "facebook.com", "instagram.com", "youtube.com",
            "tiktok.com", "reddit.com", "linkedin.com"
        ],
        "base_score": 40
    }
}

# Default blocked sources
DEFAULT_BLOCKED_SOURCES = {
    "known_disinformation": [
        "sputniknews.com", "rt.com", "infowars.com", "naturalnews.com", 
        "beforeitsnews.com", "zerohedge.com"
    ],
    "satire_sites": [
        "theonion.com", "babylonbee.com", "clickhole.com", "newsthump.com",
        "thebeaverton.com", "waterfordwhispersnews.com"
    ],
    "content_farms": [
        "examiner.com", "ezinearticles.com", "hubpages.com", "squidoo.com"
    ]
}

def load_trusted_sources():
    """Load trusted sources from file or create with defaults if not exists."""
    if os.path.exists(TRUSTED_SOURCES_PATH):
        try:
            with open(TRUSTED_SOURCES_PATH, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading trusted sources: {str(e)}")
    
    # Create directories if they don't exist
    os.makedirs(os.path.dirname(TRUSTED_SOURCES_PATH), exist_ok=True)
    
    # Save and return defaults
    with open(TRUSTED_SOURCES_PATH, 'w') as f:
        json.dump(DEFAULT_TRUSTED_SOURCES, f, indent=2)
    
    return DEFAULT_TRUSTED_SOURCES

def load_blocklist():
    """Load blocked sources from file or create with defaults if not exists."""
    if os.path.exists(BLOCKLIST_PATH):
        try:
            with open(BLOCKLIST_PATH, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading blocklist: {str(e)}")
    
    # Create directories if they don't exist
    os.makedirs(os.path.dirname(BLOCKLIST_PATH), exist_ok=True)
    
    # Save and return defaults
    with open(BLOCKLIST_PATH, 'w') as f:
        json.dump(DEFAULT_BLOCKED_SOURCES, f, indent=2)
    
    return DEFAULT_BLOCKED_SOURCES

def is_domain_match(domain, pattern):
    """Check if a domain matches a pattern, supporting wildcards."""
    if pattern.startswith('*.'):
        return domain.endswith(pattern[2:])
    return domain == pattern

def get_domain_category(domain):
    """Get the category of a domain from trusted sources."""
    trusted_sources = load_trusted_sources()
    
    for category, data in trusted_sources.items():
        for domain_pattern in data["domains"]:
            if is_domain_match(domain, domain_pattern):
                return category, data["base_score"]
    
    return None, 0

def is_blocklisted(domain):
    """Check if a domain is on the blocklist."""
    blocklist = load_blocklist()
    
    for category, domains in blocklist.items():
        for domain_pattern in domains:
            if is_domain_match(domain, domain_pattern):
                return True, category
    
    return False, None

def update_source_history(url, trust_score, success=True):
    """Update source history in database for future trust calculations."""
    domain = urlparse(url).netloc
    
    try:
        # Connect to database
        db_path = os.path.join(PROJECT_ROOT, "maga_ops.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create table if not exists
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS source_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT NOT NULL,
            url TEXT NOT NULL,
            trust_score INTEGER NOT NULL,
            success BOOLEAN NOT NULL,
            accessed_at TIMESTAMP NOT NULL
        )
        ''')
        
        # Insert record
        cursor.execute('''
        INSERT INTO source_history (domain, url, trust_score, success, accessed_at)
        VALUES (?, ?, ?, ?, ?)
        ''', (domain, url, trust_score, success, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error updating source history: {str(e)}")

def get_historical_trust(domain):
    """Get historical trust score for a domain from database."""
    try:
        # Connect to database
        db_path = os.path.join(PROJECT_ROOT, "maga_ops.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get average trust score and success rate
        cursor.execute('''
        SELECT 
            AVG(trust_score) as avg_score,
            SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as success_rate,
            COUNT(*) as total_requests
        FROM source_history
        WHERE domain = ?
        ''', (domain,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0] is not None:
            avg_score, success_rate, total_requests = result
            
            # Weight by number of requests, up to 10 (more requests = more confidence)
            request_weight = min(total_requests / 10.0, 1.0)
            
            # Return combined historical score
            return {
                "avg_score": avg_score,
                "success_rate": success_rate,
                "total_requests": total_requests,
                "historical_score": avg_score * 0.7 + success_rate * 0.3,
                "confidence": request_weight
            }
        
        return {"avg_score": 0, "success_rate": 0, "total_requests": 0, "historical_score": 0, "confidence": 0}
        
    except Exception as e:
        logger.error(f"Error getting historical trust: {str(e)}")
        return {"avg_score": 0, "success_rate": 0, "total_requests": 0, "historical_score": 0, "confidence": 0}

def calculate_trust_score(url):
    """
    Calculate a trust score (0-100) for a given URL.
    
    Factors:
    - Domain category (official, news, social media, etc.)
    - Historical reliability
    - TLD reliability (.gov, .edu, etc.)
    - Domain age factors
    
    Returns:
        Trust score between 0 and 100
    """
    if not url:
        return 0
    
    # Parse domain
    extracted = tldextract.extract(url)
    domain = f"{extracted.domain}.{extracted.suffix}"
    if extracted.subdomain:
        full_domain = f"{extracted.subdomain}.{domain}"
    else:
        full_domain = domain
    
    # Check if domain is blocklisted
    is_blocked, block_category = is_blocklisted(full_domain)
    if is_blocked:
        logger.warning(f"Domain {full_domain} is blocklisted in category: {block_category}")
        return 0
    
    # Base score - domain category
    category, base_score = get_domain_category(full_domain)
    
    # If domain not found, check without subdomain
    if not category:
        category, base_score = get_domain_category(domain)
    
    # If still not found, use default score
    if not category:
        # Default scores based on TLD
        tld_scores = {
            "gov": 85,
            "mil": 85,
            "edu": 75,
            "org": 60,
            "com": 50,
            "net": 50,
            "io": 45,
            "co": 45,
            "info": 30,
            "biz": 25,
            "xyz": 20,
        }
        
        tld = extracted.suffix.split('.')[-1]
        base_score = tld_scores.get(tld, 40)
        category = "unknown"
    
    # Historical factors
    history = get_historical_trust(full_domain)
    
    # Apply weights to different factors
    # - 60% base category score
    # - 30% historical performance (if available)
    # - 10% URL specific factors
    
    final_score = base_score * 0.6
    
    # Historical adjustment
    if history["total_requests"] > 0:
        historical_adjustment = history["historical_score"] * 0.3 * history["confidence"]
        final_score += historical_adjustment
    
    # URL specific adjustments
    url_lower = url.lower()
    
    # Penalize URLs with excessive query parameters (potential tracking/spam)
    query_params = url_lower.count('&')
    if query_params > 5:
        final_score -= min(query_params, 10)
    
    # Penalize very long URLs
    if len(url) > 150:
        final_score -= 5
    
    # Adjust for suspicious keywords in URL
    suspicious_keywords = ['hack', 'crack', 'free', 'download', 'warez', 'keygen', 'torrent']
    for keyword in suspicious_keywords:
        if keyword in url_lower:
            final_score -= 10
            break
    
    # HTTPS bonus
    if url_lower.startswith('https://'):
        final_score += 5
    elif not url_lower.startswith('http://'):
        final_score -= 5  # Not HTTP or HTTPS
    
    # Ensure score is within bounds
    final_score = max(0, min(100, final_score))
    
    logger.debug(f"Trust score for {url}: {final_score:.1f} (category: {category}, base: {base_score})")
    
    return round(final_score, 1)

def is_trusted_source(url, min_score=None):
    """
    Determine if a URL is from a trusted source.
    
    Args:
        url: The URL to check
        min_score: Minimum score to consider trusted (default: from config)
        
    Returns:
        True if the source is trusted, False otherwise
    """
    if min_score is None:
        min_score = TRUST_SCORE_MINIMUM
    
    trust_score = calculate_trust_score(url)
    return trust_score >= min_score

if __name__ == "__main__":
    # Test the trust evaluation
    test_urls = [
        "https://www.whitehouse.gov/briefing-room/",
        "https://www.donaldjtrump.com/updates/",
        "https://www.fec.gov/data/",
        "https://www.opensecrets.org/2024-presidential-race/",
        "https://www.nytimes.com/politics/",
        "https://www.foxnews.com/politics/",
        "https://www.cnn.com/politics",
        "https://twitter.com/realDonaldTrump",
        "https://www.reddit.com/r/Conservative/",
        "https://www.infowars.com/",
        "https://theonion.com/politics",
        "https://example.com/politics/article?id=12345",
    ]
    
    print("\nTrust Score Evaluation:")
    print("-" * 80)
    print(f"{'URL':<50} | {'Score':<10} | {'Trusted':<10}")
    print("-" * 80)
    
    for url in test_urls:
        score = calculate_trust_score(url)
        trusted = is_trusted_source(url)
        print(f"{url[:50]:<50} | {score:<10.1f} | {trusted!s:<10}")
    
    print("\nTrusted sources loaded:", len(load_trusted_sources()))
    print("Blocked sources loaded:", sum(len(domains) for domains in load_blocklist().values())) 