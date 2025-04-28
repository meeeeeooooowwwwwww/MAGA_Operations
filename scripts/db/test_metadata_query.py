#!/usr/bin/env python3
"""
Test AI Metadata Queries

This script tests various metadata query functions in the database_manager module.
"""
import os
import sys
import logging
import json
from tabulate import tabulate

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

def print_section(title):
    """Print a section title."""
    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)

def print_query_results(results, title=None):
    """Print query results in a tabulated format."""
    if not results:
        print("No results found.")
        return
    
    if title:
        print(f"\n{title}")
    
    if isinstance(results, list) and results and isinstance(results[0], dict):
        # Extract headers from first result
        headers = results[0].keys()
        # Extract rows
        rows = [list(result.values()) for result in results]
        print(tabulate(rows, headers=headers, tablefmt="simple"))
    else:
        print(json.dumps(results, indent=2))

def test_ai_metadata_queries(db):
    """Test AI metadata queries."""
    print_section("AI Metadata Tests")
    
    # Get all metadata for entity
    entity_id = 13  # Trump
    metadata = db.get_all_ai_metadata(entity_id)
    print_query_results(metadata, f"All AI metadata for entity ID {entity_id}")
    
    # Get specific metadata field
    field_name = "ideology_analysis"
    metadata = db.get_ai_metadata(entity_id, field_name)
    print_query_results(metadata, f"'{field_name}' metadata for entity ID {entity_id}")
    
    # Get verified metadata only
    verified_metadata = db.get_all_ai_metadata(entity_id, verified_only=True)
    print_query_results(verified_metadata, f"Verified AI metadata for entity ID {entity_id}")
    
    # Get metadata by source
    source = "Claude-3.5"
    source_metadata = db.get_ai_metadata_by_source(source)
    print_query_results(source_metadata, f"AI metadata from source '{source}'")
    
    # Get high confidence metadata
    min_confidence = 0.85
    high_confidence_metadata = db.get_high_confidence_metadata(min_confidence)
    print_query_results(high_confidence_metadata, f"AI metadata with confidence >= {min_confidence}")

def test_connection_evidence_queries(db):
    """Test connection evidence queries."""
    print_section("Connection Evidence Tests")
    
    # Get all evidence for a connection
    connection_id = 2  # Example connection ID
    evidence = db.get_connection_evidence(connection_id)
    print_query_results(evidence, f"Evidence for connection ID {connection_id}")
    
    # Get all evidence by type
    evidence_type = "video_content"
    type_evidence = db.get_evidence_by_type(evidence_type)
    print_query_results(type_evidence, f"Evidence of type '{evidence_type}'")
    
    # Get high confidence evidence
    min_confidence = 0.9
    high_confidence_evidence = db.get_high_confidence_evidence(min_confidence)
    print_query_results(high_confidence_evidence, f"Evidence with confidence >= {min_confidence}")

def test_donation_queries(db):
    """Test donation record queries."""
    print_section("Donation Record Tests")
    
    # Get donations by donor
    donor_id = 19  # MAGA Patriots Coalition
    donations_by_donor = db.get_donations_by_donor(donor_id)
    print_query_results(donations_by_donor, f"Donations from entity ID {donor_id}")
    
    # Get donations by recipient
    recipient_id = 13  # Trump
    donations_by_recipient = db.get_donations_by_recipient(recipient_id)
    print_query_results(donations_by_recipient, f"Donations to entity ID {recipient_id}")
    
    # Get donations by type
    donation_type = "pac"
    donations_by_type = db.get_donations_by_type(donation_type)
    print_query_results(donations_by_type, f"Donations of type '{donation_type}'")
    
    # Get large donations
    min_amount = 20000.0
    large_donations = db.get_large_donations(min_amount)
    print_query_results(large_donations, f"Donations >= ${min_amount}")
    
    # Get recent donations
    recent_donations = db.get_recent_donations("2023-07-01")
    print_query_results(recent_donations, f"Donations since 2023-07-01")

def test_entity_enrichment(db):
    """Test entity enrichment methods."""
    print_section("Entity Enrichment Tests")
    
    # Get entity with enriched metadata
    entity_id = 13  # Trump
    entity = db.get_entity_with_metadata(entity_id)
    print(f"\nEntity {entity_id} with metadata:")
    print(json.dumps(entity, indent=2))
    
    # Get entity with connections and evidence
    entity_with_connections = db.get_entity_with_connections(entity_id, include_evidence=True)
    print(f"\nEntity {entity_id} with connections and evidence:")
    print(json.dumps(entity_with_connections, indent=2))
    
    # Get entity with donation information
    entity_with_donations = db.get_entity_with_donations(entity_id)
    print(f"\nEntity {entity_id} with donation information:")
    print(json.dumps(entity_with_donations, indent=2))

def main():
    """Main function."""
    db = DatabaseManager()
    logger.info("Testing metadata queries...")
    
    # Run all test functions
    test_ai_metadata_queries(db)
    test_connection_evidence_queries(db)
    test_donation_queries(db)
    test_entity_enrichment(db)
    
    logger.info("Metadata query tests complete!")

if __name__ == "__main__":
    main() 