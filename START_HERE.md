# 🚀 Start Here: Quick Commands

## Run Everything (Two Terminals)

### Terminal 1 - Backend:
```bash
cd /Users/hejiang/Desktop/SkillMiner/backend
source venv/bin/activate  # If using venv
uvicorn src.api.main:app --reload --port 8000
```

### Terminal 2 - Frontend:
```bash
cd /Users/hejiang/Desktop/SkillMiner/figma_new
npm run dev
```

## Open in Browser

**URL:** `http://localhost:3000`

## Stop Everything

Press `Ctrl+C` in both terminals

---

## How It Works (Simple Explanation)

### The Connection Chain:

```
Frontend Component
    ↓ (calls)
API Service (api.ts)
    ↓ (HTTP request)
Backend Endpoint (FastAPI)
    ↓ (processes)
Returns JSON Response
    ↓ (parsed by)
API Service
    ↓ (returns to)
Frontend Component
```

### Example: Upload Resume

1. **User uploads PDF** → `UploadPageMockup.tsx`
2. **Calls** → `uploadResume(file)` in `api.ts`
3. **Sends** → `POST http://localhost:8000/upload`
4. **Backend processes** → Extracts text from PDF
5. **Returns** → `{"text": "...", "status": "success"}`
6. **Frontend receives** → Stores text in `localStorage`

### Example: Chat Message

1. **User types message** → `PersistentChatbot.tsx`
2. **Calls** → `sendChatMessage(message, resumeText)` in `api.ts`
3. **Sends** → `POST http://localhost:8000/chat`
4. **Backend retrieves** → Relevant skills from ChromaDB (RAG)
5. **Backend calls** → OpenAI API with context
6. **Returns** → `{"reply": "...", "citations": [...]}`
7. **Frontend displays** → AI response with citations

---

## Files That Connect Everything

### Frontend:
- `figma_new/src/services/api.ts` - **API Service Layer** (the bridge)
- `figma_new/src/components/mockups/UploadPageMockup.tsx` - Uses `uploadResume()`
- `figma_new/src/components/mockups/PersistentChatbot.tsx` - Uses `sendChatMessage()`

### Backend:
- `backend/src/api/main.py` - **CORS configuration** (allows frontend)
- `backend/src/api/routers/upload.py` - `POST /upload` endpoint
- `backend/src/api/routers/chat.py` - `POST /chat` endpoint

---

## Configuration Files

### Backend `.env`:
```env
OPENAI_API_KEY=your_key_here
DATASET_PATH=../database/data/gold/role_skills_by_title.parquet
```

### Frontend `.env`:
```env
VITE_API_BASE=http://localhost:8000
```

---

## Troubleshooting

### Backend won't start?
```bash
# Kill process on port 8000
kill -9 $(lsof -ti:8000)

# Restart
cd backend
uvicorn src.api.main:app --reload --port 8000
```

### Frontend won't start?
```bash
# Kill process on port 3000
kill -9 $(lsof -ti:3000)

# Restart
cd figma_new
npm run dev
```

### Connection errors?
1. Check backend is running: `curl http://localhost:8000/health`
2. Check `.env` files are correct
3. Check browser console (F12) for errors

---

## Full Documentation

- **Complete Guide:** `COMPLETE_GUIDE.md`
- **Connection Diagram:** `CONNECTION_DIAGRAM.md`
- **Quick Run:** `QUICK_RUN.md`

