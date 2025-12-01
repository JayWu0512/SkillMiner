# SkillMiner Agent Interface

This is a code bundle for SkillMiner Agent Interface. The original project is available at https://www.figma.com/design/vdAgvYjjFn0KOoBC9DngTl/SkillMiner-Agent-Interface.

## Running the code

Run `npm i` to install the dependencies.

Run `npm run dev` to start the development server.

## Overview

SkillMiner is an AI-powered career development platform that analyzes skill gaps, generates personalized study plans, and provides an intelligent chatbot assistant to guide your learning journey.

### Core Functionality
- **Resume & Job Description Analysis** - Upload your resume and target job description to identify skill gaps
- **Career Readiness Score** - Get a friendly assessment of your match with target roles
- **Personalized Study Plans** - AI-generated, calendar-driven learning paths with daily breakdowns
- **Intelligent Chatbot** - LLM-powered assistant (OpenAI GPT) for plan adjustments
- **Progress Tracking** - XP system, streaks, badges, and achievement tracking

## Quick Start

### Prerequisites
- A Supabase account with a project
- (Optional) OpenAI API key for AI chatbot

### 1. Configure Your Supabase Project

Edit `/src/utils/supabase/info.tsx`:

```typescript
export const projectId = "YOUR_PROJECT_ID"
export const publicAnonKey = "YOUR_ANON_KEY"
```

Get these from: [Supabase Dashboard](https://supabase.com/dashboard) → Your Project → Settings → API

### 2. Set Up Backend Environment Variables

In your Supabase project (Dashboard → Edge Functions → Settings), add:

**Required:**
```
SUPABASE_URL=https://YOUR_PROJECT_ID.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
SUPABASE_DB_URL=your_database_connection_string
```

**Optional (for AI chatbot):**
```
OPENAI_API_KEY=sk-...          # For OpenAI GPT
```

### 3. Enable OAuth Providers (Optional)

**For Google:**
1. Create OAuth credentials at [Google Cloud Console](https://console.cloud.google.com/)
2. Add redirect URI: `https://YOUR_PROJECT_ID.supabase.co/auth/v1/callback`
3. Enable in Supabase Dashboard → Authentication → Providers → Google

**For GitHub:**
1. Create OAuth app at [GitHub Settings](https://github.com/settings/developers)
2. Add callback URL: `https://YOUR_PROJECT_ID.supabase.co/auth/v1/callback`
3. Enable in Supabase Dashboard → Authentication → Providers → GitHub

See [Authentication Setup](#authentication-setup) section below for detailed instructions.

## Backend Connection

### Upload Page Connection

**Component:** `src/components/mockups/UploadPageMockup.tsx`  
**Backend Endpoint:** `POST /upload`

**Features:**
- Backend health check on page load
- PDF file upload to backend
- Resume text extraction
- Stores resume text in localStorage for chatbot access
- Error handling with user-friendly messages
- Connection status indicator
- Loading states during upload

**How it works:**
1. User selects a PDF file
2. Clicks "Analyze My Skills"
3. File is uploaded to `http://localhost:8000/upload`
4. Backend extracts text from PDF
5. Resume text is stored in localStorage
6. Custom event is dispatched to notify chatbot
7. User is redirected to next page

### Persistent Chatbot Connection

**Component:** `src/components/mockups/PersistentChatbot.tsx`  
**Backend Endpoint:** `POST /chat`

**Features:**
- RAG-powered chat with resume context
- Automatically loads resume text from localStorage
- Listens for resume text updates (cross-page communication)
- Citations display (shows references from dataset)
- Error handling
- Loading states (typing indicator)
- Works on all pages (right-side window)

**How it works:**
1. Chatbot loads resume text from localStorage on mount
2. User types a message
3. Message is sent to `http://localhost:8000/chat` with resume context
4. Backend uses RAG to retrieve relevant skills
5. AI generates response with citations
6. Response is displayed with citation badges

### API Service Layer

**File:** `src/services/api.ts`

Provides centralized backend communication:
- `checkHealth()` - Test backend connection
- `uploadResume()` - Upload PDF resume
- `sendChatMessage()` - Send chat message with RAG
- `getApiBase()` - Get API base URL

### Environment Setup

Make sure you have a `.env` file in `figma-mockups/` directory:

```env
VITE_API_BASE=http://localhost:8000
```

## Study Plan Backend Integration

### Summary

The study plan generation backend integration includes:

1. **Backend API Endpoints** (Supabase Edge Function)
   - `POST /study-plan/generate` - Generates a study plan using GPT-4o-mini
   - `GET /study-plan/:planId` - Retrieves a study plan
   - `PATCH /study-plan/:planId/tasks/:taskIndex/complete` - Updates task completion status

2. **Frontend API Service** (`src/services/studyPlan.ts`)
   - TypeScript interfaces for study plan data
   - API functions for generating, fetching, and updating study plans

3. **Updated Components**
   - `SkillReportMockup.tsx` - Now supports backend integration (optional)
   - `StudyPlanMockup.tsx` - Fetches and displays real study plan data when `planId` is provided
   - `App.tsx` - Passes `planId` to StudyPlanMockup

### Deploying the Supabase Edge Function

1. Go to your Supabase Dashboard
2. Navigate to **Edge Functions**
3. Click **Create Function**
4. Name it: `server`
5. Copy the entire code from `src/supabase/functions/server/index.tsx`
6. Paste it into the function editor
7. Click **Deploy**

Set environment variables in Edge Functions → Settings → Secrets:
```
SUPABASE_URL=https://wjfodecgrlbievxtzfoq.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

### Testing Study Plan Generation

1. Enable backend in mockup mode: In `App.tsx`, change `useBackend={false}` to `useBackend={true}`
2. Navigate to the "Skill Report" tab
3. Click "Create My Study Plan"
4. Fill in your preferences (hours/day, timeline, study days)
5. Click "Generate My X-Day Plan"
6. The system will call the backend API and generate a study plan using GPT-4o-mini

## Authentication Setup

### Configure Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Go to **APIs & Services** → **Credentials**
4. Click **Create Credentials** → **OAuth client ID**
5. Configure the OAuth consent screen:
   - Choose **External** user type
   - Fill in app name: "SkillMiner"
   - Add your email as support email
   - Save and continue
6. Select **Application type**: **Web application**
7. Name: "SkillMiner Web Client"
8. **Authorized JavaScript origins**: Add `https://<your-project-id>.supabase.co`
9. **Authorized redirect URIs**: Add `https://<your-project-id>.supabase.co/auth/v1/callback`
10. Click **Create** and copy the **Client ID** and **Client Secret**
11. In Supabase Dashboard → **Authentication** → **Providers** → Enable **Google** and paste credentials

### Configure GitHub OAuth

1. Go to [GitHub Developer Settings](https://github.com/settings/developers)
2. Click **OAuth Apps** → **New OAuth App**
3. Fill in:
   - **Application name**: SkillMiner
   - **Homepage URL**: `https://<your-project-id>.supabase.co`
   - **Authorization callback URL**: `https://<your-project-id>.supabase.co/auth/v1/callback`
4. Click **Register application**
5. Copy the **Client ID** and generate a **Client Secret**
6. In Supabase Dashboard → **Authentication** → **Providers** → Enable **GitHub** and paste credentials

### Configure Redirect URLs

1. In Supabase Dashboard, go to **Authentication** → **URL Configuration**
2. Set **Site URL** to your application URL
3. Under **Redirect URLs**, add your production URL and any development URLs

## Troubleshooting

### Study Plan Generation Issues

**"Failed to fetch" Error:**
- Check if the Edge Function is deployed
- Verify environment variables are set in Supabase Edge Functions settings
- Check browser console for CORS errors

**Database Table Issues:**
- Verify the `study_plans` table exists
- Check table schema matches expected structure
- For mockup mode, ensure `user_id` column is nullable

**LLM not generating plans:**
- Verify `OPENAI_API_KEY` is set in Supabase Edge Function environment
- Check Supabase Edge Function logs for errors
- The system will fall back to mock data if the API fails

### Backend Connection Issues

**"Backend connection issue":**
1. Check backend is running: `curl http://localhost:8000/health`
2. Check browser console (F12) for errors
3. Verify `.env` file has `VITE_API_BASE=http://localhost:8000`
4. Restart frontend: `cd figma-mockups && npm run dev`

**Upload fails:**
1. Check browser console for error details
2. Verify backend is running
3. Check file is PDF format
4. Check file size (< 10MB)

**Chatbot doesn't work:**
1. Make sure resume was uploaded first
2. Check browser console for errors
3. Verify resume text in localStorage (F12 → Application → Local Storage)

### OAuth Issues

**"Provider not enabled":**
- Make sure you've enabled the provider in Supabase Dashboard and saved the credentials

**"Invalid redirect URI":**
- Check that your redirect URL in Google/GitHub matches exactly: `https://<project-id>.supabase.co/auth/v1/callback`
- Verify the Site URL in Supabase matches your app's URL

**Login button shows error immediately:**
- Verify `/src/utils/supabase/info.tsx` has correct credentials
- Check browser console for detailed error messages
- Ensure your Supabase project is active

## Architecture

```
Frontend (React + Tailwind)
    ↓
Supabase Client
    ↓
Edge Function Server (Hono + Deno)
    ↓
├── KV Store (Database)
├── LLM APIs (OpenAI)
└── Auth (OAuth Providers)
```

## Tech Stack

- **Frontend**: React, TypeScript, Tailwind CSS v4
- **UI Components**: Shadcn UI
- **Backend**: Supabase Edge Functions (Hono + Deno)
- **Database**: Supabase PostgreSQL with KV Store
- **Authentication**: Supabase Auth (Google & GitHub OAuth)
- **AI/LLM**: OpenAI GPT
- **Icons**: Lucide React
- **Charts**: Recharts

## Project Structure

```
├── /components
│   ├── /mockups          # Mockup pages for design preview
│   ├── /ui               # Shadcn UI components
│   ├── LoginPage.tsx     # OAuth authentication
│   ├── UploadPage.tsx    # Resume & job upload
│   └── SkillReport.tsx   # Skill analysis display
├── /supabase/functions/server
│   ├── index.tsx         # Main server with API endpoints
│   └── kv_store.tsx      # Key-value database utilities
├── /utils/supabase
│   ├── client.tsx        # Supabase client singleton
│   └── info.tsx          # Project configuration
├── /styles
│   └── globals.css       # Global styles and design tokens
└── App.tsx               # Main app with routing logic
```

## Attributions

This Figma Make file includes components from [shadcn/ui](https://ui.shadcn.com/) used under [MIT license](https://github.com/shadcn-ui/ui/blob/main/LICENSE.md).

This Figma Make file includes photos from [Unsplash](https://unsplash.com) used under [license](https://unsplash.com/license).
