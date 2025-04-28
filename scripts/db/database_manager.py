import sqlite3
import os
import logging
from datetime import datetime
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
DB_PATH = os.path.join(PROJECT_ROOT, 'maga_ops.db')

class DatabaseManager:
    """Handles SQLite database interactions for the new normalized schema."""

    def __init__(self, db_path=DB_PATH):
        """Initialize the database manager with the path to the SQLite DB."""
        self.db_path = db_path
        logger.info(f"DatabaseManager initialized with path: {self.db_path}")
        
        # Basic check on startup
        if not os.path.exists(self.db_path):
            logger.warning(f"Database file not found at {self.db_path}. Queries will fail until created.")
    
    def _get_connection(self):
        """Create and return a database connection with Row factory."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            logger.error(f"Error connecting to database: {e}")
            raise
    
    def execute_query(self, query, params=(), fetch_all=True, commit=False):
        """Execute a SQL query and return results."""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            if commit:
                conn.commit()
                return cursor.lastrowid if cursor.lastrowid else True
            
            if fetch_all:
                results = cursor.fetchall()
                return [dict(row) for row in results]
            else:
                result = cursor.fetchone()
                return dict(result) if result else None
                
        except sqlite3.Error as e:
            logger.error(f"Database error executing query: {e}")
            if commit and conn:
                conn.rollback()
            return None if fetch_all else None
        finally:
            if conn:
                conn.close()
    
    # ======== Entity Search Methods ========
    
    def search_entities(self, query, entity_type=None, category=None, limit=50):
        """
        Search for entities by name, bio, or categories.
        
        Args:
            query: The search term
            entity_type: Optional filter by entity type (politician, influencer)
            category: Optional filter by category ID or code
            limit: Maximum results to return
            
        Returns:
            List of matching entity dictionaries
        """
        search_pattern = f"%{query}%"
        
        # Base query using the entity profiles view for simplicity
        sql = """
        SELECT * FROM view_entity_profiles
        WHERE (name LIKE ? OR normalized_name LIKE ? OR bio LIKE ?)
        """
        
        params = [search_pattern, search_pattern, search_pattern]
        
        # Add entity type filter if specified
        if entity_type:
            sql += " AND entity_type = ?"
            params.append(entity_type)
        
        # Add category filter if specified
        if category:
            if isinstance(category, int) or category.isdigit():
                # Filter by category ID
                sql = """
                SELECT v.* FROM view_entity_profiles v
                JOIN entity_categories ec ON v.id = ec.entity_id
                WHERE (v.name LIKE ? OR v.normalized_name LIKE ? OR v.bio LIKE ?)
                """
                if entity_type:
                    sql += " AND v.entity_type = ?"
                
                sql += " AND ec.category_id = ?"
                params.append(int(category))
            else:
                # Filter by category code (more complex)
                sql = """
                SELECT v.* FROM view_entity_profiles v
                JOIN entity_categories ec ON v.id = ec.entity_id
                JOIN categories c ON ec.category_id = c.id
                WHERE (v.name LIKE ? OR v.normalized_name LIKE ? OR v.bio LIKE ?)
                """
                if entity_type:
                    sql += " AND v.entity_type = ?"
                
                sql += " AND c.code = ?"
                params.append(category)
        
        # Add order and limit
        sql += " ORDER BY relevance_score DESC, name LIMIT ?"
        params.append(limit)
        
        return self.execute_query(sql, params)
    
    def get_entity(self, entity_id):
        """Get complete entity details by ID."""
        # First get basic entity info
        sql = "SELECT * FROM entities WHERE id = ?"
        entity = self.execute_query(sql, (entity_id,), fetch_all=False)
        
        if not entity:
            return None
        
        # Get entity-specific details based on type
        if entity['entity_type'] == 'politician':
            sql = "SELECT * FROM politicians WHERE entity_id = ?"
            politician_data = self.execute_query(sql, (entity_id,), fetch_all=False)
            if politician_data:
                entity.update(politician_data)
        
        elif entity['entity_type'] == 'influencer':
            sql = "SELECT * FROM influencers WHERE entity_id = ?"
            influencer_data = self.execute_query(sql, (entity_id,), fetch_all=False)
            if influencer_data:
                entity.update(influencer_data)
        
        # Get categories
        sql = """
        SELECT c.id, c.code, c.name, c.description, ct.name as category_type, ec.confidence_score
        FROM entity_categories ec
        JOIN categories c ON ec.category_id = c.id
        JOIN category_types ct ON c.category_type_id = ct.id
        WHERE ec.entity_id = ?
        """
        categories = self.execute_query(sql, (entity_id,))
        
        # Organize categories by type
        categorized = {}
        for cat in categories:
            cat_type = cat['category_type']
            if cat_type not in categorized:
                categorized[cat_type] = []
            categorized[cat_type].append({
                'id': cat['id'],
                'code': cat['code'],
                'name': cat['name'],
                'description': cat['description'],
                'confidence': cat['confidence_score']
            })
        
        entity['categories'] = categorized
        
        return entity
    
    def get_entity_by_name(self, name):
        """Get entity by name (exact match)."""
        sql = "SELECT id FROM entities WHERE normalized_name = ? LIMIT 1"
        result = self.execute_query(sql, (name.lower(),), fetch_all=False)
        if result:
            return self.get_entity(result['id'])
        return None
    
    # ======== Entity Field Methods ========
    
    def get_entity_field(self, entity_type, entity_id, field):
        """Get a specific field for an entity."""
        # Check if field exists in base entity table
        base_fields = ['name', 'normalized_name', 'bio', 'twitter_handle', 
                      'instagram_handle', 'facebook_url', 'website_url']
        
        if field in base_fields:
            sql = f"SELECT {field} FROM entities WHERE id = ?"
            result = self.execute_query(sql, (entity_id,), fetch_all=False)
            return result[field] if result else None
        
        # Type-specific fields
        if entity_type == 'politician':
            politician_fields = ['office', 'state', 'district', 'election_year', 'bioguide_id']
            if field in politician_fields:
                sql = f"SELECT {field} FROM politicians WHERE entity_id = ?"
                result = self.execute_query(sql, (entity_id,), fetch_all=False)
                return result[field] if result else None
        
        elif entity_type == 'influencer':
            influencer_fields = ['platform', 'audience_size', 'content_focus', 'influence_score']
            if field in influencer_fields:
                sql = f"SELECT {field} FROM influencers WHERE entity_id = ?"
                result = self.execute_query(sql, (entity_id,), fetch_all=False)
                return result[field] if result else None
        
        # Special fields that require joining
        if field == 'categories':
            sql = """
            SELECT c.id, c.code, c.name, c.description, ct.name as category_type
            FROM entity_categories ec
            JOIN categories c ON ec.category_id = c.id
            JOIN category_types ct ON c.category_type_id = ct.id
            WHERE ec.entity_id = ?
            """
            return self.execute_query(sql, (entity_id,))
        
        if field == 'party':
            sql = """
            SELECT c.code, c.name
            FROM entity_categories ec
            JOIN categories c ON ec.category_id = c.id
            JOIN category_types ct ON c.category_type_id = ct.id
            WHERE ec.entity_id = ? AND ct.name = 'party'
            LIMIT 1
            """
            result = self.execute_query(sql, (entity_id,), fetch_all=False)
            return result['name'] if result else None
        
        # Field not found
        logger.warning(f"Field '{field}' not recognized for {entity_type} with ID {entity_id}")
        return None
    
    def update_entity_field(self, entity_type, entity_id, field, value):
        """Update a specific field for an entity."""
        # Serialize data if necessary
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        
        # Check if field exists in base entity table
        base_fields = ['name', 'normalized_name', 'bio', 'twitter_handle', 
                      'instagram_handle', 'facebook_url', 'website_url', 'relevance_score']
        
        if field in base_fields:
            sql = f"UPDATE entities SET {field} = ?, last_updated = ? WHERE id = ?"
            return self.execute_query(sql, (value, datetime.now().isoformat(), entity_id), commit=True)
        
        # Type-specific fields
        if entity_type == 'politician':
            politician_fields = ['office', 'state', 'district', 'election_year', 'bioguide_id']
            if field in politician_fields:
                sql = f"UPDATE politicians SET {field} = ? WHERE entity_id = ?"
                return self.execute_query(sql, (value, entity_id), commit=True)
        
        elif entity_type == 'influencer':
            influencer_fields = ['platform', 'audience_size', 'content_focus', 'influence_score']
            if field in influencer_fields:
                sql = f"UPDATE influencers SET {field} = ? WHERE entity_id = ?"
                return self.execute_query(sql, (value, entity_id), commit=True)
        
        # Special case: adding/updating a category
        if field.startswith('category_'):
            category_type = field.replace('category_', '')
            return self._update_entity_category(entity_id, category_type, value)
        
        # Field not found
        logger.warning(f"Field '{field}' not recognized for {entity_type} with ID {entity_id}")
        return False
    
    def _update_entity_category(self, entity_id, category_type, category_value):
        """Update an entity's category of the specified type."""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get category type ID
            cursor.execute("SELECT id FROM category_types WHERE name = ?", (category_type,))
            type_result = cursor.fetchone()
            
            if not type_result:
                logger.error(f"Category type '{category_type}' not found")
                return False
            
            category_type_id = type_result['id']
            
            # Find if this type allows multiple values
            cursor.execute("SELECT is_multiple FROM category_types WHERE id = ?", (category_type_id,))
            is_multiple = cursor.fetchone()['is_multiple']
            
            # Get category ID
            if isinstance(category_value, int):
                # Direct category ID
                category_id = category_value
                cursor.execute("SELECT id FROM categories WHERE id = ? AND category_type_id = ?", 
                               (category_id, category_type_id))
                if not cursor.fetchone():
                    logger.error(f"Category ID {category_id} not found for type {category_type}")
                    return False
            else:
                # Code or name lookup
                cursor.execute("""
                    SELECT id FROM categories 
                    WHERE (code = ? OR name = ?) AND category_type_id = ?
                """, (category_value, category_value, category_type_id))
                result = cursor.fetchone()
                if not result:
                    logger.error(f"Category '{category_value}' not found for type {category_type}")
                    return False
                category_id = result['id']
            
            # If not multiple, remove existing categories of this type
            if not is_multiple:
                cursor.execute("""
                    DELETE FROM entity_categories 
                    WHERE entity_id = ? AND category_id IN (
                        SELECT id FROM categories WHERE category_type_id = ?
                    )
                """, (entity_id, category_type_id))
            
            # Add new category
            cursor.execute("""
                INSERT OR REPLACE INTO entity_categories (entity_id, category_id, source) 
                VALUES (?, ?, 'api_update')
            """, (entity_id, category_id))
            
            conn.commit()
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Database error updating category: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    # ======== Category Methods ========
    
    def get_categories(self, category_type=None):
        """Get all categories, optionally filtered by type."""
        if category_type:
            sql = """
            SELECT c.* 
            FROM categories c
            JOIN category_types ct ON c.category_type_id = ct.id
            WHERE ct.name = ?
            ORDER BY c.display_order, c.name
            """
            return self.execute_query(sql, (category_type,))
        else:
            sql = """
            SELECT c.*, ct.name as category_type 
            FROM categories c
            JOIN category_types ct ON c.category_type_id = ct.id
            ORDER BY ct.name, c.display_order, c.name
            """
            return self.execute_query(sql)
    
    def add_category(self, category_type, code, name, description=None):
        """Add a new category."""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get category type ID
            cursor.execute("SELECT id FROM category_types WHERE name = ?", (category_type,))
            result = cursor.fetchone()
            
            if not result:
                logger.error(f"Category type '{category_type}' not found")
                return False
            
            category_type_id = result['id']
            
            # Insert new category
            cursor.execute("""
                INSERT INTO categories (category_type_id, code, name, description)
                VALUES (?, ?, ?, ?)
            """, (category_type_id, code, name, description))
            
            conn.commit()
            return cursor.lastrowid
            
        except sqlite3.Error as e:
            logger.error(f"Database error adding category: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    # ======== Related Entity Methods ========
    
    def get_related_entities(self, entity_id, relationship_type=None, limit=10):
        """Get entities related to the specified entity."""
        if relationship_type:
            sql = """
            SELECT e.id, e.name, e.entity_type, ec.connection_type, ec.strength
            FROM entity_connections ec
            JOIN entities e ON (ec.entity2_id = e.id AND ec.entity1_id = ?)
                           OR (ec.entity1_id = e.id AND ec.entity2_id = ?)
            WHERE ec.connection_type = ?
            ORDER BY ec.strength DESC
            LIMIT ?
            """
            return self.execute_query(sql, (entity_id, entity_id, relationship_type, limit))
        else:
            sql = """
            SELECT e.id, e.name, e.entity_type, ec.connection_type, ec.strength
            FROM entity_connections ec
            JOIN entities e ON (ec.entity2_id = e.id AND ec.entity1_id = ?)
                           OR (ec.entity1_id = e.id AND ec.entity2_id = ?)
            ORDER BY ec.strength DESC
            LIMIT ?
            """
            return self.execute_query(sql, (entity_id, entity_id, limit))
    
    def get_entities_by_category(self, category, entity_type=None, limit=50):
        """Get entities with the specified category."""
        if isinstance(category, int) or (isinstance(category, str) and category.isdigit()):
            # Direct category ID
            category_id = int(category)
            sql = """
            SELECT e.* FROM entities e
            JOIN entity_categories ec ON e.id = ec.entity_id
            WHERE ec.category_id = ?
            """
            params = [category_id]
        else:
            # Category code or name
            sql = """
            SELECT e.* FROM entities e
            JOIN entity_categories ec ON e.id = ec.entity_id
            JOIN categories c ON ec.category_id = c.id
            WHERE c.code = ? OR c.name = ?
            """
            params = [category, category]
        
        # Add entity type filter if specified
        if entity_type:
            sql += " AND e.entity_type = ?"
            params.append(entity_type)
        
        # Add order and limit
        sql += " ORDER BY e.relevance_score DESC, e.name LIMIT ?"
        params.append(limit)
        
        return self.execute_query(sql, params)
    
    # ======== Social Post Methods ========
    
    def add_social_post(self, entity_id, platform, post_id, content, posted_at, engagement_count=0):
        """Add or update a social media post."""
        sql = """
        INSERT OR REPLACE INTO social_posts 
        (entity_id, platform, post_id, content, posted_at, engagement_count)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        return self.execute_query(sql, (
            entity_id, platform, post_id, content, posted_at, engagement_count
        ), commit=True)
    
    def get_social_posts(self, entity_id, platform=None, limit=10):
        """Get recent social posts for an entity."""
        if platform:
            sql = """
            SELECT * FROM social_posts
            WHERE entity_id = ? AND platform = ?
            ORDER BY posted_at DESC
            LIMIT ?
            """
            return self.execute_query(sql, (entity_id, platform, limit))
        else:
            sql = """
            SELECT * FROM social_posts
            WHERE entity_id = ?
            ORDER BY posted_at DESC
            LIMIT ?
            """
            return self.execute_query(sql, (entity_id, limit))
    
    def update_post_analysis(self, post_id, sentiment_score, analysis_data):
        """Update the AI analysis for a social post."""
        if isinstance(analysis_data, (dict, list)):
            analysis_data = json.dumps(analysis_data)
            
        sql = """
        UPDATE social_posts
        SET sentiment_score = ?, analysis_data = ?, ai_analyzed = 1
        WHERE id = ?
        """
        return self.execute_query(sql, (sentiment_score, analysis_data, post_id), commit=True)
    
    # ======== Voting Record Methods ========
    
    def add_voting_record(self, politician_id, vote_id, bill_id, bill_title, vote_date, 
                          vote_position, congress):
        """Add a voting record for a politician."""
        sql = """
        INSERT OR REPLACE INTO voting_records
        (politician_id, vote_id, bill_id, bill_title, vote_date, vote_position, congress)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        return self.execute_query(sql, (
            politician_id, vote_id, bill_id, bill_title, vote_date, vote_position, congress
        ), commit=True)
    
    def get_voting_records(self, politician_id, limit=20):
        """Get recent voting records for a politician."""
        sql = """
        SELECT * FROM voting_records
        WHERE politician_id = ?
        ORDER BY vote_date DESC
        LIMIT ?
        """
        return self.execute_query(sql, (politician_id, limit))
    
    # ======== Search History Methods ========
    
    def log_search(self, query, results_count):
        """Log a search query for analytics."""
        sql = """
        INSERT INTO search_history (query, timestamp, results_count)
        VALUES (?, ?, ?)
        """
        return self.execute_query(sql, (
            query, datetime.now().isoformat(), results_count
        ), commit=True)
    
    def get_top_searches(self, days=7, limit=10):
        """Get the most popular searches in the past days."""
        timeframe = datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        ).timestamp() - (days * 86400)
        
        sql = """
        SELECT query, COUNT(*) as count
        FROM search_history
        WHERE timestamp > datetime(?, 'unixepoch')
        GROUP BY query
        ORDER BY count DESC
        LIMIT ?
        """
        return self.execute_query(sql, (timeframe, limit))
    
    # ======== Utility Methods ========
    
    def get_entity_count(self, entity_type=None):
        """Get the count of entities, optionally filtered by type."""
        if entity_type:
            sql = "SELECT COUNT(*) as count FROM entities WHERE entity_type = ?"
            result = self.execute_query(sql, (entity_type,), fetch_all=False)
        else:
            sql = "SELECT COUNT(*) as count FROM entities"
            result = self.execute_query(sql, fetch_all=False)
        
        return result['count'] if result else 0
    
    # ======== AI Metadata Methods ========
    
    def add_ai_metadata(self, entity_id, field_name, field_value, confidence_score, source=None):
        """Add AI-generated metadata for an entity."""
        sql = """
        INSERT INTO ai_metadata
        (entity_id, field_name, field_value, confidence_score, source, extraction_date)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        return self.execute_query(sql, (
            entity_id, field_name, field_value, confidence_score, source, datetime.now().isoformat()
        ), commit=True)
    
    def get_ai_metadata(self, entity_id, field_name=None):
        """Get AI metadata for an entity, optionally filtered by field name."""
        if field_name:
            sql = """
            SELECT * FROM ai_metadata
            WHERE entity_id = ? AND field_name = ?
            ORDER BY confidence_score DESC, extraction_date DESC
            """
            return self.execute_query(sql, (entity_id, field_name))
        else:
            sql = """
            SELECT * FROM ai_metadata
            WHERE entity_id = ?
            ORDER BY field_name, confidence_score DESC
            """
            return self.execute_query(sql, (entity_id,))
    
    def mark_ai_metadata_verified(self, metadata_id, verified=True):
        """Mark AI metadata as verified (or unverified)."""
        sql = """
        UPDATE ai_metadata
        SET verified = ?, verified_date = ?
        WHERE id = ?
        """
        return self.execute_query(sql, (
            1 if verified else 0,
            datetime.now().isoformat() if verified else None,
            metadata_id
        ), commit=True)
    
    def get_all_ai_metadata(self, entity_id, verified_only=False):
        """Get all AI metadata for an entity, optionally only verified ones."""
        sql = """
        SELECT * FROM ai_metadata
        WHERE entity_id = ?
        """
        
        if verified_only:
            sql += " AND verified = 1"
        
        sql += " ORDER BY field_name, confidence_score DESC"
        
        return self.execute_query(sql, (entity_id,))
    
    def get_ai_metadata_by_source(self, source):
        """Get all AI metadata from a specific source."""
        sql = """
        SELECT am.*, e.name as entity_name, e.entity_type
        FROM ai_metadata am
        JOIN entities e ON am.entity_id = e.id
        WHERE am.source = ?
        ORDER BY am.entity_id, am.field_name
        """
        return self.execute_query(sql, (source,))
    
    def get_high_confidence_metadata(self, min_confidence=0.8):
        """Get all AI metadata with confidence score above threshold."""
        sql = """
        SELECT am.*, e.name as entity_name, e.entity_type
        FROM ai_metadata am
        JOIN entities e ON am.entity_id = e.id
        WHERE am.confidence_score >= ?
        ORDER BY am.confidence_score DESC
        """
        return self.execute_query(sql, (min_confidence,))
    
    def get_entity_with_metadata(self, entity_id):
        """Get entity enriched with all AI metadata."""
        # Get basic entity data
        entity = self.get_entity(entity_id)
        
        if not entity:
            return None
        
        # Get AI metadata
        metadata = self.get_all_ai_metadata(entity_id)
        
        # Organize metadata by field name
        metadata_by_field = {}
        for item in metadata:
            field_name = item['field_name']
            if field_name not in metadata_by_field:
                metadata_by_field[field_name] = []
            metadata_by_field[field_name].append({
                'id': item['id'],
                'value': item['field_value'],
                'confidence': item['confidence_score'],
                'source': item['source'],
                'date': item['extraction_date'],
                'verified': bool(item['verified'])
            })
        
        entity['ai_metadata'] = metadata_by_field
        
        return entity
    
    # ======== Connection Evidence Methods ========
    
    def add_connection_evidence(self, connection_id, evidence_type, description, source_url=None, confidence_score=1.0):
        """Add evidence for an entity connection."""
        sql = """
        INSERT INTO connection_evidence
        (connection_id, evidence_type, description, source_url, confidence_score, extraction_date)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        return self.execute_query(sql, (
            connection_id, evidence_type, description, source_url, confidence_score, datetime.now().isoformat()
        ), commit=True)
    
    def get_connection_evidence(self, connection_id):
        """Get all evidence for a specific connection."""
        sql = """
        SELECT * FROM connection_evidence
        WHERE connection_id = ?
        ORDER BY confidence_score DESC
        """
        return self.execute_query(sql, (connection_id,))
    
    def get_evidence_by_type(self, evidence_type):
        """Get all evidence of a specific type."""
        sql = """
        SELECT ce.*, ec.entity1_id, ec.entity2_id, ec.connection_type,
        e1.name as entity1_name, e2.name as entity2_name
        FROM connection_evidence ce
        JOIN entity_connections ec ON ce.connection_id = ec.id
        JOIN entities e1 ON ec.entity1_id = e1.id
        JOIN entities e2 ON ec.entity2_id = e2.id
        WHERE ce.evidence_type = ?
        ORDER BY ce.confidence_score DESC
        """
        return self.execute_query(sql, (evidence_type,))
    
    def get_high_confidence_evidence(self, min_confidence=0.8):
        """Get all evidence with confidence score above threshold."""
        sql = """
        SELECT ce.*, ec.entity1_id, ec.entity2_id, ec.connection_type,
        e1.name as entity1_name, e2.name as entity2_name
        FROM connection_evidence ce
        JOIN entity_connections ec ON ce.connection_id = ec.id
        JOIN entities e1 ON ec.entity1_id = e1.id
        JOIN entities e2 ON ec.entity2_id = e2.id
        WHERE ce.confidence_score >= ?
        ORDER BY ce.confidence_score DESC
        """
        return self.execute_query(sql, (min_confidence,))
    
    def get_entity_with_connections(self, entity_id, include_evidence=False):
        """Get entity with all connections, optionally including evidence."""
        # Get basic entity data
        entity = self.get_entity(entity_id)
        
        if not entity:
            return None
        
        # Get connections where entity is either entity1 or entity2
        sql = """
        SELECT ec.*, 
        e1.name as entity1_name, e1.entity_type as entity1_type,
        e2.name as entity2_name, e2.entity_type as entity2_type
        FROM entity_connections ec
        JOIN entities e1 ON ec.entity1_id = e1.id
        JOIN entities e2 ON ec.entity2_id = e2.id
        WHERE ec.entity1_id = ? OR ec.entity2_id = ?
        """
        connections = self.execute_query(sql, (entity_id, entity_id))
        
        # Transform connections to a more useful format
        transformed_connections = []
        
        for conn in connections:
            # If this entity is entity1, we want to show connection to entity2
            if conn['entity1_id'] == entity_id:
                connected_entity = {
                    'id': conn['entity2_id'],
                    'name': conn['entity2_name'],
                    'type': conn['entity2_type'],
                    'connection_type': conn['connection_type'],
                    'connection_id': conn['id'],
                    'direction': 'outgoing'
                }
            else:
                # This entity is entity2, show connection to entity1
                connected_entity = {
                    'id': conn['entity1_id'],
                    'name': conn['entity1_name'],
                    'type': conn['entity1_type'],
                    'connection_type': conn['connection_type'],
                    'connection_id': conn['id'],
                    'direction': 'incoming'
                }
            
            # Add evidence if requested
            if include_evidence:
                evidence = self.get_connection_evidence(conn['id'])
                connected_entity['evidence'] = evidence
            
            transformed_connections.append(connected_entity)
        
        entity['connections'] = transformed_connections
        
        return entity
        
    # ======== Donation Methods ========
    
    def add_donation_record(self, donor_id, recipient_id, amount, donation_date, 
                           donation_type=None, source_url=None, source_id=None):
        """Add a donation record between entities."""
        sql = """
        INSERT INTO donation_records
        (donor_id, recipient_id, amount, donation_date, donation_type, source_url, source_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        return self.execute_query(sql, (
            donor_id, recipient_id, amount, donation_date, donation_type, source_url, source_id
        ), commit=True)
    
    def get_donations_by_donor(self, donor_id, limit=20):
        """Get donations made by an entity."""
        sql = """
        SELECT dr.*, e.name as recipient_name, e.entity_type as recipient_type
        FROM donation_records dr
        JOIN entities e ON dr.recipient_id = e.id
        WHERE dr.donor_id = ?
        ORDER BY dr.donation_date DESC
        LIMIT ?
        """
        return self.execute_query(sql, (donor_id, limit))
    
    def get_donations_by_recipient(self, recipient_id, limit=20):
        """Get donations received by an entity."""
        sql = """
        SELECT dr.*, e.name as donor_name, e.entity_type as donor_type
        FROM donation_records dr
        JOIN entities e ON dr.donor_id = e.id
        WHERE dr.recipient_id = ?
        ORDER BY dr.donation_date DESC
        LIMIT ?
        """
        return self.execute_query(sql, (recipient_id, limit))
    
    def get_donations_by_type(self, donation_type, limit=50):
        """Get donations of a specific type."""
        sql = """
        SELECT dr.*, 
        d.name as donor_name, d.entity_type as donor_type,
        r.name as recipient_name, r.entity_type as recipient_type
        FROM donation_records dr
        JOIN entities d ON dr.donor_id = d.id
        JOIN entities r ON dr.recipient_id = r.id
        WHERE dr.donation_type = ?
        ORDER BY dr.donation_date DESC, dr.amount DESC
        LIMIT ?
        """
        return self.execute_query(sql, (donation_type, limit))
    
    def get_large_donations(self, min_amount, limit=50):
        """Get donations above a certain amount."""
        sql = """
        SELECT dr.*, 
        d.name as donor_name, d.entity_type as donor_type,
        r.name as recipient_name, r.entity_type as recipient_type
        FROM donation_records dr
        JOIN entities d ON dr.donor_id = d.id
        JOIN entities r ON dr.recipient_id = r.id
        WHERE dr.amount >= ?
        ORDER BY dr.amount DESC, dr.donation_date DESC
        LIMIT ?
        """
        return self.execute_query(sql, (min_amount, limit))
    
    def get_recent_donations(self, start_date, limit=50):
        """Get recent donations from a start date."""
        sql = """
        SELECT dr.*, 
        d.name as donor_name, d.entity_type as donor_type,
        r.name as recipient_name, r.entity_type as recipient_type
        FROM donation_records dr
        JOIN entities d ON dr.donor_id = d.id
        JOIN entities r ON dr.recipient_id = r.id
        WHERE dr.donation_date >= ?
        ORDER BY dr.donation_date DESC, dr.amount DESC
        LIMIT ?
        """
        return self.execute_query(sql, (start_date, limit))
    
    def get_entity_with_donations(self, entity_id):
        """Get entity with donation information (both as donor and recipient)."""
        # Get basic entity data
        entity = self.get_entity(entity_id)
        
        if not entity:
            return None
        
        # Get donations this entity made
        donations_made = self.get_donations_by_donor(entity_id, limit=100)
        
        # Get donations this entity received
        donations_received = self.get_donations_by_recipient(entity_id, limit=100)
        
        # Add to entity
        entity['donations_made'] = donations_made
        entity['donations_received'] = donations_received
        
        # Calculate summary statistics
        total_made = sum(d['amount'] for d in donations_made)
        total_received = sum(d['amount'] for d in donations_received)
        
        entity['donation_summary'] = {
            'total_donated': total_made,
            'total_received': total_received,
            'net_flow': total_received - total_made,
            'donors_count': len(donations_received),
            'recipients_count': len(donations_made)
        }
        
        return entity
    
    # ======== Data Enrichment Methods ========
    
    def get_enrichment_priorities(self, entity_type=None, limit=20):
        """Get entities that need data enrichment, prioritized by gaps."""
        if entity_type:
            sql = """
            SELECT * FROM view_enrichment_priorities
            WHERE entity_type = ?
            LIMIT ?
            """
            return self.execute_query(sql, (entity_type, limit))
        else:
            sql = "SELECT * FROM view_enrichment_priorities LIMIT ?"
            return self.execute_query(sql, (limit,))
    
    def get_entity_completeness(self, entity_id):
        """Get completeness analysis for a specific entity."""
        sql = "SELECT * FROM view_entity_gaps WHERE id = ?"
        return self.execute_query(sql, (entity_id,), fetch_all=False)