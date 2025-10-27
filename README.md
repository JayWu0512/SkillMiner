# SkillMiner

AI-powered job skills analysis and career development platform.

## Overview

SkillMiner consists of two main components:

1. **Database Pipeline** (`database/`) - ETL pipeline for processing job posting data and extracting skill insights
2. **SkillMiner Agent** (`frontend/`) - AI-powered web interface for skill gap analysis and career recommendations

## Quick Start

### SkillMiner Agent (Recommended)

The SkillMiner Agent provides an intuitive web interface for analyzing skill gaps between job requirements and your resume:

```bash
# Easy startup (from project root)
python3 start_skillminer.py

# Or manually
cd frontend
python3 start.py

# Or with uvicorn directly
cd frontend
python3 -m uvicorn src.api:app --host 0.0.0.0 --port 8000
```

Open http://localhost:8000 to access the web interface.

**Features:**
- Upload job descriptions and resumes (PDF/DOCX)
- AI-powered skill extraction and matching
- Personalized gap analysis and recommendations
- RESTful API for external integrations

### Database Pipeline

For data processing and building the skills database:

```bash
cd database
pip install -r requirements.txt
make all
```

## Architecture

```
SkillMiner/
├── database/           # Data processing pipeline
│   ├── src/           # Core data processing logic
│   ├── data/          # Raw, bronze, silver, gold data layers
│   └── notebooks/     # Analysis and insights
└── frontend/          # SkillMiner Agent web interface
    ├── src/           # FastAPI application
    ├── templates/     # Web UI
    └── static/        # Frontend assets
```

## Use Cases

- **Job Seekers**: Analyze skill gaps and get personalized learning recommendations
- **Career Counselors**: Provide data-driven career guidance
- **HR Teams**: Screen candidates and identify skill requirements
- **Recruiters**: Match candidates to positions more effectively
- **Developers**: Integrate skill analysis into existing platforms via API

## API Integration

```python
import requests

# Analyze skills programmatically
response = requests.post("http://localhost:8000/api/analyze-json", json={
    "job_description": "Data Scientist role requiring Python, ML, SQL...",
    "resume_text": "Experienced Python developer with 3 years..."
})

result = response.json()
print(f"Match Score: {result['match_score']:.1f}%")
```

See `frontend/api_client_example.py` for complete integration examples.