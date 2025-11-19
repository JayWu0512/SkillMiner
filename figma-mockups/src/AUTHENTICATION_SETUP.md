# Authentication Setup Guide

This guide will help you set up Google and GitHub OAuth authentication for SkillMiner.

## Prerequisites

1. A Supabase account and project
2. Your Supabase project credentials configured (see `CHANGE_SUPABASE_ACCOUNT.md`)

## Step 1: Configure Google OAuth

### 1.1 Create Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Go to **APIs & Services** → **Credentials**
4. Click **Create Credentials** → **OAuth client ID**
5. If prompted, configure the OAuth consent screen first:
   - Choose **External** user type
   - Fill in app name: "SkillMiner"
   - Add your email as support email
   - Skip optional fields
   - Add test users if needed
   - Save and continue

### 1.2 Configure OAuth Client

1. Select **Application type**: **Web application**
2. Name: "SkillMiner Web Client"
3. **Authorized JavaScript origins**:
   - Add: `https://<your-project-id>.supabase.co`
   - For local testing: `http://localhost:5173` (if applicable)
4. **Authorized redirect URIs**:
   - Add: `https://<your-project-id>.supabase.co/auth/v1/callback`
5. Click **Create**
6. Copy the **Client ID** and **Client Secret**

### 1.3 Enable Google Provider in Supabase

1. Go to your [Supabase Dashboard](https://supabase.com/dashboard)
2. Select your project
3. Navigate to **Authentication** → **Providers**
4. Find **Google** and toggle it **ON**
5. Paste your **Client ID** and **Client Secret**
6. Click **Save**

## Step 2: Configure GitHub OAuth

### 2.1 Create GitHub OAuth App

1. Go to [GitHub Developer Settings](https://github.com/settings/developers)
2. Click **OAuth Apps** → **New OAuth App**
3. Fill in the details:
   - **Application name**: SkillMiner
   - **Homepage URL**: `https://<your-project-id>.supabase.co` or your custom domain
   - **Authorization callback URL**: `https://<your-project-id>.supabase.co/auth/v1/callback`
4. Click **Register application**
5. On the app page, note the **Client ID**
6. Click **Generate a new client secret** and copy the secret

### 2.2 Enable GitHub Provider in Supabase

1. Go to your [Supabase Dashboard](https://supabase.com/dashboard)
2. Select your project
3. Navigate to **Authentication** → **Providers**
4. Find **GitHub** and toggle it **ON**
5. Paste your **Client ID** and **Client Secret**
6. Click **Save**

## Step 3: Configure Redirect URLs

### 3.1 Update Site URL

1. In Supabase Dashboard, go to **Authentication** → **URL Configuration**
2. Set **Site URL** to your application URL:
   - Production: Your custom domain or `https://<your-project-id>.supabase.co`
   - Local dev: `http://localhost:5173`

### 3.2 Add Redirect URLs

Under **Redirect URLs**, add:
- Your production URL
- Any development/staging URLs
- For local dev: `http://localhost:5173`

Click **Save** after adding URLs.

## Step 4: Test Authentication

### 4.1 Enable Real Authentication

In `/App.tsx`, ensure the flag is set:
```typescript
const USE_REAL_AUTH = true;
```

### 4.2 Test Google Login

1. Toggle off "Mockup Mode" in the app
2. Click "Continue with Google"
3. You should be redirected to Google's login page
4. After successful login, you'll be redirected back to the app

### 4.3 Test GitHub Login

1. Click "Continue with GitHub"
2. You should be redirected to GitHub's authorization page
3. After authorizing, you'll be redirected back to the app

## Troubleshooting

### Error: "Provider not enabled"

**Solution**: Make sure you've enabled the provider in Supabase Dashboard and saved the credentials.

### Error: "Invalid redirect URI"

**Solution**: 
- Check that your redirect URL in Google/GitHub matches exactly: `https://<project-id>.supabase.co/auth/v1/callback`
- Verify the Site URL in Supabase matches your app's URL
- For local dev, ensure `http://localhost:5173` is in both redirect URLs lists

### Error: "Failed to fetch"

**Solution**: Check your browser console for CORS errors. Make sure:
- The Site URL in Supabase is correctly configured
- Your app is running on the same domain as configured

### Login button shows error immediately

**Solution**: 
- Verify `/utils/supabase/info.tsx` has correct credentials
- Check browser console for detailed error messages
- Ensure your Supabase project is active

### OAuth redirect happens but no login

**Solution**: 
- Check browser console for session errors
- Verify that `onLoginSuccess` callback is being called
- Try clearing browser cookies and cache

## Security Best Practices

1. **Never commit secrets**: Keep OAuth secrets secure and never commit them to version control
2. **Use environment variables**: Store sensitive credentials in Supabase environment variables
3. **Restrict domains**: Only add necessary redirect URLs
4. **Enable email confirmation**: For production, consider enabling email confirmation
5. **Review permissions**: Only request necessary OAuth scopes

## Additional Features

### Email Authentication (Optional)

You can also enable email/password authentication:

1. In Supabase Dashboard, go to **Authentication** → **Providers**
2. Enable **Email** provider
3. Configure email templates if desired
4. Update LoginPage.tsx to include email/password inputs

### Multi-Factor Authentication (Optional)

For enhanced security:

1. Go to **Authentication** → **Settings**
2. Enable **Multi-factor authentication**
3. Choose factors: SMS, Authenticator app, etc.

### Session Management

The app automatically handles:
- Session persistence across page reloads
- Token refresh
- Logout functionality

Sessions are stored securely in localStorage by Supabase client.

## Next Steps

Once authentication is working:

1. Test the complete user flow (login → upload → analysis → chatbot)
2. Configure LLM API keys for intelligent chatbot responses (see `CHANGE_SUPABASE_ACCOUNT.md`)
3. Customize the user experience
4. Deploy to production

## Support Resources

- [Supabase Auth Documentation](https://supabase.com/docs/guides/auth)
- [Google OAuth Setup](https://supabase.com/docs/guides/auth/social-login/auth-google)
- [GitHub OAuth Setup](https://supabase.com/docs/guides/auth/social-login/auth-github)
- [OAuth 2.0 Overview](https://oauth.net/2/)

## Common OAuth Scopes

### Google
- Default: `openid`, `email`, `profile`
- Additional: `https://www.googleapis.com/auth/userinfo.email`

### GitHub
- Default: `read:user`, `user:email`
- Additional: `repo`, `gist` (if needed for your app)

You can customize scopes in the Supabase provider configuration if needed.
