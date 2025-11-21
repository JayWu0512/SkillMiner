# Testing the Memory-Augmented LSTM System

This guide explains how to test and verify that the memory system is working correctly.

## Where Logs Appear

### Backend Logs (Python print statements)
All `print()` statements in the code will appear in:
- **Your local terminal/console** where you run the FastAPI server
- Example: If you run `uvicorn src.api.main:app --reload`, logs appear in that terminal

### Log Messages to Look For

The system uses prefixed log messages for easy identification:
- `[STM]` - Short-Term Memory operations
- `[LTM]` - Long-Term Memory operations  
- `[Memory]` or `[MemoryChat]` - Memory service operations
- `[RAG]` - RAG retrieval (existing)
- `[Chat]` - Chat endpoint operations

## Testing Setup

### 1. Start the Backend Server

```bash
cd backend
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

Watch the terminal for any startup errors or warnings.

### 2. Verify Dependencies

Check that all dependencies are installed:
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 3. Verify Database Connection

Make sure your `.env` file has:
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
OPENAI_API_KEY=your_openai_key
```

## Testing Scenarios

### Test 1: Basic Chat Without Memory (Backward Compatibility)

**Purpose**: Verify the system works without `user_id` (backward compatible)

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What skills should I learn for data science?",
    "resume_text": "I have experience with Python and SQL."
  }'
```

**Expected Behavior**:
- Should work normally (no memory errors)
- No `[Memory]` logs should appear
- Response should be generated

### Test 2: First Chat with Memory (STM Initialization)

**Purpose**: Test STM initialization and first message storage

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want to become a data scientist. What should I learn?",
    "resume_text": "I have 2 years of Python experience.",
    "user_id": "test-user-123"
  }'
```

**What to Check in Terminal**:
```
[Memory] Building memory context for user: test-user-123
[STM] Initializing STM for user: test-user-123
[LTM] Storing memory for user: test-user-123
[Memory] Memory updated successfully
```

**Expected Behavior**:
- STM should initialize (no errors)
- LTM should store the message with embedding
- Response should be generated
- No errors in terminal

### Test 3: Multi-Turn Conversation (STM Summarization)

**Purpose**: Verify STM maintains conversation context across multiple turns

```bash
# Message 1
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want to learn machine learning",
    "user_id": "test-user-123"
  }'

# Message 2 (should reference previous conversation)
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the best resources for that?",
    "user_id": "test-user-123"
  }'

# Message 3 (should have context from both previous messages)
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How long will it take me?",
    "user_id": "test-user-123"
  }'
```

**What to Check in Terminal**:
```
[STM] Adding message to STM
[STM] Updating summary (conversation length: 2 messages)
[STM] Summarizing conversation (estimated tokens: 150)
[LTM] Retrieving memories for query: "What are the best resources for that?"
[LTM] Found 1 relevant memories
```

**Expected Behavior**:
- STM should show increasing message counts
- After a few messages, you should see summarization happening
- Responses should reference previous conversation context
- Assistant should remember what was discussed

### Test 4: LTM Semantic Retrieval

**Purpose**: Test long-term memory retrieval based on semantic similarity

```bash
# First, create some diverse conversations
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I work at Google as a software engineer",
    "user_id": "test-user-123"
  }'

curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I know Python, JavaScript, and React",
    "user_id": "test-user-123"
  }'

# Later, ask a semantically similar question
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What programming languages do I know?",
    "user_id": "test-user-123"
  }'
```

**What to Check in Terminal**:
```
[LTM] Generating embedding for query
[LTM] Calling RPC function: match_ltm_memories
[LTM] Retrieved 2 memories with similarity > 0.7
[LTM] Building summary from memories:
  - Skills mentioned: Python, JavaScript, React
  - Relevant context: I know Python, JavaScript, and React
```

**Expected Behavior**:
- LTM should retrieve the "I know Python..." message
- Response should mention the languages you mentioned
- Similarity scores should be logged

### Test 5: Error Handling and Fallbacks

**Purpose**: Verify graceful error handling

```bash
# Test with invalid user_id format (should still work)
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Test message",
    "user_id": "invalid-format"
  }'
```

**What to Check in Terminal**:
- If there are errors, they should be caught and logged
- System should fallback gracefully
- No crashes or unhandled exceptions

## Verification Checklist

### ✅ STM (Short-Term Memory) Working If:
- [ ] See `[STM]` logs in terminal
- [ ] STM summary appears in conversation context
- [ ] Multi-turn conversations maintain context
- [ ] Summarization happens when conversation gets long

### ✅ LTM (Long-Term Memory) Working If:
- [ ] See `[LTM]` logs in terminal
- [ ] See "Storing memory" messages after each chat
- [ ] See "Retrieving memories" messages during retrieval
- [ ] Similar past conversations are retrieved
- [ ] NER entities are extracted (skills, companies, etc.)

### ✅ Database Integration Working If:
- [ ] No database connection errors
- [ ] Messages are stored in `chat_messages` table
- [ ] LTM entries appear in `chat_ltm_memory` table
- [ ] Vector embeddings are stored (check `semantic_embedding` column)

### ✅ RPC Function Working If:
- [ ] See "Calling RPC function: match_ltm_memories" in logs
- [ ] No "RPC function not available" fallback messages
- [ ] Fast retrieval (no Python fallback)

## Debugging Common Issues

### Issue: "spaCy model not found"
**Solution**: Run `python -m spacy download en_core_web_sm`

### Issue: "OpenAI client not available"
**Solution**: Check `OPENAI_API_KEY` in `.env` file

### Issue: "Supabase not available"
**Solution**: Check `SUPABASE_URL` and `SUPABASE_KEY` in `.env`

### Issue: "RPC function not available"
**Solution**: Run the migration SQL to create `match_ltm_memories` function

### Issue: "Vector type error"
**Solution**: Ensure pgvector extension is enabled in Supabase

## Database Verification

### Check if data is being stored:

```sql
-- NOTE: user_id column is UUID. Use a real Supabase auth.users.id here.
-- Example placeholder UUID:
--   '00000000-0000-0000-0000-000000000000'

-- Check chat messages
SELECT id, user_id, role, content, created_at 
FROM chat_messages 
WHERE user_id = '00000000-0000-0000-0000-000000000000'
ORDER BY created_at DESC
LIMIT 10;

-- Check LTM memories
SELECT id, user_id, message_content, ner_entities, created_at
FROM chat_ltm_memory
WHERE user_id = '00000000-0000-0000-0000-000000000000'
ORDER BY created_at DESC
LIMIT 10;

-- Check if embeddings are stored (should show vector type)
SELECT id, semantic_embedding, pg_typeof(semantic_embedding) as embedding_type
FROM chat_ltm_memory
WHERE user_id = '00000000-0000-0000-0000-000000000000'
LIMIT 1;
```

### Test RPC function directly:

```sql
-- Get an embedding first
SELECT semantic_embedding FROM chat_ltm_memory LIMIT 1;

-- Then test the function (replace with actual embedding)
SELECT * FROM match_ltm_memories(
  query_embedding := (SELECT semantic_embedding FROM chat_ltm_memory LIMIT 1),
  match_user_id := '00000000-0000-0000-0000-000000000000'::uuid,
  match_threshold := 0.7,
  match_count := 5
);
```

## Performance Testing

### Test with many messages:

```bash
# Send 20 messages rapidly
for i in {1..20}; do
  curl -X POST "http://localhost:8000/chat" \
    -H "Content-Type: application/json" \
    -d "{\"message\": \"Message $i\", \"user_id\": \"test-user-123\"}"
  sleep 1
done
```

**What to Check**:
- STM should summarize after ~15 messages
- LTM retrieval should still be fast
- No memory leaks or performance degradation

## Expected Log Flow for a Working System

```
[Memory] Building memory context for user: test-user-123
[STM] Getting STM summary (0 messages)
[LTM] Retrieving memories for query: "What should I learn?"
[LTM] Generating embedding for query
[LTM] Calling RPC function: match_ltm_memories
[LTM] Retrieved 0 memories (first conversation)
[Memory] Combined context built successfully
[Chat] Sending to LLM...
[Memory] Updating memory after response
[STM] Adding message to STM (1 messages)
[LTM] Extracting NER entities
[LTM] Entities found: {'skills': ['Python'], 'roles': []}
[LTM] Storing memory with embedding
[LTM] Memory stored successfully (id: abc-123)
```

## Next Steps

1. Run through all test scenarios above
2. Check terminal logs for any errors
3. Verify database has data
4. Test with real user IDs from your frontend
5. Monitor performance with multiple users

