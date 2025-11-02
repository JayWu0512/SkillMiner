# 🧠 SkillMiner Frontend

**SkillMiner** is an AI-powered web application that analyzes your resume, identifies skill gaps, and recommends learning paths toward your target roles.

This repository contains the **frontend** of SkillMiner, built with **Vite + React + TypeScript + Tailwind CSS**.  
It connects to a local or cloud backend (Node.js + PostgreSQL) for authentication and data persistence.

---

## 📁 Project Structure

```
frontend/
├── public/                 
│   ├── skillminer-icon.png
│
├── src/
│   ├── components/
│   │   ├── figma/              # Components exported or inspired from Figma design
│   │   └── ui/                 # Reusable UI components (e.g., Button, Card, Input)
│   │
│   ├── pages/                  # Major application pages
│   │   ├── ChatbotPage.tsx     # AI chatbot interface
│   │   ├── LoginPage.tsx       # Google/GitHub login page
│   │   ├── SkillReport.tsx     # Skill gap analysis report
│   │   └── UploadPage.tsx      # Resume upload & analysis trigger
│   │
│   ├── styles/                 # Global CSS and Tailwind styling
│   ├── supabase/               # (Optional) Supabase client setup
│   ├── utils/                  # Helper functions and API utilities
│   │
│   ├── App.tsx                 # Root component / Router entry
│   ├── main.tsx                # Application entry point
│   └── env.d.ts                # Type definitions for environment variables
│
├── .env                        # Local environment configuration
├── index.html                  # Root HTML template
├── tsconfig.json               # TypeScript configuration
├── vite.config.ts              # Vite build configuration
├── package.json                # Project dependencies & scripts
└── README.md                   # Project documentation
```

---

## ⚙️ Setup Instructions

### 1. Install dependencies

```bash
npm install
```

### 2. Configure environment variables

Create a `.env` file in the project root:

```bash
# === Frontend Environment ===
VITE_API_BASE=http://localhost:8787     # Local backend endpoint
VITE_APP_NAME=SkillMiner
```

### 3. Run the development server

```bash
npm run dev
```

Then open → [http://localhost:5173](http://localhost:5173)

---


## 🧩 Tech Stack

| Category | Technology |
|-----------|-------------|
| **Framework** | React (Vite + TypeScript) |
| **Styling** | Tailwind CSS + Shadcn/UI |
| **Icons** | Lucide React |
| **Auth** | Google OAuth 2.0 (or Supabase optional) |
| **State Mgmt** | React Hooks |
| **Database (Backend)** | PostgreSQL (AWS or local) |
| **Bundler** | Vite |
| **Language** | TypeScript |

---

## 📦 Common Commands

| Command | Description |
|----------|-------------|
| `npm run dev` | Start local dev server (Vite) |
| `npm run build` | Build optimized production bundle |
| `npm run preview` | Preview production build locally |
| `npm run lint` | Run ESLint checks (if configured) |

---


## 🌐 Deployment Tips

- **Frontend Hosting:** Vercel / Netlify  
- **Backend Hosting:** Render / Railway / AWS EC2  
- **Database:** AWS RDS (PostgreSQL)

For production:
```bash
npm run build
```
Then deploy the generated `/dist` folder.

---

## 📜 License

MIT © 2025 **SkillMiner Team**
