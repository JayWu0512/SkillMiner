#!/usr/bin/env python3
"""
Example API client for SkillMiner Agent
Demonstrates how to integrate with the SkillMiner API programmatically
"""

import requests
import json
from pathlib import Path


class SkillMinerClient:
    """Client for interacting with SkillMiner Agent API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
    
    def analyze_text(self, job_description: str, resume_text: str = None) -> dict:
        """
        Analyze skills using text input.
        
        Args:
            job_description: The job posting text
            resume_text: Optional resume text
            
        Returns:
            Analysis result dictionary
        """
        url = f"{self.base_url}/api/analyze-json"
        
        payload = {
            "job_description": job_description,
            "resume_text": resume_text
        }
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        return response.json()
    
    def analyze_with_file(self, job_description: str, resume_file_path: str) -> dict:
        """
        Analyze skills with resume file upload.
        
        Args:
            job_description: The job posting text
            resume_file_path: Path to PDF or DOCX resume file
            
        Returns:
            Analysis result dictionary
        """
        url = f"{self.base_url}/api/analyze"
        
        files = {
            'resume_file': open(resume_file_path, 'rb')
        }
        
        data = {
            'job_description': job_description
        }
        
        try:
            response = requests.post(url, files=files, data=data)
            response.raise_for_status()
            return response.json()
        finally:
            files['resume_file'].close()
    
    def get_available_skills(self) -> dict:
        """Get list of skills in the database."""
        url = f"{self.base_url}/api/skills"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    
    def health_check(self) -> dict:
        """Check if the API is healthy."""
        url = f"{self.base_url}/api/health"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()


def example_usage():
    """Demonstrate how to use the SkillMiner API client."""
    
    print("🚀 SkillMiner Agent API Client Example\n")
    
    # Initialize client
    client = SkillMinerClient()
    
    try:
        # Health check
        health = client.health_check()
        print(f"✅ API Health: {health['status']}")
        
        # Get available skills
        skills_info = client.get_available_skills()
        print(f"✅ Available skills: {skills_info['count']} skills in database")
        
        # Example job description
        job_description = """
        Machine Learning Engineer - Remote
        
        We're looking for a Machine Learning Engineer to build and deploy ML models.
        
        Required:
        - Python (3+ years)
        - Machine Learning frameworks (TensorFlow, PyTorch)
        - SQL and data manipulation
        - Cloud platforms (AWS or GCP)
        
        Preferred:
        - Docker and Kubernetes
        - MLOps experience
        - Statistics background
        """
        
        # Example resume text
        resume_text = """
        Jane Smith - Software Engineer
        
        Skills:
        - Python development (4 years)
        - TensorFlow and scikit-learn
        - SQL and PostgreSQL
        - AWS cloud services
        - Docker containerization
        - Git and CI/CD
        
        Experience:
        - Built recommendation systems
        - Deployed ML models to production
        - Data pipeline development
        """
        
        # Perform analysis
        print("\n🔍 Analyzing skills...")
        result = client.analyze_text(job_description, resume_text)
        
        # Display results
        print(f"\n📊 Analysis Results:")
        print(f"Job Title: {result['job_title']}")
        print(f"Match Score: {result['match_score']:.1f}%")
        print(f"Summary: {result['summary']}")
        
        print(f"\n✅ Skills You Have ({len(result['existing_skills'])}):")
        for skill in result['existing_skills'][:5]:
            level = f" ({skill['level']})" if skill.get('level') else ""
            print(f"   - {skill['name']}{level}")
        
        if result['missing_skills']:
            print(f"\n❌ Skills to Develop ({len(result['missing_skills'])}):")
            for skill in result['missing_skills'][:5]:
                print(f"   - {skill}")
        
        if result['recommendations']:
            print(f"\n💡 Top Recommendations:")
            for i, rec in enumerate(result['recommendations'][:3], 1):
                print(f"   {i}. {rec}")
        
        print("\n✅ API integration example completed successfully!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to SkillMiner API")
        print("Make sure the server is running: python main.py")
    except requests.exceptions.HTTPError as e:
        print(f"❌ API error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def batch_analysis_example():
    """Example of analyzing multiple job postings in batch."""
    
    print("\n📦 Batch Analysis Example")
    
    client = SkillMinerClient()
    
    # Sample job postings
    jobs = [
        {
            "title": "Data Scientist",
            "description": "Looking for a Data Scientist with Python, R, and machine learning experience..."
        },
        {
            "title": "Software Engineer", 
            "description": "Full-stack developer needed with JavaScript, React, Node.js, and database skills..."
        },
        {
            "title": "DevOps Engineer",
            "description": "DevOps role requiring Docker, Kubernetes, AWS, and CI/CD pipeline experience..."
        }
    ]
    
    resume_text = "Experienced developer with Python, JavaScript, Docker, and AWS skills..."
    
    results = []
    
    for job in jobs:
        try:
            result = client.analyze_text(job["description"], resume_text)
            results.append({
                "job_title": job["title"],
                "match_score": result["match_score"],
                "missing_count": len(result["missing_skills"])
            })
        except Exception as e:
            print(f"Error analyzing {job['title']}: {e}")
    
    # Sort by match score
    results.sort(key=lambda x: x["match_score"], reverse=True)
    
    print("\n🏆 Job Match Rankings:")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['job_title']}: {result['match_score']:.1f}% match "
              f"({result['missing_count']} skills to develop)")


if __name__ == "__main__":
    example_usage()
    batch_analysis_example()
    
    print("\n📚 Integration Examples:")
    print("1. Web scraping job boards and analyzing matches")
    print("2. Building a job recommendation system")
    print("3. Creating personalized learning paths")
    print("4. Integrating with HR systems for candidate screening")