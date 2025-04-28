#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Query the AI-Optimized Influencers Database
-------------------------------------------
This script demonstrates various query capabilities of our AI-ready database.
"""

import os
import sqlite3
import argparse
import json
from datetime import datetime

# Configuration
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DB_PATH = os.path.join(DATA_DIR, "influencers_ai.db")

def connect_to_db():
    """Connect to the database."""
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return None
    
    return sqlite3.connect(DB_PATH)

def display_results(results, headers=None):
    """Display query results in a formatted table."""
    if not results:
        print("No results found.")
        return
    
    # If headers weren't provided, use the first result's keys
    if not headers and isinstance(results[0], dict):
        headers = results[0].keys()
    
    # Convert all results to dictionaries if they're tuples
    if isinstance(results[0], tuple):
        if not headers:
            print("Error: Headers required for tuple results")
            return
        
        dict_results = []
        for result in results:
            dict_result = {}
            for i, header in enumerate(headers):
                dict_result[header] = result[i] if i < len(result) else ""
            dict_results.append(dict_result)
        results = dict_results
    
    # Get maximum width for each column
    col_widths = {}
    for header in headers:
        col_widths[header] = max(len(str(header)), 
                                 max(len(str(result.get(header, ""))) for result in results))
    
    # Create a format string for each row
    format_str = " | ".join([f"{{:{col_widths[header]}}}" for header in headers])
    
    # Print the header
    print(format_str.format(*[header for header in headers]))
    print("-" * (sum(col_widths.values()) + 3 * (len(headers) - 1)))
    
    # Print each row
    for result in results:
        print(format_str.format(*[str(result.get(header, "")) for header in headers]))

def search_influencers(query, limit=None):
    """Search for influencers by name, with fuzzy matching."""
    conn = connect_to_db()
    if not conn:
        return []
    
    results = []
    try:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        normalized_query = query.lower().replace("'", "").replace('"', '')
        
        # Build base query
        sql = """
            SELECT i.id, i.name, c.name as category, i.twitter_handle, 
                   i.bio, i.relevance_score
            FROM influencers i
            LEFT JOIN categories c ON i.category_id = c.id
            WHERE i.normalized_name LIKE ? OR i.name LIKE ?
            ORDER BY i.relevance_score DESC
        """
        params = (f'%{normalized_query}%', f'%{query}%')

        # Add limit if provided
        if limit is not None:
            sql += " LIMIT ?"
            params += (int(limit),)
            
        cursor.execute(sql, params)
        direct_results = [dict(row) for row in cursor.fetchall()]
        
        # --- Combine with variation search (Consider if needed for suggestions) ---
        # For simplicity in suggestions, we might skip variation search initially
        # If variation search is kept, apply limit logic there too or combine before limiting.
        # Let's keep it simple for now and just return direct results when limit is used.
        if limit is None:
            # Search in name variations if no limit is set (for full search)
            cursor.execute("""
                SELECT i.id, i.name, c.name as category, i.twitter_handle, 
                       i.bio, i.relevance_score, v.variation
                FROM influencers i
                LEFT JOIN categories c ON i.category_id = c.id
                JOIN name_variations v ON i.id = v.influencer_id
                WHERE v.variation LIKE ?
                ORDER BY i.relevance_score DESC
            """, (f'%{query}%',))
            variation_results = [dict(row) for row in cursor.fetchall()]
            
            seen_ids = set(result['id'] for result in direct_results)
            for result in variation_results:
                if result['id'] not in seen_ids:
                    del result['variation']
                    direct_results.append(result)
                    seen_ids.add(result['id'])
        # ---------------------------------------------------------------------

        results = direct_results

    except Exception as e:
        print(f"Error during influencer search: {e}")
        results = []
    finally:
        if conn:
            conn.close()
            
    return results

def list_top_influencers(category=None, limit=10):
    """List top influencers, optionally filtered by category."""
    conn = connect_to_db()
    if not conn:
        return
    
    # Create a cursor with row factory
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if category:
        # Get the category id
        cursor.execute("SELECT id FROM categories WHERE name LIKE ?", (f'%{category}%',))
        category_ids = [row['id'] for row in cursor.fetchall()]
        
        if not category_ids:
            print(f"No category found matching '{category}'")
            conn.close()
            return
        
        placeholders = ','.join(['?'] * len(category_ids))
        
        # Query with category filter
        cursor.execute(f"""
            SELECT i.id, i.name, c.name as category, i.twitter_handle, 
                   i.bio, i.relevance_score
            FROM influencers i
            LEFT JOIN categories c ON i.category_id = c.id
            WHERE i.category_id IN ({placeholders})
            ORDER BY i.relevance_score DESC
            LIMIT ?
        """, category_ids + [limit])
    else:
        # Query without category filter
        cursor.execute("""
            SELECT i.id, i.name, c.name as category, i.twitter_handle, 
                   i.bio, i.relevance_score
            FROM influencers i
            LEFT JOIN categories c ON i.category_id = c.id
            ORDER BY i.relevance_score DESC
            LIMIT ?
        """, (limit,))
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    # Comment out direct printing
    # headers = ['id', 'name', 'category', 'twitter_handle', 'relevance_score']
    # print(f"\nTop {limit} influencers" + (f" in category '{category}'" if category else "") + ":")
    # display_results(results, headers)
    
    return results

def get_influencer_details(influencer_id):
    """Get detailed information about a specific influencer."""
    conn = connect_to_db()
    if not conn:
        return
    
    # Create a cursor with row factory
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get the basic influencer info
    cursor.execute("""
        SELECT i.*, c.name as category_name
        FROM influencers i
        LEFT JOIN categories c ON i.category_id = c.id
        WHERE i.id = ?
    """, (influencer_id,))
    
    influencer = dict(cursor.fetchone() or {})
    if not influencer:
        print(f"No influencer found with ID {influencer_id}")
        conn.close()
        return
    
    # Get affiliations
    cursor.execute("""
        SELECT a.name, a.ideology_spectrum_position
        FROM influencer_affiliations ia
        JOIN affiliations a ON ia.affiliation_id = a.id
        WHERE ia.influencer_id = ?
    """, (influencer_id,))
    
    influencer['affiliations'] = [dict(row) for row in cursor.fetchall()]
    
    # Get name variations
    cursor.execute("""
        SELECT variation, frequency
        FROM name_variations
        WHERE influencer_id = ?
    """, (influencer_id,))
    
    influencer['name_variations'] = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    # Comment out direct printing of details
    # print(f"\nInfluencer Details for {influencer['name']} (ID: {influencer['id']}):")
    # print("-" * 50)
    # print(f"Category: {influencer.get('category_name', 'Unknown')}")
    # print(f"Bio: {influencer.get('bio', '')}")
    # print(f"Twitter: {influencer.get('twitter_handle', '')}")
    # print(f"Relevance Score: {influencer.get('relevance_score', 0)}")
    
    # if influencer.get('affiliations'):
    #     print("\nAffiliations:")
    #     for affiliation in influencer['affiliations']:
    #         position = affiliation.get('ideology_spectrum_position')
    #         position_str = ""
    #         if position is not None:
    #             if position < -0.5:
    #                 position_str = " (Left)"
    #             elif position > 0.5:
    #                 position_str = " (Right)"
    #             elif -0.5 <= position <= 0.5:
    #                 position_str = " (Center)"
            
    #         print(f"- {affiliation['name']}{position_str}")
    
    # if influencer.get('name_variations'):
    #     print("\nAlso known as:")
    #     for variation in influencer['name_variations']:
    #         print(f"- {variation['variation']} (mentioned {variation['frequency']} times)")
    
    return influencer

def get_ideological_distribution():
    """Get distribution of influencers across the ideological spectrum."""
    conn = connect_to_db()
    if not conn:
        return
    
    # Create a cursor with row factory
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Count influencers by affiliation and ideological position
    cursor.execute("""
        SELECT a.name, a.ideology_spectrum_position, COUNT(DISTINCT ia.influencer_id) as count
        FROM influencer_affiliations ia
        JOIN affiliations a ON ia.affiliation_id = a.id
        WHERE a.ideology_spectrum_position IS NOT NULL
        GROUP BY a.id
        ORDER BY a.ideology_spectrum_position
    """)
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    # Define ideological buckets
    buckets = {
        "Far Left": [-1.0, -0.7],
        "Left": [-0.7, -0.3],
        "Center Left": [-0.3, 0],
        "Center": [0, 0],
        "Center Right": [0, 0.3],
        "Right": [0.3, 0.7],
        "Far Right": [0.7, 1.0]
    }
    
    # Count influencers in each bucket
    bucket_counts = {bucket: 0 for bucket in buckets}
    for result in results:
        position = result.get('ideology_spectrum_position')
        if position is not None:
            for bucket, [lower, upper] in buckets.items():
                if lower <= position <= upper:
                    bucket_counts[bucket] += result['count']
                    break
    
    # Display the results
    print("\nIdeological Distribution of Influencers:")
    print("-" * 40)
    
    # Create a simple ASCII chart
    max_count = max(bucket_counts.values()) if bucket_counts.values() else 0
    for bucket, count in bucket_counts.items():
        bar_length = int(count * 30 / max_count) if max_count > 0 else 0
        bar = "█" * bar_length
        print(f"{bucket:12}: {bar} ({count})")
    
    return bucket_counts

def search_by_affiliation(affiliation):
    """Find influencers with a specific political affiliation."""
    conn = connect_to_db()
    if not conn:
        return
    
    # Create a cursor with row factory
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Find the affiliation ID
    cursor.execute("SELECT id FROM affiliations WHERE name LIKE ?", (f'%{affiliation}%',))
    affiliation_ids = [row['id'] for row in cursor.fetchall()]
    
    if not affiliation_ids:
        print(f"No affiliation found matching '{affiliation}'")
        conn.close()
        return
    
    placeholders = ','.join(['?'] * len(affiliation_ids))
    
    # Find influencers with this affiliation
    cursor.execute(f"""
        SELECT i.id, i.name, c.name as category, i.twitter_handle,
               i.relevance_score, a.name as affiliation
        FROM influencers i
        LEFT JOIN categories c ON i.category_id = c.id
        JOIN influencer_affiliations ia ON i.id = ia.influencer_id
        JOIN affiliations a ON ia.affiliation_id = a.id
        WHERE ia.affiliation_id IN ({placeholders})
        ORDER BY i.relevance_score DESC
    """, affiliation_ids)
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    headers = ['id', 'name', 'category', 'twitter_handle', 'affiliation', 'relevance_score']
    print(f"\nInfluencers with affiliation matching '{affiliation}':")
    display_results(results, headers)
    
    return results

def export_to_json(output_file=None):
    """Export the entire database to a JSON file for AI training."""
    conn = connect_to_db()
    if not conn:
        return
    
    # Create a cursor with row factory
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all influencers with their details
    cursor.execute("""
        SELECT i.*, c.name as category 
        FROM influencers i
        LEFT JOIN categories c ON i.category_id = c.id
    """)
    
    influencers = [dict(row) for row in cursor.fetchall()]
    
    # For each influencer, get their affiliations and name variations
    for influencer in influencers:
        # Get affiliations
        cursor.execute("""
            SELECT a.name
            FROM influencer_affiliations ia
            JOIN affiliations a ON ia.affiliation_id = a.id
            WHERE ia.influencer_id = ?
        """, (influencer['id'],))
        
        influencer['affiliations'] = [row['name'] for row in cursor.fetchall()]
        
        # Get name variations
        cursor.execute("""
            SELECT variation
            FROM name_variations
            WHERE influencer_id = ?
        """, (influencer['id'],))
        
        influencer['name_variations'] = [row['variation'] for row in cursor.fetchall()]
    
    conn.close()
    
    # Set default filename if none provided
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(DATA_DIR, f"influencers_export_{timestamp}.json")
    
    # Save to JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(influencers, f, indent=2, ensure_ascii=False)
    
    print(f"\nExported {len(influencers)} influencers to {output_file}")
    return influencers

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Query the AI-Optimized Influencers Database')
    
    # Create command subparsers
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search for influencers by name')
    search_parser.add_argument('query', help='Name to search for')
    
    # Top influencers command
    top_parser = subparsers.add_parser('top', help='List top influencers')
    top_parser.add_argument('--category', '-c', help='Filter by category')
    top_parser.add_argument('--limit', '-l', type=int, default=10, help='Number of results')
    
    # Influencer details command
    details_parser = subparsers.add_parser('details', help='Get details about a specific influencer')
    details_parser.add_argument('id', type=int, help='Influencer ID')
    
    # Ideological distribution command
    subparsers.add_parser('ideology', help='Get ideological distribution of influencers')
    
    # Search by affiliation command
    affiliation_parser = subparsers.add_parser('affiliation', help='Search by political affiliation')
    affiliation_parser.add_argument('affiliation', help='Affiliation to search for')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export the database to JSON')
    export_parser.add_argument('--output', '-o', help='Output file path')
    
    args = parser.parse_args()
    
    # If no command is provided, show all top influencers
    if not args.command:
        list_top_influencers()
        return
    
    # Execute the requested command
    if args.command == 'search':
        search_influencers(args.query, args.limit)
    elif args.command == 'top':
        list_top_influencers(args.category, args.limit)
    elif args.command == 'details':
        get_influencer_details(args.id)
    elif args.command == 'ideology':
        get_ideological_distribution()
    elif args.command == 'affiliation':
        search_by_affiliation(args.affiliation)
    elif args.command == 'export':
        export_to_json(args.output)

if __name__ == "__main__":
    main() 