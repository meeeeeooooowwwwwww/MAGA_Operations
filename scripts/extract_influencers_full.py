#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YouTube Video Political Figure Extractor (Complete Channel)
----------------------------------------------------------
Enhanced script to extract political figure names from ALL of Benny Johnson's YouTube videos
using Selenium for browser automation to load multiple pages of content.
"""

import os
import re
import json
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import argparse

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
except ImportError:
    print("Selenium is required. Installing...")
    import subprocess
    subprocess.check_call(["pip", "install", "selenium"])
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

try:
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    print("WebDriver Manager is required. Installing...")
    import subprocess
    subprocess.check_call(["pip", "install", "webdriver-manager"])
    from webdriver_manager.chrome import ChromeDriverManager

# Configuration
CHANNEL_URL = "https://www.youtube.com/@bennyjohnson/videos"
# Default max pages to scan (scroll iterations)
MAX_PAGES = 100  # Maximum number of "pages" (scrolls) to load
SCROLL_PAUSE_TIME = 2  # Time to pause between scrolls

# Output directory for JSON
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../data")

# --- CLI Configuration ---
parser = argparse.ArgumentParser(description="Extract video titles and influencer names from a YouTube channel")
parser.add_argument("--channel", type=str, default=CHANNEL_URL, help="YouTube channel URL to scrape, e.g. https://www.youtube.com/@bennyjohnson/videos")
parser.add_argument("--pages", type=int, default=MAX_PAGES, help="Max scroll pages to load (default 100)")
args = parser.parse_args()
# Override configuration from CLI
CHANNEL_URL = args.channel
MAX_PAGES = args.pages

def ensure_output_dir():
    """Ensure the output directory exists."""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created output directory: {OUTPUT_DIR}")

def get_all_video_titles():
    """Fetch ALL video titles from the YouTube channel using Selenium."""
    print(f"Fetching video titles from {CHANNEL_URL}")
    print("Using Selenium to load multiple pages...")
    
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Set up the Chrome driver
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    except Exception as e:
        print(f"Error setting up Chrome driver: {e}")
        print("Trying alternative setup method...")
        try:
            # Alternative method without webdriver_manager
            driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            print(f"Still couldn't set up Chrome driver: {e}")
            print("Please make sure Chrome is installed on your system.")
            return []
    
    try:
        # Navigate to the YouTube channel videos page
        driver.get(CHANNEL_URL)
        time.sleep(3)  # Wait for page to load
        
        # Scroll down to load more videos
        video_count = 0
        page_count = 0
        last_height = driver.execute_script("return document.documentElement.scrollHeight")
        
        print("Scrolling to load more videos...")
        while page_count < MAX_PAGES:
            # Scroll down
            driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            
            # Wait for more videos to load
            time.sleep(SCROLL_PAUSE_TIME)
            
            # Calculate new scroll height and compare with last scroll height
            new_height = driver.execute_script("return document.documentElement.scrollHeight")
            
            # Count current videos
            current_videos = driver.find_elements(By.CSS_SELECTOR, "#video-title")
            
            # Print progress
            if len(current_videos) > video_count:
                video_count = len(current_videos)
                print(f"Loaded {video_count} videos so far... (Page {page_count + 1})")
            
            # If heights are the same, we've reached the end
            if new_height == last_height:
                print("Reached the end of the page or no more videos to load.")
                break
                
            last_height = new_height
            page_count += 1
        
        # Extract video information
        videos = []
        video_elements = driver.find_elements(By.CSS_SELECTOR, "#video-title")
        
        for element in video_elements:
            if element.get_attribute("title"):
                title = element.get_attribute("title")
                url = element.get_attribute("href") or ""
                videos.append({
                    "title": title,
                    "url": url
                })
        
        print(f"Found {len(videos)} unique videos")
        return videos
        
    except Exception as e:
        print(f"Error fetching video titles with Selenium: {e}")
        return []
    finally:
        # Close the browser
        driver.quit()

def extract_names_from_title(title):
    """Extract potential person names from a video title using regex patterns."""
    names = []
    
    # List of important political figures to check for
    political_figures = [
        "Trump", "Biden", "Obama", "Clinton", "DeSantis", "Pence", "Elon Musk", "Musk",
        "JD Vance", "Vance", "Kamala", "Harris", "Kamala Harris", "MTG", "Marjorie Taylor Greene", 
        "AOC", "Alexandria Ocasio-Cortez", "Kari Lake", "Tucker", "Carlson", "Tucker Carlson",
        "Matt Gaetz", "Gaetz", "Lauren Boebert", "Boebert", "McConnell", "McCarthy", "RFK Jr",
        "Robert Kennedy", "Tim Walz", "JD Vance", "Vivek", "Nikki Haley", "Haley", "Fetterman",
        "Shapiro", "Ben Shapiro", "Mark Robinson", "Kristi Noem", "Ron DeSantis", "Pelosi",
        "Nancy Pelosi", "Mike Johnson", "Ted Cruz", "Cruz", "Rand Paul", "Hawley", "Josh Hawley",
        "Greg Abbott", "Abbott", "Youngkin", "Glenn Youngkin", "Marco Rubio", "Rubio"
    ]
    
    # Check if any political figures are mentioned in the title
    for figure in political_figures:
        pattern = r'\b' + re.escape(figure) + r'\b'
        if re.search(pattern, title, re.IGNORECASE):
            if figure not in names:
                names.append(figure)
    
    # Try to extract names with Title Case format (two words)
    title_case_pattern = r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b'
    title_case_matches = re.findall(title_case_pattern, title)
    for match in title_case_matches:
        if match not in names and not any(kw.lower() in match.lower() for kw in ['Secret', 'White House', 'Breaking', 'Media']):
            names.append(match)
    
    return names

def process_videos(videos):
    """Process videos to extract political figures."""
    results = []
    name_counter = {}
    
    print("\nExtracting names from video titles...")
    for i, video in enumerate(videos):
        title = video["title"]
        url = video["url"]
        
        # Print progress periodically
        if i % 50 == 0 or i == len(videos) - 1:
            print(f"Processing video {i+1}/{len(videos)}")
        
        names = extract_names_from_title(title)
        
        # Update name counter
        for name in names:
            if name in name_counter:
                name_counter[name] += 1
            else:
                name_counter[name] = 1
        
        results.append({
            "title": title,
            "url": url,
            "names": names
        })
    
    # Get unique names sorted by frequency
    unique_names = [{"name": name, "mentions": count} for name, count in name_counter.items()]
    unique_names.sort(key=lambda x: x["mentions"], reverse=True)
    
    # Filter out likely false positives
    filtered_names = []
    blacklist = ["Multiple Shows", "Ticket Sales", "Secret Mystery", "Fake Space", 
                 "Spring Break", "General", "Playback", "Keyboard shortcuts", 
                 "Subtitles", "Spherical videos", "History"]
    
    for item in unique_names:
        if item["name"] not in blacklist and not any(bl.lower() in item["name"].lower() for bl in blacklist):
            filtered_names.append(item)
    
    print(f"Filtered out {len(unique_names) - len(filtered_names)} likely false positives")
    
    return results, filtered_names

def create_influencer_entries(names_data):
    """Create structured influencer entries that match our database schema."""
    influencers = []
    known_affiliations = {
        "Trump": ["Republican", "MAGA", "America First"],
        "Biden": ["Democrat"],
        "Obama": ["Democrat"],
        "Clinton": ["Democrat"],
        "DeSantis": ["Republican"],
        "Ron DeSantis": ["Republican"],
        "Pence": ["Republican"],
        "Elon Musk": ["Independent", "Trump Supporter"],
        "Musk": ["Independent", "Trump Supporter"],
        "JD Vance": ["Republican", "MAGA", "America First"],
        "Vance": ["Republican", "MAGA", "America First"],
        "Kamala": ["Democrat"],
        "Harris": ["Democrat"],
        "Kamala Harris": ["Democrat"],
        "MTG": ["Republican", "MAGA", "America First"],
        "Marjorie Taylor Greene": ["Republican", "MAGA", "America First"],
        "AOC": ["Democrat", "Progressive"],
        "Alexandria Ocasio-Cortez": ["Democrat", "Progressive"],
        "Kari Lake": ["Republican", "MAGA", "America First"],
        "Tucker": ["Media Personality", "America First"],
        "Carlson": ["Media Personality", "America First"],
        "Tucker Carlson": ["Media Personality", "America First"],
        "Matt Gaetz": ["Republican", "MAGA", "America First"],
        "Gaetz": ["Republican", "MAGA", "America First"],
        "Lauren Boebert": ["Republican", "MAGA", "America First"],
        "Boebert": ["Republican", "MAGA", "America First"],
        "McConnell": ["Republican"],
        "McCarthy": ["Republican"],
        "RFK Jr": ["Independent", "Trump Supporter"],
        "Robert Kennedy": ["Independent", "Trump Supporter"]
    }
    
    for item in names_data:
        name = item["name"]
        mentions = item["mentions"]
        
        category = "Politician"
        affiliations = ["Republican", "MAGA"]  # Default assumption
        if name in known_affiliations:
            affiliations = known_affiliations[name]
        
        # Determine category based on known figures
        if name in ["Tucker", "Carlson", "Tucker Carlson", "Benny Johnson"]:
            category = "Media Personality"
        
        # For names not in our known list, make reasonable assumptions
        twitter_handle = "@" + name.lower().replace(" ", "")
        
        influencer = {
            "name": name,
            "category": category,
            "bio": f"Featured in {mentions} video(s) on Benny Johnson's YouTube channel.",
            "twitter_handle": twitter_handle,
            "notes": "Automatically extracted from YouTube video titles. Needs research.",
            "affiliations": affiliations,
            "media_outlets": ["YouTube"],  # Default
            "sources": [
                {
                    "name": "Benny Johnson YouTube Channel",
                    "url": "https://www.youtube.com/@bennyjohnson",
                    "date_accessed": datetime.now().strftime("%Y-%m-%d")
                }
            ]
        }
        
        influencers.append(influencer)
    
    return influencers

def save_to_json(videos_data, names_data, influencers_data):
    """Save extracted data to JSON files."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save videos data
    videos_file = os.path.join(OUTPUT_DIR, f"benny_johnson_videos_{timestamp}.json")
    with open(videos_file, 'w', encoding='utf-8') as f:
        json.dump(videos_data, f, indent=2, ensure_ascii=False)
    
    # Save names data
    names_file = os.path.join(OUTPUT_DIR, f"benny_johnson_names_{timestamp}.json")
    with open(names_file, 'w', encoding='utf-8') as f:
        json.dump(names_data, f, indent=2, ensure_ascii=False)
    
    # Save influencers data
    influencers_file = os.path.join(OUTPUT_DIR, f"benny_johnson_influencers_{timestamp}.json")
    with open(influencers_file, 'w', encoding='utf-8') as f:
        json.dump(influencers_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nSaved videos data to: {videos_file}")
    print(f"Saved names data to: {names_file}")
    print(f"Saved influencers data to: {influencers_file}")
    return videos_file, names_file, influencers_file

def main():
    """Main function."""
    print("YouTube Video Political Figure Extractor (Complete Channel)")
    print("----------------------------------------------------------")
    
    # Ensure output directory exists
    ensure_output_dir()
    
    # Get all video titles
    videos = get_all_video_titles()
    
    if not videos:
        print("No videos found. Exiting.")
        return
    
    # Process videos to extract names
    videos_data, names_data = process_videos(videos)
    
    # Create structured influencer entries
    influencers_data = create_influencer_entries(names_data)
    
    # Save results to JSON
    videos_file, names_file, influencers_file = save_to_json(videos_data, names_data, influencers_data)
    
    # Print summary
    print("\nExtraction Summary:")
    print(f"- Videos processed: {len(videos_data)}")
    print(f"- Unique names found: {len(names_data)}")
    print(f"- Influencer profiles created: {len(influencers_data)}")
    
    if names_data:
        print("\nTop 20 most mentioned figures:")
        for i, item in enumerate(names_data[:20]):
            print(f"{i+1}. {item['name']} ({item['mentions']} mentions)")
    
    print("\nComplete!")

if __name__ == "__main__":
    main() 