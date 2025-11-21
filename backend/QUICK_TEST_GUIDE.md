# Quick Test Guide - Memory System

## Where Logs Appear

### ✅ Backend Logs (Python `print()` statements)
**Location**: Your terminal/console where you run the FastAPI server

**How to see them**:
1. Start your server: `uvicorn src.api.main:app --reload`
2. Watch the terminal window
3. All `print()` statements appear there in real-time

**Example output**:
```
[STM] Initializing STM for user: test-user-123
[LTM] Storing memory with embedding
[Memory] Memory updated successfully
```

### ❌ NOT in Web Browser Console
- Python `print()` statements do NOT appear in browser DevTools console
- They only appear in the backend terminal
- Frontend JavaScript `console.log()` appears in browser console

## Quick Test (5 minutes)

### Step 1: Start the server
```bash
cd backend
uvicorn src.api.main:app --reload
```

### Step 2: Send a test message with user_id

**On macOS/Linux (curl):**
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want to learn Python",
    "user_id": "test-user-123"
  }'
```

**On Windows PowerShell (Invoke-WebRequest):**
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/chat" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{
    "message": "I want to learn Python",
    "user_id": "test-user-123"
  }'
```

### Step 3: Check your terminal
You should see logs like:
```
[Memory] Building memory context for user: test-user-123
[STM] Adding message to STM
[LTM] Storing memory...
[Memory] Memory updated successfully
```

### Step 4: Send a follow-up message
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the best resources?",
    "user_id": "test-user-123"
  }'
```

### Step 5: Verify context retention
- Check terminal for `[STM]` logs showing previous conversation
- Check terminal for `[LTM]` logs showing memory retrieval
- The response should reference the previous "Python" conversation

## What Success Looks Like

### ✅ Working Correctly:
- Terminal shows `[STM]` and `[LTM]` logs
- No error messages
- Responses reference previous conversations
- Database has entries in `chat_ltm_memory` table

### ❌ Not Working:
- No `[STM]` or `[LTM]` logs (memory not being used)
- Error messages in terminal
- Responses don't remember previous conversations
- Database empty

## Common Issues

### "No logs appearing"
- Make sure you're looking at the **backend terminal**, not browser console
- Check that server is running
- Verify `user_id` is being sent in requests

### "spaCy model not found"
```bash
python -m spacy download en_core_web_sm
```

### "OpenAI/Supabase errors"
- Check `.env` file has correct API keys
- Verify Supabase connection

## Database Check

Run in Supabase SQL Editor:
```sql
-- Check if data is being stored
SELECT COUNT(*) FROM chat_ltm_memory;
SELECT COUNT(*) FROM chat_messages;
```

If counts are 0, memory isn't being stored (check logs for errors).

