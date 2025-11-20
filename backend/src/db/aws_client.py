# backend/src/db/aws_client.py
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

def get_learning_resources_for_skills(skill_names: List[str], limit_per_skill: int = 5) -> Dict[str, List[Dict]]:
    """
    Get learning resources for given skills from resource_skills and learning_resources tables.
    
    Args:
        skill_names: List of skill names to get resources for
        limit_per_skill: Maximum number of resources to return per skill
    
    Returns:
        Dict mapping skill_name to list of resources, ordered by relevance and learning score
    """
    if not skill_names:
        return {}
    
    try:
        conn = get_postgres_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Query to get resources for skills, ordered by relevance and learning scores
        query = """
            SELECT 
                rs.skill_name,
                lr.resource_id,
                lr.resource_url,
                lr.resource_type,
                lr.title,
                lr.description,
                lr.platform,
                lr.popularity_score,
                lr.engagement_score,
                rs.relevance_score,
                rs.learning_score,
                (rs.relevance_score + rs.learning_score) as combined_score
            FROM resource_skills rs
            JOIN learning_resources lr ON rs.resource_id = lr.resource_id
            WHERE LOWER(rs.skill_name) = ANY(%s)
            ORDER BY rs.skill_name, combined_score DESC, lr.popularity_score DESC
        """
        
        # Convert to lowercase for case-insensitive matching
        lowercase_names = [name.lower() for name in skill_names]
        
        cursor.execute(query, (lowercase_names,))
        results = cursor.fetchall()
        cursor.close()
        
        # Group resources by skill name
        resources_by_skill = {}
        for row in results:
            skill = row['skill_name']
            
            if skill not in resources_by_skill:
                resources_by_skill[skill] = []
            
            # Only add up to limit_per_skill resources
            if len(resources_by_skill[skill]) < limit_per_skill:
                resources_by_skill[skill].append({
                    'resource_id': row['resource_id'],
                    'resource_url': row['resource_url'],
                    'resource_type': row['resource_type'],
                    'title': row['title'],
                    'description': row['description'],
                    'platform': row['platform'],
                    'popularity_score': float(row['popularity_score']) if row['popularity_score'] else 0,
                    'engagement_score': float(row['engagement_score']) if row['engagement_score'] else 0,
                    'relevance_score': float(row['relevance_score']) if row['relevance_score'] else 0,
                    'learning_score': float(row['learning_score']) if row['learning_score'] else 0
                })
        
        print(f"[PostgreSQL] Found resources for {len(resources_by_skill)} skills")
        return resources_by_skill
        
    except Exception as e:
        print(f"[PostgreSQL] Error querying learning resources: {e}")
        import traceback
        print(traceback.format_exc())
        return {}

def close_postgres_connection():
    """Close PostgreSQL connection."""
    global _pg_connection
    if _pg_connection and not _pg_connection.closed:
        _pg_connection.close()
        print("[PostgreSQL] Connection closed")