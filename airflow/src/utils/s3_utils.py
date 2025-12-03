# src/utils/s3_utils.py

import boto3
import json
from datetime import datetime
from typing import Dict, List, Any
import os

# Initialize S3 client
s3_client = boto3.client('s3', region_name='us-east-1')

# Your bucket name
BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'skillminer-buckets3')

def upload_json_to_s3(data: Dict or List, key: str) -> bool:
    """
    Upload JSON data to S3
    
    Args:
        data: Dictionary or list to upload
        key: S3 key (path) for the file
    
    Returns:
        True if successful, False otherwise
    """
    try:
        json_data = json.dumps(data, indent=2, default=str)
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=key,
            Body=json_data,
            ContentType='application/json'
        )
        print(f"✓ Uploaded to s3://{BUCKET_NAME}/{key}")
        return True
    except Exception as e:
        print(f"✗ Error uploading to S3: {e}")
        return False

def upload_raw_github_response(skill_name: str, repos: List[Dict]) -> bool:
    """
    Upload raw GitHub API response to S3
    
    Args:
        skill_name: Name of the skill
        repos: List of repository dictionaries from GitHub API
    
    Returns:
        True if successful
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_skill = skill_name.replace(' ', '_').replace('/', '_')
    key = f"github_responses/{safe_skill}_{timestamp}.json"
    
    data = {
        'skill': skill_name,
        'timestamp': timestamp,
        'count': len(repos),
        'repos': repos
    }
    
    return upload_json_to_s3(data, key)

def upload_raw_youtube_response(skill_name: str, videos: List[Dict]) -> bool:
    """
    Upload raw YouTube API response to S3
    
    Args:
        skill_name: Name of the skill
        videos: List of video dictionaries from YouTube API
    
    Returns:
        True if successful
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_skill = skill_name.replace(' ', '_').replace('/', '_')
    key = f"youtube_responses/{safe_skill}_{timestamp}.json"
    
    data = {
        'skill': skill_name,
        'timestamp': timestamp,
        'count': len(videos),
        'videos': videos
    }
    
    return upload_json_to_s3(data, key)