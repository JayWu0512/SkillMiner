# airflow/dags/fetch_youtube_resources.py

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
import os

# Add src to Python path
sys.path.insert(0, '/opt/airflow')
from src.utils.s3_utils import upload_raw_youtube_response
from src.utils.db_utils import get_skills_by_type, insert_learning_resource, update_skill_last_fetched
from src.utils.youtube_utils import search_youtube_videos, calculate_learning_score_youtube

default_args = {
    'owner': 'skillminer',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(hours=2),
}

def fetch_youtube_resources_for_all_skills(**context):
    """
    Fetch YouTube videos for all soft skills
    """
    print("Starting YouTube resource fetch...")
    
    # Get all soft skills
    skills = get_skills_by_type('soft')
    print(f"Found {len(skills)} soft skills to process")
    
    total_resources_added = 0
    skills_processed = 0
    
    for i, skill_data in enumerate(skills, 1):
        skill_name = skill_data['skill_name']
        print(f"\n[{i}/{len(skills)}] Processing: {skill_name}")
        
        try:
            # Search YouTube for videos
            videos = search_youtube_videos(skill_name, max_results=10)
            
            if not videos:
                print(f"  No videos found for {skill_name}")
                continue
            try:
                upload_raw_youtube_response(skill_name, videos)
            except Exception as e:
                print(f"  Warning: Failed to upload to S3: {e}")
            skill_resources = 0
            
            # Insert each video
            for video in videos:
                try:
                    # Calculate learning score
                    learning_score = calculate_learning_score_youtube(video)
                    relevance_score = 50.0  # Default for YouTube
                    
                    # Prepare metadata
                    metadata = {
                        'video_id': video['video_id'],
                        'channel': video['channel_name'],
                        'duration': video['duration'],
                        'likes': video['like_count'],
                        'comments': video['comment_count']
                    }
                    
                    # Insert into database
                    resource_id = insert_learning_resource(
                        resource_url=video['url'],
                        resource_type='youtube_video',
                        title=video['title'],
                        description=video.get('description', '')[:500] if video.get('description') else '',
                        platform='youtube',
                        popularity_score=video['view_count'],
                        engagement_score=video['like_count'],
                        metadata=metadata,
                        published_at=video['published_at'],
                        skill_name=skill_name,
                        relevance_score=relevance_score,
                        learning_score=learning_score,
                        detected_from=f"weekly_fetch_{datetime.now().strftime('%Y%m%d')}"
                    )
                    
                    if resource_id:
                        skill_resources += 1
                        total_resources_added += 1
                    
                except Exception as e:
                    print(f"  Error inserting video {video.get('url', 'unknown')}: {e}")
                    continue
            
            print(f"  ✓ Added {skill_resources} videos for {skill_name}")
            
            # Update last_fetched timestamp
            update_skill_last_fetched(skill_name)
            skills_processed += 1
            
        except Exception as e:
            print(f"  ✗ Error processing {skill_name}: {e}")
            continue
    
    print(f"\n{'='*60}")
    print(f"YouTube Fetch Complete!")
    print(f"Skills processed: {skills_processed}/{len(skills)}")
    print(f"Total resources added/updated: {total_resources_added}")
    print(f"{'='*60}")
    
    # Push metrics to XCom for monitoring
    context['task_instance'].xcom_push(key='skills_processed', value=skills_processed)
    context['task_instance'].xcom_push(key='resources_added', value=total_resources_added)

# Define the DAG
dag = DAG(
    'fetch_youtube_resources_weekly',
    default_args=default_args,
    description='Fetch YouTube videos for soft skills (Weekly)',
    schedule_interval='0 3 * * 0',  # Every Sunday at 3 AM (after GitHub finishes)
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['skillminer', 'youtube', 'weekly'],
)

# Define tasks
fetch_youtube_task = PythonOperator(
    task_id='fetch_youtube_resources',
    python_callable=fetch_youtube_resources_for_all_skills,
    dag=dag,
)

# Task dependencies
fetch_youtube_task