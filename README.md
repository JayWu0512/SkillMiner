![Python Version](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)

[![SkillMiner Backend CI Check](https://github.com/JayWu0512/SkillMiner/actions/workflows/backend-ci.yml/badge.svg)](https://github.com/JayWu0512/SkillMiner/actions/workflows/backend-ci.yml)
[![SkillMiner Database CI Check](https://github.com/JayWu0512/SkillMiner/actions/workflows/database-ci.yml/badge.svg)](https://github.com/JayWu0512/SkillMiner/actions/workflows/database-ci.yml)

![Vercel Deploy](https://deploy-badge.vercel.app/vercel/skillminer?style=plastic&logo=Vercel&name=Vercel)
![Railway Deploy](https://deploy-badge.vercel.app/?url=https%3A%2F%2Fskillminer-production.up.railway.app%2F&style=plastic&logo=Railway&name=Railway)
# SkillMiner

SkillMiner is an AI-powered career & study copilot.  
It analyzes your resume, extracts skills, identifies gaps, retrieves learning resources, and generates a personalized study plan powered by an LLM agent, RAG system, and a modern data engineering pipeline.

Please watch our demo video! [Click here](https://youtu.be/5HNZr0QxKIk)

### Try SkillMiner Now — Click Below to Explore!

https://skillminer.vercel.app/

## System Architecture

![SkillMiner Architecture](docs/skillminer-architecture.png)


## Repository Structure

```
.
├─ .github/                   # GitHub Actions (CI/CD pipelines)
├─ airflow/                   # Airflow DAGs, scheduler, ETL pipeline (AWS EC2 in production)
├─ backend/                   # FastAPI backend, RAG, Agent services (Dockerified)
├─ database/                  # Data scripts, ETL, test data generator
├─ docs/                      # Architecture diagrams, documentation
├─ figma-mockups/            # UI mockups
├─ frontend/                  # React/Vite frontend client (Dockerified)
├─ docker-compose.yml         # Run full system with Docker
├─ LICENSE
└─ README.md         
```


# Getting Started — Local Development

SkillMiner consists of:

- **Frontend** — React/Vite (local) → production on **Vercel**
- **Backend** — FastAPI (local) → production on **Railway**
- **Database** — Supabase (PostgreSQL + Auth), AWS (S3, RDS)
- **ETL & Data Infra** — Airflow, S3, RDS, Polars
- **Full Docker Support** — frontend + backend + airflow + helper jobs


# Running Full Stack (Docker)

The easiest way to start all services:

### 1. From the project root:

```bash
docker compose up --build
```

### 2. After the first build:

```bash
docker compose up
```

### 3. Stop all services:

```bash
docker compose down
```


# Service URLs (Docker Mode)

| Service        | URL |
|----------------|---------------------------|
| **Frontend**   | http://localhost:3000     |
| **Backend**    | http://localhost:8000/docs |
| **Airflow UI** | http://localhost:8080     |


# Standalone Service Development

You can still run each service independently using its local Docker Compose.


## Standalone Backend (FastAPI)

```bash
cd backend
docker compose up --build
```

Backend endpoints:  
http://localhost:8000/docs


## Standalone Frontend (React/Vite)

```bash
cd frontend
docker compose up --build
```

Frontend:  
http://localhost:3000


## Standalone Airflow (ETL Pipeline)

```bash
cd airflow
docker compose up --build
```

Airflow UI:  
http://localhost:8080  

## AWS Airflow (Production)

Production Airflow runs on AWS EC2 with automated learning resource collection:
```bash
# Deploy to EC2
cd airflow
docker-compose up airflow-init
docker-compose up -d
```

**Services:**
- EC2 (t2.medium) — Airflow scheduler + webserver
- S3 — Raw API responses (`github_responses/`, `youtube_responses/`)
- RDS PostgreSQL — Skills taxonomy + learning resources

**DAGs:**
- `fetch_github_resources_weekly` — Sundays 2:00 AM UTC
- `fetch_youtube_resources_weekly` — Sundays 3:00 AM UTC

Environment setup in `airflow/.env`:
```bash
DB_HOST=your-rds-endpoint.rds.amazonaws.com
S3_BUCKET_NAME=your-bucket-name
GITHUB_TOKEN=your_token
YOUTUBE_API_KEY=your_key
```

# Backend Setup (Without Docker)

```bash
cd backend
pip install -r ../requirements.txt
cp .env.example .env
uvicorn src.api.main:app --reload --port 8000
```

# Database Setup
```bash
cd database
make install
python scripts/download_kaggle.py
```

**Production databases:**
- Supabase → User auth, chat history
- AWS RDS → Skills, learning resources (auto-populated by Airflow)
- AWS S3 → API response archive

# Frontend Setup (Without Docker)

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Open:  
http://localhost:3000


# Manual Full-Stack (Without Docker)

```bash
cd backend && uvicorn src.api.main:app --reload --port 8000
cd frontend && npm run dev
```

# CI/CD & Deployment

## GitHub Actions (CI)

Located in:

```
.github/workflows/backend-ci.yml
.github/workflows/database-ci.yml
```

## Frontend Deployment — Vercel

Set environment variable:

```
API_BASE=https://your-backend-railway-url
```

## Backend Deployment — Railway

Use environment variables defined in `backend/.env.example`.


# License

See LICENSE file.


---
---

# Appendix - Undercurrents of Data Engineering

SkillMiner is built following modern Data Engineering principles to ensure the system is **scalable, modular, observable, secure, and production-ready**. Below are the key principles demonstrated in this project.

---

### **1. Scalability**

SkillMiner scales across compute and data layers:

- Stateless FastAPI backend allows horizontal scaling.
- Supabase externalizes authentication and database state.
- ChromaDB embeddings stored in mounted volumes support scalable vector search.
- Airflow ETL uses LocalExecutor but can scale to CeleryExecutor without code changes.

---

### **2. Modularity**

The system is separated into fully independent modules:

- `backend/` — API, LLM agent, RAG pipeline  
- `frontend/` — React/Vite UI  
- `database/` — ETL scripts & data management  
- `airflow/` — Orchestration layer  
- `docker-compose.yml` — Multi-service orchestration  

Each component can be developed, deployed, and tested independently.

---

### **3. Reusability**

SkillMiner avoids duplication through shared logical units:

- Shared Python utilities reused by RAG, agent, and API layers.
- Reusable UI components in frontend (header, chatbot, cards, layout).
- Reusable Airflow operators enabling modular DAG design.
- Embedding logic reused for study plans, resume analysis, and skill inference.

---

### **4. Observability**

The system supports effective monitoring:

- FastAPI structured logging (under `core/logging`).
- Airflow UI provides DAG visibility, task retries, logs, and lineage.
- Docker logs expose runtime for all services.
- GitHub Actions logs tests, coverage, lint results.

---

### **5. Data Governance**

Data is validated, structured, and securely handled:

- Supabase enforces schema integrity and row-level security.
- Resume text used for RAG is kept ephemeral unless stored intentionally.
- Airflow pipelines enforce lineage between ingestion → transform → output.
- ETL scripts ensure deterministic and reproducible workflows.

---

### **6. Reliability**

The system is built for dependable execution:

- Test suite includes unit + integration tests.
- Airflow retry policies protect long-running data pipelines.
- Docker containers ensure consistent runtime environments.
- CI rejects broken builds via linting + tests.

---

### **7. Efficiency**

The platform optimizes latency and compute usage:

- ChromaDB allows fast vector retrieval.
- Polars accelerates ETL transformations dramatically.
- Cached embeddings reduce redundant computation.
- Streaming responses reduce latency in conversations.

---

### **8. Security**

Security is implemented at multiple levels:

- Supabase Auth ensures secure identity + session management.
- Sensitive credentials stored in environment variables, not in code.
- File uploads sanitized before processing.
- API request validation using Pydantic models.
- Production deployments (Vercel/Railway) enforce HTTPS.
