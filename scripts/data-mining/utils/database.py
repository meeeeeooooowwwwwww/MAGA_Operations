#!/usr/bin/env python3
"""
Database utility for data mining scripts.
Handles database connections, transactions, and common operations.
"""
import os
import sys
import sqlite3
import json
import datetime
from contextlib import contextmanager

# Add parent directory to path for relative imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.data_mining.utils.config import DB_FILE
from scripts.data_mining.utils.logger import get_logger

logger = get_logger('database')

def dict_factory(cursor, row):
    """Convert row to dictionary with column names as keys"""
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

class Database:
    """SQLite database handler"""
    
    def __init__(self, db_path=None):
        """
        Initialize database connection
        
        Args:
            db_path (str, optional): Path to database file. If None, uses default.
        """
        self.db_path = db_path or DB_FILE
        self._validate_db_path()
    
    def _validate_db_path(self):
        """Validate database path and create parent directories if needed"""
        db_dir = os.path.dirname(self.db_path)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            logger.info(f"Created database directory: {db_dir}")
    
    @contextmanager
    def connect(self, dict_cursor=True):
        """
        Context manager for database connection
        
        Args:
            dict_cursor (bool): Whether to return rows as dictionaries
            
        Yields:
            tuple: (connection, cursor)
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Enable foreign keys
            conn.execute('PRAGMA foreign_keys = ON')
            
            # Configure JSON serialization for datetime objects
            conn.execute('PRAGMA journal_mode = WAL')
            
            # Return rows as dictionaries if requested
            if dict_cursor:
                conn.row_factory = dict_factory
            
            cursor = conn.cursor()
            yield conn, cursor
            
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    @contextmanager
    def transaction(self, dict_cursor=True):
        """
        Context manager for database transaction
        
        Args:
            dict_cursor (bool): Whether to return rows as dictionaries
            
        Yields:
            tuple: (connection, cursor)
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Enable foreign keys
            conn.execute('PRAGMA foreign_keys = ON')
            
            # Return rows as dictionaries if requested
            if dict_cursor:
                conn.row_factory = dict_factory
            
            cursor = conn.cursor()
            yield conn, cursor
            conn.commit()
            
        except Exception as e:
            logger.error(f"Database transaction error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def execute(self, query, params=None, dict_cursor=True):
        """
        Execute a query and return all results
        
        Args:
            query (str): SQL query
            params (tuple or dict, optional): Query parameters
            dict_cursor (bool): Whether to return rows as dictionaries
            
        Returns:
            list: Query results
        """
        with self.connect(dict_cursor) as (conn, cursor):
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            return cursor.fetchall()
    
    def execute_one(self, query, params=None, dict_cursor=True):
        """
        Execute a query and return the first result
        
        Args:
            query (str): SQL query
            params (tuple or dict, optional): Query parameters
            dict_cursor (bool): Whether to return rows as dictionaries
            
        Returns:
            dict or tuple: First row of query results or None
        """
        with self.connect(dict_cursor) as (conn, cursor):
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            return cursor.fetchone()
    
    def execute_script(self, script):
        """
        Execute a SQL script
        
        Args:
            script (str): SQL script
        """
        with self.connect(dict_cursor=False) as (conn, cursor):
            cursor.executescript(script)
            conn.commit()
    
    def insert(self, table, data, replace=False):
        """
        Insert a row into a table
        
        Args:
            table (str): Table name
            data (dict): Column data
            replace (bool): Whether to replace existing row
            
        Returns:
            int: Row ID
        """
        with self.transaction() as (conn, cursor):
            columns = list(data.keys())
            placeholders = ['?' for _ in columns]
            values = [self._convert_value(data[col]) for col in columns]
            
            if replace:
                query = f"INSERT OR REPLACE INTO {table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
            else:
                query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
            
            cursor.execute(query, values)
            return cursor.lastrowid
    
    def insert_many(self, table, data_list, replace=False):
        """
        Insert multiple rows into a table
        
        Args:
            table (str): Table name
            data_list (list): List of row dictionaries
            replace (bool): Whether to replace existing rows
            
        Returns:
            int: Number of rows inserted
        """
        if not data_list:
            return 0
        
        with self.transaction() as (conn, cursor):
            # Get columns from first row
            columns = list(data_list[0].keys())
            placeholders = ['?' for _ in columns]
            
            if replace:
                query = f"INSERT OR REPLACE INTO {table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
            else:
                query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
            
            values = [
                [self._convert_value(row[col]) for col in columns]
                for row in data_list
            ]
            
            cursor.executemany(query, values)
            return cursor.rowcount
    
    def update(self, table, data, condition, params=None):
        """
        Update rows in a table
        
        Args:
            table (str): Table name
            data (dict): Column data to update
            condition (str): WHERE condition
            params (tuple or dict, optional): Condition parameters
            
        Returns:
            int: Number of rows updated
        """
        with self.transaction() as (conn, cursor):
            set_clause = ', '.join([f"{col} = ?" for col in data.keys()])
            values = [self._convert_value(val) for val in data.values()]
            
            query = f"UPDATE {table} SET {set_clause} WHERE {condition}"
            
            if params:
                if isinstance(params, dict):
                    # Convert dict params to list in correct order
                    param_values = list(params.values())
                else:
                    param_values = params
                
                cursor.execute(query, values + list(param_values))
            else:
                cursor.execute(query, values)
            
            return cursor.rowcount
    
    def delete(self, table, condition, params=None):
        """
        Delete rows from a table
        
        Args:
            table (str): Table name
            condition (str): WHERE condition
            params (tuple or dict, optional): Condition parameters
            
        Returns:
            int: Number of rows deleted
        """
        with self.transaction() as (conn, cursor):
            query = f"DELETE FROM {table} WHERE {condition}"
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            return cursor.rowcount
    
    def table_exists(self, table):
        """
        Check if a table exists
        
        Args:
            table (str): Table name
            
        Returns:
            bool: Whether the table exists
        """
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        result = self.execute_one(query, (table,))
        return result is not None
    
    def create_backup(self, backup_path=None):
        """
        Create a backup of the database
        
        Args:
            backup_path (str, optional): Path for backup file. If None, uses timestamp.
            
        Returns:
            str: Path to backup file
        """
        if backup_path is None:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = os.path.dirname(self.db_path)
            db_name = os.path.basename(self.db_path).split('.')[0]
            backup_path = os.path.join(backup_dir, f"{db_name}_backup_{timestamp}.db")
        
        logger.info(f"Creating database backup: {backup_path}")
        
        try:
            # Open source database
            src_conn = sqlite3.connect(self.db_path)
            
            # Create backup directory if it doesn't exist
            backup_dir = os.path.dirname(backup_path)
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            # Open destination database
            dst_conn = sqlite3.connect(backup_path)
            
            # Copy database
            src_conn.backup(dst_conn)
            
            # Close connections
            dst_conn.close()
            src_conn.close()
            
            logger.info(f"Database backup created: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Database backup error: {e}")
            raise
    
    def vacuum(self):
        """
        Vacuum the database to optimize space
        """
        with self.connect() as (conn, cursor):
            cursor.execute("VACUUM")
            logger.info("Database vacuumed")
    
    def _convert_value(self, value):
        """
        Convert value for database storage
        
        Args:
            value: Value to convert
            
        Returns:
            Value in appropriate format for SQLite
        """
        if isinstance(value, (dict, list)):
            return json.dumps(value)
        elif isinstance(value, datetime.datetime):
            return value.isoformat()
        elif isinstance(value, datetime.date):
            return value.isoformat()
        else:
            return value

# Create a singleton instance
db = Database()

# SQL helper for creating tables if they don't exist
def create_table_if_not_exists(table_name, columns_definitions, conn=None):
    """
    Create a table if it doesn't exist
    
    Args:
        table_name (str): Table name
        columns_definitions (str): Column definitions
        conn (sqlite3.Connection, optional): Database connection
        
    Returns:
        bool: Whether the table was created
    """
    close_conn = False
    if conn is None:
        conn = sqlite3.connect(DB_FILE)
        close_conn = True
    
    cursor = conn.cursor()
    
    try:
        # Check if table exists
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        exists = cursor.fetchone() is not None
        
        if not exists:
            # Create table
            cursor.execute(f"CREATE TABLE {table_name} ({columns_definitions})")
            conn.commit()
            logger.info(f"Created table: {table_name}")
            return True
        
        return False
    finally:
        if close_conn:
            conn.close()

if __name__ == "__main__":
    # Test database functions
    db = Database()
    
    test_table = """
    CREATE TABLE IF NOT EXISTS test_table (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        value REAL,
        data JSON,
        timestamp TEXT
    )
    """
    
    with db.connect() as (conn, cursor):
        cursor.executescript(test_table)
    
    # Test insert
    test_id = db.insert('test_table', {
        'name': 'Test Item',
        'value': 123.45,
        'data': {'key': 'value', 'nested': [1, 2, 3]},
        'timestamp': datetime.datetime.now()
    })
    print(f"Inserted row with ID: {test_id}")
    
    # Test select
    results = db.execute("SELECT * FROM test_table")
    print("All rows:")
    for row in results:
        print(row)
    
    # Test update
    updated_rows = db.update('test_table', {'value': 999.99}, 'id = ?', (test_id,))
    print(f"Updated {updated_rows} rows")
    
    # Test select one
    updated_row = db.execute_one("SELECT * FROM test_table WHERE id = ?", (test_id,))
    print("Updated row:")
    print(updated_row)
    
    # Clean up
    db.delete('test_table', '1=1')
    print("Test completed") 