#!/usr/bin/env python3
"""
Database Utility Module.

Provides functions for database operations using SQLite.
Handles connections, transactions, and query execution.
"""
import os
import sqlite3
import threading
import datetime
import json
from typing import Any, Dict, List, Optional, Tuple, Union

# Import utility modules
from scripts.utils.logger import get_logger
from scripts.utils.config import get

# Initialize logger
logger = get_logger("db")

# Default database path
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "maga_ops.db")

# Thread-local storage for connection management
_local = threading.local()

def get_db_path() -> str:
    """
    Get database path from configuration or default.
    
    Returns:
        str: Database path
    """
    return get("database.path", DEFAULT_DB_PATH)

def get_connection() -> sqlite3.Connection:
    """
    Get a thread-local database connection.
    
    Returns:
        sqlite3.Connection: Database connection
    """
    # Get thread-local connection
    if not hasattr(_local, "connection") or _local.connection is None:
        # Create new connection
        db_path = get_db_path()
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Connect to database
        _local.connection = sqlite3.connect(db_path)
        
        # Enable foreign keys
        _local.connection.execute("PRAGMA foreign_keys = ON")
        
        # Set row factory
        _local.connection.row_factory = sqlite3.Row
        
        # Register adapters and converters
        sqlite3.register_adapter(datetime.datetime, lambda dt: dt.isoformat())
        sqlite3.register_adapter(datetime.date, lambda d: d.isoformat())
        sqlite3.register_adapter(dict, json.dumps)
        sqlite3.register_adapter(list, json.dumps)
        sqlite3.register_converter("DATETIME", lambda b: datetime.datetime.fromisoformat(b.decode()))
        sqlite3.register_converter("DATE", lambda b: datetime.date.fromisoformat(b.decode()))
        sqlite3.register_converter("JSON", lambda b: json.loads(b.decode()))
        
        logger.debug(f"Connected to database: {db_path}")
    
    return _local.connection

def close_connection() -> None:
    """Close the current thread's database connection if open."""
    if hasattr(_local, "connection") and _local.connection is not None:
        _local.connection.close()
        _local.connection = None
        logger.debug("Closed database connection")

def execute(query: str, params: Union[Tuple, Dict, List] = None) -> sqlite3.Cursor:
    """
    Execute a SQL query.
    
    Args:
        query (str): SQL query
        params (tuple, dict, or list, optional): Query parameters
        
    Returns:
        sqlite3.Cursor: Query cursor
    """
    conn = get_connection()
    
    try:
        if params is None:
            cursor = conn.execute(query)
        else:
            cursor = conn.execute(query, params)
        
        return cursor
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        raise

def execute_many(query: str, params_list: List[Union[Tuple, Dict]]) -> sqlite3.Cursor:
    """
    Execute a SQL query with multiple parameter sets.
    
    Args:
        query (str): SQL query
        params_list (list): List of parameter sets
        
    Returns:
        sqlite3.Cursor: Query cursor
    """
    conn = get_connection()
    
    try:
        cursor = conn.executemany(query, params_list)
        return cursor
    except Exception as e:
        logger.error(f"Error executing query with multiple parameters: {e}")
        raise

def transaction(func):
    """
    Transaction decorator for database operations.
    
    Args:
        func: Function to wrap in transaction
        
    Returns:
        wrapped: Wrapped function with transaction management
    """
    def wrapped(*args, **kwargs):
        conn = get_connection()
        
        try:
            # Begin transaction
            conn.execute("BEGIN")
            
            # Call function
            result = func(*args, **kwargs)
            
            # Commit transaction
            conn.commit()
            
            return result
        except Exception as e:
            # Rollback transaction
            conn.rollback()
            logger.error(f"Transaction failed: {e}")
            raise
    
    return wrapped

def fetch_one(query: str, params: Union[Tuple, Dict, List] = None) -> Optional[Dict[str, Any]]:
    """
    Fetch a single row from a query.
    
    Args:
        query (str): SQL query
        params (tuple, dict, or list, optional): Query parameters
        
    Returns:
        dict or None: Row as dictionary or None if no results
    """
    cursor = execute(query, params)
    row = cursor.fetchone()
    
    if row is None:
        return None
    
    return dict(row)

def fetch_all(query: str, params: Union[Tuple, Dict, List] = None) -> List[Dict[str, Any]]:
    """
    Fetch all rows from a query.
    
    Args:
        query (str): SQL query
        params (tuple, dict, or list, optional): Query parameters
        
    Returns:
        list: List of rows as dictionaries
    """
    cursor = execute(query, params)
    rows = cursor.fetchall()
    
    return [dict(row) for row in rows]

def fetch_value(query: str, params: Union[Tuple, Dict, List] = None) -> Any:
    """
    Fetch a single value from a query.
    
    Args:
        query (str): SQL query
        params (tuple, dict, or list, optional): Query parameters
        
    Returns:
        any: Value or None if no results
    """
    cursor = execute(query, params)
    row = cursor.fetchone()
    
    if row is None:
        return None
    
    return row[0]

def insert(table: str, data: Dict[str, Any]) -> int:
    """
    Insert a row into a table.
    
    Args:
        table (str): Table name
        data (dict): Data to insert
        
    Returns:
        int: Last row ID
    """
    # Prepare query
    columns = ", ".join(data.keys())
    placeholders = ", ".join(["?" for _ in data])
    query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
    
    # Execute query
    cursor = execute(query, list(data.values()))
    
    # Return last row ID
    return cursor.lastrowid

def update(table: str, data: Dict[str, Any], where: str, params: Union[Tuple, Dict, List] = None) -> int:
    """
    Update rows in a table.
    
    Args:
        table (str): Table name
        data (dict): Data to update
        where (str): WHERE clause
        params (tuple, dict, or list, optional): Query parameters for WHERE clause
        
    Returns:
        int: Number of rows affected
    """
    # Prepare query
    set_clause = ", ".join([f"{column} = ?" for column in data.keys()])
    query = f"UPDATE {table} SET {set_clause} WHERE {where}"
    
    # Combine data values and where params
    all_params = list(data.values())
    if params:
        if isinstance(params, dict):
            all_params.extend(params.values())
        else:
            all_params.extend(params if isinstance(params, list) else [params])
    
    # Execute query
    cursor = execute(query, all_params)
    
    # Return number of affected rows
    return cursor.rowcount

def delete(table: str, where: str, params: Union[Tuple, Dict, List] = None) -> int:
    """
    Delete rows from a table.
    
    Args:
        table (str): Table name
        where (str): WHERE clause
        params (tuple, dict, or list, optional): Query parameters for WHERE clause
        
    Returns:
        int: Number of rows affected
    """
    # Prepare query
    query = f"DELETE FROM {table} WHERE {where}"
    
    # Execute query
    cursor = execute(query, params)
    
    # Return number of affected rows
    return cursor.rowcount

def table_exists(table: str) -> bool:
    """
    Check if a table exists.
    
    Args:
        table (str): Table name
        
    Returns:
        bool: True if table exists, False otherwise
    """
    # Query to check if table exists
    query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
    
    # Execute query
    cursor = execute(query, (table,))
    
    # Return True if table exists
    return cursor.fetchone() is not None

def create_table(table: str, columns: Dict[str, str], if_not_exists: bool = True) -> None:
    """
    Create a table.
    
    Args:
        table (str): Table name
        columns (dict): Dictionary of column name to definition
        if_not_exists (bool, optional): Add IF NOT EXISTS clause
    """
    # Prepare query
    column_definitions = ", ".join([f"{name} {definition}" for name, definition in columns.items()])
    exists_clause = "IF NOT EXISTS " if if_not_exists else ""
    query = f"CREATE TABLE {exists_clause}{table} ({column_definitions})"
    
    # Execute query
    execute(query)

def backup_database(backup_path: str = None) -> str:
    """
    Backup the database.
    
    Args:
        backup_path (str, optional): Path to save backup
        
    Returns:
        str: Backup file path
    """
    # Get database path
    db_path = get_db_path()
    
    # Generate backup path if not provided
    if backup_path is None:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.dirname(db_path)
        db_name = os.path.splitext(os.path.basename(db_path))[0]
        backup_path = os.path.join(backup_dir, f"{db_name}_backup_{timestamp}.db")
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
    
    # Create backup connection
    backup_conn = sqlite3.connect(backup_path)
    
    # Get source connection
    source_conn = get_connection()
    
    # Backup database
    source_conn.backup(backup_conn)
    
    # Close backup connection
    backup_conn.close()
    
    logger.info(f"Database backup created: {backup_path}")
    
    return backup_path

def vacuum() -> None:
    """Optimize the database by rebuilding it."""
    execute("VACUUM")
    logger.info("Database optimized using VACUUM")

def initialize() -> None:
    """Initialize database with default tables and indexes."""
    # Create schema tables if they don't exist
    create_schema()
    
    logger.info("Database initialized")

def create_schema() -> None:
    """Create database schema tables if they don't exist."""
    # Create tracking table for database migrations
    create_table(
        "migrations", 
        {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "name": "TEXT NOT NULL UNIQUE",
            "applied_at": "DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP"
        },
        if_not_exists=True
    )
    
    # Create table for general settings
    create_table(
        "settings", 
        {
            "key": "TEXT PRIMARY KEY",
            "value": "TEXT",
            "description": "TEXT",
            "updated_at": "DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP"
        },
        if_not_exists=True
    )
    
    # Create table for caching external API responses
    create_table(
        "api_cache", 
        {
            "key": "TEXT PRIMARY KEY",
            "value": "TEXT",
            "expiry": "DATETIME",
            "created_at": "DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP"
        },
        if_not_exists=True
    )
    
    # Create index for api_cache expiry
    execute("CREATE INDEX IF NOT EXISTS idx_api_cache_expiry ON api_cache (expiry)")

if __name__ == "__main__":
    # Test database operations
    try:
        # Initialize database
        initialize()
        
        # Test transactions with decorator
        @transaction
        def test_transaction():
            # Insert a setting
            execute("INSERT OR REPLACE INTO settings (key, value, description) VALUES (?, ?, ?)",
                   ("test_key", "test_value", "Test setting"))
            
            # Fetch the setting
            return fetch_one("SELECT * FROM settings WHERE key = ?", ("test_key",))
        
        # Run transaction test
        result = test_transaction()
        print("Transaction test successful:")
        print(result)
        
        # Test backup
        backup_path = backup_database()
        print(f"Database backup created: {backup_path}")
        
        # Cleanup - delete test data
        delete("settings", "key = ?", ("test_key",))
        
    finally:
        # Close connection
        close_connection() 