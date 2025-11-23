from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
import time
import html
from typing import List, Dict

def get_youtube_client():
    """Get authenticated YouTube API client"""
    return build('youtube', 'v3', developerKey=os.getenv('YOUTUBE_API_KEY'))

def calculate_learning_score_youtube(video: Dict) -> float:
    """Calculate learning value score for YouTube video (0-100)"""
    score = 0.0
    
    # View count (popularity)
    score += min(video['view_count'] / 10000, 30)
    
    # Engagement rate
    if video['view_count'] > 0:
        engagement_rate = ((video['like_count'] + video['comment_count']) / video['view_count']) * 100
        score += min(engagement_rate * 10, 30)
    
    # Educational keywords
    title_desc = (video['title'] + ' ' + video.get('description', '')).lower()
    if any(word in title_desc for word in ['tutorial', 'guide', 'learn', 'training', 'course']):
        score += 20
    
    # TEDx or professional channels bonus
    channel_lower = video['channel_name'].lower()
    if 'tedx' in channel_lower or 'professional' in channel_lower or 'simplilearn' in channel_lower:
        score += 20
    
    return min(score, 100.0)

def search_youtube_videos(skill_name: str, max_results: int = 10) -> List[Dict]:
    """
    Search YouTube for educational videos about a skill
    
    Args:
        skill_name: The skill to search for
        max_results: Maximum number of results to return
    
    Returns:
        List of video dictionaries
    """
    youtube = get_youtube_client()
    
    queries = [
        f'{skill_name} skills tutorial',
        f'how to improve {skill_name}',
        f'effective {skill_name} skills',
    ]
    
    all_videos = {}  # Use dict to deduplicate by video_id
    
    for query in queries:
        try:
            # Search for videos
            search_request = youtube.search().list(
                part='snippet',
                q=query,
                type='video',
                order='relevance',
                maxResults=5,
                videoDuration='medium',  # 4-20 minutes
                relevanceLanguage='en'
            )
            
            search_response = search_request.execute()
            
            if 'items' not in search_response:
                continue
            
            # Get video IDs
            video_ids = [item['id']['videoId'] for item in search_response['items']]
            
            # Get detailed statistics
            stats_request = youtube.videos().list(
                part='statistics,contentDetails',
                id=','.join(video_ids)
            )
            
            stats_response = stats_request.execute()
            
            # Combine and store
            for search_item, stats_item in zip(search_response['items'], stats_response['items']):
                video_id = search_item['id']['videoId']
                
                # Skip if already have this video
                if video_id in all_videos:
                    continue
                
                # Decode HTML entities in title and description
                title = html.unescape(search_item['snippet']['title'])
                description = html.unescape(search_item['snippet']['description'])
                
                all_videos[video_id] = {
                    'video_id': video_id,
                    'title': title,
                    'channel_name': search_item['snippet']['channelTitle'],
                    'description': description,
                    'published_at': search_item['snippet']['publishedAt'],
                    'url': f"https://www.youtube.com/watch?v={video_id}",
                    'view_count': int(stats_item['statistics'].get('viewCount', 0)),
                    'like_count': int(stats_item['statistics'].get('likeCount', 0)),
                    'comment_count': int(stats_item['statistics'].get('commentCount', 0)),
                    'duration': stats_item['contentDetails']['duration'],
                    'query_used': query
                }
                
                if len(all_videos) >= max_results:
                    return list(all_videos.values())
            
            # Rate limiting
            time.sleep(1)
            
        except HttpError as e:
            print(f"YouTube API error for query '{query}': {e}")
            continue
        except Exception as e:
            print(f"Error with query '{query}': {e}")
            continue
    
    return list(all_videos.values())