# Study Plan Backend Integration - Setup Guide

## Summary

I've implemented the study plan generation backend integration. Here's what was added:

### ✅ Completed

1. **Backend API Endpoints** (Supabase Edge Function)
   - `POST /study-plan/generate` - Generates a study plan using GPT-4o-mini
   - `GET /study-plan/:planId` - Retrieves a study plan
   - `PATCH /study-plan/:planId/tasks/:taskIndex/complete` - Updates task completion status

2. **Frontend API Service** (`figma_new/src/services/studyPlan.ts`)
   - TypeScript interfaces for study plan data
   - API functions for generating, fetching, and updating study plans

3. **Updated Components**
   - `SkillReportMockup.tsx` - Now supports backend integration (optional)
   - `StudyPlanMockup.tsx` - Fetches and displays real study plan data when `planId` is provided
   - `App.tsx` - Passes `planId` to StudyPlanMockup

## How to Use

### Option 1: Test with Mock Data (Recommended First Step)

1. **Enable backend in mockup mode:**
   - In `App.tsx`, change `useBackend={false}` to `useBackend={true}` on line 208
   - This will allow testing the backend with mock analysis data

2. **Generate a study plan:**
   - Navigate to the "Skill Report" tab
   - Click "Create My Study Plan"
   - Fill in your preferences (hours/day, timeline, study days)
   - Click "Generate My X-Day Plan"
   - The system will call the backend API and generate a study plan using GPT-4o-mini

3. **View the study plan:**
   - After generation, you'll be redirected to the "Study Plan" tab
   - The study plan will be fetched from the backend and displayed

### Option 2: Use with Real User Data

1. **Set up authentication:**
   - Ensure users are logged in via Supabase Auth
   - Pass `accessToken` and `analysisId` to `SkillReportMockup`

2. **Generate study plan:**
   - The component will use the real user's skill analysis
   - Study plan will be personalized based on their actual skills and gaps

## Data Storage

Currently, study plans are stored in the KV store (JSONB). This is fine for development, but for production, consider migrating to a proper table structure as outlined in `STUDY_PLAN_IMPLEMENTATION.md`.

## Environment Variables

Make sure your Supabase Edge Function has:
- `OPENAI_API_KEY` - Your OpenAI API key for GPT-4o-mini
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` - Your Supabase service role key

## Testing the LLM Integration

1. **With OpenAI API Key:**
   - The system will call GPT-4o-mini to generate personalized study plans
   - Plans will be structured with tasks, phases, resources, and XP points

2. **Without OpenAI API Key:**
   - The system will fall back to mock data generation
   - This allows testing the UI without API costs

## Next Steps

1. **Test the integration:**
   - Enable `useBackend={true}` in App.tsx
   - Generate a study plan and verify it works
   - Check that tasks can be marked as complete

2. **Migrate to database table (optional):**
   - Create the `study_plans` table in Supabase (see `STUDY_PLAN_IMPLEMENTATION.md`)
   - Update the backend to use the table instead of KV store
   - This will enable better querying and indexing

3. **Add real user data:**
   - Connect to real resume uploads
   - Use actual skill analysis results
   - Personalize study plans based on real user profiles

4. **Enhance the LLM prompt:**
   - Fine-tune the prompt for better study plan generation
   - Add more context about learning resources
   - Include user preferences and learning style

## Files Modified

- `figma_new/src/supabase/functions/server/index.tsx` - Added study plan endpoints
- `figma_new/src/services/studyPlan.ts` - New API service file
- `figma_new/src/components/mockups/SkillReportMockup.tsx` - Added backend integration
- `figma_new/src/components/mockups/StudyPlanMockup.tsx` - Added data fetching
- `figma_new/src/App.tsx` - Updated to pass planId

## Files Created

- `figma_new/STUDY_PLAN_IMPLEMENTATION.md` - Implementation guide with data storage recommendations
- `figma_new/STUDY_PLAN_SETUP.md` - This file

## Troubleshooting

1. **"Analysis not found" error:**
   - In mockup mode, the system creates a mock analysis automatically
   - Make sure `useBackend={true}` is set

2. **"Unauthorized" error:**
   - Check that the user is logged in
   - Verify the access token is valid

3. **Study plan not loading:**
   - Check browser console for errors
   - Verify the planId is stored in localStorage
   - Check that the backend endpoint is accessible

4. **LLM not generating plans:**
   - Verify OPENAI_API_KEY is set in Supabase Edge Function environment
   - Check Supabase Edge Function logs for errors
   - The system will fall back to mock data if the API fails

