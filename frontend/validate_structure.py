#!/usr/bin/env python3
"""
Validate SkillMiner Agent structure and basic functionality
"""

import os
import sys
from pathlib import Path


def validate_file_structure():
    """Validate that all required files are present."""
    
    print("📁 Validating file structure...")
    
    required_files = [
        "src/__init__.py",
        "src/api.py", 
        "src/models.py",
        "src/document_parser.py",
        "src/skill_extractor.py",
        "src/analyzer.py",
        "src/templates/index.html",
        "src/static/app.js",
        "requirements.txt",
        "main.py",
        "README.md"
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
        else:
            print(f"   ✅ {file_path}")
    
    if missing_files:
        print(f"\n❌ Missing files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False
    
    print("✅ All required files present")
    return True


def validate_python_syntax():
    """Validate Python syntax in all Python files."""
    
    print("\n🐍 Validating Python syntax...")
    
    python_files = [
        "src/api.py",
        "src/models.py", 
        "src/document_parser.py",
        "src/skill_extractor.py",
        "src/analyzer.py",
        "main.py"
    ]
    
    errors = []
    
    for file_path in python_files:
        try:
            with open(file_path, 'r') as f:
                compile(f.read(), file_path, 'exec')
            print(f"   ✅ {file_path}")
        except SyntaxError as e:
            errors.append(f"{file_path}: {e}")
            print(f"   ❌ {file_path}: {e}")
        except Exception as e:
            errors.append(f"{file_path}: {e}")
            print(f"   ⚠️  {file_path}: {e}")
    
    if errors:
        print(f"\n❌ Syntax errors found:")
        for error in errors:
            print(f"   - {error}")
        return False
    
    print("✅ All Python files have valid syntax")
    return True


def validate_requirements():
    """Check requirements.txt format."""
    
    print("\n📦 Validating requirements...")
    
    try:
        with open("requirements.txt", 'r') as f:
            lines = f.readlines()
        
        print(f"   ✅ Found {len(lines)} dependencies")
        
        # Check for key dependencies
        content = ''.join(lines).lower()
        key_deps = ['fastapi', 'uvicorn', 'polars', 'pydantic']
        
        for dep in key_deps:
            if dep in content:
                print(f"   ✅ {dep}")
            else:
                print(f"   ⚠️  {dep} not found")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error reading requirements.txt: {e}")
        return False


def validate_database_integration():
    """Check if database integration paths are correct."""
    
    print("\n🗄️  Validating database integration...")
    
    # Check if database directory exists
    db_path = Path("../database")
    if db_path.exists():
        print("   ✅ Database directory found")
        
        # Check for key database files
        key_files = [
            "src/infra/transformers.py",
            "src/settings.py",
            "src/app/pipeline.py"
        ]
        
        for file_path in key_files:
            full_path = db_path / file_path
            if full_path.exists():
                print(f"   ✅ {file_path}")
            else:
                print(f"   ⚠️  {file_path} not found")
        
        return True
    else:
        print("   ⚠️  Database directory not found (../database)")
        print("   ℹ️  Agent will work with limited skill recognition")
        return True


def validate_html_template():
    """Basic validation of HTML template."""
    
    print("\n🌐 Validating HTML template...")
    
    try:
        with open("src/templates/index.html", 'r') as f:
            content = f.read()
        
        # Check for key elements
        required_elements = [
            '<form id="analysisForm"',
            'id="jobDescription"',
            'id="resumeFile"',
            'results-section'
        ]
        
        for element in required_elements:
            if element in content:
                print(f"   ✅ {element}")
            else:
                print(f"   ❌ Missing: {element}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error reading HTML template: {e}")
        return False


def main():
    """Run all validations."""
    
    print("🔍 SkillMiner Agent Structure Validation\n")
    
    # Change to frontend directory if not already there
    if Path("frontend").exists() and not Path("src").exists():
        os.chdir("frontend")
        print("📂 Changed to frontend directory\n")
    
    validations = [
        validate_file_structure,
        validate_python_syntax,
        validate_requirements,
        validate_database_integration,
        validate_html_template
    ]
    
    results = []
    
    for validation in validations:
        try:
            result = validation()
            results.append(result)
        except Exception as e:
            print(f"❌ Validation error: {e}")
            results.append(False)
    
    # Summary
    print(f"\n📊 Validation Summary:")
    passed = sum(results)
    total = len(results)
    
    print(f"   ✅ Passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All validations passed!")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Start the server: python main.py")
        print("3. Open http://localhost:8000 in your browser")
    else:
        print(f"\n⚠️  {total - passed} validation(s) failed")
        print("Please review the errors above before proceeding")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)