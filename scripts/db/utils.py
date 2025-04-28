#!/usr/bin/env python3
"""
Database Utility Functions

This script provides common utility functions for database operations:
1. Statistical queries and reporting
2. Database health checks
3. Simple CLI for querying entities
4. Database backup and maintenance
"""
import os
import sys
import json
import logging
import argparse
import sqlite3
import shutil
from datetime import datetime, timedelta
from tabulate import tabulate
from pathlib import Path

# Add parent directory to path to import database_manager
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(PROJECT_ROOT)

# Import our database manager
from scripts.db.database_manager import DatabaseManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Database path
DB_PATH = os.path.join(PROJECT_ROOT, 'maga_ops.db')

def backup_database(backup_dir=None):
    """Create a backup of the database."""
    if not backup_dir:
        backup_dir = os.path.join(PROJECT_ROOT, 'backups')
    
    # Create backup directory if it doesn't exist
    os.makedirs(backup_dir, exist_ok=True)
    
    # Generate backup filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(backup_dir, f'maga_ops_{timestamp}.db')
    
    # Check if database exists
    if not os.path.exists(DB_PATH):
        logger.error(f"Database file not found at {DB_PATH}")
        return False
    
    # Create backup
    try:
        shutil.copy2(DB_PATH, backup_file)
        logger.info(f"Database backup created at {backup_file}")
        return True
    except Exception as e:
        logger.error(f"Error creating database backup: {str(e)}")
        return False

def database_stats():
    """Get database statistics."""
    db = DatabaseManager()
    
    stats = {
        'database_size_mb': os.path.getsize(DB_PATH) / (1024 * 1024),
        'entities': {
            'total': db.get_entity_count(),
            'politicians': db.get_entity_count('politician'),
            'influencers': db.get_entity_count('influencer'),
            'organizations': db.get_entity_count('organization')
        },
        'categories': {},
        'connections': 0,
        'last_updated': ''
    }
    
    # Get categories count by type
    categories = db.get_categories()
    category_counts = {}
    for category in categories:
        cat_type = category['category_type']
        if cat_type not in category_counts:
            category_counts[cat_type] = 0
        category_counts[cat_type] += 1
    
    stats['categories'] = category_counts
    
    # Get connections count - use direct SQL since there's no method for this
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM entity_connections")
        result = cursor.fetchone()
        stats['connections'] = result['count'] if result else 0
        
        # Get last updated date
        cursor.execute("SELECT MAX(last_updated) as last_updated FROM entities")
        result = cursor.fetchone()
        stats['last_updated'] = result['last_updated'] if result and result['last_updated'] else ''
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
    finally:
        if conn:
            conn.close()
    
    return stats

def print_stats():
    """Print database statistics in a readable format."""
    stats = database_stats()
    
    print("\n=== MAGA_Ops Database Statistics ===\n")
    
    print(f"Database Size: {stats['database_size_mb']:.2f} MB")
    print(f"Last Updated: {stats['last_updated']}")
    
    print("\nEntity Counts:")
    entity_table = [
        ["Total", stats['entities']['total']],
        ["Politicians", stats['entities']['politicians']],
        ["Influencers", stats['entities']['influencers']],
        ["Organizations", stats['entities']['organizations']]
    ]
    print(tabulate(entity_table, tablefmt="simple"))
    
    print("\nCategory Counts:")
    category_table = [
        [cat_type, count] for cat_type, count in stats['categories'].items()
    ]
    print(tabulate(category_table, headers=["Category Type", "Count"], tablefmt="simple"))
    
    print(f"\nTotal Connections: {stats['connections']}")
    print("\n" + "="*40 + "\n")

def search_entities(query, entity_type=None, limit=10):
    """Search for entities and print results."""
    db = DatabaseManager()
    results = db.search_entities(query, entity_type=entity_type, limit=limit)
    
    if not results:
        print(f"No entities found matching '{query}'")
        return
    
    print(f"\nFound {len(results)} entities matching '{query}':\n")
    
    # Create a table for better display
    table_data = []
    for entity in results:
        # Extract ideologies from categories if present
        ideologies = ""
        if 'categories' in entity and 'ideology' in entity['categories']:
            ideologies = ", ".join([cat['name'] for cat in entity['categories']['ideology']])
        
        # Get party from categories or direct field
        party = entity.get('party', '')
        if not party and 'categories' in entity and 'party' in entity['categories']:
            party = ", ".join([cat['name'] for cat in entity['categories']['party']])
        
        table_data.append([
            entity['id'],
            entity['name'],
            entity['entity_type'],
            party,
            ideologies[:30] + ('...' if ideologies and len(ideologies) > 30 else '')
        ])
    
    headers = ["ID", "Name", "Type", "Party", "Ideologies"]
    print(tabulate(table_data, headers=headers, tablefmt="simple"))

def display_entity(entity_id):
    """Display detailed information about an entity."""
    db = DatabaseManager()
    entity = db.get_entity(entity_id)
    
    if not entity:
        print(f"No entity found with ID {entity_id}")
        return
    
    print("\n" + "="*50)
    print(f"Entity: {entity['name']} (ID: {entity['id']})")
    print("="*50)
    
    # Basic information
    print(f"Type: {entity['entity_type']}")
    print(f"Bio: {entity.get('bio', 'N/A')}")
    
    # Social media
    social_media = []
    if entity.get('twitter_handle'):
        social_media.append(f"Twitter: @{entity['twitter_handle']}")
    if entity.get('instagram_handle'):
        social_media.append(f"Instagram: @{entity['instagram_handle']}")
    if entity.get('facebook_url'):
        social_media.append(f"Facebook: {entity['facebook_url']}")
    if entity.get('website_url'):
        social_media.append(f"Website: {entity['website_url']}")
    
    if social_media:
        print("\nSocial Media:")
        for sm in social_media:
            print(f"- {sm}")
    
    # Categories
    if 'categories' in entity:
        print("\nCategories:")
        for cat_type, categories in entity['categories'].items():
            print(f"\n{cat_type.title()}:")
            for cat in categories:
                confidence = cat.get('confidence', 1.0)
                confidence_str = f" (confidence: {confidence:.2f})" if confidence < 1.0 else ""
                print(f"- {cat['name']}{confidence_str}")
    
    # Type-specific fields
    if entity['entity_type'] == 'politician':
        print("\nPolitician Details:")
        pol_fields = [
            ("Office", entity.get('office', 'N/A')),
            ("State", entity.get('state', 'N/A')),
            ("District", entity.get('district', 'N/A')),
            ("Election Year", entity.get('election_year', 'N/A')),
            ("Bioguide ID", entity.get('bioguide_id', 'N/A'))
        ]
        for label, value in pol_fields:
            print(f"- {label}: {value}")
    
    elif entity['entity_type'] == 'influencer':
        print("\nInfluencer Details:")
        inf_fields = [
            ("Platform", entity.get('platform', 'N/A')),
            ("Audience Size", entity.get('audience_size', 'N/A')),
            ("Content Focus", entity.get('content_focus', 'N/A')),
            ("Influence Score", entity.get('influence_score', 'N/A'))
        ]
        for label, value in inf_fields:
            print(f"- {label}: {value}")
    
    # Related entities
    related = db.get_related_entities(entity_id, limit=5)
    if related:
        print("\nRelated Entities:")
        for rel in related:
            print(f"- {rel['name']} ({rel['entity_type']}): {rel.get('connection_type', 'connected')} (strength: {rel.get('strength', 1.0):.2f})")
    
    print("\n" + "="*50)

def vacuum_database():
    """Run VACUUM command on the database to optimize size and performance."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("VACUUM")
        conn.close()
        logger.info("Database vacuumed successfully")
        return True
    except Exception as e:
        logger.error(f"Error vacuuming database: {str(e)}")
        return False

def check_database_integrity():
    """Check the integrity of the database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()[0]
        conn.close()
        
        if result == "ok":
            logger.info("Database integrity check passed")
            return True
        else:
            logger.error(f"Database integrity check failed: {result}")
            return False
    except Exception as e:
        logger.error(f"Error checking database integrity: {str(e)}")
        return False

def show_entity_completeness(entity_id):
    """Show completeness analysis for an entity."""
    db = DatabaseManager()
    completeness = db.get_entity_completeness(entity_id)
    
    if not completeness:
        print(f"No entity found with ID {entity_id}")
        return
    
    entity = db.get_entity(entity_id)
    
    print("\n" + "="*50)
    print(f"Data Completeness Report: {entity['name']} (ID: {entity_id})")
    print("="*50)
    
    # Total fields
    total_fields = 7  # Basic fields we're tracking
    missing_fields = completeness['missing_bio'] + completeness['missing_twitter'] + \
                     completeness['missing_website'] + completeness['missing_image'] + \
                     completeness['missing_positions'] + completeness['missing_affiliations'] + \
                     completeness['missing_location']
    
    completeness_pct = ((total_fields - missing_fields) / total_fields) * 100
    
    print(f"Profile Completeness: {completeness_pct:.1f}%")
    print(f"Missing Fields: {missing_fields} of {total_fields}")
    
    # Fields status
    fields_status = [
        ["Biography", "Missing" if completeness['missing_bio'] else "Present"],
        ["Twitter", "Missing" if completeness['missing_twitter'] else "Present"],
        ["Website", "Missing" if completeness['missing_website'] else "Present"],
        ["Image", "Missing" if completeness['missing_image'] else "Present"],
        ["Positions", "Missing" if completeness['missing_positions'] else "Present"],
        ["Affiliations", "Missing" if completeness['missing_affiliations'] else "Present"],
        ["Location", "Missing" if completeness['missing_location'] else "Present"]
    ]
    
    print("\nField Status:")
    print(tabulate(fields_status, headers=["Field", "Status"], tablefmt="simple"))
    
    # Relationship data
    print("\nRelationship Data:")
    print(f"Categories: {completeness['category_count']}")
    print(f"Connections: {completeness['connection_count']}")
    if entity['entity_type'] == 'politician':
        print(f"Voting Records: {completeness['vote_count']}")
    
    # AI Metadata
    ai_metadata = db.get_ai_metadata(entity_id)
    if ai_metadata:
        print("\nAI-Generated Metadata:")
        metadata_table = []
        for meta in ai_metadata:
            verified = "✓" if meta['verified'] else "❌"
            confidence = f"{meta['confidence_score']*100:.1f}%" if meta['confidence_score'] else "N/A"
            metadata_table.append([
                meta['field_name'],
                meta['field_value'][:30] + ('...' if meta['field_value'] and len(meta['field_value']) > 30 else ''),
                confidence,
                verified,
                meta['extraction_date'][:10]
            ])
        
        print(tabulate(metadata_table, 
                     headers=["Field", "Value", "Confidence", "Verified", "Date"], 
                     tablefmt="simple"))
    
    print("\n" + "="*50)

def show_enrichment_priorities(entity_type=None, limit=10):
    """Show entities that need data enrichment, prioritized by gaps."""
    db = DatabaseManager()
    priorities = db.get_enrichment_priorities(entity_type, limit)
    
    if not priorities:
        print("No entities found needing enrichment")
        return
    
    print("\n" + "="*50)
    print(f"Data Enrichment Priorities" + (f" for {entity_type}s" if entity_type else ""))
    print("="*50)
    
    priority_table = []
    for p in priorities:
        priority_table.append([
            p['id'],
            p['name'],
            p['entity_type'],
            p['missing_field_count'],
            p['category_count'],
            p['connection_count'],
            f"{p['priority_score']:.1f}"
        ])
    
    headers = ["ID", "Name", "Type", "Missing Fields", "Categories", "Connections", "Priority Score"]
    print(tabulate(priority_table, headers=headers, tablefmt="simple"))
    print("\nNote: Higher priority score = needs more attention")
    
    print("\n" + "="*50)

def show_entity_connections(entity_id, include_evidence=False):
    """Show connections for an entity with optional evidence details."""
    db = DatabaseManager()
    entity = db.get_entity(entity_id)
    
    if not entity:
        print(f"No entity found with ID {entity_id}")
        return
    
    connections = db.get_related_entities(entity_id, limit=100)
    
    if not connections:
        print(f"No connections found for entity {entity['name']} (ID: {entity_id})")
        return
    
    print("\n" + "="*50)
    print(f"Connections for: {entity['name']} (ID: {entity_id})")
    print("="*50)
    
    # Create a table for connections
    conn_table = []
    for conn in connections:
        conn_table.append([
            conn['id'],
            conn['name'],
            conn['entity_type'],
            conn.get('connection_type', 'connected'),
            f"{conn.get('strength', 0.0):.2f}"
        ])
    
    headers = ["ID", "Name", "Type", "Relationship", "Strength (0-1)"]
    print(tabulate(conn_table, headers=headers, tablefmt="simple"))
    
    # If requested, show evidence for each connection
    if include_evidence and connections:
        print("\nEvidence for Connections:")
        print("-" * 40)
        
        for conn in connections:
            evidence = db.get_connection_evidence(conn['id'])
            if evidence:
                print(f"\nEvidence for connection with {conn['name']}:")
                evidence_table = []
                for e in evidence:
                    evidence_table.append([
                        e['evidence_type'],
                        e['description'][:50] + ('...' if e['description'] and len(e['description']) > 50 else ''),
                        f"{e['confidence_score']:.2f}",
                        e['source_url'][:30] if e['source_url'] else 'N/A'
                    ])
                print(tabulate(evidence_table, 
                             headers=["Type", "Description", "Confidence", "Source"], 
                             tablefmt="simple"))
    
    print("\n" + "="*50)

def show_donations(entity_id, as_donor=True, as_recipient=True, limit=10):
    """Show donation records for an entity, either as donor or recipient."""
    db = DatabaseManager()
    entity = db.get_entity(entity_id)
    
    if not entity:
        print(f"No entity found with ID {entity_id}")
        return
    
    print("\n" + "="*50)
    print(f"Donation Records for: {entity['name']} (ID: {entity_id})")
    print("="*50)
    
    if as_donor:
        donations_made = db.get_donations_by_donor(entity_id, limit=limit)
        if donations_made:
            print("\nDonations Made:")
            donation_table = []
            for d in donations_made:
                donation_table.append([
                    d['recipient_name'],
                    d['recipient_type'],
                    f"${d['amount']:,.2f}",
                    d['donation_date'],
                    d['donation_type'] or 'N/A'
                ])
            print(tabulate(donation_table, 
                         headers=["Recipient", "Type", "Amount", "Date", "Type"], 
                         tablefmt="simple"))
        else:
            print("\nNo donations made by this entity.")
    
    if as_recipient:
        donations_received = db.get_donations_by_recipient(entity_id, limit=limit)
        if donations_received:
            print("\nDonations Received:")
            donation_table = []
            for d in donations_received:
                donation_table.append([
                    d['donor_name'],
                    d['donor_type'],
                    f"${d['amount']:,.2f}",
                    d['donation_date'],
                    d['donation_type'] or 'N/A'
                ])
            print(tabulate(donation_table, 
                         headers=["Donor", "Type", "Amount", "Date", "Type"], 
                         tablefmt="simple"))
        else:
            print("\nNo donations received by this entity.")
    
    print("\n" + "="*50)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Database Utility Functions")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show database statistics")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search for entities")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--type", "-t", choices=["politician", "influencer", "organization"], 
                             help="Filter by entity type")
    search_parser.add_argument("--limit", "-l", type=int, default=10, help="Maximum results to return")
    
    # Display entity command
    entity_parser = subparsers.add_parser("entity", help="Display entity details")
    entity_parser.add_argument("id", type=int, help="Entity ID")
    
    # Backup command
    backup_parser = subparsers.add_parser("backup", help="Create database backup")
    backup_parser.add_argument("--dir", "-d", help="Backup directory (default: PROJECT_ROOT/backups)")
    
    # Vacuum command
    vacuum_parser = subparsers.add_parser("vacuum", help="Vacuum database to optimize size and performance")
    
    # Check integrity command
    integrity_parser = subparsers.add_parser("check", help="Check database integrity")
    
    # New commands
    completeness_parser = subparsers.add_parser("completeness", help="Show entity data completeness")
    completeness_parser.add_argument("id", type=int, help="Entity ID")
    
    priorities_parser = subparsers.add_parser("priorities", help="Show entities needing data enrichment")
    priorities_parser.add_argument("--type", "-t", choices=["politician", "influencer", "organization"], 
                                 help="Filter by entity type")
    priorities_parser.add_argument("--limit", "-l", type=int, default=10, help="Maximum results to return")
    
    connections_parser = subparsers.add_parser("connections", help="Show entity connections")
    connections_parser.add_argument("id", type=int, help="Entity ID")
    connections_parser.add_argument("--evidence", "-e", action="store_true", 
                                  help="Include evidence details")
    
    donations_parser = subparsers.add_parser("donations", help="Show donation records")
    donations_parser.add_argument("id", type=int, help="Entity ID")
    donations_parser.add_argument("--donor", action="store_true", default=True,
                                help="Show donations made by this entity")
    donations_parser.add_argument("--recipient", action="store_true", default=True,
                                help="Show donations received by this entity")
    donations_parser.add_argument("--limit", "-l", type=int, default=10,
                                help="Maximum donations to show")
    
    return parser.parse_args()

def main():
    """Main function."""
    args = parse_args()
    
    if args.command == "stats":
        print_stats()
    
    elif args.command == "search":
        search_entities(args.query, entity_type=args.type, limit=args.limit)
    
    elif args.command == "entity":
        display_entity(args.id)
    
    elif args.command == "backup":
        backup_database(backup_dir=args.dir)
    
    elif args.command == "vacuum":
        vacuum_database()
    
    elif args.command == "check":
        check_database_integrity()
    
    # New commands
    elif args.command == "completeness":
        show_entity_completeness(args.id)
    
    elif args.command == "priorities":
        show_enrichment_priorities(entity_type=args.type, limit=args.limit)
    
    elif args.command == "connections":
        show_entity_connections(args.id, include_evidence=args.evidence)
    
    elif args.command == "donations":
        show_donations(args.id, as_donor=args.donor, as_recipient=args.recipient, limit=args.limit)
    
    else:
        print("Please specify a command. Use --help for available commands.")

if __name__ == "__main__":
    main() 