-- Check if study_plans table exists and has correct structure
-- Run this in Supabase SQL Editor

-- 1. Check if table exists
SELECT 
    table_name,
    table_type
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name = 'study_plans';

-- 2. Check table structure
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default,
    character_maximum_length
FROM information_schema.columns
WHERE table_name = 'study_plans'
ORDER BY ordinal_position;

-- 3. Check indexes
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'study_plans';

-- 4. Check constraints
SELECT
    conname AS constraint_name,
    contype AS constraint_type,
    pg_get_constraintdef(oid) AS constraint_definition
FROM pg_constraint
WHERE conrelid = 'study_plans'::regclass;

-- 5. Test insert (should work if schema is correct)
-- This will fail if there are issues, but won't insert if table doesn't exist
DO $$
BEGIN
    -- Test if we can insert (rollback afterwards)
    INSERT INTO study_plans (
        id,
        user_id,
        analysis_id,
        status,
        start_date,
        end_date,
        total_days,
        hours_per_day,
        study_days,
        plan_data,
        metadata
    ) VALUES (
        gen_random_uuid(),
        'mock_user_test'::uuid,  -- This will fail if user_id must be UUID
        'test_analysis',
        'active',
        CURRENT_DATE,
        CURRENT_DATE + INTERVAL '60 days',
        60,
        '2-3',
        ARRAY['Mon', 'Tue', 'Wed'],
        '{"test": true}'::jsonb,
        '{}'::jsonb
    );
    RAISE NOTICE 'Table structure is correct!';
    ROLLBACK;  -- Don't actually insert
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Error: %', SQLERRM;
END $$;

-- 6. If user_id constraint is the issue, you can fix it with:
-- ALTER TABLE study_plans ALTER COLUMN user_id DROP NOT NULL;
-- ALTER TABLE study_plans DROP CONSTRAINT IF EXISTS study_plans_user_id_fkey;

