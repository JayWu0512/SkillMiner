#!/usr/bin/env python3
"""
SkillMiner Startup Script
Convenient way to start the SkillMiner Agent
"""

import subprocess
import sys
import os
from pathlib import Path


def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import fastapi
        import polars
        import uvicorn
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install dependencies first:")
        print("   cd frontend && pip install -r requirements.txt")
        return False


def main():
    """Start the SkillMiner Agent."""
    
    print("🚀 Starting SkillMiner Agent...")
    
    # Check if we're in the right directory
    if not Path("frontend").exists():
        print("❌ Please run this script from the SkillMiner root directory")
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Change to frontend directory
    os.chdir("frontend")
    
    try:
        print("🌐 Starting web server on http://localhost:8000")
        print("📊 SkillMiner Agent will be available in your browser")
        print("⏹️  Press Ctrl+C to stop the server\n")
        
        # Start the server using uvicorn directly with import string
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "src.api:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ])
        
    except KeyboardInterrupt:
        print("\n👋 SkillMiner Agent stopped")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()