#!/usr/bin/env python3
"""
Import influencer candidates from JSON into the influencers SQLite database.
Creates or updates a table 'influencer_candidates' with columns name (TEXT) and mentions (INTEGER).
"""
import os
import json
import sqlite3

DB_PATH = os.path.join('data', 'influencers.db')
JSON_PATH = os.path.join('data', 'influencers.json')
TABLE_NAME = 'influencer_candidates'


def main():
    if not os.path.isfile(JSON_PATH):
        print(f"JSON file not found: {JSON_PATH}")
        return

    # Load JSON data
    with open(JSON_PATH, 'r', encoding='utf-8') as jf:
        influencers = json.load(jf)

    # Ensure DB directory exists
    db_dir = os.path.dirname(DB_PATH)
    os.makedirs(db_dir, exist_ok=True)

    # Connect to SQLite database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create table if not exists
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            name TEXT PRIMARY KEY,
            mentions INTEGER
        )
    """)

    # Insert or update each influencer
    for inf in influencers:
        name = inf.get('name')
        mentions = inf.get('count', 0)
        if name:
            cursor.execute(f"""
                INSERT INTO {TABLE_NAME} (name, mentions)
                VALUES (?, ?)
                ON CONFLICT(name) DO UPDATE SET mentions = excluded.mentions;
            """, (name, mentions))

    conn.commit()
    conn.close()
    print(f"Imported {len(influencers)} influencers into {DB_PATH}.{TABLE_NAME}")


if __name__ == '__main__':
    main() 