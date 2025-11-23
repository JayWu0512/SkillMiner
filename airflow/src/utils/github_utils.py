import requests
import time
import os
from typing import List, Dict, Optional
from datetime import datetime, timezone

def get_github_headers():
    """Get GitHub API headers with authentication"""
    return {
        'Authorization': f"token {os.getenv('GITHUB_TOKEN')}",
        'Accept': 'application/vnd.github.v3+json'
    }

def check_rate_limit() -> tuple:
    """
    Check GitHub API rate limit
    
    Returns:
        (remaining_requests, reset_timestamp)
    """
    response = requests.get(
        'https://api.github.com/rate_limit',
        headers=get_github_headers()
    )
    data = response.json()
    search_limit = data['resources']['search']
    return search_limit['remaining'], search_limit['reset']

def wait_for_rate_limit_reset():
    """Wait until rate limit resets"""
    remaining, reset_time = check_rate_limit()
    
    if remaining <= 2:  # Leave small buffer
        wait_seconds = reset_time - time.time() + 5
        print(f"Rate limit reached. Waiting {wait_seconds/60:.1f} minutes...")
        if wait_seconds > 0:
            time.sleep(wait_seconds)
        print("Rate limit reset. Continuing...")
    
    return remaining

def is_likely_english(repo: Dict) -> bool:
    """
    Check if repo is likely English based on description
    """
    text_to_check = (repo.get('description', '') or '') + ' ' + repo.get('full_name', '')
    
    if not text_to_check:
        return True
    
    # Check for CJK characters (Chinese, Japanese, Korean)
    cjk_chars = sum(1 for char in text_to_check if 
                    '\u4e00' <= char <= '\u9fff' or  # Chinese
                    '\u3040' <= char <= '\u309f' or  # Hiragana
                    '\u30a0' <= char <= '\u30ff' or  # Katakana
                    '\uac00' <= char <= '\ud7af')    # Korean
    
    # Check for Cyrillic
    cyrillic_chars = sum(1 for char in text_to_check if '\u0400' <= char <= '\u04ff')
    
    total_non_latin = cjk_chars + cyrillic_chars
    
    # If more than 15% non-Latin, likely not English
    if len(text_to_check) > 0 and (total_non_latin / len(text_to_check)) > 0.15:
        return False
    
    return True

def calculate_learning_score_github(repo: Dict) -> float:
    """Calculate learning value score for GitHub repo (0-100)"""
    score = 0.0
    
    full_name_lower = repo['full_name'].lower()
    desc_lower = (repo.get('description') or '').lower()
    
    # Educational keywords
    educational_keywords = [
        'tutorial', 'learn', 'course', 'guide', 'beginner',
        'awesome', 'examples', 'projects', 'practice', 'introduction'
    ]
    
    for keyword in educational_keywords:
        if keyword in full_name_lower:
            score += 10
        if keyword in desc_lower:
            score += 5
    
    # Awesome lists get big bonus
    if 'awesome' in full_name_lower:
        score += 20
    
    # Stars bonus (capped)
    score += min(repo['stargazers_count'] / 100, 20)
    
    # Recent updates bonus
    try:
        updated_at = datetime.strptime(repo['updated_at'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
        days_since_update = (datetime.now(timezone.utc) - updated_at).days
        if days_since_update < 180:
            score += 10
    except:
        pass
    
    return min(score, 100.0)

def calculate_relevance_score(repo: Dict, skill: str) -> float:
    """Calculate how relevant a repo is to a specific skill (0-100)"""
    score = 0.0
    skill_lower = skill.lower()
    
    if skill_lower in repo['full_name'].lower():
        score += 40
    if skill_lower in (repo.get('description') or '').lower():
        score += 20
    if skill_lower in ' '.join(repo.get('topics', [])).lower():
        score += 30
    if skill_lower == (repo.get('language') or '').lower():
        score += 10
    
    return min(score, 100.0)

def search_github_repos(skill_name: str, max_results: int = 10) -> List[Dict]:
    """
    Search GitHub for educational repos about a skill
    
    Args:
        skill_name: The skill to search for
        max_results: Maximum number of results to return
    
    Returns:
        List of repo dictionaries
    """
    # Map skills to programming languages for better filtering
    skill_to_language = {
        'python': 'Python',
        'javascript': 'JavaScript',
        'java': 'Java',
        'c++': 'C++',
        'c#': 'C#',
        'go': 'Go',
        'rust': 'Rust',
        'typescript': 'TypeScript',
        'ruby': 'Ruby',
        'php': 'PHP',
    }
    
    skill_lower = skill_name.lower()
    
    # Add language filter if skill is a programming language
    if skill_lower in skill_to_language:
        lang_filter = f' language:{skill_to_language[skill_lower]}'
    else:
        # For non-language skills, prefer Python/JavaScript (most English content)
        lang_filter = ' language:Python OR language:JavaScript OR language:Jupyter-Notebook'
    
    queries = [
        f'awesome {skill_name}{lang_filter}',
        f'{skill_name} tutorial{lang_filter}',
        f'{skill_name} examples{lang_filter}',
    ]
    
    all_repos = []
    seen_urls = set()
    headers = get_github_headers()
    
    for query in queries:
        try:
            # Check rate limit
            wait_for_rate_limit_reset()
            
            url = f'https://api.github.com/search/repositories?q={query}&sort=stars&order=desc&per_page=5'
            response = requests.get(url, headers=headers)
            
            # Handle rate limiting
            if response.status_code == 403:
                print(f"Rate limit hit for query: {query}")
                wait_for_rate_limit_reset()
                response = requests.get(url, headers=headers)
            
            response.raise_for_status()
            results = response.json()
            
            if 'items' in results:
                for repo in results['items']:
                    # Skip duplicates
                    if repo['html_url'] in seen_urls:
                        continue
                    
                    # Skip non-English repos
                    if not is_likely_english(repo):
                        continue
                    
                    seen_urls.add(repo['html_url'])
                    all_repos.append(repo)
                    
                    if len(all_repos) >= max_results:
                        return all_repos
            
            # Rate limiting: 30 requests per minute = 2 seconds between requests
            time.sleep(2.5)
            
        except Exception as e:
            print(f"Error with query '{query}': {e}")
            continue
    
    return all_repos