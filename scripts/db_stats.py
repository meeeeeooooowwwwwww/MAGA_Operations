import sqlite3

def show_table_counts():
    conn = sqlite3.connect('maga_ops.db')
    cursor = conn.cursor()
    
    tables = [
        'entities', 
        'politicians', 
        'influencers', 
        'committees', 
        'committee_memberships', 
        'district_offices', 
        'executive_officials', 
        'social_posts'
    ]
    
    print('Database Table Counts:')
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f'{table}: {count} records')
        except sqlite3.OperationalError as e:
            print(f'{table}: Error - {e}')
    
    conn.close()

if __name__ == "__main__":
    show_table_counts() 