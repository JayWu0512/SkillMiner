# SkillMiner Agent - Quick Start Guide

## 🚀 Getting Started

### 1. Start the Server

Choose one of these methods:

**Option A: Simple Startup (Recommended)**
```bash
cd frontend
python3 start.py
```

**Option B: From Project Root**
```bash
python3 start_skillminer.py
```

**Option C: Direct Uvicorn**
```bash
cd frontend
python3 -m uvicorn src.api:app --host 0.0.0.0 --port 8000
```

### 2. Access the Web Interface

Open your browser and go to: **http://localhost:8000**

### 3. Use the Application

1. **Paste a job description** in the text area
2. **Upload your resume** (PDF or DOCX format) - optional
3. **Click "Analyze Skills"**
4. **Review the results**:
   - Match score percentage
   - Required vs existing skills
   - Missing skills to develop
   - Personalized recommendations

## 🔧 API Usage

### Health Check
```bash
curl http://localhost:8000/api/health
```

### Analyze Skills (JSON)
```bash
curl -X POST "http://localhost:8000/api/analyze-json" \
  -H "Content-Type: application/json" \
  -d '{
    "job_description": "Data Scientist role requiring Python, ML, SQL...",
    "resume_text": "Experienced Python developer with 3 years..."
  }'
```

### Analyze with File Upload
```bash
curl -X POST "http://localhost:8000/api/analyze" \
  -F "job_description=Software Engineer position..." \
  -F "resume_file=@resume.pdf"
```

### Get Available Skills
```bash
curl http://localhost:8000/api/skills
```

## 📊 Sample Analysis

**Input:**
- Job: "Senior Data Scientist requiring Python, machine learning, and SQL"
- Resume: "Python developer with 3 years experience, familiar with pandas and numpy"

**Output:**
- Match Score: 65%
- Existing Skills: Python (intermediate)
- Missing Skills: machine learning, SQL
- Recommendations: Take ML course, practice SQL queries

## 🛠️ Troubleshooting

### Dependencies Missing
```bash
pip install fastapi uvicorn polars pydantic python-docx PyPDF2 pdfplumber
```

### Port Already in Use
Change the port in the startup command:
```bash
python3 -m uvicorn src.api:app --host 0.0.0.0 --port 8001
```

### Database Not Found
The agent works with built-in skills but performs better with the SkillMiner database:
```bash
cd ../database
make all  # Build the skills database
```

## 🎯 Next Steps

1. **Try different job descriptions** to see how analysis changes
2. **Upload various resume formats** to test parsing
3. **Use the API** to integrate with your own applications
4. **Customize skill patterns** in `src/skill_extractor.py`
5. **Add new recommendation logic** in `src/analyzer.py`

## 📚 Documentation

- **Full API docs**: http://localhost:8000/docs (when server is running)
- **Implementation details**: See `SKILLMINER_AGENT_SUMMARY.md`
- **Code examples**: Check `api_client_example.py`