# Memory-Augmented LSTM System

This directory contains the Memory-Augmented LSTM implementation for chat context retention.

## Components

### 1. `lstm_memory.py`
Base LSTM Encoder-Decoder architecture with memory fusion capabilities.

### 2. `stm.py` (Short-Term Memory)
- Maintains recent conversation summaries
- Uses pre-trained summarization models (BART/T5)
- Token limit controller for memory management
- In-memory storage per user session

### 3. `ltm.py` (Long-Term Memory)
- Semantic embeddings using OpenAI's text-embedding-3-large
- Named Entity Recognition (NER) using spaCy
- Database storage in Supabase
- Semantic similarity retrieval

## Setup

### Install Dependencies
```bash
pip install torch transformers spacy sentencepiece
```

### Install spaCy Model
```bash
python -m spacy download en_core_web_sm
```

### Database Setup
1. **Enable pgvector extension** in Supabase:
   - Go to Supabase Dashboard → Database → Extensions
   - Search for "vector" and click "Enable"

2. **Run the migration SQL file** to create the LTM table:
   ```sql
   -- See: backend/supabase/migrations/create_ltm_memory_table.sql
   ```
   
   This migration will:
   - Create the `chat_ltm_memory` table with vector(1536) column
   - Create vector similarity index for fast retrieval
   - Create RPC function `match_ltm_memories` for optimized similarity search
   - Set up Row Level Security (RLS) policies

## Configuration

Environment variables (in `.env`):
- `STM_MAX_MESSAGES`: Number of recent messages in STM (default: 15)
- `STM_MAX_TOKENS`: Max tokens in STM summary (default: 500)
- `LTM_TOP_K`: Number of LTM entries to retrieve (default: 5)
- `LTM_SIMILARITY_THRESHOLD`: Min similarity for retrieval (default: 0.7)
- `NER_MODEL`: spaCy model name (default: "en_core_web_sm")
- `SUMMARIZATION_MODEL`: HuggingFace model (default: "facebook/bart-large-cnn")

## Usage

The memory system is automatically integrated into the chat endpoint. Simply include `user_id` in the `ChatRequest`:

```python
{
    "message": "What skills should I learn?",
    "user_id": "user-uuid-here",
    "resume_text": "optional resume text"
}
```

The system will:
1. Retrieve STM summary of recent conversations
2. Retrieve relevant LTM memories based on semantic similarity
3. Combine with current input and RAG context
4. Update STM and LTM after each conversation turn

## Architecture

```
User Message
    ↓
[STM Retrieval] → Recent conversation summary
    ↓
[LTM Retrieval] → pgvector similarity search + NER entities
    ↓
[Memory Fusion] → Combined context
    ↓
[RAG Retrieval] → External knowledge
    ↓
[LLM] → Response
    ↓
[Memory Update] → Update STM & LTM (vector embeddings stored)
```

## Vector Similarity Search

The system uses **pgvector** for efficient vector similarity search:

- **Storage**: Embeddings stored as `vector(1536)` type in PostgreSQL
- **Index**: IVFFlat index for fast approximate nearest neighbor search
- **Search**: Uses cosine distance (`<=>`) operator for similarity matching
- **RPC Function**: `match_ltm_memories()` provides optimized similarity search

The code automatically uses the RPC function when available, with a Python fallback for compatibility.

