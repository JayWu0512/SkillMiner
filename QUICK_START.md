# Quick Start Guide - SkillMiner

## Prerequisites

- Python 3.8+ installed
- Node.js 18+ installed
- OpenAI API key

## Step 1: Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create `.env` file in `backend/` directory:**
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   MODEL_CHAT=gpt-4o-mini
   MODEL_EMBED=text-embedding-3-large
   TOP_K=6
   MAX_RESUME_CTX=4000
   MAX_USER_CTX=1200
   DATASET_PATH=../database/data/gold/role_skills_by_title.parquet
   CHROMA_DIR=./chroma
   ```

5. **Start the backend server:**
   ```bash
   uvicorn src.api.main:app --reload --port 8000
   ```

   You should see:
   ```
   INFO:     Uvicorn running on http://127.0.0.1:8000
   ```

6. **Test backend (in a new terminal):**
   ```bash
   curl http://localhost:8000/health
   ```
   
   Should return: `{"status":"ok"}`

## Step 2: Frontend Setup

1. **Open a new terminal and navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Create `.env` file in `frontend/` directory:**
   ```env
   VITE_API_BASE=http://localhost:8000
   ```

4. **Start the frontend server:**
   ```bash
   npm run dev
   ```

   You should see:
   ```
   VITE v6.x.x  ready in xxx ms
   ➜  Local:   http://localhost:3000/
   ```

## Step 3: Test the Application

1. **Open your browser:**
   - Go to `http://localhost:3000`
   - You should see the SkillMiner upload page

2. **Check backend connection:**
   - The page should show "✅ Backend connected" (green box)
   - If it shows "⚠️ Backend connection issue", check:
     - Backend is running on port 8000
     - No CORS errors in browser console (F12)

3. **Test upload:**
   - Click "Click to upload your resume"
   - Select a PDF file
   - Click "Upload Resume & Continue"
   - You should see success and the extracted text

## Troubleshooting

### Backend Issues

**Problem:** Backend won't start
- Check Python version: `python --version` (should be 3.8+)
- Check if port 8000 is already in use: `lsof -i :8000` (Mac/Linux) or `netstat -ano | findstr :8000` (Windows)
- Try a different port: `uvicorn src.api.main:app --reload --port 8001`

**Problem:** OpenAI API errors
- Verify your `OPENAI_API_KEY` is set correctly in `backend/.env`
- Check API key is valid and has credits

**Problem:** Dataset not found
- Verify the path in `DATASET_PATH` in `.env` is correct
- Check if `../database/data/gold/role_skills_by_title.parquet` exists

### Frontend Issues

**Problem:** Frontend won't start
- Check Node.js version: `node --version` (should be 18+)
- Delete `node_modules` and reinstall: `rm -rf node_modules && npm install`
- Check if port 3000 is already in use

**Problem:** Cannot connect to backend
- Verify `VITE_API_BASE=http://localhost:8000` in `frontend/.env`
- Restart the frontend dev server after creating/editing `.env`
- Check browser console (F12) for CORS errors
- Verify backend is running: `curl http://localhost:8000/health`

**Problem:** Upload fails
- Check browser console (F12) for error messages
- Verify file is PDF format
- Check file size (should be < 10MB)
- Check backend logs for errors

### CORS Issues

If you see CORS errors in the browser console:
1. Check `backend/src/api/main.py` has your frontend URL in `allow_origins`
2. Make sure backend is running
3. Clear browser cache and reload

## View API Documentation

Once backend is running:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Next Steps

After successful upload:
- The resume text will be extracted
- You can proceed to chat with the AI about your skills
- The RAG system will search for matching skills in the dataset

