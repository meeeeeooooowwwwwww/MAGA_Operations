#!/usr/bin/env python3
"""
Classify extracted influencers by entity type and political leaning using their Twitter profiles.
Updates the influencer_candidates table by adding type TEXT, affiliation TEXT, ideology TEXT.
"""
import os
import sqlite3
import re
from social.twitter import get_api, fetch_profiles
from dotenv import load_dotenv

# Load Twitter API credentials from .env
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# Twitter OAuth credentials
CONSUMER_KEY = os.getenv('TWITTER_CONSUMER_KEY')
CONSUMER_SECRET = os.getenv('TWITTER_CONSUMER_SECRET')
ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')

DB_PATH = os.path.join('data', 'influencers.db')
TABLE = 'influencer_candidates'

# Keywords for classification
TYPE_KEYWORDS = {
    'Politician': ['senator', 'congress', 'representative', 'governor', 'mayor', 'legislator'],
    'Journalist': ['journalist', 'reporter', 'editor', 'news'],
    'Lawyer': ['attorney', 'lawyer'],
    'Judge': ['judge'],
    'Media Personality': ['host', 'anchor', 'podcast'],
    'Activist': ['activist', 'campaign', 'advocate']
}
PARTY_KEYWORDS = {
    'Republican': ['republican'],
    'Democrat': ['democrat'],
    'Independent': ['independent'],
    'Libertarian': ['libertarian']
}
IDEOLOGY_KEYWORDS = {
    'MAGA': ['maga', 'america first'],
    'Trump Supporter': ['maga', 'trump supporter'],
    'Never Trumper': ['never trumper'],
}

# Connect to DB and add columns if missing
def ensure_schema(conn):
    cur = conn.cursor()
    # Add columns if not exists
    for col, coltype in [('type', 'TEXT'), ('affiliation', 'TEXT'), ('ideology', 'TEXT')]:
        try:
            cur.execute(f"ALTER TABLE {TABLE} ADD COLUMN {col} {coltype}")
        except sqlite3.OperationalError:
            # Column already exists
            pass
    conn.commit()

# Classify one bio
def classify_bio(bio):
    bio_lower = bio.lower()
    etype = 'Unknown'
    for t, kws in TYPE_KEYWORDS.items():
        if any(kw in bio_lower for kw in kws):
            etype = t
            break
    affiliation = 'Unknown'
    for p, kws in PARTY_KEYWORDS.items():
        if any(kw in bio_lower for kw in kws): affiliation = p
    ideology = 'None'
    for i, kws in IDEOLOGY_KEYWORDS.items():
        if any(kw in bio_lower for kw in kws): ideology = i
    return etype, affiliation, ideology

# Main classification process
def main():
    print('Connecting to DB...')
    conn = sqlite3.connect(DB_PATH)
    ensure_schema(conn)
    cur = conn.cursor()

    # Fetch candidates
    cur.execute(f"SELECT name FROM {TABLE}")
    rows = cur.fetchall()
    names = [r[0] for r in rows]
    print(f'Found {len(names)} names to classify')

    # Initialize Twitter API
    api = get_api(ACCESS_TOKEN, ACCESS_TOKEN_SECRET, CONSUMER_KEY, CONSUMER_SECRET)

    # Lookup profiles in batches of 100
    for i in range(0, len(names), 100):
        batch = names[i:i+100]
        print(f'Fetching Twitter profiles for batch {i//100+1}...')
        profiles = fetch_profiles(api, screen_names=[n.replace(' ', '') for n in batch])
        for profile in profiles:
            screen_name = profile.get('screen_name')
            bio = profile.get('description', '')
            name = profile.get('name')
            # Classify
            etype, affiliation, ideology = classify_bio(bio)
            # Update DB row where name matches
            cur.execute(f"""
                UPDATE {TABLE}
                SET type = ?, affiliation = ?, ideology = ?
                WHERE name = ?
            """, (etype, affiliation, ideology, name))
    conn.commit()
    conn.close()
    print('Classification complete and DB updated.')

if __name__ == '__main__':
    main() 