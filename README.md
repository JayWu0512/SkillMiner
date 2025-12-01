
# SkillMiner

SkillMiner is an AI-powered career & study copilot.  
It analyzes your resume, extracts skills, identifies gaps, retrieves learning resources, and generates a personalized study plan powered by an LLM agent, RAG system, and a modern data engineering pipeline.

---

## 📌 System Architecture

![SkillMiner Architecture](docs/skillminer-architecture.png)

---

## 📁 Repository Structure

```
.
├─ .github/              # GitHub Actions (CI/CD pipelines)
├─ backend/              # FastAPI backend, RAG, Agent, API Gateway
├─ database/             # DB schema, SQL migrations, seed files
├─ figma-mockups/        # UI mockups
├─ frontend/             # Next.js (React) frontend client
├─ LICENSE
├─ README.md            
├─ requirements.txt
```

---

# 🚀 Getting Started (Local Development)

SkillMiner consists of:

- **Frontend** — Next.js (local) → production on **Vercel**
- **Backend** — FastAPI (local) → production on **Railway**
- **Database** — Supabase (PostgreSQL + Auth), AWS(S3, RDS)
- **ETL & Data Infra** — AWS EC2, Airflow, S3, RDS, Polars

---

# 1️⃣ Backend Setup (FastAPI)

### Step 1 — Create virtual environment

```bash
cd backend
```

### Step 2 — Install backend dependencies

```bash
pip install -r ../requirements.txt
```
(Python version: 3.11.13 (3.11.9 for windows))

### Step 3 — Create backend .env

```
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

# 2️⃣ Database Setup

### Local ETL

```bash
python scripts/download_kaggle.py
make install
```

### Supabase
https://supabase.com/docs/guides/getting-started

### AWS
https://aws.amazon.com/tw/getting-started/

---

# 3️⃣ Frontend Setup (Next.js)

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

# 4️⃣ Running Full Stack

```bash
cd backend && uvicorn src.api.main:app --reload --port 8000
cd frontend && npm run dev
```

Open: http://localhost:3000

---

# 5️⃣ CI/CD & Deployment

## CI (GitHub Actions)

Located in:

```
.github/workflows/backend-ci.yml
.github/workflows/database-ci.yml
```

## Frontend Deployment — Vercel

```
NEXT_PUBLIC_API_BASE_URL=https://your-railway-url
```

## Backend Deployment — Railway

Please see the env file in the backend

---

# License

See LICENSE file.
