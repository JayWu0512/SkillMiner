
# SkillMiner

SkillMiner is an AI-powered career & study copilot.  
It analyzes your resume, extracts skills, identifies gaps, retrieves learning resources, and generates a personalized study plan powered by an LLM agent, RAG system, and a modern data engineering pipeline.

Please watch our demo video! [Click here](https://youtu.be/5HNZr0QxKIk)

---

## System Architecture

![SkillMiner Architecture](docs/skillminer-architecture.png)

---

## Repository Structure

```
.
├─ .github/              # GitHub Actions (CI/CD pipelines)
├─ backend/              # FastAPI backend, RAG, Agent, API Gateway
├─ database/             # DB schema, SQL migrations, seed files
├─ figma-mockups/        # UI mockups
├─ frontend/             # Next.js (React) frontend client
├─ LICENSE
├─ README.md            
```

---

# Getting Started (Local Development)

SkillMiner consists of:

- **Frontend** — Next.js (local) → production on **Vercel**
- **Backend** — FastAPI (local) → production on **Railway**
- **Database** — Supabase (PostgreSQL + Auth), AWS(S3, RDS)
- **ETL & Data Infra** — AWS EC2, Airflow, S3, RDS, Polars

---

# Backend Setup (FastAPI)

### Step 1 — enter backend

```bash
cd backend
```

### Step 2 — Install backend dependencies

```bash
pip install -r ../requirements.txt
```
(Python version: 3.11.13 (3.11.9 for windows))

### Step 3 — Create backend .env

```bash
cp .env.example .env
```

### Step 4 — Run backend

```bash
uvicorn src.api.main:app --reload --port 8000
```

Backend:

http://localhost:8000  
http://localhost:8000/docs

---

# Database Setup

### Step 1 — enter database

```bash
cd database
```

### Step 2 — Local ETL

```bash
python scripts/download_kaggle.py
make install
```

### (Optional)Supabase
https://supabase.com/docs/guides/getting-started

### (Optional)AWS
https://aws.amazon.com/tw/getting-started/

---

# Frontend Setup (Next.js)

```bash
cd frontend
npm install

cp .env.example .env
```

Run:

```bash
npm run dev
```

---

# Running Full Stack

```bash
cd backend && uvicorn src.api.main:app --reload --port 8000
cd frontend && npm run dev
```

Open: http://localhost:3000

---

# CI/CD & Deployment

## CI (GitHub Actions)

Located in:

```
.github/workflows/backend-ci.yml
.github/workflows/database-ci.yml
```

## Frontend Deployment — Vercel

```
API_BASE=https://your-railway-url
```

## Backend Deployment — Railway

Please see the env file in the backend

---

# License

See LICENSE file.

