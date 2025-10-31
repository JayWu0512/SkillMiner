import sqlite3
import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# PostgreSQL connection details from environment variables
PG_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

# SQLite database path from environment variable
SQLITE_DB = os.getenv('SQLITE_DB_PATH', 'data/skillminer.db')

def convert_sqlite_to_pg_type(sqlite_type: str) -> str:
    """Convert SQLite types to PostgreSQL types"""
    sqlite_type = sqlite_type.upper()
    type_mapping = {
        'INTEGER': 'INTEGER',
        'TEXT': 'TEXT',
        'REAL': 'REAL',
        'BLOB': 'BYTEA',
        'NUMERIC': 'NUMERIC',
    }
    
    for sqlite, pg in type_mapping.items():
        if sqlite in sqlite_type:
            return pg
    return 'TEXT'  # Default fallback

def migrate_table(sqlite_conn, pg_conn, table_name: str):
    """Migrate a single table from SQLite to PostgreSQL"""
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()
    
    print(f"\n📊 Migrating table: {table_name}")
    
    # Get table info from SQLite
    sqlite_cursor.execute(f"PRAGMA table_info({table_name})")
    columns = sqlite_cursor.fetchall()
    
    if not columns:
        print(f"⚠️  No columns found for {table_name}")
        return
    
    # Create table in PostgreSQL
    column_defs = []
    for col in columns:
        col_name = col[1]
        col_type = convert_sqlite_to_pg_type(col[2])
        not_null = "NOT NULL" if col[3] else ""
        pk = "PRIMARY KEY" if col[5] else ""
        column_defs.append(f"{col_name} {col_type} {not_null} {pk}".strip())
    
    create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(column_defs)})"
    
    try:
        pg_cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
        pg_cursor.execute(create_table_sql)
        print(f"✅ Created table: {table_name}")
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        return
    
    # Get all data from SQLite
    sqlite_cursor.execute(f"SELECT * FROM {table_name}")
    rows = sqlite_cursor.fetchall()
    
    if not rows:
        print(f"⚠️  No data to migrate for {table_name}")
        pg_conn.commit()
        return
    
    # Insert data into PostgreSQL
    column_names = [col[1] for col in columns]
    placeholders = ', '.join(['%s'] * len(column_names))
    insert_sql = f"INSERT INTO {table_name} ({', '.join(column_names)}) VALUES ({placeholders})"
    
    try:
        pg_cursor.executemany(insert_sql, rows)
        pg_conn.commit()
        print(f"✅ Migrated {len(rows)} rows to {table_name}")
    except Exception as e:
        print(f"❌ Error inserting data: {e}")
        pg_conn.rollback()

def main():
    print("🚀 Starting migration from SQLite to PostgreSQL\n")
    
    # Verify environment variables are set
    required_vars = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file")
        return
    
    # Connect to databases
    try:
        sqlite_conn = sqlite3.connect(SQLITE_DB)
        print(f"✅ Connected to SQLite: {SQLITE_DB}")
    except Exception as e:
        print(f"❌ Failed to connect to SQLite: {e}")
        return
    
    try:
        pg_conn = psycopg2.connect(**PG_CONFIG)
        print(f"✅ Connected to PostgreSQL: {PG_CONFIG['host']}")
    except Exception as e:
        print(f"❌ Failed to connect to PostgreSQL: {e}")
        print("Check your database credentials and network access")
        sqlite_conn.close()
        return
    
    # Get actual table names from SQLite
    sqlite_cursor = sqlite_conn.cursor()
    sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in sqlite_cursor.fetchall()]
    
    print(f"\n📋 Found tables in SQLite: {tables}")
    
    if not tables:
        print("⚠️  No tables found in SQLite database")
        sqlite_conn.close()
        pg_conn.close()
        return
    
    # Migrate all tables
    for table in tables:
        migrate_table(sqlite_conn, pg_conn, table)
    
    # Close connections
    sqlite_conn.close()
    pg_conn.close()
    
    print("\n🎉 Migration complete!")

if __name__ == "__main__":
    main()
