# Study Plan Implementation Guide

## Data Storage Recommendations

### Recommendation: Hybrid Approach (JSONB + Structured Columns)

For Supabase, I recommend using a **hybrid approach** that combines the flexibility of JSONB with the queryability of structured columns:

#### Why Not Pure JSONB?
- ❌ Harder to query specific fields (e.g., "get all study plans created this week")
- ❌ No built-in indexing on nested fields
- ❌ Can't easily filter/sort by date ranges, user_id, status
- ❌ More complex migrations when schema changes

#### Why Not Pure Table Structure?
- ❌ Very rigid schema - hard to add new fields
- ❌ Complex joins for nested data (skills, tasks, resources)
- ❌ Over-normalized for semi-structured data like LLM responses
- ❌ Difficult to store variable-length arrays (daily tasks, skills list)

#### Recommended Schema Structure

```sql
-- Study Plans Table
-- Note: user_id is nullable to support mockup mode testing
CREATE TABLE study_plans (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID, -- Nullable for mockup mode, can add FK constraint later: REFERENCES auth.users(id) ON DELETE CASCADE
  analysis_id TEXT NOT NULL, -- References the skill analysis
  
  -- Structured fields (for querying)
  status TEXT NOT NULL DEFAULT 'active', -- 'active', 'completed', 'archived'
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  total_days INTEGER NOT NULL,
  
  -- User preferences (structured for filtering)
  hours_per_day TEXT NOT NULL, -- '1-2', '2-3', '3-4', '4+'
  study_days TEXT[] NOT NULL, -- ['Mon', 'Tue', 'Wed', ...]
  
  -- LLM-generated content (JSONB for flexibility)
  plan_data JSONB NOT NULL, -- Contains: tasks, phases, skills, resources
  metadata JSONB DEFAULT '{}' -- Additional metadata: XP tracking, progress, etc.
);

-- Optional: Add foreign key constraint after testing (for production)
-- ALTER TABLE study_plans 
-- ADD CONSTRAINT study_plans_user_id_fkey 
-- FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;

CREATE INDEX idx_study_plans_user_id ON study_plans(user_id);
CREATE INDEX idx_study_plans_analysis_id ON study_plans(analysis_id);
CREATE INDEX idx_study_plans_status ON study_plans(status);
CREATE INDEX idx_study_plans_created_at ON study_plans(created_at);
CREATE INDEX idx_study_plans_plan_data ON study_plans USING GIN(plan_data);

-- Example plan_data JSONB structure:
{
  "skills": [
    {
      "name": "SQL",
      "priority": "High",
      "estimatedTime": "20 hours",
      "resources": ["Mode SQL Tutorial", "LeetCode SQL"]
    }
  ],
  "tasks": [
    {
      "date": "2024-11-11",
      "dayOfWeek": "Mon",
      "theme": "Orientation",
      "task": "Review Skill Report + Install Jupyter/VSCode",
      "resources": "SkillMiner Docs",
      "estTime": "1h",
      "xp": 20,
      "completed": false
    }
  ],
  "phases": [
    {
      "range": [0, 1],
      "label": "Foundations",
      "color": "purple"
    }
  ],
  "summary": {
    "totalXP": 650,
    "totalHours": 70,
    "currentProgress": 34
  }
}
```

#### Benefits of This Approach:
✅ **Flexible**: JSONB allows storing variable LLM-generated content
✅ **Queryable**: Structured fields enable efficient queries (user_id, dates, status)
✅ **Indexed**: GIN indexes on JSONB for fast searches
✅ **Scalable**: Easy to add new fields to JSONB without migrations
✅ **Type-safe**: Can use TypeScript interfaces on frontend
✅ **Easy retrieval**: Simple queries like `SELECT * FROM study_plans WHERE user_id = $1`

---

## Implementation Strategy

### Phase 1: Mock Data First (Current State)
- ✅ Frontend displays mock study plans
- ✅ User can input preferences (hours, timeline, study days)

### Phase 2: Backend Integration (Recommended Next Steps)
1. **Create study plan generation endpoint** in Supabase Edge Function
   - Takes: analysis_id, user preferences, skill report data
   - Calls: GPT-4o-mini to generate personalized study plan
   - Stores: Plan in database with structured + JSONB fields
   - Returns: Study plan ID and initial data

2. **Update frontend to call backend**
   - SkillReportMockup → calls `/study-plan/generate` endpoint
   - StudyPlanMockup → calls `/study-plan/:planId` to fetch real data
   - Add loading states and error handling

3. **Test with mock/fake resume data first**
   - Use existing fake resume data
   - Verify LLM prompt works correctly
   - Ensure data storage/retrieval works
   - Test frontend-backend integration

### Phase 3: Real User Data (After Phase 2 Works)
- Connect to real user-uploaded resumes
- Use real skill analysis data
- Add user authentication checks
- Add progress tracking

---

## Files to Create/Modify

### Backend (Supabase Edge Function)
1. **`figma_new/src/supabase/functions/server/index.tsx`**
   - Add `/study-plan/generate` endpoint
   - Add `/study-plan/:planId` endpoint
   - Add `/study-plan/:planId/tasks/:taskId/complete` endpoint (for marking tasks complete)

### Frontend
1. **`figma_new/src/components/mockups/SkillReportMockup.tsx`**
   - Update `onGenerateStudyPlan` to call backend API
   - Add loading state during generation
   - Navigate to study plan page with plan ID

2. **`figma_new/src/components/mockups/StudyPlanMockup.tsx`**
   - Add props to accept `planId` and `userId`
   - Fetch study plan data from backend
   - Replace hardcoded data with real data
   - Add task completion functionality

3. **Create: `figma_new/src/services/studyPlan.ts`**
   - API service functions for study plan operations
   - TypeScript interfaces for study plan data

---

## LLM Prompt Structure

The study plan generation should use a structured prompt that includes:
1. User's skill analysis (existing + missing skills)
2. User preferences (hours/day, timeline, study days)
3. Job description/target role
4. Output format (JSON structure for tasks, phases, resources)

---

## Next Steps

1. ✅ Review this document
2. Create database schema in Supabase
3. Implement backend endpoints
4. Update frontend components
5. Test with mock data
6. Test with real user data

