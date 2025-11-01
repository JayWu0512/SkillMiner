# SkillMiner - Authentication Setup Guide

This guide will help you enable real authentication for the SkillMiner application.

## Current State

The application is currently running in **Mockup Mode**, which allows you to preview and customize all pages without authentication.

## Quick Toggle

You can now switch between Mockup Mode and Real Auth Mode using the toggle in the top-right corner of the header.

## Enabling Real Authentication

### Step 1: Configure OAuth Providers in Supabase

You need to set up OAuth providers in your Supabase dashboard:

#### Google OAuth Setup
1. Go to your Supabase project dashboard
2. Navigate to **Authentication** → **Providers**
3. Find **Google** and click to configure
4. Follow the setup guide: https://supabase.com/docs/guides/auth/social-login/auth-google
5. You'll need to:
   - Create a Google Cloud project
   - Set up OAuth consent screen
   - Create OAuth 2.0 credentials
   - Add authorized redirect URIs
   - Copy Client ID and Client Secret to Supabase

#### GitHub OAuth Setup
1. In Supabase dashboard, go to **Authentication** → **Providers**
2. Find **GitHub** and click to configure
3. Follow the setup guide: https://supabase.com/docs/guides/auth/social-login/auth-github
4. You'll need to:
   - Create a GitHub OAuth App
   - Set Authorization callback URL
   - Copy Client ID and Client Secret to Supabase

### Step 2: Update App.tsx Configuration

Once OAuth is configured, you can enable real authentication:

```typescript
// In /App.tsx, change this line:
const USE_REAL_AUTH = false;

// To:
const USE_REAL_AUTH = true;
```

### Step 3: Test Authentication Flow

1. Turn off "Mockup Mode" using the toggle switch
2. You should see the real login page
3. Click "Continue with Google" or "Continue with GitHub"
4. Complete the OAuth flow
5. You'll be redirected back to the Upload page

## File Structure

### Real Authentication Components
- `/components/LoginPage.tsx` - Real login with OAuth
- `/components/UploadPage.tsx` - Resume and JD upload with backend
- `/components/ChatbotPage.tsx` - Chat interface with AI analysis
- `/components/SkillReport.tsx` - Full skill gap report

### Mockup Components (for design preview)
- `/components/mockups/LoginPageMockup.tsx`
- `/components/mockups/UploadPageMockup.tsx`
- `/components/mockups/ChatbotPageMockup.tsx`
- `/components/mockups/SkillReportMockup.tsx`

### Backend
- `/supabase/functions/server/index.tsx` - Hono server with all API routes
- `/utils/supabase/client.tsx` - Supabase client configuration

## API Routes

The backend server provides these routes:

- `POST /make-server-b8961ff5/analyze` - Analyze resume vs job description
- `GET /make-server-b8961ff5/analysis/:analysisId` - Get analysis summary
- `POST /make-server-b8961ff5/chat` - Send chat message and get AI response
- `GET /make-server-b8961ff5/report/:analysisId` - Get detailed skill report

## Authentication Flow

1. **Login** → User clicks Google/GitHub → OAuth redirect → Session created
2. **Upload** → User uploads resume and JD → Server processes → Analysis ID returned
3. **Chat** → User asks questions → Server provides contextual answers
4. **Report** → User views detailed report → Server returns skill gaps and resources

## Security Notes

- All routes except login require authentication
- Access tokens are validated on the server
- User data is stored in KV store with user ID as key
- OAuth tokens are handled by Supabase Auth

## Troubleshooting

### "Provider is not enabled" Error
- Make sure you've configured OAuth providers in Supabase dashboard
- Check that redirect URIs are correctly set

### "Unauthorized" Error
- Ensure OAuth flow completed successfully
- Check browser console for access token
- Verify server is validating tokens correctly

### Session Not Persisting
- Check that Supabase client is properly configured
- Ensure `onAuthStateChange` listener is working
- Clear browser cookies and try again

## Next Steps

1. Configure OAuth providers in Supabase
2. Set `USE_REAL_AUTH = true` in App.tsx
3. Test login flow
4. Customize mockup pages as needed
5. Deploy to production

## Support

For issues with:
- **Supabase Auth**: https://supabase.com/docs/guides/auth
- **OAuth Setup**: See provider-specific guides above
- **Application Logic**: Check browser console and server logs
