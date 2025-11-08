# SkillMiner Quick Start Guide

This guide will get you up and running with SkillMiner in minutes.

## Overview

SkillMiner is an AI-powered skill gap analysis and personalized study planning application with:
- Google & GitHub OAuth authentication
- Resume and job description analysis
- Intelligent chatbot assistant (with LLM integration)
- Personalized study plans with calendar view
- Coding and interview practice modules
- Progress tracking with XP, streaks, and badges

## Quick Setup (5 minutes)

### 1. Configure Supabase Account

Edit `/utils/supabase/info.tsx`:

```typescript
export const projectId = "YOUR_PROJECT_ID"
export const publicAnonKey = "YOUR_ANON_KEY"
```

Get these from: [Supabase Dashboard](https://supabase.com/dashboard) → Your Project → Settings → API

### 2. Set Environment Variables

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
# OR
ANTHROPIC_API_KEY=sk-ant-...   # For Claude
```

### 3. Enable OAuth Providers

**For Google:**
1. Create OAuth credentials at [Google Cloud Console](https://console.cloud.google.com/)
2. Add redirect URI: `https://YOUR_PROJECT_ID.supabase.co/auth/v1/callback`
3. Enable in Supabase Dashboard → Authentication → Providers → Google

**For GitHub:**
1. Create OAuth app at [GitHub Settings](https://github.com/settings/developers)
2. Add callback URL: `https://YOUR_PROJECT_ID.supabase.co/auth/v1/callback`
3. Enable in Supabase Dashboard → Authentication → Providers → GitHub

📖 **Detailed instructions:** See `AUTHENTICATION_SETUP.md`

### 4. Enable Real Authentication

In `/App.tsx`, set:

```typescript
const USE_REAL_AUTH = true;
```

### 5. Toggle Mockup Mode Off

In the app, use the "Mockup Mode" switch to disable mockup mode and test real authentication.

## Features Overview

### 🔐 Authentication (LoginPage)
- Google OAuth login
- GitHub OAuth login
- Automatic session management
- Secure token handling

### 📤 Upload & Analysis (UploadPage)
- Upload resume (PDF/DOCX)
- Paste job description
- AI-powered skill gap analysis
- Career readiness score

### 📊 Skill Report
- Visual skill matching
- Missing skills identification
- Learning resource recommendations
- Customizable study plan settings

### 📅 Study Plan
- Calendar view (Week/Month/List)
- Daily task breakdown
- Progress tracking
- Adjustable timeline

### 💬 AI Chatbot Assistant
- Context-aware responses
- Study plan modifications
- Quick actions (reschedule, adjust difficulty)
- Persistent across pages

### 💻 Coding Practice
- LeetCode-style problems
- Multiple difficulty levels
- Solution submission
- Progress tracking

### 🎤 Interview Practice
- Video recording
- BigInterview-style interface
- Behavioral and technical questions
- Feedback and tips

### 👤 Profile & Progress
- XP and level system
- Streak tracking
- Achievement badges
- Statistics dashboard

## Application Modes

### Mockup Mode (Default)
- Browse all pages via tabs
- Test UI and interactions
- No authentication required
- Perfect for design review

### Real Mode
- Full authentication flow
- Backend integration
- Data persistence
- Production-ready

Toggle between modes using the switch in the header.

## Architecture

```
Frontend (React + Tailwind)
    ↓
Supabase Client
    ↓
Edge Function Server (Hono)
    ↓
├── KV Store (Database)
├── LLM APIs (OpenAI/Anthropic)
└── Auth (OAuth Providers)
```

## API Endpoints

The backend server provides these endpoints:

- `POST /server/analyze` - Analyze resume & job description
- `GET /server/analysis/:id` - Get analysis summary
- `GET /server/report/:id` - Get detailed skill report
- `POST /server/chat` - Chat with AI assistant

All endpoints require authentication (Bearer token in Authorization header).

## Key Files

```
/App.tsx                           # Main app component & routing
/components/LoginPage.tsx          # OAuth authentication
/components/UploadPage.tsx         # Resume & job description upload
/components/SkillReport.tsx        # Skill analysis display
/components/mockups/               # All mockup pages
/components/ui/                    # Shadcn UI components
/supabase/functions/server/        # Backend server code
/utils/supabase/client.tsx         # Supabase client singleton
/utils/supabase/info.tsx           # Project configuration
/styles/globals.css                # Global styles & tokens
```

## Development Tips

### Testing OAuth Locally

1. Update redirect URLs to include `http://localhost:5173`
2. Update Site URL in Supabase to local URL
3. Test both Google and GitHub flows

### Debugging Authentication

Check browser console for:
- Session check results
- OAuth redirect errors
- Token validation issues

### Chatbot Without LLM

If no API key is set, the chatbot uses rule-based responses. It's still functional but less conversational.

### Adding New Features

1. Create component in `/components`
2. Add to mockup tabs in App.tsx
3. Implement backend endpoint if needed
4. Update routing logic

## Common Issues

**"Unauthorized" errors**
- Verify all environment variables are set
- Check access token is being passed correctly
- Ensure user is authenticated

**OAuth redirect fails**
- Check redirect URIs match exactly
- Verify provider is enabled in Supabase
- Clear browser cache and cookies

**Chatbot not responding**
- Check API key is configured
- Verify server is running
- Check browser console for errors

**Session not persisting**
- Check localStorage is enabled
- Verify Supabase client is initialized
- Check for CORS issues

## Next Steps

1. ✅ Set up Supabase account
2. ✅ Configure OAuth providers
3. ✅ Enable real authentication
4. 🎯 Test the complete user flow
5. 🎯 Configure LLM API for chatbot
6. 🎯 Customize branding and content
7. 🎯 Deploy to production

## Resources

- 📖 [Full Authentication Setup](AUTHENTICATION_SETUP.md)
- 📖 [Supabase Account Configuration](CHANGE_SUPABASE_ACCOUNT.md)
- 🔗 [Supabase Documentation](https://supabase.com/docs)
- 🔗 [Shadcn UI Components](https://ui.shadcn.com/)
- 🔗 [Tailwind CSS](https://tailwindcss.com/)

## Support

For issues or questions:
1. Check error messages in browser console
2. Review setup documentation
3. Verify all credentials and environment variables
4. Test OAuth providers individually

Happy coding! 🚀
