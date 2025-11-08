# SkillMiner v2 - Study Plan Edition

An AI-powered career development platform that analyzes skill gaps, generates personalized study plans, and provides an intelligent chatbot assistant to guide your learning journey.

## 🌟 Features

### Core Functionality
- **Resume & Job Description Analysis** - Upload your resume and target job description to identify skill gaps
- **Career Readiness Score** - Get a friendly assessment of your match with target roles
- **Personalized Study Plans** - AI-generated, calendar-driven learning paths with daily breakdowns
- **Intelligent Chatbot** - LLM-powered assistant (OpenAI GPT or Anthropic Claude) for plan adjustments
- **Progress Tracking** - XP system, streaks, badges, and achievement tracking

### Application Pages
1. **Login** - Google & GitHub OAuth authentication
2. **Upload** - Resume and job description input
3. **Skill Report** - Visual skill gap analysis with learning resources
4. **Dashboard** - "Today" view with daily tasks and progress
5. **Study Plan** - Calendar interface (Week/Month/List views)
6. **Coding Practice** - LeetCode-style programming challenges
7. **Interview Practice** - Video recording with BigInterview-style interface
8. **Profile** - User statistics, achievements, and settings
9. **Resume Manager** - Upload and manage multiple resumes

## 🚀 Quick Start

### Prerequisites
- A Supabase account with a project
- (Optional) OpenAI or Anthropic API key for AI chatbot

### 1. Configure Your Supabase Project

Your project is already configured with:
- **Project ID**: `wjfodecgrlbievxtzfoq`
- **Credentials**: Set in `/utils/supabase/info.tsx`

### 2. Set Up OAuth Authentication

Follow the detailed guide in `AUTHENTICATION_SETUP.md` to enable:
- ✅ Google OAuth login
- ✅ GitHub OAuth login

**Quick steps:**
1. Create OAuth apps in [Google Cloud Console](https://console.cloud.google.com/) and [GitHub Settings](https://github.com/settings/developers)
2. Add redirect URI: `https://wjfodecgrlbievxtzfoq.supabase.co/auth/v1/callback`
3. Enable providers in Supabase Dashboard → Authentication → Providers
4. Add Client ID and Client Secret for each provider

### 3. Configure Backend Environment Variables

In your Supabase Dashboard (Edge Functions → Settings), add:

```bash
# Required
SUPABASE_URL=https://wjfodecgrlbievxtzfoq.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndqZm9kZWNncmxiaWV2eHR6Zm9xIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjIxOTUxMjYsImV4cCI6MjA3Nzc3MTEyNn0.b4kWNXDG53krE3K6TY1FNsclwRUBI5zVnwEpqNF_0iw
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
SUPABASE_DB_URL=your_database_connection_string

# Optional - For AI Chatbot
OPENAI_API_KEY=sk-...          # Use OpenAI GPT
# OR
ANTHROPIC_API_KEY=sk-ant-...   # Use Anthropic Claude
```

### 4. Start Using the App

The app has two modes:

**Mockup Mode (Default)** - Browse all pages without authentication:
```typescript
// In App.tsx
const USE_REAL_AUTH = false;  // Keep as false for mockup mode
```

**Real Mode** - Full authentication and backend integration:
```typescript
// In App.tsx
const USE_REAL_AUTH = true;   // Set to true for real auth
```

Toggle the "Mockup Mode" switch in the app header to switch between modes.

## 📖 Documentation

- **[QUICK_START.md](QUICK_START.md)** - Get up and running in 5 minutes
- **[AUTHENTICATION_SETUP.md](AUTHENTICATION_SETUP.md)** - Detailed OAuth setup guide
- **[CHANGE_SUPABASE_ACCOUNT.md](CHANGE_SUPABASE_ACCOUNT.md)** - Switch to a different Supabase project

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│          Frontend (React + Tailwind)        │
│  - OAuth Authentication                     │
│  - Resume Upload & Analysis                 │
│  - Study Plan Calendar                      │
│  - Persistent Chatbot                       │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│         Supabase Client SDK                 │
│  - Auth Management                          │
│  - API Requests                             │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│    Edge Function Server (Hono + Deno)       │
│  - Resume & Job Analysis                    │
│  - Skill Gap Identification                 │
│  - Chatbot with LLM Integration             │
│  - Learning Resource Matching               │
└──────────────────┬──────────────────────────┘
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
    ┌─────┐   ┌──────┐   ┌─────────┐
    │ KV  │   │ Auth │   │   LLM   │
    │Store│   │OAuth │   │   APIs  │
    └─────┘   └──────┘   └─────────┘
```

## 🔧 Tech Stack

- **Frontend**: React, TypeScript, Tailwind CSS v4
- **UI Components**: Shadcn UI
- **Backend**: Supabase Edge Functions (Hono + Deno)
- **Database**: Supabase PostgreSQL with KV Store
- **Authentication**: Supabase Auth (Google & GitHub OAuth)
- **AI/LLM**: OpenAI GPT or Anthropic Claude
- **Icons**: Lucide React
- **Charts**: Recharts

## 📁 Project Structure

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
├── App.tsx               # Main app with routing logic
├── AUTHENTICATION_SETUP.md
├── CHANGE_SUPABASE_ACCOUNT.md
├── QUICK_START.md
└── README.md
```

## 🤖 Chatbot Integration

The chatbot supports two LLM providers:

### OpenAI (GPT)
```bash
OPENAI_API_KEY=sk-...
```
- Uses `gpt-4o-mini` model (cost-effective)
- Excellent for conversational responses
- Good context understanding

### Anthropic (Claude)
```bash
ANTHROPIC_API_KEY=sk-ant-...
```
- Uses `claude-3-haiku` model (cost-effective)
- Strong reasoning capabilities
- Great for detailed explanations

### Fallback Mode
If no API key is configured, the chatbot uses rule-based responses:
- Still functional
- Provides helpful guidance
- No LLM costs
- Good for testing and development

## 🔐 Security

- OAuth credentials stored securely in Supabase
- Service role key never exposed to frontend
- User sessions managed with secure tokens
- CORS enabled with proper origins
- All API endpoints require authentication

## 🎨 Customization

### Design Tokens
Edit `/styles/globals.css` to customize:
- Color schemes
- Typography
- Spacing
- Border radius
- Shadows

### Study Plan Examples
Edit `/supabase/functions/server/index.tsx` to modify:
- Learning resources database
- Skill matching algorithms
- Default study plan templates

## 🧪 Testing

### Test OAuth Flow
1. Set `USE_REAL_AUTH = true` in App.tsx
2. Toggle off Mockup Mode
3. Click "Continue with Google" or "Continue with GitHub"
4. Verify redirect and session creation

### Test Backend APIs
```javascript
// Example: Test chat endpoint
const response = await fetch(
  'https://wjfodecgrlbievxtzfoq.supabase.co/functions/v1/server/chat',
  {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer YOUR_ACCESS_TOKEN'
    },
    body: JSON.stringify({
      message: 'Tell me about my skill gaps',
      analysisId: 'analysis_123'
    })
  }
);
```

## 📊 Study Plan Example

The app includes a 14-day Data Analyst study plan with:
- **Daily breakdowns** (6 hours/day)
- **Learning phases** (Fundamentals → Advanced → Practice → Mock Interviews)
- **Specific resources** (Udemy courses, practice datasets, interview prep)
- **Time estimates** for each task
- **Progressive difficulty**

## 🎯 Roadmap

- [x] OAuth authentication (Google & GitHub)
- [x] Resume and job description upload
- [x] AI skill gap analysis
- [x] Personalized study plan generation
- [x] Calendar view (Week/Month/List)
- [x] Persistent chatbot with LLM integration
- [x] Coding practice interface
- [x] Interview practice with video recording
- [x] Progress tracking with gamification
- [ ] Email authentication
- [ ] Study plan export (Google Calendar, Outlook)
- [ ] Mobile app (React Native)
- [ ] Community features (forums, study groups)
- [ ] Mentor matching
- [ ] Job application tracking

## 🐛 Troubleshooting

**OAuth not working?**
- Check redirect URIs match exactly
- Verify providers are enabled in Supabase
- See `AUTHENTICATION_SETUP.md` for detailed steps

**Chatbot not responding?**
- Check API key is configured correctly
- Verify environment variables are set
- Check browser console for errors

**Session not persisting?**
- Clear browser cache and cookies
- Check localStorage is enabled
- Verify Supabase client initialization

## 📝 License

This project is for educational and demonstration purposes.

## 🤝 Contributing

This is a prototype/demo application. For production use:
1. Add proper error handling
2. Implement rate limiting
3. Add comprehensive testing
4. Set up monitoring and logging
5. Configure production environment

## 📧 Support

For issues:
1. Check browser console for errors
2. Review documentation files
3. Verify all credentials and environment variables
4. Test each feature individually

---

**Built with ❤️ using React, Supabase, and AI**

Ready to start? Check out [QUICK_START.md](QUICK_START.md) for a 5-minute setup guide!
