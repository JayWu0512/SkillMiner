-- SQL translations of pandas operations from 02_insights.ipynb
-- These queries help select data for visualization

-- ============================================================================
-- 3. Role distribution in overall job market
-- ============================================================================
-- Count roles matching patterns and calculate percentages
-- Note: REGEXP requires SQLite extension. If not available, use LIKE patterns below.
WITH role_counts AS (
    SELECT 
        'data scientist' AS role,
        COUNT(*) AS count
    FROM jobs_text
    WHERE title_lc REGEXP '\b(data scientist|scientist)\b'
       OR (title_lc LIKE '%data scientist%' OR title_lc LIKE '% scientist %' OR title_lc LIKE 'scientist %' OR title_lc LIKE '% scientist')
    
    UNION ALL
    
    SELECT 
        'data analyst' AS role,
        COUNT(*) AS count
    FROM jobs_text
    WHERE title_lc REGEXP '\b(data analyst|analyst)\b'
       OR (title_lc LIKE '%data analyst%' OR title_lc LIKE '% analyst %' OR title_lc LIKE 'analyst %' OR title_lc LIKE '% analyst')
    
    UNION ALL
    
    SELECT 
        'data engineer' AS role,
        COUNT(*) AS count
    FROM jobs_text
    WHERE title_lc REGEXP '\bdata engineer\b'
       OR title_lc LIKE '%data engineer%'
    
    UNION ALL
    
    SELECT 
        'software engineer' AS role,
        COUNT(*) AS count
    FROM jobs_text
    WHERE title_lc REGEXP '\bsoftware engineer\b'
       OR title_lc LIKE '%software engineer%'
),
total_jobs AS (
    SELECT COUNT(*) AS total FROM jobs_text
)
SELECT 
    rc.role,
    rc.count,
    ROUND(rc.count * 100.0 / t.total, 6) AS percentage
FROM role_counts rc
CROSS JOIN total_jobs t
ORDER BY rc.count DESC;

-- ============================================================================
-- 4. Top 20 Skills across all roles (DA + DS + DE + SWE)
-- ============================================================================
-- Unnest skills_list (stored as JSON array), count skills, get top 20
WITH skills_unnested AS (
    SELECT 
        json_each.value AS skill
    FROM jobs_text,
    json_each(json(skills_list))
    WHERE skills_list IS NOT NULL
)
SELECT 
    skill,
    COUNT(*) AS count
FROM skills_unnested
GROUP BY skill
ORDER BY count DESC
LIMIT 20;

-- ============================================================================
-- 5. Top 20 Skills (Normalized across DA/DS/DE/SWE)
-- ============================================================================
-- Normalize skills within each role, then average proportions across roles
WITH role_skills_unnested AS (
    -- Data Scientist
    SELECT 
        'data scientist' AS role,
        json_each.value AS skill
    FROM jobs_text jt
    CROSS JOIN json_each(json(jt.skills_list))
    WHERE jt.title_lc IS NOT NULL
      AND jt.skills_list IS NOT NULL
      AND (jt.title_lc REGEXP '\b(data scientist|scientist)\b'
           OR jt.title_lc LIKE '%data scientist%' 
           OR jt.title_lc LIKE '% scientist %' 
           OR jt.title_lc LIKE 'scientist %' 
           OR jt.title_lc LIKE '% scientist')
    
    UNION ALL
    
    -- Data Analyst
    SELECT 
        'data analyst' AS role,
        json_each.value AS skill
    FROM jobs_text jt
    CROSS JOIN json_each(json(jt.skills_list))
    WHERE jt.title_lc IS NOT NULL
      AND jt.skills_list IS NOT NULL
      AND (jt.title_lc REGEXP '\b(data analyst|analyst)\b'
           OR jt.title_lc LIKE '%data analyst%' 
           OR jt.title_lc LIKE '% analyst %' 
           OR jt.title_lc LIKE 'analyst %' 
           OR jt.title_lc LIKE '% analyst')
    
    UNION ALL
    
    -- Data Engineer
    SELECT 
        'data engineer' AS role,
        json_each.value AS skill
    FROM jobs_text jt
    CROSS JOIN json_each(json(jt.skills_list))
    WHERE jt.title_lc IS NOT NULL
      AND jt.skills_list IS NOT NULL
      AND (jt.title_lc REGEXP '\bdata engineer\b'
           OR jt.title_lc LIKE '%data engineer%')
    
    UNION ALL
    
    -- Software Engineer
    SELECT 
        'software engineer' AS role,
        json_each.value AS skill
    FROM jobs_text jt
    CROSS JOIN json_each(json(jt.skills_list))
    WHERE jt.title_lc IS NOT NULL
      AND jt.skills_list IS NOT NULL
      AND (jt.title_lc REGEXP '\bsoftware engineer\b'
           OR jt.title_lc LIKE '%software engineer%')
),
role_skill_counts AS (
    SELECT 
        role,
        skill,
        COUNT(*) AS skill_count
    FROM role_skills_unnested
    GROUP BY role, skill
),
role_totals AS (
    SELECT 
        role,
        SUM(skill_count) AS total_skills
    FROM role_skill_counts
    GROUP BY role
),
role_skill_proportions AS (
    SELECT 
        rsc.role,
        rsc.skill,
        CAST(rsc.skill_count AS REAL) / rt.total_skills AS proportion
    FROM role_skill_counts rsc
    JOIN role_totals rt ON rsc.role = rt.role
),
avg_skill_proportions AS (
    SELECT 
        skill,
        AVG(proportion) AS avg_proportion
    FROM role_skill_proportions
    GROUP BY skill
)
SELECT 
    skill,
    avg_proportion
FROM avg_skill_proportions
ORDER BY avg_proportion DESC
LIMIT 20;

-- ============================================================================
-- 6. Top Skills by Role (DA / DS / DE / SWE)
-- ============================================================================
-- Get top 10 skills for each role
WITH role_skills_unnested AS (
    -- Data Scientist
    SELECT 
        'data scientist' AS role,
        json_each.value AS skill
    FROM jobs_text jt
    CROSS JOIN json_each(json(jt.skills_list))
    WHERE jt.title_lc IS NOT NULL
      AND jt.skills_list IS NOT NULL
      AND (jt.title_lc REGEXP '\b(data scientist|scientist)\b'
           OR jt.title_lc LIKE '%data scientist%' 
           OR jt.title_lc LIKE '% scientist %' 
           OR jt.title_lc LIKE 'scientist %' 
           OR jt.title_lc LIKE '% scientist')
    
    UNION ALL
    
    -- Data Analyst
    SELECT 
        'data analyst' AS role,
        json_each.value AS skill
    FROM jobs_text jt
    CROSS JOIN json_each(json(jt.skills_list))
    WHERE jt.title_lc IS NOT NULL
      AND jt.skills_list IS NOT NULL
      AND (jt.title_lc REGEXP '\b(data analyst|analyst)\b'
           OR jt.title_lc LIKE '%data analyst%' 
           OR jt.title_lc LIKE '% analyst %' 
           OR jt.title_lc LIKE 'analyst %' 
           OR jt.title_lc LIKE '% analyst')
    
    UNION ALL
    
    -- Data Engineer
    SELECT 
        'data engineer' AS role,
        json_each.value AS skill
    FROM jobs_text jt
    CROSS JOIN json_each(json(jt.skills_list))
    WHERE jt.title_lc IS NOT NULL
      AND jt.skills_list IS NOT NULL
      AND (jt.title_lc REGEXP '\bdata engineer\b'
           OR jt.title_lc LIKE '%data engineer%')
    
    UNION ALL
    
    -- Software Engineer
    SELECT 
        'software engineer' AS role,
        json_each.value AS skill
    FROM jobs_text jt
    CROSS JOIN json_each(json(jt.skills_list))
    WHERE jt.title_lc IS NOT NULL
      AND jt.skills_list IS NOT NULL
      AND (jt.title_lc REGEXP '\bsoftware engineer\b'
           OR jt.title_lc LIKE '%software engineer%')
),
role_skill_counts AS (
    SELECT 
        role,
        skill,
        COUNT(*) AS count,
        ROW_NUMBER() OVER (PARTITION BY role ORDER BY COUNT(*) DESC) AS rn
    FROM role_skills_unnested
    GROUP BY role, skill
)
SELECT 
    role,
    skill,
    count
FROM role_skill_counts
WHERE rn <= 10
ORDER BY role, count DESC;

-- ============================================================================
-- 7. Top 20 Regions for DA, DS, DE, SWE (US states + countries)
-- ============================================================================
-- Parse location to extract region (state/country) and count top 20
-- Logic: Split by comma, take last part (trimmed)
-- Note: Uses recursive CTE to find position of last comma
WITH RECURSIVE comma_positions AS (
    -- Base case: find all comma positions
    SELECT 
        location,
        1 AS search_pos,
        INSTR(SUBSTR(location, 1), ',') AS comma_pos
    FROM jobs_text
    WHERE location IS NOT NULL AND location LIKE '%,%'
    
    UNION ALL
    
    -- Recursive case: find next comma
    SELECT 
        location,
        comma_pos + 1 AS search_pos,
        CASE 
            WHEN INSTR(SUBSTR(location, comma_pos + 1), ',') > 0 
            THEN comma_pos + INSTR(SUBSTR(location, comma_pos + 1), ',')
            ELSE 0
        END AS comma_pos
    FROM comma_positions
    WHERE comma_pos > 0
),
last_comma AS (
    SELECT 
        location,
        MAX(comma_pos) AS last_comma_pos
    FROM comma_positions
    GROUP BY location
),
parsed_regions AS (
    SELECT 
        CASE 
            WHEN jt.location IS NULL THEN 'NA'
            WHEN lc.last_comma_pos IS NULL OR lc.last_comma_pos = 0 
            THEN TRIM(jt.location)
            ELSE TRIM(SUBSTR(jt.location, lc.last_comma_pos + 1))
        END AS region
    FROM jobs_text jt
    LEFT JOIN last_comma lc ON jt.location = lc.location
)
SELECT 
    region,
    COUNT(*) AS count
FROM parsed_regions
GROUP BY region
ORDER BY count DESC
LIMIT 20;
