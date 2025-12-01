[![Python Template for SkillMiner/backend](https://github.com/JayWu0512/SkillMiner/actions/workflows/backend-ci.yml/badge.svg)](https://github.com/JayWu0512/SkillMiner/actions/workflows/backend-ci.yml)

# SkillMiner Backend API

FastAPI-based backend service for SkillMiner, providing career guidance, resume analysis, and skill matching capabilities.

## Features

- **RAG-powered Chat**: Intelligent career advice using Retrieval-Augmented Generation
- **Resume Analysis**: PDF parsing and skill gap analysis
- **Study Plan Generation**: Personalized learning roadmaps
- **Memory-Augmented Chat**: Context retention across conversations (optional)

## Project Structure

```
backend/
├── src/
│   ├── api/              # FastAPI routes and endpoints
│   ├── core/             # Configuration and logging
│   ├── db/               # Database clients (Supabase, AWS)
│   ├── llm/              # OpenAI client wrapper
│   ├── rag/              # RAG retrieval and PDF parsing
│   ├── services/         # Business logic services
│   └── util/             # Utility functions
├── tests/                # Test suite
│   ├── unit/             # Unit tests
│   └── integration/       # Integration tests
├── supabase/             # Database migrations
└── chroma/               # ChromaDB vector store

```

## Setup

### 1. Install Dependencies

```bash
make install
```

### 2. Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# Required
OPENAI_API_KEY=sk-...
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_key

# Optional
MODEL_CHAT=gpt-4o-mini
MODEL_EMBED=text-embedding-3-large
DATASET_PATH=../database/data/gold/role_skills_by_title.parquet
```

See `API_KEYS_REQUIRED.md` for detailed API key requirements.

### 3. Run the Server

```bash
uvicorn src.api.main:app --reload --port 8000
```

## Testing

### Run Tests Locally

```bash
make test
```

### Run Tests in CI Mode (Quiet)

```bash
make test-ci
```

### Run Linting

```bash
make lint
```

## API Endpoints

- `GET /health` - Health check
- `POST /chat` - Chat with career assistant
- `POST /upload` - Upload and parse resume PDF
- `POST /analysis` - Analyze skill gaps
- `POST /study-plan` - Generate study plan
- `GET /study-plan/{plan_id}` - Get study plan by ID

## CI/CD

This project includes a GitHub Actions workflow (`.github/workflows/backend-ci.yml`).  
Every push or pull request to `backend/` will:
- Install dependencies
- Lint code with flake8
- Run unit and integration tests with coverage reporting

## Notes

- Tests use mocking to avoid calling external APIs during CI
- Some tests may require API keys if they test actual integrations (currently mocked)
- The workflow includes optional secrets for `OPENAI_API_KEY`, `SUPABASE_URL`, and `SUPABASE_KEY` if needed for integration tests

