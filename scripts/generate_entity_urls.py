#!/usr/bin/env python3
"""
Generate Google search URLs to manually classify each extracted influencer/entity.
Outputs a CSV with columns: name, twitter_search_url, wikipedia_search_url
"""
import os
import csv
import urllib.parse

JSON_PATH = os.path.join('data', 'influencers.json')
OUTPUT_CSV = os.path.join('data', 'entity_classification_urls.csv')


def main():
    if not os.path.isfile(JSON_PATH):
        print(f"JSON not found: {JSON_PATH}")
        return

    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        influencers = json.load(f)

    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)

    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['name', 'twitter_search_url', 'wikipedia_search_url'])

        for inf in influencers:
            name = inf.get('name')
            if not name:
                continue
            query_twitter = urllib.parse.quote_plus(f"{name} site:twitter.com")
            twitter_url = f"https://www.google.com/search?q={query_twitter}"
            query_wiki = urllib.parse.quote_plus(f"{name} site:wikipedia.org")
            wiki_url = f"https://www.google.com/search?q={query_wiki}"
            writer.writerow([name, twitter_url, wiki_url])

    print(f"Generated classification URLs in {OUTPUT_CSV}")

if __name__ == '__main__':
    import json
    main() 