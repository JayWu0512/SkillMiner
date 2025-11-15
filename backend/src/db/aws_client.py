# backend/src/db/postgres_client.py
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional, List, Dict

_pg_connection = None

def get_postgres_connection():
    """Get or create PostgreSQL connection singleton."""
    global _pg_connection
    
    if _pg_connection is None or _pg_connection.closed:
        db_host = os.getenv("DB_HOST")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME")
        db_user = os.getenv("DB_USER")
        db_password = os.getenv("DB_PASSWORD")
        
        if not all([db_host, db_name, db_user, db_password]):
            raise RuntimeError(
                "Database credentials missing. Check DB_HOST, DB_NAME, DB_USER, DB_PASSWORD in .env"
            )
        
        try:
            _pg_connection = psycopg2.connect(
                host=db_host,
                port=db_port,
                database=db_name,
                user=db_user,
                password=db_password
            )
            print(f"[PostgreSQL] Connected to {db_name}")
        except Exception as e:
            raise RuntimeError(f"Failed to connect to PostgreSQL: {str(e)}")
    
    return _pg_connection

def get_skills_by_names(skill_names: List[str]) -> List[Dict]:
    """
    Query skills table by skill names.
    Returns list of matching skills with their type (technical/soft).
    """
    if not skill_names:
        return []
    
    try:
        conn = get_postgres_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Query for matching skills (case-insensitive)
        query = """
            SELECT skill_name, skill_type, frequency, fetch_priority
            FROM skills
            WHERE LOWER(skill_name) = ANY(%s)
            AND is_active = true
        """
        
        # Convert to lowercase for case-insensitive matching
        lowercase_names = [name.lower() for name in skill_names]
        
        cursor.execute(query, (lowercase_names,))
        results = cursor.fetchall()
        cursor.close()
        
        # Convert to list of dicts
        return [dict(row) for row in results]
        
    except Exception as e:
        print(f"[PostgreSQL] Error querying skills: {e}")
        return []

def close_postgres_connection():
    """Close PostgreSQL connection."""
    global _pg_connection
    if _pg_connection and not _pg_connection.closed:
        _pg_connection.close()
        print("[PostgreSQL] Connection closed")