# airflow/dags/fetch_github_resources.py

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
import os


# Add src to Python path
sys.path.insert(0, '/opt/airflow') 
from src.utils.s3_utils import upload_raw_github_response
from src.utils.db_utils import get_skills_by_type, insert_learning_resource, update_skill_last_fetched
from src.utils.github_utils import (
    search_github_repos,
    calculate_learning_score_github,
    calculate_relevance_score
)

default_args = {
    'owner': 'skillminer',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(hours=2),
}

def fetch_github_resources_for_all_skills(**context):
    """
    Fetch GitHub repos for all technical skills
    """
    print("Starting GitHub resource fetch...")
    
    # Get all technical skills
    skills = get_skills_by_type('technical')
    print(f"Found {len(skills)} technical skills to process")
    
    total_resources_added = 0
    skills_processed = 0
    
    for i, skill_data in enumerate(skills, 1):
        skill_name = skill_data['skill_name']
        print(f"\n[{i}/{len(skills)}] Processing: {skill_name}")
        
        try:
            # Search GitHub for repos
            repos = search_github_repos(skill_name, max_results=10)
            
            if not repos:
                print(f"  No repos found for {skill_name}")
                continue
            
            try:
                upload_raw_github_response(skill_name, repos)
            except Exception as e:
                print(f"  Warning: Failed to upload to S3: {e}")
                
            skill_resources = 0
            
            # Insert each repo
            for repo in repos:
                try:
                    # Calculate scores
                    learning_score = calculate_learning_score_github(repo)
                    relevance_score = calculate_relevance_score(repo, skill_name)
                    
                    # Prepare metadata
                    metadata = {
                        'owner': repo['owner']['login'],
                        'repo_name': repo['name'],
                        'language': repo.get('language', ''),
                        'topics': repo.get('topics', []),
                        'forks': repo['forks_count'],
                        'watchers': repo['watchers_count'],
                        'open_issues': repo['open_issues_count'],
                        'created_at': repo['created_at'],
                        'updated_at': repo['updated_at']
                    }
                    
                    # Insert into database
                    resource_id = insert_learning_resource(
                        resource_url=repo['html_url'],
                        resource_type='github_repo',
                        title=repo['full_name'],
                        description=repo.get('description', '')[:500] if repo.get('description') else '',
                        platform='github',
                        popularity_score=repo['stargazers_count'],
                        engagement_score=repo['forks_count'],
                        metadata=metadata,
                        published_at=repo['created_at'],
                        skill_name=skill_name,
                        relevance_score=relevance_score,
                        learning_score=learning_score,
                        detected_from=f"weekly_fetch_{datetime.now().strftime('%Y%m%d')}"
                    )
                    
                    if resource_id:
                        skill_resources += 1
                        total_resources_added += 1
                    
                except Exception as e:
                    print(f"  Error inserting repo {repo.get('html_url', 'unknown')}: {e}")
                    continue
            
            print(f"  ✓ Added {skill_resources} repos for {skill_name}")
            
            # Update last_fetched timestamp
            update_skill_last_fetched(skill_name)
            skills_processed += 1
            
        except Exception as e:
            print(f"  ✗ Error processing {skill_name}: {e}")
            continue
    
    print(f"\n{'='*60}")
    print(f"GitHub Fetch Complete!")
    print(f"Skills processed: {skills_processed}/{len(skills)}")
    print(f"Total resources added/updated: {total_resources_added}")
    print(f"{'='*60}")
    
    # Push metrics to XCom for monitoring
    context['task_instance'].xcom_push(key='skills_processed', value=skills_processed)
    context['task_instance'].xcom_push(key='resources_added', value=total_resources_added)

# Define the DAG
dag = DAG(
    'fetch_github_resources_weekly',
    default_args=default_args,
    description='Fetch GitHub repositories for technical skills (Weekly)',
    schedule_interval='0 2 * * 0',  # Every Sunday at 2 AM
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['skillminer', 'github', 'weekly'],
)

# Define tasks
fetch_github_task = PythonOperator(
    task_id='fetch_github_resources',
    python_callable=fetch_github_resources_for_all_skills,
    dag=dag,
)

# Task dependencies (just one task for now)
fetch_github_task