# Memory-Augmented LSTM Integration Plan

## Overview

Integrate a Memory-Augmented LSTM system into the chat endpoint to improve context retention across conversations. The system will maintain Short-Term Memory (STM) for recent context summarization and Long-Term Memory (LTM) for semantic embeddings and NER extraction.

## Architecture Components

### 1. LSTM Core Module (`backend/src/models/lstm_memory.py`)

- Base LSTM Encoder-Decoder architecture
- Input processing and tokenization
- Hidden state management
- Output generation

### 2. Short-Term Memory (STM) Module (`backend/src/models/stm.py`)

- **Summarization Layer**: Uses pre-trained summarization model (e.g., T5-small or BART) to condense recent conversations
- **Token Limit Controller**: Manages STM size, truncates/compresses when limit is reached
- In-memory storage (per session/user)
- Processes last N messages (configurable, default: 10-20 messages)

### 3. Long-Term Memory (LTM) Module (`backend/src/models/ltm.py`)

- **Semantic Search Embeddings**: Uses existing embedding model (text-embedding-3-large) to create semantic representations
- **NER (Named Entity Recognition)**: Uses spaCy or similar pre-trained NER model to extract entities (skills, companies, roles, etc.)
- Database storage in Supabase (new table: `chat_ltm_memory`)
- Retrieval based on semantic similarity to current query

### 4. Memory-Augmented Service (`backend/src/services/memory_augmented_chat.py`)

- Orchestrates STM and LTM retrieval
- Concatenates memory summaries with current input
- Manages memory updates after each conversation turn
- Integrates with existing chat flow

### 5. Database Schema Updates

- New Supabase table: `chat_ltm_memory` to store:
- `user_id` (UUID, references auth.users)
- `message_id` (UUID, references chat_messages)
- `semantic_embedding` (vector, using pgvector extension)
- `ner_entities` (JSONB: skills, companies, roles, etc.)
- `created_at` (timestamp)
- Update `chat_messages` table if needed to link with LTM

### 6. Chat Endpoint Integration (`backend/src/api/routers/chat.py`)

- Add `user_id` to `ChatRequest` schema (optional for backward compatibility)
- Retrieve chat history from Supabase
- Initialize/retrieve STM for user session
- Retrieve relevant LTM entries based on current query
- Concatenate STM + LTM + current input before passing to LLM
- Update STM and LTM after response generation

## Implementation Steps

### Phase 1: Core Infrastructure

1. Create model directory structure (`backend/src/models/`)
2. Install required dependencies (torch, transformers, spacy, pgvector)
3. Set up database schema for LTM storage
4. Create base LSTM architecture

### Phase 2: STM Implementation

1. Implement summarization layer using pre-trained model
2. Implement token limit controller
3. Create STM manager for in-memory storage
4. Add STM update logic after each conversation turn

### Phase 3: LTM Implementation

1. Implement semantic embedding extraction
2. Implement NER extraction using spaCy
3. Create LTM storage/retrieval functions
4. Add LTM update logic after each conversation turn

### Phase 4: Integration

1. Create memory-augmented chat service
2. Update chat endpoint to use memory system
3. Update ChatRequest schema to include user_id
4. Integrate with existing RAG retrieval (memory + RAG)

### Phase 5: Testing & Optimization

1. Test with multi-turn conversations
2. Optimize memory retrieval performance
3. Tune STM/LTM parameters (token limits, retrieval top-k)
4. Add error handling and fallbacks

## Key Files to Create/Modify

### New Files:

- `backend/src/models/__init__.py`
- `backend/src/models/lstm_memory.py` - Base LSTM architecture
- `backend/src/models/stm.py` - Short-Term Memory module
- `backend/src/models/ltm.py` - Long-Term Memory module
- `backend/src/services/memory_augmented_chat.py` - Memory orchestration service
- `backend/supabase/migrations/create_ltm_memory_table.sql` - Database schema

### Modified Files:

- `backend/src/schemas.py` - Add user_id to ChatRequest
- `backend/src/api/routers/chat.py` - Integrate memory system
- `backend/src/db/supabase_client.py` - Add LTM storage/retrieval functions
- `backend/requirements.txt` - Add dependencies (torch, transformers, spacy, pgvector)
- `backend/src/core/config.py` - Add memory-related configuration

## Configuration Parameters

- `STM_MAX_MESSAGES`: Number of recent messages to keep in STM (default: 15)
- `STM_MAX_TOKENS`: Maximum tokens in STM summary (default: 500)
- `LTM_TOP_K`: Number of LTM entries to retrieve (default: 5)
- `LTM_SIMILARITY_THRESHOLD`: Minimum similarity score for LTM retrieval (default: 0.7)
- `NER_MODEL`: spaCy model to use (default: "en_core_web_sm")

## Dependencies to Add

- `torch` - LSTM implementation
- `transformers` - Pre-trained summarization models
- `spacy` - NER extraction
- `pgvector` - Vector storage in Supabase (or use ChromaDB for vectors)

## Notes

- The LSTM architecture will be built by hand as specified
- STM and LTM components will use pre-trained models (summarization, embeddings, NER)
- STM stored in-memory (per user session)
- LTM stored in Supabase database with vector embeddings
- Memory system works alongside existing RAG retrieval
- Backward compatibility: user_id is optional in ChatRequest
