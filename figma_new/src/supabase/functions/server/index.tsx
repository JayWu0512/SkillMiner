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
app.post('/analyze', async (c) => {
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
app.get('/analysis/:analysisId', async (c) => {
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
app.post('/chat', async (c) => {
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

    // Check if LLM API key is configured
    const llmApiKey = Deno.env.get('OPENAI_API_KEY') || Deno.env.get('ANTHROPIC_API_KEY');
    
    let response = '';
    
    if (llmApiKey && Deno.env.get('OPENAI_API_KEY')) {
      // Use OpenAI API
      response = await callOpenAI(message, messages || [], analysis);
    } else if (llmApiKey && Deno.env.get('ANTHROPIC_API_KEY')) {
      // Use Anthropic Claude API
      response = await callAnthropic(message, messages || [], analysis);
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

// Helper function to call Anthropic Claude API
async function callAnthropic(userMessage: string, conversationHistory: any[], analysis: any): Promise<string> {
  const apiKey = Deno.env.get('ANTHROPIC_API_KEY');
  
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

  // Build messages array (Claude format)
  const messages = conversationHistory.map((msg: any) => ({
    role: msg.role === 'assistant' ? 'assistant' : 'user',
    content: msg.content
  }));
  
  messages.push({ role: 'user', content: userMessage });

  try {
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01'
      },
      body: JSON.stringify({
        model: 'claude-3-haiku-20240307', // Cost-effective model
        max_tokens: 500,
        system: systemPrompt,
        messages: messages
      })
    });

    if (!response.ok) {
      const error = await response.text();
      console.error('Anthropic API error:', error);
      throw new Error(`Anthropic API error: ${response.status}`);
    }

    const data = await response.json();
    return data.content[0].text;
  } catch (error: any) {
    console.error('Error calling Anthropic:', error);
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
app.get('/report/:analysisId', async (c) => {
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

Deno.serve(app.fetch);
