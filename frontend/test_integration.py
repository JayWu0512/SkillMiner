#!/usr/bin/env python3
"""
Test script to verify SkillMiner Agent integration
"""

import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.models import AnalysisRequest
from src.analyzer import SkillGapAnalyzer


def test_basic_analysis():
    """Test basic skill gap analysis functionality."""
    
    print("🔍 Testing SkillMiner Agent Integration...")
    
    # Sample job description
    job_description = """
    Senior Data Scientist Position
    
    We are seeking a Senior Data Scientist to join our AI team.
    
    Required Skills:
    - Python programming (5+ years)
    - Machine Learning and Deep Learning
    - SQL and database management
    - Statistical analysis and hypothesis testing
    - Data visualization (matplotlib, seaborn, plotly)
    
    Preferred Skills:
    - TensorFlow or PyTorch experience
    - Cloud platforms (AWS, Azure)
    - Docker containerization
    - Agile development experience
    """
    
    # Sample resume text
    resume_text = """
    John Doe - Data Analyst
    
    Experience:
    - 3 years of Python development
    - Proficient in SQL and PostgreSQL
    - Experience with pandas, numpy, matplotlib
    - Basic machine learning with scikit-learn
    - Statistical analysis and A/B testing
    - Git version control
    
    Education:
    - MS in Statistics
    - BS in Computer Science
    """
    
    try:
        # Initialize analyzer
        analyzer = SkillGapAnalyzer()
        print("✅ Analyzer initialized successfully")
        
        # Create analysis request
        request = AnalysisRequest(
            job_description=job_description,
            resume_text=resume_text
        )
        
        # Perform analysis
        result = analyzer.analyze(request)
        print("✅ Analysis completed successfully")
        
        # Display results
        print(f"\n📊 Analysis Results:")
        print(f"Job Title: {result.job_title}")
        print(f"Match Score: {result.match_score:.1f}%")
        print(f"Required Skills: {len(result.required_skills)}")
        print(f"Existing Skills: {len(result.existing_skills)}")
        print(f"Missing Skills: {len(result.missing_skills)}")
        print(f"Skill Gaps: {len(result.skill_gaps)}")
        
        print(f"\n📝 Summary: {result.summary}")
        
        if result.missing_skills:
            print(f"\n❌ Missing Skills: {', '.join(result.missing_skills[:5])}")
        
        if result.recommendations:
            print(f"\n💡 Top Recommendations:")
            for i, rec in enumerate(result.recommendations[:3], 1):
                print(f"   {i}. {rec}")
        
        print("\n✅ Integration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_skill_extraction():
    """Test skill extraction functionality."""
    
    print("\n🔧 Testing Skill Extraction...")
    
    try:
        from src.skill_extractor import SkillExtractor
        
        extractor = SkillExtractor()
        print("✅ Skill extractor initialized")
        
        # Test text
        test_text = "I have 5 years of Python experience and expertise in machine learning, SQL, and Docker."
        
        skills = extractor.extract_skills_from_text(test_text)
        print(f"✅ Extracted {len(skills)} skills from test text")
        
        for skill in skills[:5]:  # Show first 5
            print(f"   - {skill.name} ({skill.level or 'unknown level'})")
        
        return True
        
    except Exception as e:
        print(f"❌ Skill extraction test failed: {e}")
        return False


if __name__ == "__main__":
    print("🚀 SkillMiner Agent Integration Test\n")
    
    success = True
    success &= test_skill_extraction()
    success &= test_basic_analysis()
    
    if success:
        print("\n🎉 All tests passed! The SkillMiner Agent is ready to use.")
        print("\nTo start the web interface, run:")
        print("   python main.py")
        print("\nThen open http://localhost:8000 in your browser")
    else:
        print("\n💥 Some tests failed. Please check the error messages above.")
        sys.exit(1)