# src/utils/db_utils.py

import psycopg2
import os
from contextlib import contextmanager
from typing import List, Dict, Optional
import json

@contextmanager
def get_db_connection():
    """
    Context manager for database connections
    Usage:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(...)
    """
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        port=os.getenv('DB_PORT', 5432),
        sslmode='require'
    )
    try:
        yield conn
    finally:
        conn.close()

def get_skills_by_type(skill_type: str) -> List[Dict]:
    """
    Get all active skills of a specific type from database
    
    Args:
        skill_type: 'technical' or 'soft'
    
    Returns:
        List of skill dictionaries
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT skill_name, skill_type, frequency, fetch_priority
            FROM skills
            WHERE skill_type = %s AND is_active = TRUE
            ORDER BY fetch_priority DESC, frequency DESC
        """, (skill_type,))
        
        skills = []
        for row in cursor.fetchall():
            skills.append({
                'skill_name': row[0],
                'skill_type': row[1],
                'frequency': row[2],
                'fetch_priority': row[3]
            })
        
        return skills

def ensure_skill_exists(skill_name: str, skill_type: str = 'other'):
    """Ensure a skill exists in the database"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO skills (skill_name, skill_type, frequency, fetch_priority, is_active)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (skill_name) DO NOTHING
        """, (skill_name, skill_type, 0, 1, True))
        
        conn.commit()

def insert_learning_resource(
    resource_url: str,
    resource_type: str,
    title: str,
    description: str,
    platform: str,
    popularity_score: int,
    engagement_score: int,
    metadata: Dict,
    published_at: str,
    skill_name: str,
    relevance_score: float,
    learning_score: float,
    detected_from: str
) -> Optional[int]:
    """
    Insert a learning resource and link it to a skill
    
    Returns:
        resource_id if successful, None otherwise
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        try:
            # Ensure skill exists
            ensure_skill_exists(skill_name, 'technical' if resource_type == 'github_repo' else 'soft')
            
            # Insert resource
            cursor.execute("""
                INSERT INTO learning_resources 
                (resource_url, resource_type, title, description, platform, 
                 popularity_score, engagement_score, metadata, published_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (resource_url) 
                DO UPDATE SET
                    popularity_score = EXCLUDED.popularity_score,
                    engagement_score = EXCLUDED.engagement_score,
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    last_updated = NOW()
                RETURNING resource_id
            """, (
                resource_url,
                resource_type,
                title,
                description,
                platform,
                popularity_score,
                engagement_score,
                json.dumps(metadata),
                published_at
            ))
            
            resource_id = cursor.fetchone()[0]
            
            # Link to skill
            cursor.execute("""
                INSERT INTO resource_skills 
                (resource_id, skill_name, relevance_score, learning_score, detected_from)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (resource_id, skill_name) 
                DO UPDATE SET
                    relevance_score = EXCLUDED.relevance_score,
                    learning_score = EXCLUDED.learning_score,
                    detected_at = NOW()
            """, (
                resource_id,
                skill_name,
                relevance_score,
                learning_score,
                detected_from
            ))
            
            conn.commit()
            return resource_id
            
        except Exception as e:
            print(f"Error inserting resource: {e}")
            conn.rollback()
            return None

def update_skill_last_fetched(skill_name: str):
    """Update the last_fetched timestamp for a skill"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE skills
            SET last_fetched = NOW()
            WHERE skill_name = %s
        """, (skill_name,))
        
        conn.commit()