# Deploying the Supabase Edge Function

## Step 1: Create the Function in Supabase Dashboard

1. Go to your Supabase Dashboard
2. Navigate to **Edge Functions**
3. Click **Create Function**
4. Name it: `server`
5. Copy the entire code from `figma_new/src/supabase/functions/server/index.tsx`
6. Paste it into the function editor
7. Click **Deploy**

## Step 2: Set Environment Variables

1. Go to **Edge Functions** → **Settings** → **Secrets**
2. Add these environment variables:

```
SUPABASE_URL=https://wjfodecgrlbievxtzfoq.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

**How to find these:**
- **SUPABASE_URL**: Dashboard → Settings → API → Project URL
- **SUPABASE_SERVICE_ROLE_KEY**: Dashboard → Settings → API → service_role key (keep this secret!)
- **OPENAI_API_KEY**: Get from [OpenAI Platform](https://platform.openai.com/api-keys)

## Step 3: Verify Deployment

After deployment, you should see:
- Function name: `server`
- URL: `https://wjfodecgrlbievxtzfoq.supabase.co/functions/v1/server`
- Status: Active

## Step 4: Test the Function

You can test the function using curl:

```bash
curl -X POST https://wjfodecgrlbievxtzfoq.supabase.co/functions/v1/server/study-plan/generate \
  -H "Content-Type: application/json" \
  -d '{
    "analysisId": "mock_analysis_test",
    "hoursPerDay": "2-3",
    "timeline": "60",
    "studyDays": ["Mon", "Tue", "Wed"],
    "jobDescription": "Data Analyst"
  }'
```

## Alternative: Deploy using Supabase CLI

If you have Supabase CLI installed:

```bash
# Install Supabase CLI (if not installed)
npm install -g supabase

# Login to Supabase
supabase login

# Link to your project
supabase link --project-ref wjfodecgrlbievxtzfoq

# Deploy the function
cd figma_new
supabase functions deploy server
```

## Troubleshooting

### Function not found (404)
- Make sure the function is named exactly `server`
- Check that it's deployed and active
- Verify the URL matches: `/functions/v1/server`

### Environment variables not set
- Go to Edge Functions → Settings → Secrets
- Make sure all required variables are set
- Restart the function after adding new secrets

### Database errors
- Make sure the `study_plans` table exists
- Verify `user_id` column is nullable (for mockup mode)
- Check that you have the correct database permissions

### Authentication errors
- For mockup mode, the function allows null `user_id`
- For production, make sure users are authenticated
- Check that `SUPABASE_SERVICE_ROLE_KEY` is set correctly

## Function Endpoints

The function provides these endpoints:

- `POST /study-plan/generate` - Generate a new study plan
- `GET /study-plan/:planId` - Get a study plan by ID
- `PATCH /study-plan/:planId/tasks/:taskIndex/complete` - Update task completion
- `POST /analyze` - Analyze resume and job description
- `GET /analysis/:analysisId` - Get analysis summary
- `GET /report/:analysisId` - Get detailed report
- `POST /chat` - Chat with AI assistant

All endpoints are accessible at: `https://wjfodecgrlbievxtzfoq.supabase.co/functions/v1/server/<endpoint>`

