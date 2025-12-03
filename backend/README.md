[![Python Template for SkillMiner/backend](https://github.com/JayWu0512/SkillMiner/actions/workflows/backend-ci.yml/badge.svg)](https://github.com/JayWu0512/SkillMiner/actions/workflows/backend-ci.yml)

# SkillMiner Backend API

FastAPI-based backend service for SkillMiner, providing career guidance, resume analysis, and skill matching capabilities.

## Features

- **RAG-powered Chat**: Intelligent career advice using Retrieval-Augmented Generation
- **Resume Analysis**: PDF parsing and skill gap analysis
- **Study Plan Generation**: Personalized learning roadmaps
- **Docker Support**: Run backend standalone using Docker or Docker Compose  

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
│   └── integration/      # Integration tests
├── supabase/             # Database migrations
├── chroma/               # ChromaDB vector store
├── Dockerfile            # Backend Dockerfile
└── docker-compose.yml    # Run backend using Docker Compose
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

### 3. Run the Server

Start the development server with auto-reload:

```bash
uvicorn src.api.main:app --reload --port 8000
```

For production:

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`. API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

# Running Backend with Docker

The backend supports standalone Docker and Docker Compose execution.

---

## 1. Build the Docker Image

From the `backend/` directory:

```bash
docker build -t skillminer-backend .
```

## 2. Run the Container

```bash
docker run -p 8000:8000 --env-file .env skillminer-backend
```

Backend will be available at:

http://localhost:8000/docs

---

# Running via Docker Compose (Recommended)

The `backend/docker-compose.yml` makes development easier with hot reload and mounted volumes.

### docker-compose.yml (reference)

```yaml
version: "3.9"

services:
  backend:
    build: .
    container_name: skillminer-backend
    env_file:
      - .env
    ports:
      - "8000:8000"
    volumes:
      - .:/app
      - ./chroma:/app/chroma
    command: uvicorn src.api.main:app --port 8000 --reload
    restart: unless-stopped
```

### Start backend using Compose

```bash
docker compose up --build
```

After initial build:

```bash
docker compose up
```

Stop:

```bash
docker compose down
```

## RAG (Retrieval-Augmented Generation)

The backend uses RAG to provide context-aware responses by:

1. **Vector Store**: ChromaDB stores embeddings of job roles and skills
2. **Retrieval**: Semantic search retrieves relevant skills based on user queries
3. **Context Building**: Retrieved context is combined with resume text and user messages
4. **LLM Generation**: OpenAI GPT models generate responses with relevant context

### RAG Components

- **Retriever** (`src/rag/retriever.py`): Handles vector similarity search
- **Parser** (`src/rag/parser.py`): Parses PDF resumes and extracts text
- **ChromaDB**: Persistent vector database for skill embeddings

## Testing

### Run Tests Locally

```bash
make test
```

### Run Tests in CI Mode (Quiet)

```bash
make test-ci
```

### Run Specific Test Files

```bash
# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run specific test file
pytest tests/unit/test_rag_retriever.py
```

### Run Linting

```bash
make lint
```

### Test Coverage

```bash
pytest --cov=src --cov-report=html
```

## API Endpoints

- `GET /health` - Health check
- `POST /chat` - Chat with career assistant (RAG-powered)
- `POST /upload` - Upload and parse resume PDF
- `POST /analysis` - Analyze skill gaps
- `POST /study-plan` - Generate study plan
- `GET /study-plan/{plan_id}` - Get study plan by ID

### Example: Chat Endpoint

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What skills should I learn for data science?",
    "resume_text": "I have experience with Python and SQL."
  }'
```

### Example: Upload Resume

```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@resume.pdf"
```

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
