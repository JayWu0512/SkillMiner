import { Hono } from 'npm:hono';
import { cors } from 'npm:hono/cors';
import { logger } from 'npm:hono/logger';
import { createClient } from 'jsr:@supabase/supabase-js@2';
import * as kv from './kv_store.tsx';

const app = new Hono();

app.use('*', cors());
app.use('*', logger(console.log));

// Mock skill database
const SKILL_DATABASE = {
  hardSkills: [
    'JavaScript', 'TypeScript', 'React', 'Node.js', 'Python', 'Java', 'SQL',
    'AWS', 'Docker', 'Kubernetes', 'Git', 'REST APIs', 'GraphQL', 'MongoDB',
    'PostgreSQL', 'Machine Learning', 'Data Analysis', 'Agile', 'CI/CD', 'TDD'
  ],
  softSkills: [
    'Leadership', 'Communication', 'Team Collaboration', 'Problem Solving',
    'Critical Thinking', 'Time Management', 'Adaptability', 'Creativity',
    'Conflict Resolution', 'Emotional Intelligence', 'Presentation Skills',
    'Mentoring', 'Strategic Thinking', 'Decision Making'
  ]
};

// Mock learning resources
const LEARNING_RESOURCES: Record<string, any[]> = {
  'JavaScript': [
    { title: 'JavaScript: The Complete Guide (Udemy)', url: 'https://www.udemy.com/course/javascript-the-complete-guide-2020-beginner-advanced/', hours: 52 },
    { title: 'MDN JavaScript Guide', url: 'https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide', hours: 20 }
  ],
  'TypeScript': [
    { title: 'Understanding TypeScript (Udemy)', url: 'https://www.udemy.com/course/understanding-typescript/', hours: 15 },
    { title: 'TypeScript Official Docs', url: 'https://www.typescriptlang.org/docs/', hours: 10 }
  ],
  'React': [
    { title: 'React - The Complete Guide (Udemy)', url: 'https://www.udemy.com/course/react-the-complete-guide-incl-redux/', hours: 48 },
    { title: 'Official React Tutorial', url: 'https://react.dev/learn', hours: 8 }
  ],
  'Python': [
    { title: 'Complete Python Bootcamp (Udemy)', url: 'https://www.udemy.com/course/complete-python-bootcamp/', hours: 22 },
    { title: 'Python for Everybody (Coursera)', url: 'https://www.coursera.org/specializations/python', hours: 32 }
  ],
  'AWS': [
    { title: 'AWS Certified Solutions Architect', url: 'https://aws.amazon.com/training/', hours: 40 },
    { title: 'AWS Cloud Practitioner Essentials', url: 'https://explore.skillbuilder.aws/learn', hours: 6 }
  ],
  'Docker': [
    { title: 'Docker Mastery (Udemy)', url: 'https://www.udemy.com/course/docker-mastery/', hours: 19 },
    { title: 'Docker Official Getting Started', url: 'https://docs.docker.com/get-started/', hours: 5 }
  ],
  'Leadership': [
    { title: 'Leadership Principles (Coursera)', url: 'https://www.coursera.org/learn/leadership-principles', hours: 15 },
    { title: 'Developing Leadership Skills', url: 'https://www.linkedin.com/learning/topics/leadership', hours: 12 }
  ],
  'Communication': [
    { title: 'Effective Communication Skills', url: 'https://www.coursera.org/learn/communication-skills', hours: 10 },
    { title: 'Business Communication', url: 'https://www.linkedin.com/learning/topics/business-communication', hours: 8 }
  ],
  'Problem Solving': [
    { title: 'Creative Problem Solving', url: 'https://www.coursera.org/learn/creative-problem-solving', hours: 12 },
    { title: 'Critical Thinking Skills', url: 'https://www.linkedin.com/learning/topics/critical-thinking', hours: 6 }
  ]
};

// Helper function to extract skills from text
function extractSkills(text: string, skillsList: string[]): string[] {
  const textLower = text.toLowerCase();
  return skillsList.filter(skill => 
    textLower.includes(skill.toLowerCase())
  );
}

// Helper function to parse resume (mock implementation)
function parseResume(resumeText: string) {
  // In a real implementation, this would use PDF/DOCX parsing libraries
  // For demo, we'll simulate extracted text
  const hardSkills = extractSkills(resumeText, SKILL_DATABASE.hardSkills);
  const softSkills = extractSkills(resumeText, SKILL_DATABASE.softSkills);
  
  return {
    hardSkills,
    softSkills,
    experience: resumeText.match(/\d+\+?\s*years?/gi) || [],
    education: resumeText.match(/(bachelor|master|phd|diploma)/gi) || []
  };
}

// Analyze job description and resume
app.post('/server/analyze', async (c) => {
  try {
    const accessToken = c.req.header('Authorization')?.split(' ')[1];
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL')!,
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    );

    const { data: { user }, error: authError } = await supabase.auth.getUser(accessToken);
    if (!user?.id) {
      return c.json({ error: 'Unauthorized' }, 401);
    }

    const formData = await c.req.formData();
    const jobDescription = formData.get('jobDescription') as string;
    const resumeFile = formData.get('resume') as File;

    if (!jobDescription || !resumeFile) {
      return c.json({ error: 'Missing required fields' }, 400);
    }

    // Read resume file
    const resumeText = await resumeFile.text();
    
    // Parse resume
    const resumeData = parseResume(resumeText);
    
    // Extract job requirements
    const requiredHardSkills = extractSkills(jobDescription, SKILL_DATABASE.hardSkills);
    const requiredSoftSkills = extractSkills(jobDescription, SKILL_DATABASE.softSkills);
    
    // Calculate matches and gaps
    const matchingHardSkills = resumeData.hardSkills.filter(skill => 
      requiredHardSkills.includes(skill)
    );
    const missingHardSkills = requiredHardSkills.filter(skill => 
      !resumeData.hardSkills.includes(skill)
    );
    
    const matchingSoftSkills = resumeData.softSkills.filter(skill => 
      requiredSoftSkills.includes(skill)
    );
    const missingSoftSkills = requiredSoftSkills.filter(skill => 
      !resumeData.softSkills.includes(skill)
    );
    
    // Calculate match score
    const totalRequired = requiredHardSkills.length + requiredSoftSkills.length;
    const totalMatched = matchingHardSkills.length + matchingSoftSkills.length;
    const matchScore = totalRequired > 0 
      ? Math.round((totalMatched / totalRequired) * 100)
      : 0;
    
    // Generate analysis result
    const analysisId = `analysis_${user.id}_${Date.now()}`;
    const analysisResult = {
      userId: user.id,
      analysisId,
      timestamp: new Date().toISOString(),
      matchScore,
      jobDescription,
      resumeData,
      requiredHardSkills,
      requiredSoftSkills,
      matchingHardSkills,
      missingHardSkills,
      matchingSoftSkills,
      missingSoftSkills,
      totalLearningHours: missingHardSkills.reduce((total, skill) => {
        const resources = LEARNING_RESOURCES[skill] || [];
        return total + (resources[0]?.hours || 0);
      }, 0)
    };
    
    // Store in KV store
    await kv.set(analysisId, analysisResult);
    
    console.log(`Analysis completed for user ${user.id}: ${matchScore}% match`);
    
    return c.json({
      analysisId,
      matchScore,
      matchingSkills: totalMatched,
      missingSkills: missingHardSkills.length + missingSoftSkills.length
    });
    
  } catch (error: any) {
    console.error('Analysis error:', error);
    return c.json({ error: `Analysis failed: ${error.message}` }, 500);
  }
});

// Get analysis summary
app.get('/server/analysis/:analysisId', async (c) => {
  try {
    const accessToken = c.req.header('Authorization')?.split(' ')[1];
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL')!,
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    );

    const { data: { user }, error: authError } = await supabase.auth.getUser(accessToken);
    if (!user?.id) {
      return c.json({ error: 'Unauthorized' }, 401);
    }

    const analysisId = c.req.param('analysisId');
    const analysis = await kv.get(analysisId);
    
    if (!analysis) {
      return c.json({ error: 'Analysis not found' }, 404);
    }

    if (analysis.userId !== user.id) {
      return c.json({ error: 'Unauthorized' }, 403);
    }

    return c.json({
      matchScore: analysis.matchScore,
      matchingSkills: analysis.matchingHardSkills.length + analysis.matchingSoftSkills.length,
      missingSkills: analysis.missingHardSkills.length + analysis.missingSoftSkills.length
    });
    
  } catch (error: any) {
    console.error('Error fetching analysis:', error);
    return c.json({ error: `Failed to fetch analysis: ${error.message}` }, 500);
  }
});

// Chat endpoint with LLM integration
app.post('/server/chat', async (c) => {
  try {
    const accessToken = c.req.header('Authorization')?.split(' ')[1];
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL')!,
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    );

    const { data: { user }, error: authError } = await supabase.auth.getUser(accessToken);
    if (!user?.id) {
      return c.json({ error: 'Unauthorized' }, 401);
    }

    const { analysisId, message, messages } = await c.req.json();
    
    // Get user's analysis if analysisId is provided
    let analysis = null;
    if (analysisId) {
      analysis = await kv.get(analysisId);
      if (analysis && analysis.userId !== user.id) {
        return c.json({ error: 'Analysis not found' }, 404);
      }
    }

    const openAIApiKey = Deno.env.get('OPENAI_API_KEY');

    let response = '';

    if (openAIApiKey) {
      response = await callOpenAI(message, messages || [], analysis);
    } else {
      // Fallback to rule-based responses if no API key configured
      response = generateRuleBasedResponse(message, analysis);
    }
    
    // Store conversation history
    const conversationKey = `conversation_${user.id}_${Date.now()}`;
    await kv.set(conversationKey, {
      userId: user.id,
      analysisId,
      message,
      response,
      timestamp: new Date().toISOString()
    });
    
    return c.json({ response });
    
  } catch (error: any) {
    console.error('Chat error:', error);
    return c.json({ error: `Chat failed: ${error.message}` }, 500);
  }
});

// Helper function to call OpenAI API
async function callOpenAI(userMessage: string, conversationHistory: any[], analysis: any): Promise<string> {
  const apiKey = Deno.env.get('OPENAI_API_KEY');
  
  // Build system prompt with user's analysis context
  let systemPrompt = `You are a helpful career development and study planning assistant for SkillMiner, an application that helps users identify skill gaps and create personalized learning plans.

Your role is to:
- Help users understand their skill assessment results
- Provide guidance on creating effective study plans
- Suggest learning resources and strategies
- Motivate and support users in their learning journey
- Answer questions about rescheduling tasks, adjusting difficulty, or modifying their study plan

Be encouraging, practical, and specific in your responses.`;

  if (analysis) {
    systemPrompt += `\n\nUser's Current Analysis:
- Match Score: ${analysis.matchScore}%
- Matching Skills: ${analysis.matchingHardSkills?.join(', ') || 'None'}
- Missing Hard Skills: ${analysis.missingHardSkills?.join(', ') || 'None'}
- Missing Soft Skills: ${analysis.missingSoftSkills?.join(', ') || 'None'}
- Total Learning Hours Needed: ${analysis.totalLearningHours || 0}`;
  }

  // Build messages array
  const messages = [
    { role: 'system', content: systemPrompt },
    ...conversationHistory.map((msg: any) => ({
      role: msg.role,
      content: msg.content
    })),
    { role: 'user', content: userMessage }
  ];

  try {
    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify({
        model: 'gpt-4o-mini', // Cost-effective model
        messages: messages,
        max_tokens: 500,
        temperature: 0.7
      })
    });

    if (!response.ok) {
      const error = await response.text();
      console.error('OpenAI API error:', error);
      throw new Error(`OpenAI API error: ${response.status}`);
    }

    const data = await response.json();
    return data.choices[0].message.content;
  } catch (error: any) {
    console.error('Error calling OpenAI:', error);
    // Fallback to rule-based if API fails
    return generateRuleBasedResponse(userMessage, analysis);
  }
}

// Fallback rule-based response generator
function generateRuleBasedResponse(message: string, analysis: any): string {
  const messageLower = message.toLowerCase();
  
  if (!analysis) {
    return `I'm here to help! I can assist you with:

• Understanding your skill assessment
• Creating a personalized learning plan
• Rescheduling tasks or adjusting difficulty
• Finding learning resources
• Preparing for interviews

What would you like help with today?`;
  }
  
  if (messageLower.includes('hard skill')) {
    if (analysis.missingHardSkills?.length > 0) {
      return `You're missing the following hard skills:\n\n${analysis.missingHardSkills.map((skill: string) => `• ${skill}`).join('\n')}\n\nI recommend focusing on the most critical ones first. Would you like me to suggest learning resources for any specific skill?`;
    } else {
      return `Great news! You have all the hard skills mentioned in the job description: ${analysis.matchingHardSkills.join(', ')}.`;
    }
  } else if (messageLower.includes('soft skill')) {
    if (analysis.missingSoftSkills?.length > 0) {
      return `The job requires these soft skills that could be highlighted better:\n\n${analysis.missingSoftSkills.map((skill: string) => `• ${skill}`).join('\n')}\n\nThese can often be demonstrated through your experience and achievements.`;
    } else {
      return `You demonstrate all the soft skills mentioned: ${analysis.matchingSoftSkills.join(', ')}. Well done!`;
    }
  } else if (messageLower.includes('learning plan') || messageLower.includes('study plan') || messageLower.includes('improve')) {
    const totalHours = analysis.totalLearningHours;
    return `Based on your skill gaps, here's a recommended learning plan:\n\n**Estimated Time:** ${totalHours} hours (about ${Math.ceil(totalHours / 20)} weeks at 20 hours/week)\n\n**Priority Skills:**\n${analysis.missingHardSkills?.slice(0, 3).map((skill: string, i: number) => `${i + 1}. ${skill}`).join('\n') || 'No missing skills identified'}\n\nWould you like detailed resources for any of these?`;
  } else if (messageLower.includes('reschedule') || messageLower.includes('schedule')) {
    return `I can help you reschedule tasks! You can:\n\n• Move tasks to different days\n• Adjust your daily study hours\n• Add or remove days off\n• Extend your timeline\n\nWhat specific changes would you like to make to your schedule?`;
  } else if (messageLower.includes('harder') || messageLower.includes('difficult')) {
    return `I'll help you increase the challenge level! This might include:\n\n• Adding more advanced topics\n• Increasing practice problems per day\n• Shortening your timeline\n• Adding real-world projects\n\nWhich aspect would you like to make more challenging?`;
  } else if (messageLower.includes('easier') || messageLower.includes('slow down')) {
    return `No problem! We can adjust the difficulty by:\n\n• Extending your timeline\n• Reducing daily study hours\n• Breaking topics into smaller chunks\n• Adding more review days\n\nWhat would help you most right now?`;
  } else if (messageLower.includes('resume')) {
    return `Here are some tips to improve your resume:\n\n1. **Highlight matching skills** - Emphasize: ${analysis.matchingHardSkills?.slice(0, 3).join(', ') || 'your key skills'}\n2. **Add missing keywords** - Consider adding projects or experience with: ${analysis.missingHardSkills?.slice(0, 2).join(', ') || 'relevant technologies'}\n3. **Quantify achievements** - Use numbers and metrics\n4. **Tailor your summary** - Align it with the job requirements\n\nWould you like specific examples for any section?`;
  } else {
    return `I can help you with:\n\n• Understanding your ${analysis.matchScore}% match score\n• Creating a learning plan for the ${analysis.missingHardSkills?.length || 0} skills you need\n• Rescheduling tasks or adjusting difficulty\n• Improving your resume\n• Finding resources for specific skills\n\nWhat would you like to know more about?`;
  }
}

// Get detailed report
app.get('/server/report/:analysisId', async (c) => {
  try {
    const accessToken = c.req.header('Authorization')?.split(' ')[1];
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL')!,
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    );

    const { data: { user }, error: authError } = await supabase.auth.getUser(accessToken);
    if (!user?.id) {
      return c.json({ error: 'Unauthorized' }, 401);
    }

    const analysisId = c.req.param('analysisId');
    const analysis = await kv.get(analysisId);
    
    if (!analysis || analysis.userId !== user.id) {
      return c.json({ error: 'Analysis not found' }, 404);
    }

    // Build detailed report with resources
    const hardSkillsWithResources = analysis.missingHardSkills.map((skill: string) => ({
      name: skill,
      resources: LEARNING_RESOURCES[skill] || [
        { title: `Learn ${skill} Online`, url: 'https://www.coursera.org', hours: 20 }
      ]
    }));

    const softSkillsWithResources = analysis.missingSoftSkills.map((skill: string) => ({
      name: skill,
      resources: LEARNING_RESOURCES[skill] || [
        { title: `Develop ${skill}`, url: 'https://www.linkedin.com/learning', hours: 10 }
      ]
    }));

    return c.json({
      matchScore: analysis.matchScore,
      hardSkills: {
        existing: analysis.matchingHardSkills.map((skill: string) => ({
          name: skill,
          level: 'Intermediate'
        })),
        missing: hardSkillsWithResources
      },
      softSkills: {
        existing: analysis.matchingSoftSkills.map((skill: string) => ({
          name: skill
        })),
        missing: softSkillsWithResources
      },
      totalLearningHours: analysis.totalLearningHours
    });
    
  } catch (error: any) {
    console.error('Report error:', error);
    return c.json({ error: `Failed to generate report: ${error.message}` }, 500);
  }
});

// -----------------------------------------
// Study plan handlers (shared implementations)
// -----------------------------------------

const handleGenerateStudyPlan = async (c: any) => {
  try {
    const authHeader = c.req.header('Authorization');
    const accessToken = authHeader?.split(' ')[1];
    
    // Create Supabase client with service role for database operations
    const supabaseAdmin = createClient(
      Deno.env.get('SUPABASE_URL')!,
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    );

    // Try to get user, but allow anonymous access for mockup mode
    let userId: string | null = null;
    if (accessToken) {
      try {
        const { data: { user }, error: authError } = await supabaseAdmin.auth.getUser(accessToken);
        if (user?.id) {
          userId = user.id;
        }
      } catch (authErr) {
        // If auth fails, continue with null user_id for mockup mode
        console.log('Auth check failed, using null user_id for mockup mode:', authErr);
      }
    }

    // For mockup mode, use null user_id (table allows nullable user_id)
    // This allows testing without authentication

    const { analysisId, hoursPerDay, timeline, studyDays, jobDescription } = await c.req.json();

    if (!analysisId || !hoursPerDay || !timeline || !studyDays) {
      return c.json({ error: 'Missing required fields', details: { analysisId, hoursPerDay, timeline, studyDays } }, 400);
    }

    // Get analysis data from KV store (or create mock if doesn't exist)
    let analysis = await kv.get(analysisId);
    
    // If analysis doesn't exist and it's a mock analysis, create one
    if (!analysis && analysisId.startsWith('mock_analysis_')) {
      analysis = {
        userId: userId,
        analysisId,
        matchScore: 68,
        matchingHardSkills: ['Python', 'Excel', 'Communication'],
        missingHardSkills: ['SQL', 'Tableau', 'Statistics'],
        matchingSoftSkills: ['Communication'],
        missingSoftSkills: ['Problem Solving'],
        jobDescription: jobDescription || 'Data Analyst (Entry-Level) Position',
        totalLearningHours: 70
      };
    }
    
    if (!analysis) {
      return c.json({ error: 'Analysis not found', analysisId }, 404);
    }

    // Generate study plan using LLM
    const studyPlan = await generateStudyPlanWithLLM({
      analysis,
      hoursPerDay,
      timeline: parseInt(timeline),
      studyDays,
      jobDescription: jobDescription || analysis.jobDescription
    });

    // Calculate dates
    const startDate = new Date();
    const endDate = new Date();
    endDate.setDate(endDate.getDate() + parseInt(timeline));

    // Generate UUID for plan ID (use crypto.randomUUID or fallback)
    let planId: string;
    try {
      planId = crypto.randomUUID();
    } catch {
      // Fallback if crypto.randomUUID is not available
      planId = `plan_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    // Prepare study plan data for database
    // user_id can be null for mockup mode (table allows nullable user_id)
    const studyPlanData: any = {
      id: planId,
      analysis_id: analysisId,
      status: 'active',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      start_date: startDate.toISOString().split('T')[0],
      end_date: endDate.toISOString().split('T')[0],
      total_days: parseInt(timeline),
      hours_per_day: hoursPerDay,
      study_days: studyDays,
      plan_data: studyPlan,
      metadata: {
        progress: 0,
        totalXP: studyPlan.summary?.totalXP || 0,
        completedTasks: 0
      }
    };

    // Only include user_id if it's a valid UUID (not null)
    if (userId && userId.match(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i)) {
      studyPlanData.user_id = userId;
    }
    // Otherwise, user_id will be null (allowed for mockup mode)

    // Store study plan in database table
    const { data: insertedData, error: insertError } = await supabaseAdmin
      .from('study_plans')
      .insert(studyPlanData)
      .select()
      .single();

    if (insertError) {
      console.error('Database insert error:', insertError);
      // Fallback to KV store if database insert fails
      await kv.set(planId, {
        ...studyPlanData,
        userId: studyPlanData.user_id,
        analysisId: studyPlanData.analysis_id,
        createdAt: studyPlanData.created_at,
        updatedAt: studyPlanData.updated_at,
        startDate: studyPlanData.start_date,
        endDate: studyPlanData.end_date,
        totalDays: studyPlanData.total_days,
        hoursPerDay: studyPlanData.hours_per_day,
        studyDays: studyPlanData.study_days,
        planData: studyPlanData.plan_data,
      });
      console.log('Fell back to KV store for study plan:', planId);
    } else {
      console.log(`Study plan generated and stored in database for user ${userId}: ${planId}`);
    }

    // Return data in the format expected by frontend
    return c.json({
      planId,
      id: planId,
      userId: userId,
      analysisId,
      status: 'active',
      createdAt: studyPlanData.created_at,
      updatedAt: studyPlanData.updated_at,
      startDate: studyPlanData.start_date,
      endDate: studyPlanData.end_date,
      totalDays: studyPlanData.total_days,
      hoursPerDay,
      studyDays,
      planData: studyPlan,
      metadata: studyPlanData.metadata
    });
    
  } catch (error: any) {
    console.error('Study plan generation error:', error);
    console.error('Error stack:', error.stack);
    return c.json({ 
      error: `Failed to generate study plan: ${error.message}`,
      details: error.stack 
    }, 500);
  }
};

app.post('/server/study-plan/generate', handleGenerateStudyPlan);
app.post('/study-plan/generate', handleGenerateStudyPlan); // fallback for direct path

// Get study plan
const handleGetStudyPlan = async (c: any) => {
  try {
    const authHeader = c.req.header('Authorization');
    const accessToken = authHeader?.split(' ')[1];
    
    const supabaseAdmin = createClient(
      Deno.env.get('SUPABASE_URL')!,
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    );

    // Try to get user, but allow anonymous access for mockup mode
    let userId: string | null = null;
    if (accessToken) {
      try {
        const { data: { user } } = await supabaseAdmin.auth.getUser(accessToken);
        if (user?.id) {
          userId = user.id;
        }
      } catch (authErr) {
        // Continue without user for mockup mode
      }
    }

    const planId = c.req.param('planId');
    
    // Try to get from database first
    const { data: dbPlan, error: dbError } = await supabaseAdmin
      .from('study_plans')
      .select('*')
      .eq('id', planId)
      .single();

    if (dbPlan && !dbError) {
      // Convert database format to frontend format
      const studyPlan = {
        id: dbPlan.id,
        userId: dbPlan.user_id,
        analysisId: dbPlan.analysis_id,
        status: dbPlan.status,
        createdAt: dbPlan.created_at,
        updatedAt: dbPlan.updated_at,
        startDate: dbPlan.start_date,
        endDate: dbPlan.end_date,
        totalDays: dbPlan.total_days,
        hoursPerDay: dbPlan.hours_per_day,
        studyDays: dbPlan.study_days,
        planData: dbPlan.plan_data,
        metadata: dbPlan.metadata
      };

      // Check authorization (allow if no user, user matches, or user_id is null for mockup mode)
      if (!userId || studyPlan.userId === userId || !studyPlan.userId) {
        return c.json(studyPlan);
      }
    }

    // Fallback to KV store
    const studyPlan = await kv.get(planId);
    
    if (!studyPlan) {
      return c.json({ error: 'Study plan not found', planId }, 404);
    }

    // Check authorization
    if (userId && studyPlan.userId && studyPlan.userId !== userId && !studyPlan.userId.startsWith('mock_user_')) {
      return c.json({ error: 'Unauthorized' }, 403);
    }

    return c.json(studyPlan);
    
  } catch (error: any) {
    console.error('Error fetching study plan:', error);
    return c.json({ error: `Failed to fetch study plan: ${error.message}` }, 500);
  }
};

app.get('/server/study-plan/:planId', handleGetStudyPlan);
app.get('/study-plan/:planId', handleGetStudyPlan); // fallback

// Update task completion status
const handleUpdateTask = async (c: any) => {
  try {
    const authHeader = c.req.header('Authorization');
    const accessToken = authHeader?.split(' ')[1];
    
    const supabaseAdmin = createClient(
      Deno.env.get('SUPABASE_URL')!,
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    );

    // Try to get user, but allow anonymous access for mockup mode
    let userId: string | null = null;
    if (accessToken) {
      try {
        const { data: { user } } = await supabaseAdmin.auth.getUser(accessToken);
        if (user?.id) {
          userId = user.id;
        }
      } catch (authErr) {
        // Continue without user for mockup mode
      }
    }

    const planId = c.req.param('planId');
    const taskIndex = parseInt(c.req.param('taskIndex'));
    const { completed } = await c.req.json();

    // Try to get from database first
    const { data: dbPlan, error: dbError } = await supabaseAdmin
      .from('study_plans')
      .select('*')
      .eq('id', planId)
      .single();

    if (dbPlan && !dbError) {
      // Check authorization (allow if user_id is null for mockup mode)
      if (userId && dbPlan.user_id && dbPlan.user_id !== userId) {
        return c.json({ error: 'Unauthorized' }, 403);
      }

      // Update task completion status
      if (dbPlan.plan_data.tasks && dbPlan.plan_data.tasks[taskIndex]) {
        dbPlan.plan_data.tasks[taskIndex].completed = completed === true;
        dbPlan.updated_at = new Date().toISOString();
        
        // Update metadata
        const completedTasks = dbPlan.plan_data.tasks.filter((t: any) => t.completed).length;
        dbPlan.metadata.completedTasks = completedTasks;
        dbPlan.metadata.progress = Math.round((completedTasks / dbPlan.plan_data.tasks.length) * 100);

        // Update in database
        const { data: updatedPlan, error: updateError } = await supabaseAdmin
          .from('study_plans')
          .update({
            plan_data: dbPlan.plan_data,
            metadata: dbPlan.metadata,
            updated_at: dbPlan.updated_at
          })
          .eq('id', planId)
          .select()
          .single();

        if (updateError) {
          throw updateError;
        }

        // Return in frontend format
        return c.json({
          id: updatedPlan.id,
          userId: updatedPlan.user_id,
          analysisId: updatedPlan.analysis_id,
          status: updatedPlan.status,
          createdAt: updatedPlan.created_at,
          updatedAt: updatedPlan.updated_at,
          startDate: updatedPlan.start_date,
          endDate: updatedPlan.end_date,
          totalDays: updatedPlan.total_days,
          hoursPerDay: updatedPlan.hours_per_day,
          studyDays: updatedPlan.study_days,
          planData: updatedPlan.plan_data,
          metadata: updatedPlan.metadata
        });
      }
    }

    // Fallback to KV store
    const studyPlan = await kv.get(planId);
    
    if (!studyPlan) {
      return c.json({ error: 'Study plan not found' }, 404);
    }

    // Check authorization
    if (userId && studyPlan.userId && studyPlan.userId !== userId && !studyPlan.userId.startsWith('mock_user_')) {
      return c.json({ error: 'Unauthorized' }, 403);
    }

    // Update task completion status
    if (studyPlan.planData.tasks && studyPlan.planData.tasks[taskIndex]) {
      studyPlan.planData.tasks[taskIndex].completed = completed === true;
      studyPlan.updatedAt = new Date().toISOString();
      
      // Update metadata
      const completedTasks = studyPlan.planData.tasks.filter((t: any) => t.completed).length;
      studyPlan.metadata.completedTasks = completedTasks;
      studyPlan.metadata.progress = Math.round((completedTasks / studyPlan.planData.tasks.length) * 100);

      await kv.set(planId, studyPlan);
    }

    return c.json(studyPlan);
    
  } catch (error: any) {
    console.error('Error updating task:', error);
    return c.json({ error: `Failed to update task: ${error.message}` }, 500);
  }
};

app.patch('/server/study-plan/:planId/tasks/:taskIndex/complete', handleUpdateTask);
app.patch('/study-plan/:planId/tasks/:taskIndex/complete', handleUpdateTask); // fallback

// Catch-all logging for unexpected routes
app.all('*', (c) => {
  const path = c.req.path;
  const method = c.req.method;
  console.log(`Unhandled route: ${method} ${path}`);
  return c.json({ error: 'Not Found', path, method }, 404);
});

// Helper function to generate study plan using LLM
async function generateStudyPlanWithLLM(params: {
  analysis: any;
  hoursPerDay: string;
  timeline: number;
  studyDays: string[];
  jobDescription: string;
}): Promise<any> {
  const { analysis, hoursPerDay, timeline, studyDays, jobDescription } = params;
  
  const apiKey = Deno.env.get('OPENAI_API_KEY');
  if (!apiKey) {
    // Fallback to mock data if no API key
    return generateMockStudyPlan(params);
  }

  // Build prompt for study plan generation
  const systemPrompt = `You are an expert career development and learning plan creator. Your task is to create a detailed, day-by-day study plan that helps users learn the skills they need for their target job.

Create a structured study plan with:
1. Daily tasks with specific learning objectives
2. Resources and materials for each task
3. Estimated time for each task
4. XP points for gamification (20-100 XP per task)
5. Phases/themes that group related tasks
6. Realistic progression from basics to advanced topics

The plan should be practical, actionable, and tailored to the user's availability and timeline.`;

  const userPrompt = `Create a ${timeline}-day personalized study plan with the following requirements:

**Target Job:** ${jobDescription.substring(0, 200)}...

**User's Current Skills:**
${analysis.matchingHardSkills?.map((s: string) => `- ${s}`).join('\n') || 'None identified'}

**Skills to Learn (Priority Order):**
${analysis.missingHardSkills?.map((s: string) => `- ${s}`).join('\n') || 'None'}

**Availability:**
- Hours per day: ${hoursPerDay}
- Study days per week: ${studyDays.join(', ')}
- Timeline: ${timeline} days

**Requirements:**
1. Create ${timeline} daily tasks (one per day)
2. Each task should have: date, dayOfWeek, theme, task description, resources, estTime (e.g., "2h"), xp (20-100)
3. Organize tasks into logical phases (e.g., "Foundations", "Intermediate", "Advanced", "Portfolio")
4. Balance learning new concepts with practice and projects
5. Include review/reflection days periodically
6. Make tasks progressively more challenging

Return a JSON object with this structure:
{
  "skills": [{"name": "SQL", "priority": "High", "estimatedTime": "20 hours", "resources": ["Resource 1", "Resource 2"]}],
  "tasks": [{"date": "2024-11-11", "dayOfWeek": "Mon", "theme": "Orientation", "task": "Task description", "resources": "Resource name", "estTime": "1h", "xp": 20, "completed": false}],
  "phases": [{"range": [0, 7], "label": "Foundations", "color": "purple"}],
  "summary": {"totalXP": 650, "totalHours": 70, "currentProgress": 0}
}

Make sure the JSON is valid and properly formatted.`;

  try {
    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify({
        model: 'gpt-4o-mini',
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: userPrompt }
        ],
        max_tokens: 4000,
        temperature: 0.5,
        response_format: { type: 'json_object' }
      })
    });

    if (!response.ok) {
      const error = await response.text();
      console.error('OpenAI API error:', error);
      // Fallback to mock data
      return generateMockStudyPlan(params);
    }

    const data = await response.json();
    const content = data.choices[0].message.content;
    
    // Parse JSON response
    try {
      const studyPlan = JSON.parse(content);
      // Validate and format dates
      if (studyPlan.tasks) {
        const startDate = new Date();
        studyPlan.tasks = studyPlan.tasks.map((task: any, index: number) => {
          const taskDate = new Date(startDate);
          taskDate.setDate(startDate.getDate() + index);
          return {
            ...task,
            date: taskDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
            fullDate: taskDate.toISOString().split('T')[0],
            completed: false
          };
        });
      }
      return studyPlan;
    } catch (parseError) {
      console.error('Error parsing LLM response:', parseError);
      return generateMockStudyPlan(params);
    }
  } catch (error: any) {
    console.error('Error calling OpenAI:', error);
    return generateMockStudyPlan(params);
  }
}

// Fallback mock study plan generator
function generateMockStudyPlan(params: {
  analysis: any;
  hoursPerDay: string;
  timeline: number;
  studyDays: string[];
}): any {
  const { analysis, timeline } = params;
  const startDate = new Date();
  const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  
  const tasks = [];
  const themes = [
    'Orientation',
    'Python Basics',
    'Python Practice',
    'Statistics',
    'SQL Basics',
    'Weekend Challenge',
    'Reflection'
  ];
  
  for (let i = 0; i < timeline; i++) {
    const taskDate = new Date(startDate);
    taskDate.setDate(startDate.getDate() + i);
    const dayOfWeek = days[taskDate.getDay() === 0 ? 6 : taskDate.getDay() - 1];
    const themeIndex = i % themes.length;
    
    tasks.push({
      date: taskDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      fullDate: taskDate.toISOString().split('T')[0],
      dayOfWeek,
      theme: themes[themeIndex],
      task: `${themes[themeIndex]} - Day ${i + 1} learning task`,
      resources: 'SkillMiner Resources',
      estTime: '2h',
      xp: 20 + (themeIndex * 10),
      completed: false
    });
  }
  
  return {
    skills: analysis.missingHardSkills?.map((skill: string) => ({
      name: skill,
      priority: 'High',
      estimatedTime: '20 hours',
      resources: [`Learn ${skill} Online`, `${skill} Tutorial`]
    })) || [],
    tasks,
    phases: [
      { range: [0, Math.floor(timeline * 0.25)], label: 'Foundations', color: 'purple' },
      { range: [Math.floor(timeline * 0.25) + 1, Math.floor(timeline * 0.5)], label: 'Intermediate', color: 'blue' },
      { range: [Math.floor(timeline * 0.5) + 1, Math.floor(timeline * 0.75)], label: 'Advanced', color: 'orange' },
      { range: [Math.floor(timeline * 0.75) + 1, timeline - 1], label: 'Portfolio', color: 'green' }
    ],
    summary: {
      totalXP: tasks.reduce((sum, t) => sum + t.xp, 0),
      totalHours: Math.ceil(timeline * 2),
      currentProgress: 0
    }
  };
}

Deno.serve(app.fetch);
