import sqlite3
import json

def get_db_schemas(start_from="committees"):
    conn = sqlite3.connect('maga_ops.db')
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [table[0] for table in cursor.fetchall()]
    
    # Find the index to start from
    if start_from in tables:
        start_index = tables.index(start_from)
    else:
        start_index = 0
    
    # Get schema for each table
    print("Table schemas (continued):")
    for table in tables[start_index:]:
        try:
            cursor.execute(f"PRAGMA table_info('{table}')")
            columns = cursor.fetchall()
            print(f"\n{table}:")
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
        except sqlite3.OperationalError:
            print(f"  Error getting schema for {table}")
    
    conn.close()

if __name__ == "__main__":
    get_db_schemas() 