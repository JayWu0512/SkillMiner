# SkillMiner Frontend

This directory contains the **SkillMiner** web client, built with **React**, **TypeScript**, and **Vite**.

---

## Tech Stack

- **React + TypeScript**
- **Vite**
- **Supabase Auth**
- **REST API Services**
- **Reusable UI Components**
- **Lucide Icons**

---

## Project Structure

```text
frontend/
├─ src/
│  ├─ assets/
│  │  └─ logo.png
│  ├─ components/
│  │  ├─ features/
│  │  │  ├─ Header.tsx
│  │  │  ├─ PersistentChatbot.tsx
│  │  │  └─ SkillMinerLogo.tsx
│  │  ├─ figma/
│  │  │  └─ ImageWithFallback.tsx
│  │  ├─ mockups/               # Optional mock UI components (if any)
│  │  └─ pages/
│  │     ├─ ChatbotPage.tsx
│  │     ├─ CodingPracticePage.tsx
│  │     ├─ InterviewPracticePage.tsx
│  │     ├─ LoginPage.tsx
│  │     ├─ MainDashboardPage.tsx
│  │     ├─ ProfilePage.tsx
│  │     ├─ ResumePage.tsx
│  │     ├─ SkillReportPage.tsx
│  │     ├─ StudyPlanPage.tsx
│  │     └─ UploadPage.tsx
│  ├─ ui/                        # Reusable UI components (buttons, cards, etc.)
│  ├─ services/
│  │  ├─ api.ts                  # Generic API helper
│  │  └─ studyPlan.ts            # Study plan–related API calls
│  ├─ styles/
│  │  └─ globals.css
│  ├─ utils/
│  │  └─ supabase/
│  │     ├─ client.tsx           # Supabase client setup
│  │     └─ info.tsx             # Supabase-related helpers / config
│  ├─ App.tsx                    # App shell + routing
│  ├─ main.tsx                   # Vite entry point
│  └─ index.css
├─ .env                          # Local env variables (see .env.example)
├─ .env.example                  # Sample env config
├─ index.html
├─ package.json
└─ vite.config.ts
```

---

## Setup

### 1. Install dependencies

```bash
npm install
```

### 2. Create .env

Copy `.env.example` → `.env` and fill in required values.

### 3. Start dev server

```bash
npm run dev
```

### 4. Build

```bash
npm run build
```

---

## Pages Overview

- LoginPage – login with Supabase
- UploadPage – upload resume
- ChatbotPage – SkillMiner chatbot
- StudyPlanPage – generated study plans
- SkillReportPage – skill analysis results
- Dashboard / Profile / Resume / Practice Pages, etc.

---

## Supabase

Client config is in:

```
src/utils/supabase/client.tsx
```

You can import and use it across pages or service functions.

---

