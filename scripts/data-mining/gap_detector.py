#!/usr/bin/env python3
"""
Gap Detector Script

Generates a report of missing or stale data based on view_entity_gaps,
ai_metadata low confidence, and entity_connections evidence.
"""
import os
import sys
import json
import logging
from datetime import datetime, timedelta

# Add project root to path to import DatabaseManager
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(PROJECT_ROOT)
from scripts.db.database_manager import DatabaseManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Default thresholds (can be overridden by env vars)
AI_CONF_THRESHOLD = float(os.getenv('AI_CONFIDENCE_THRESHOLD', 0.8))
STALE_REL_DAYS = int(os.getenv('STALE_RELATIONSHIP_DAYS', 180))

OUTPUT_FILE = os.getenv('GAP_REPORT_FILE', 'gap_report.json')


def main():
    logger.info('Starting gap detection run')
    db = DatabaseManager()

    report = {
        'timestamp': datetime.utcnow().isoformat(),
        'entity_gaps': {},
        'relationship_gaps': {
            'missing_evidence': [],
            'weak_relationships': [],
            'stale_relationships': []
        },
        'low_confidence_ai_metadata': []
    }

    # 1. Entity gaps from view_entity_gaps
    rows = db.execute_query('SELECT * FROM view_entity_gaps') or []
    for r in rows:
        eid = r['id']
        # missing fields
        for field in ['missing_bio', 'missing_twitter', 'missing_website',
                      'missing_image', 'missing_positions', 'missing_affiliations', 'missing_location']:
            if r.get(field):
                report['entity_gaps'].setdefault(field, []).append(eid)
        # missing categories
        if r.get('category_count', 0) == 0:
            report['entity_gaps'].setdefault('missing_categories', []).append(eid)
        # missing connections
        if r.get('connection_count', 0) == 0:
            report['entity_gaps'].setdefault('missing_connections', []).append(eid)
        # missing votes for politicians
        if r.get('entity_type') == 'politician' and r.get('vote_count', 0) == 0:
            report['entity_gaps'].setdefault('missing_votes', []).append(eid)

    # 2. Low-confidence AI metadata
    metas = db.execute_query('SELECT * FROM ai_metadata') or []
    for m in metas:
        if m.get('confidence_score', 0) < AI_CONF_THRESHOLD:
            report['low_confidence_ai_metadata'].append(m['id'])

    # 3. Relationship gaps
    # a) missing evidence
    conns = db.execute_query('SELECT id, last_updated, strength FROM entity_connections') or []
    now = datetime.utcnow()
    for conn in conns:
        cid = conn['id']
        evidence = db.get_connection_evidence(cid) or []
        if not evidence:
            report['relationship_gaps']['missing_evidence'].append(cid)
        # weak relationship (strength < 0.5)
        if conn.get('strength', 0) < 0.5:
            report['relationship_gaps']['weak_relationships'].append(cid)
        # stale relationship
        try:
            lu = datetime.fromisoformat(conn.get('last_updated'))
            if now - lu > timedelta(days=STALE_REL_DAYS):
                report['relationship_gaps']['stale_relationships'].append(cid)
        except Exception:
            pass

    # Write report
    with open(OUTPUT_FILE, 'w') as outf:
        json.dump(report, outf, indent=2)
    logger.info(f'Gap report written to {OUTPUT_FILE}')


if __name__ == '__main__':
    main() 