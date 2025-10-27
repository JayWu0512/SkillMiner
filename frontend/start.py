#!/usr/bin/env python3
"""
Simple startup script for SkillMiner Agent
"""

import sys
import os
from pathlib import Path

def main():
    """Start the SkillMiner Agent with proper error handling."""
    
    print("🚀 Starting SkillMiner Agent...")
    
    try:
        # Check if we have the required dependencies
        import fastapi
        import uvicorn
        print("✅ Dependencies found")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install dependencies first:")
        print("   pip install -r requirements.txt")
        return False
    
    try:
        # Import and run the app
        from src.api import app
        
        print("🌐 Starting web server on http://localhost:8000")
        print("📊 SkillMiner Agent will be available in your browser")
        print("⏹️  Press Ctrl+C to stop the server\n")
        
        # Run without reload to avoid import string issues
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        print("\n👋 SkillMiner Agent stopped")
        return True
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        print("\nTrying alternative startup method...")
        
        # Fallback: use command line uvicorn
        try:
            import subprocess
            subprocess.run([
                sys.executable, "-m", "uvicorn", 
                "src.api:app", 
                "--host", "0.0.0.0", 
                "--port", "8000"
            ])
        except Exception as e2:
            print(f"❌ Fallback also failed: {e2}")
            return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)