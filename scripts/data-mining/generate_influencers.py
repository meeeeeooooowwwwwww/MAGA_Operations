#!/usr/bin/env python3
"""
Script to generate a list of potential media influencers by scraping a key YouTube channel
and extracting political figure names, then writing the top names by frequency to JSON.
"""
import os
import json
import sys
# Ensure the top-level scripts directory is on the path for imports
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPT_DIR)
from extract_influencers_full import get_all_video_titles, extract_names_from_title, process_videos

# You can change this to any YouTube channel of interest
CHANNEL_NAME = 'bennyjohnson'

# Output path
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'influencers.json')


def main():
    print(f"Fetching videos from YouTube channel: {CHANNEL_NAME}")
    videos = get_all_video_titles()
    if not videos:
        print("No videos found, aborting.")
        return

    print(f"Extracting names from {len(videos)} videos...")
    # process_videos returns detailed info; but we only need name_counter
    results = process_videos(videos)

    # results contains list of {title, names} and a global name_counter
    name_counts = results if isinstance(results, dict) and 'name_counter' in results else results[1] if isinstance(results, tuple) else {}
    if not name_counts:
        print("No names extracted, aborting.")
        return

    # Sort names by count
    sorted_names = sorted(name_counts.items(), key=lambda x: x[1], reverse=True)

    # Take top 1000 influencers
    top_influencers = [{'name': name, 'count': count} for name, count in sorted_names[:1000]]

    # Ensure output directory exists
    if not os.path.isdir(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created data directory: {OUTPUT_DIR}")

    # Write to JSON file
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(top_influencers, f, indent=2)

    print(f"Saved top influencers to {OUTPUT_FILE}")


if __name__ == '__main__':
    main() 