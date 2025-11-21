# API Keys Required for Memory System

## Required API Keys

### ✅ OPENAI_API_KEY (Required)
**Used for**: Semantic embeddings (LTM module)

**Why needed**: The LTM module uses OpenAI's `text-embedding-3-large` model to generate embeddings for semantic similarity search.

**How to get**: 
1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Add to `.env` file:

```env
OPENAI_API_KEY=sk-...
```

**Already in use**: This key is already used by your existing RAG system, so you should already have it.

## Optional API Keys

### ⚠️ HF_TOKEN or HUGGINGFACE_TOKEN (Optional)
**Used for**: BART summarization model downloads (STM module)

**Why might be needed**:
- HuggingFace Hub allows anonymous downloads, but has rate limits
- If you hit rate limits, you'll see errors like "429 Too Many Requests"
- Having a token increases download limits

**When to add**:
- Only if you see rate limit errors when downloading BART model
- Or if you want to use private HuggingFace models

**How to get**:
1. Go to https://huggingface.co/settings/tokens
2. Create a token (read access is enough)
3. Add to `.env` file (optional):

```env
HF_TOKEN=hf_...
# OR
HUGGINGFACE_TOKEN=hf_...
```

**Default behavior**: Works without token for public models, but may hit rate limits.

## No API Key Needed

### ✅ spaCy (No API key)
**Used for**: Named Entity Recognition (NER) in LTM module

**Why no key needed**: spaCy is a local library that downloads models to your machine. No API calls are made.

**Setup**: Just install the model locally:
```bash
python -m spacy download en_core_web_sm
```

## Summary

### Minimum Required (System will work):
```env
OPENAI_API_KEY=sk-...
```

### Recommended (If you hit HuggingFace rate limits):
```env
OPENAI_API_KEY=sk-...
HF_TOKEN=hf_...
```

### Complete Example `.env` file:
```env
# Required
OPENAI_API_KEY=sk-...

# Optional (only if needed)
HF_TOKEN=hf_...

# Supabase (already have these)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_key

# Other existing keys...
MODEL_CHAT=gpt-4o-mini
MODEL_EMBED=text-embedding-3-large
```

## Testing Without API Keys

### If OPENAI_API_KEY is missing:
- ❌ LTM embeddings won't work
- ✅ STM summarization will still work (uses BART locally)
- ✅ NER will still work (uses spaCy locally)
- ⚠️ You'll see warnings: `[LTM] Warning: Could not initialize OpenAI client`

### If HF_TOKEN is missing:
- ✅ System will still work
- ⚠️ First model download might be slower or hit rate limits
- ✅ Once model is downloaded, no API calls needed

## Error Messages to Watch For

### OpenAI API Key Missing:
```
[LTM] Warning: Could not initialize OpenAI client: OPENAI_API_KEY is not set
[LTM] Warning: OpenAI client not available, cannot generate embeddings
```

### HuggingFace Rate Limit (if no token):
```
429 Client Error: Too Many Requests for url: https://huggingface.co/...
```

**Solution**: Add `HF_TOKEN` to `.env` or wait a bit and try again.

## Current Status

Based on your existing setup, you should already have:
- ✅ `OPENAI_API_KEY` (used by RAG system)
- ✅ `SUPABASE_URL` and `SUPABASE_KEY` (used by database)

**You only need to add**:
- ⚠️ `HF_TOKEN` (optional, only if you hit rate limits)

