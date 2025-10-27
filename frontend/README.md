# SkillMiner Agent UI

AI-powered skill gap analysis that compares resumes against job requirements and provides actionable recommendations.

## Features

- **Job Description Analysis**: Extracts required skills and their importance levels
- **Resume Parsing**: Supports PDF and DOCX file uploads with text extraction
- **Skill Matching**: Leverages the existing SkillMiner database for comprehensive skill recognition
- **Gap Analysis**: Identifies missing skills and skill level gaps
- **Actionable Recommendations**: Provides specific learning paths and improvement suggestions
- **API Interface**: RESTful API for external integrations

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**:
   ```bash
   python main.py
   ```

3. **Access the UI**:
   Open http://localhost:8000 in your browser

## API Usage

### Analyze with Form Data
```bash
curl -X POST "http://localhost:8000/api/analyze" \
  -F "job_description=Software Engineer position requiring Python, SQL, and machine learning experience..." \
  -F "resume_file=@resume.pdf"
```

### Analyze with JSON
```bash
curl -X POST "http://localhost:8000/api/analyze-json" \
  -H "Content-Type: application/json" \
  -d '{
    "job_description": "Data Scientist role...",
    "resume_text": "Experienced Python developer with 5 years..."
  }'
```

### Get Available Skills
```bash
curl "http://localhost:8000/api/skills"
```

## Architecture

- **FastAPI**: Web framework and API server
- **Polars**: Data processing (leverages existing database transformers)
- **Document Parsing**: PDF/DOCX text extraction
- **Skill Extraction**: NLP-based skill identification and matching
- **Gap Analysis**: Intelligent comparison and recommendation engine

## Integration with Existing Database

The agent leverages the existing SkillMiner database structure:
- Uses `database/data/gold/top_skills.parquet` for skill recognition
- Integrates with `database/data/gold/role_skills_by_title.parquet` for role-specific analysis
- Reuses transformers from `database/src/infra/transformers.py`

## File Structure

```
frontend/
├── src/
│   ├── api.py              # FastAPI application
│   ├── models.py           # Pydantic data models
│   ├── document_parser.py  # PDF/DOCX text extraction
│   ├── skill_extractor.py  # Skill identification and matching
│   ├── analyzer.py         # Gap analysis and recommendations
│   ├── templates/          # HTML templates
│   └── static/             # CSS/JS assets
├── requirements.txt        # Python dependencies
├── main.py                # Application entry point
└── README.md              # This file
```

## Configuration

The analyzer automatically detects and uses the database from `../database/` relative to the frontend directory. Ensure the SkillMiner database has been built using the existing pipeline.

## Development

To extend the analyzer:

1. **Add new skill patterns** in `skill_extractor.py`
2. **Customize recommendations** in `analyzer.py`
3. **Modify UI** in `templates/index.html` and `static/app.js`
4. **Add API endpoints** in `api.py`