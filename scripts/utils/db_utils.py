#!/usr/bin/env python3
"""
Database Utility Module.

Provides functions for SQLite database operations.
Supports connection management, queries, and transactions.
"""
import os
import sqlite3
import datetime
import json
from typing import Any, Dict, List, Optional, Union, Tuple, Callable

# Import utility modules
from scripts.utils.logger import get_logger

# Initialize logger
logger = get_logger("db_utils")

class Database:
    """SQLite database connection manager."""
    
    def __init__(self, db_path: str, auto_commit: bool = True, timeout: float = 30.0):
        """
        Initialize database connection.
        
        Args:
            db_path (str): Path to SQLite database file
            auto_commit (bool, optional): Auto-commit transactions
            timeout (float, optional): Connection timeout in seconds
        """
        self.db_path = os.path.abspath(db_path)
        self.auto_commit = auto_commit
        self.timeout = timeout
        self.conn = None
        self.cursor = None
    
    def __enter__(self):
        """Context manager enter method."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit method."""
        if exc_type is not None:
            self.rollback()
        elif self.auto_commit:
            self.commit()
        
        self.close()
    
    def connect(self):
        """Connect to database."""
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Connect to database
        self.conn = sqlite3.connect(
            self.db_path,
            timeout=self.timeout,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )
        
        # Enable foreign keys
        self.conn.execute("PRAGMA foreign_keys = ON")
        
        # Enable row factory
        self.conn.row_factory = sqlite3.Row
        
        # Create cursor
        self.cursor = self.conn.cursor()
        
        return self
    
    def close(self):
        """Close database connection."""
        if self.cursor:
            self.cursor.close()
            self.cursor = None
        
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def commit(self):
        """Commit transaction."""
        if self.conn:
            self.conn.commit()
    
    def rollback(self):
        """Rollback transaction."""
        if self.conn:
            self.conn.rollback()
    
    def execute(self, query: str, params: tuple = None) -> sqlite3.Cursor:
        """
        Execute SQL query.
        
        Args:
            query (str): SQL query
            params (tuple, optional): Query parameters
            
        Returns:
            sqlite3.Cursor: Query cursor
        """
        if not self.conn:
            self.connect()
        
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            
            if self.auto_commit and query.strip().upper().startswith(("INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER")):
                self.commit()
            
            return self.cursor
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            
            raise
    
    def executemany(self, query: str, param_list: List[tuple]) -> sqlite3.Cursor:
        """
        Execute SQL query with multiple parameter sets.
        
        Args:
            query (str): SQL query
            param_list (list): List of parameter tuples
            
        Returns:
            sqlite3.Cursor: Query cursor
        """
        if not self.conn:
            self.connect()
        
        try:
            self.cursor.executemany(query, param_list)
            
            if self.auto_commit and query.strip().upper().startswith(("INSERT", "UPDATE", "DELETE")):
                self.commit()
            
            return self.cursor
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Param list length: {len(param_list)}")
            
            raise
    
    def executescript(self, script: str) -> sqlite3.Cursor:
        """
        Execute SQL script.
        
        Args:
            script (str): SQL script
            
        Returns:
            sqlite3.Cursor: Query cursor
        """
        if not self.conn:
            self.connect()
        
        try:
            self.cursor.executescript(script)
            
            if self.auto_commit:
                self.commit()
            
            return self.cursor
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            logger.error(f"Script: {script[:100]}...")
            
            raise
    
    def query(self, query: str, params: tuple = None, as_dict: bool = True) -> List[Dict[str, Any]]:
        """
        Execute query and fetch all results.
        
        Args:
            query (str): SQL query
            params (tuple, optional): Query parameters
            as_dict (bool, optional): Return results as dictionaries
            
        Returns:
            list: Query results
        """
        cursor = self.execute(query, params)
        
        if as_dict:
            # Convert rows to dictionaries
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        else:
            return cursor.fetchall()
    
    def query_one(self, query: str, params: tuple = None, as_dict: bool = True) -> Optional[Dict[str, Any]]:
        """
        Execute query and fetch one result.
        
        Args:
            query (str): SQL query
            params (tuple, optional): Query parameters
            as_dict (bool, optional): Return result as dictionary
            
        Returns:
            dict or None: Query result
        """
        cursor = self.execute(query, params)
        row = cursor.fetchone()
        
        if row is None:
            return None
        
        if as_dict:
            # Convert row to dictionary
            columns = [column[0] for column in cursor.description]
            return dict(zip(columns, row))
        else:
            return row
    
    def query_value(self, query: str, params: tuple = None) -> Any:
        """
        Execute query and fetch single value.
        
        Args:
            query (str): SQL query
            params (tuple, optional): Query parameters
            
        Returns:
            any: Query value
        """
        cursor = self.execute(query, params)
        row = cursor.fetchone()
        
        if row is None:
            return None
        
        return row[0]
    
    def insert(self, table: str, data: Dict[str, Any]) -> int:
        """
        Insert row into table.
        
        Args:
            table (str): Table name
            data (dict): Column values
            
        Returns:
            int: Last row ID
        """
        # Build query
        columns = list(data.keys())
        placeholders = ["?"] * len(columns)
        values = [data[column] for column in columns]
        
        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        
        # Execute query
        self.execute(query, tuple(values))
        
        # Return last row ID
        return self.cursor.lastrowid
    
    def insert_many(self, table: str, data_list: List[Dict[str, Any]]) -> int:
        """
        Insert multiple rows into table.
        
        Args:
            table (str): Table name
            data_list (list): List of row dictionaries
            
        Returns:
            int: Number of rows inserted
        """
        if not data_list:
            return 0
        
        # Build query
        columns = list(data_list[0].keys())
        placeholders = ["?"] * len(columns)
        values_list = [[data[column] for column in columns] for data in data_list]
        
        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        
        # Execute query
        self.executemany(query, values_list)
        
        # Return number of rows inserted
        return self.cursor.rowcount
    
    def update(self, table: str, data: Dict[str, Any], where: str, params: tuple = None) -> int:
        """
        Update rows in table.
        
        Args:
            table (str): Table name
            data (dict): Column values
            where (str): WHERE clause
            params (tuple, optional): WHERE parameters
            
        Returns:
            int: Number of rows updated
        """
        # Build query
        set_clause = ", ".join([f"{column} = ?" for column in data.keys()])
        values = list(data.values())
        
        query = f"UPDATE {table} SET {set_clause}"
        
        if where:
            query += f" WHERE {where}"
            if params:
                values.extend(params)
        
        # Execute query
        self.execute(query, tuple(values))
        
        # Return number of rows updated
        return self.cursor.rowcount
    
    def delete(self, table: str, where: str = "", params: tuple = None) -> int:
        """
        Delete rows from table.
        
        Args:
            table (str): Table name
            where (str, optional): WHERE clause
            params (tuple, optional): WHERE parameters
            
        Returns:
            int: Number of rows deleted
        """
        # Build query
        query = f"DELETE FROM {table}"
        
        if where:
            query += f" WHERE {where}"
        
        # Execute query
        self.execute(query, params)
        
        # Return number of rows deleted
        return self.cursor.rowcount
    
    def table_exists(self, table: str) -> bool:
        """
        Check if table exists.
        
        Args:
            table (str): Table name
            
        Returns:
            bool: True if table exists
        """
        query = "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?"
        result = self.query_value(query, (table,))
        
        return result is not None
    
    def column_exists(self, table: str, column: str) -> bool:
        """
        Check if column exists in table.
        
        Args:
            table (str): Table name
            column (str): Column name
            
        Returns:
            bool: True if column exists
        """
        query = f"PRAGMA table_info({table})"
        rows = self.query(query)
        
        for row in rows:
            if row["name"] == column:
                return True
        
        return False
    
    def create_table(self, table: str, columns: Dict[str, str], if_not_exists: bool = True) -> None:
        """
        Create table.
        
        Args:
            table (str): Table name
            columns (dict): Column definitions
            if_not_exists (bool, optional): Add IF NOT EXISTS
        """
        # Build query
        column_defs = [f"{name} {definition}" for name, definition in columns.items()]
        exists_clause = "IF NOT EXISTS " if if_not_exists else ""
        
        query = f"CREATE TABLE {exists_clause}{table} ({', '.join(column_defs)})"
        
        # Execute query
        self.execute(query)
    
    def add_column(self, table: str, column: str, definition: str, if_not_exists: bool = True) -> None:
        """
        Add column to table.
        
        Args:
            table (str): Table name
            column (str): Column name
            definition (str): Column definition
            if_not_exists (bool, optional): Check if column exists
        """
        if if_not_exists and self.column_exists(table, column):
            return
        
        query = f"ALTER TABLE {table} ADD COLUMN {column} {definition}"
        self.execute(query)
    
    def backup(self, backup_path: str = None) -> str:
        """
        Backup database.
        
        Args:
            backup_path (str, optional): Backup file path
            
        Returns:
            str: Backup file path
        """
        if not backup_path:
            # Generate backup filename
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = os.path.splitext(os.path.basename(self.db_path))[0]
            backup_path = f"{base_name}_backup_{timestamp}{os.path.splitext(self.db_path)[1]}"
            backup_path = os.path.join(os.path.dirname(self.db_path), backup_path)
        
        # Create connection to backup file
        backup_conn = sqlite3.connect(backup_path)
        
        # Backup database
        if self.conn:
            with backup_conn:
                self.conn.backup(backup_conn)
        else:
            with sqlite3.connect(self.db_path) as conn:
                conn.backup(backup_conn)
        
        backup_conn.close()
        
        return backup_path
    
    def vacuum(self) -> None:
        """Vacuum database to optimize storage."""
        self.execute("VACUUM")
    
    def begin_transaction(self) -> None:
        """Begin transaction."""
        self.execute("BEGIN TRANSACTION")
    
    def create_index(self, table: str, columns: List[str], unique: bool = False, 
                   if_not_exists: bool = True) -> None:
        """
        Create index on table.
        
        Args:
            table (str): Table name
            columns (list): Column names
            unique (bool, optional): Create unique index
            if_not_exists (bool, optional): Add IF NOT EXISTS
        """
        # Generate index name
        index_name = f"idx_{table}_{'_'.join(columns)}"
        
        # Build query
        unique_clause = "UNIQUE " if unique else ""
        exists_clause = "IF NOT EXISTS " if if_not_exists else ""
        
        query = f"CREATE {unique_clause}INDEX {exists_clause}{index_name} ON {table} ({', '.join(columns)})"
        
        # Execute query
        self.execute(query)
    
    def get_table_names(self) -> List[str]:
        """
        Get list of table names.
        
        Returns:
            list: Table names
        """
        query = "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        rows = self.query(query)
        
        return [row["name"] for row in rows]
    
    def get_table_info(self, table: str) -> List[Dict[str, Any]]:
        """
        Get table schema information.
        
        Args:
            table (str): Table name
            
        Returns:
            list: Column information
        """
        query = f"PRAGMA table_info({table})"
        return self.query(query)
    
    def get_table_count(self, table: str, where: str = "", params: tuple = None) -> int:
        """
        Get row count for table.
        
        Args:
            table (str): Table name
            where (str, optional): WHERE clause
            params (tuple, optional): WHERE parameters
            
        Returns:
            int: Row count
        """
        query = f"SELECT COUNT(*) FROM {table}"
        
        if where:
            query += f" WHERE {where}"
        
        return self.query_value(query, params)
    
    def get_foreign_keys(self, table: str) -> List[Dict[str, Any]]:
        """
        Get foreign key constraints for table.
        
        Args:
            table (str): Table name
            
        Returns:
            list: Foreign key information
        """
        query = f"PRAGMA foreign_key_list({table})"
        return self.query(query)
    
    def get_indexes(self, table: str) -> List[Dict[str, Any]]:
        """
        Get indexes for table.
        
        Args:
            table (str): Table name
            
        Returns:
            list: Index information
        """
        query = f"PRAGMA index_list({table})"
        return self.query(query)
    
    def transaction(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function within transaction.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            any: Function result
        """
        # Save auto-commit setting
        original_auto_commit = self.auto_commit
        self.auto_commit = False
        
        try:
            # Begin transaction
            self.begin_transaction()
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Commit transaction
            self.commit()
            
            return result
        except Exception as e:
            # Rollback transaction
            self.rollback()
            
            # Re-raise exception
            raise e
        finally:
            # Restore auto-commit setting
            self.auto_commit = original_auto_commit

def get_db_connection(db_path: str, auto_commit: bool = True) -> Database:
    """
    Get database connection.
    
    Args:
        db_path (str): Database file path
        auto_commit (bool, optional): Auto-commit transactions
        
    Returns:
        Database: Database connection
    """
    return Database(db_path, auto_commit)

def execute_script(db_path: str, script: str) -> None:
    """
    Execute SQL script.
    
    Args:
        db_path (str): Database file path
        script (str): SQL script
    """
    with Database(db_path) as db:
        db.executescript(script)

def backup_database(db_path: str, backup_path: str = None) -> str:
    """
    Backup database.
    
    Args:
        db_path (str): Database file path
        backup_path (str, optional): Backup file path
        
    Returns:
        str: Backup file path
    """
    with Database(db_path) as db:
        return db.backup(backup_path)

def query_to_json(db_path: str, query: str, params: tuple = None, indent: int = 2) -> str:
    """
    Execute query and return results as JSON.
    
    Args:
        db_path (str): Database file path
        query (str): SQL query
        params (tuple, optional): Query parameters
        indent (int, optional): JSON indent
        
    Returns:
        str: JSON string
    """
    with Database(db_path) as db:
        results = db.query(query, params)
        return json.dumps(results, indent=indent, default=str)

def query_to_csv(db_path: str, query: str, params: tuple = None) -> str:
    """
    Execute query and return results as CSV.
    
    Args:
        db_path (str): Database file path
        query (str): SQL query
        params (tuple, optional): Query parameters
        
    Returns:
        str: CSV string
    """
    import csv
    import io
    
    with Database(db_path) as db:
        results = db.query(query, params)
        
        if not results:
            return ""
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
        
        return output.getvalue()

if __name__ == "__main__":
    # Test database utilities
    import tempfile
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
        db_path = temp_file.name
    
    try:
        # Create database connection
        db = Database(db_path)
        
        # Create test table
        db.create_table("test", {
            "id": "INTEGER PRIMARY KEY",
            "name": "TEXT NOT NULL",
            "age": "INTEGER",
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        })
        
        # Insert data
        db.insert("test", {"name": "John", "age": 30})
        db.insert("test", {"name": "Jane", "age": 25})
        db.insert("test", {"name": "Bob", "age": 40})
        
        # Query data
        results = db.query("SELECT * FROM test ORDER BY age")
        print("Query results:")
        for row in results:
            print(f"  {row['id']}: {row['name']} ({row['age']})")
        
        # Update data
        db.update("test", {"age": 35}, "name = ?", ("John",))
        
        # Query one
        john = db.query_one("SELECT * FROM test WHERE name = ?", ("John",))
        print(f"John's age: {john['age']}")
        
        # Count
        count = db.get_table_count("test", "age > ?", (30,))
        print(f"People over 30: {count}")
        
        # Transaction
        def update_ages(db, multiplier):
            results = db.query("SELECT id, age FROM test")
            for row in results:
                db.update("test", {"age": row["age"] * multiplier}, "id = ?", (row["id"],))
            return db.query("SELECT SUM(age) as total FROM test")[0]["total"]
        
        total_age = db.transaction(update_ages, db, 2)
        print(f"Total age after doubling: {total_age}")
        
        # Table info
        table_info = db.get_table_info("test")
        print("Table columns:")
        for column in table_info:
            print(f"  {column['name']} ({column['type']})")
        
        # JSON export
        json_data = query_to_json(db_path, "SELECT * FROM test ORDER BY name")
        print(f"JSON export:\n{json_data}")
        
        # CSV export
        csv_data = query_to_csv(db_path, "SELECT name, age FROM test ORDER BY name")
        print(f"CSV export:\n{csv_data}")
        
        # Backup
        backup_path = backup_database(db_path)
        print(f"Backup created: {backup_path}")
        
        # Close connection
        db.close()
    finally:
        # Clean up
        try:
            os.remove(db_path)
            if 'backup_path' in locals():
                os.remove(backup_path)
        except:
            pass 