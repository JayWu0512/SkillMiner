# Troubleshooting Study Plan Generation

## Common Issues and Solutions

### 1. "Failed to fetch" Error

This usually means the Supabase Edge Function is not deployed or not accessible.

#### Solution: Deploy the Edge Function

1. **Check if the function is deployed:**
   - Go to your Supabase Dashboard
   - Navigate to **Edge Functions**
   - Look for a function named `server`
   - If it doesn't exist, you need to deploy it

2. **Deploy the Edge Function:**
   
   **Option A: Using Supabase CLI (Recommended)**
   ```bash
   # Install Supabase CLI if not installed
   npm install -g supabase
   
   # Login to Supabase
   supabase login
   
   # Link to your project
   supabase link --project-ref wjfodecgrlbievxtzfoq
   
   # Deploy the function
   supabase functions deploy server
   ```

   **Option B: Using Supabase Dashboard**
   - Go to **Edge Functions** → **Create Function**
   - Name it `server`
   - Copy the code from `figma_new/src/supabase/functions/server/index.tsx`
   - Paste it into the function editor
   - Deploy

3. **Set Environment Variables:**
   - Go to **Edge Functions** → **Settings** → **Secrets**
   - Add these environment variables:
     ```
     SUPABASE_URL=https://wjfodecgrlbievxtzfoq.supabase.co
     SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
     OPENAI_API_KEY=your_openai_api_key
     ```

### 2. Database Table Issues

#### Check Table Schema

Make sure your `study_plans` table has the correct schema:

```sql
-- Check if table exists
SELECT * FROM information_schema.tables 
WHERE table_name = 'study_plans';

-- Check table structure
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'study_plans';
```

#### Fix Foreign Key Constraint

The table might fail to insert if the foreign key constraint is too strict. For mockup mode, you can:

**Option A: Make user_id nullable (Recommended for testing)**
```sql
ALTER TABLE study_plans 
ALTER COLUMN user_id DROP NOT NULL;
```

**Option B: Remove foreign key constraint (for testing only)**
```sql
ALTER TABLE study_plans 
DROP CONSTRAINT IF EXISTS study_plans_user_id_fkey;
```

**Option C: Use a proper UUID for mock users**
The backend now generates mock user IDs like `mock_user_1234567890`. You can either:
1. Keep the foreign key but insert real users first
2. Remove the foreign key constraint for development
3. Create a mock user in auth.users table

### 3. Check Database Table Schema

Run this SQL to verify your table structure:

```sql
-- Verify table structure
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'study_plans'
ORDER BY ordinal_position;
```

Expected columns:
- `id` (UUID, PRIMARY KEY)
- `user_id` (UUID, nullable for mockup mode)
- `analysis_id` (TEXT)
- `status` (TEXT)
- `created_at` (TIMESTAMPTZ)
- `updated_at` (TIMESTAMPTZ)
- `start_date` (DATE)
- `end_date` (DATE)
- `total_days` (INTEGER)
- `hours_per_day` (TEXT)
- `study_days` (TEXT[])
- `plan_data` (JSONB)
- `metadata` (JSONB)

### 4. Test the Endpoint Directly

You can test the endpoint using curl or Postman:

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

### 5. Check Browser Console

1. Open browser Developer Tools (F12)
2. Go to **Console** tab
3. Look for error messages
4. Check **Network** tab to see the actual request/response

### 6. Check Supabase Edge Function Logs

1. Go to Supabase Dashboard
2. Navigate to **Edge Functions** → **server**
3. Click on **Logs**
4. Look for error messages

### 7. Verify Environment Variables

Make sure these are set in Supabase Edge Function settings:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `OPENAI_API_KEY` (optional, will use mock data if not set)

## Quick Fix for Testing

If you just want to test quickly, you can temporarily modify the table to allow nullable user_id:

```sql
-- Allow null user_id for mockup mode
ALTER TABLE study_plans 
ALTER COLUMN user_id DROP NOT NULL;

-- Remove foreign key constraint temporarily
ALTER TABLE study_plans 
DROP CONSTRAINT IF EXISTS study_plans_user_id_fkey;
```

## Testing Checklist

- [ ] Edge Function is deployed
- [ ] Environment variables are set
- [ ] Database table exists
- [ ] Table schema is correct
- [ ] Foreign key constraint allows mock users (or is removed)
- [ ] Browser console shows no CORS errors
- [ ] Network tab shows the request is being sent
- [ ] Supabase logs show the function is being called

## Still Having Issues?

1. Check the browser console for specific error messages
2. Check Supabase Edge Function logs
3. Verify the endpoint URL is correct: `https://wjfodecgrlbievxtzfoq.supabase.co/functions/v1/server/study-plan/generate`
4. Make sure CORS is enabled (it should be with `app.use('*', cors())`)

