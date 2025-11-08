# Backend Connection Summary - Figma New Frontend

## ✅ Connections Completed

### 1. Upload Page Connection ✅

**Component:** `src/components/mockups/UploadPageMockup.tsx`
**Backend Endpoint:** `POST /upload`

**Features Added:**
- ✅ Backend health check on page load
- ✅ PDF file upload to backend
- ✅ Resume text extraction
- ✅ Stores resume text in localStorage for chatbot access
- ✅ Error handling with user-friendly messages
- ✅ Connection status indicator
- ✅ Loading states during upload

**How it works:**
1. User selects a PDF file
2. Clicks "Analyze My Skills"
3. File is uploaded to `http://localhost:8000/upload`
4. Backend extracts text from PDF
5. Resume text is stored in localStorage
6. Custom event is dispatched to notify chatbot
7. User is redirected to next page

### 2. Persistent Chatbot Connection ✅

**Component:** `src/components/mockups/PersistentChatbot.tsx`
**Backend Endpoint:** `POST /chat`

**Features Added:**
- ✅ RAG-powered chat with resume context
- ✅ Automatically loads resume text from localStorage
- ✅ Listens for resume text updates (cross-page communication)
- ✅ Citations display (shows references from dataset)
- ✅ Error handling
- ✅ Loading states (typing indicator)
- ✅ Works on all pages (right-side window)

**How it works:**
1. Chatbot loads resume text from localStorage on mount
2. User types a message
3. Message is sent to `http://localhost:8000/chat` with resume context
4. Backend uses RAG to retrieve relevant skills
5. AI generates response with citations
6. Response is displayed with citation badges

## API Service Layer

**File:** `src/services/api.ts`

Provides centralized backend communication:
- `checkHealth()` - Test backend connection
- `uploadResume()` - Upload PDF resume
- `sendChatMessage()` - Send chat message with RAG
- `getApiBase()` - Get API base URL

## Data Flow

### Upload Flow:
```
User selects PDF → UploadPageMockup
  ↓
uploadResume() → POST /upload
  ↓
Backend extracts text
  ↓
Stored in localStorage
  ↓
Custom event dispatched
  ↓
Chatbot receives update
```

### Chat Flow:
```
User types message → PersistentChatbot
  ↓
sendChatMessage() → POST /chat
  ↓
Backend RAG retrieval + OpenAI
  ↓
Returns { reply, citations }
  ↓
Displayed with citation badges
```

## Resume Text Sharing

The resume text is shared between components via:
1. **localStorage** - Stores resume text persistently
2. **Custom Events** - Notifies chatbot when resume is uploaded
3. **Storage Events** - Handles cross-tab communication

## Environment Setup

Make sure you have a `.env` file in `figma_new/` directory:

```env
VITE_API_BASE=http://localhost:8000
```

## Testing

### Test Upload:
1. Start backend: `cd backend && uvicorn src.api.main:app --reload --port 8000`
2. Start frontend: `cd figma_new && npm run dev`
3. Go to Upload tab in mockup mode
4. Upload a PDF resume
5. Should see "✅ Backend connected" status
6. After upload, resume text is stored and chatbot is notified

### Test Chatbot:
1. After uploading resume, go to any page with PersistentChatbot
2. Click the chatbot button (bottom-right)
3. Type a question like: "What skills are most relevant to my resume?"
4. Should see AI response with citations
5. Citations appear as badges below the response

## Features

### Upload Page:
- ✅ Backend health check indicator
- ✅ PDF-only file validation
- ✅ Real-time upload progress
- ✅ Error messages
- ✅ Resume text storage

### Chatbot:
- ✅ Persistent across all pages
- ✅ Resume context awareness
- ✅ RAG-powered responses
- ✅ Citation display
- ✅ Auto-updates when resume is uploaded
- ✅ Error handling
- ✅ Loading states

## Notes

- The chatbot appears on all pages that include `<PersistentChatbot />`
- Resume text is automatically loaded when chatbot opens
- Citations show references from the dataset
- All API calls use the centralized service layer
- Error messages are user-friendly and actionable

## Next Steps

Everything is connected! The upload page and chatbot are now fully integrated with the backend API.

