import {
  projectId,
  edgeFunctionName,
  publicAnonKey,
} from '../utils/supabase/info';

import { API_BASE } from "./api";

export interface DailyTask {
  date: string;
  fullDate?: string;
  dayOfWeek: string;
  theme: string;
  task: string;
  resources: string;
  estTime: string;
  xp: number;
  completed?: boolean;
  isRestDay?: boolean;
}

export interface StudyPlanPhase {
  range: [number, number];
  label: string;
  color: string;
}

export interface StudyPlanSummary {
  totalXP: number;
  totalHours: number;
  currentProgress: number;
}

export interface StudyPlanData {
  skills: Array<{
    name: string;
    priority: string;
    estimatedTime: string;
    resources: string[];
  }>;
  tasks: DailyTask[];
  phases: StudyPlanPhase[];
  summary: StudyPlanSummary;
}

export interface StudyPlan {
  id: string;
  userId: string;
  analysisId: string;
  status: string;
  createdAt: string;
  updatedAt: string;
  startDate: string;
  endDate: string;
  totalDays: number;
  hoursPerDay: string;
  studyDays: string[];
  planData: StudyPlanData;
  metadata: {
    progress: number;
    totalXP: number;
    completedTasks: number;
  };
}

export interface GenerateStudyPlanRequest {
  analysisId: string;
  hoursPerDay: string;
  timeline: string;
  studyDays: string[];
  jobDescription?: string;
}

/**
 * Generate a new study plan
 */
export async function generateStudyPlan(
  accessToken: string | null,
  request: GenerateStudyPlanRequest
): Promise<StudyPlan> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    apikey: publicAnonKey,
  };

  // Add authorization header if token is provided
  if (accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`;
  } else {
    headers['Authorization'] = `Bearer ${publicAnonKey}`;
  }

  const response = await fetch(
    `https://${projectId}.supabase.co/functions/v1/${edgeFunctionName}/study-plan/generate`,
    {
      method: 'POST',
      headers,
      body: JSON.stringify(request),
    }
  );

  if (!response.ok) {
    const errorText = await response.text();
    let errorMessage = `Failed to generate study plan: ${errorText}`;
    try {
      const errorJson = JSON.parse(errorText);
      errorMessage = errorJson.error || errorMessage;
      if (errorJson.details) {
        errorMessage += ` - ${JSON.stringify(errorJson.details)}`;
      }
    } catch {
      // If not JSON, use the text as is
    }
    throw new Error(errorMessage);
  }

  return response.json();
}

/**
 * Get a study plan by ID
 */
export async function getStudyPlan(
  accessToken: string | null,
  planId: string
): Promise<StudyPlan> {
  const headers: Record<string, string> = {
    apikey: publicAnonKey,
  };

  // Add authorization header if token is provided
  if (accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`;
  } else {
    headers['Authorization'] = `Bearer ${publicAnonKey}`;
  }

  const response = await fetch(
    `https://${projectId}.supabase.co/functions/v1/${edgeFunctionName}/study-plan/${planId}`,
    {
      method: 'GET',
      headers,
    }
  );

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to fetch study plan: ${error}`);
  }

  return response.json();
}

/**
 * Update task completion status
 */
export async function updateTaskCompletion(
  accessToken: string | null,
  planId: string,
  taskIndex: number,
  completed: boolean
): Promise<StudyPlan> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    apikey: publicAnonKey,
  };

  // Add authorization header if token is provided
  if (accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`;
  } else {
    headers['Authorization'] = `Bearer ${publicAnonKey}`;
  }

  const response = await fetch(
    `https://${projectId}.supabase.co/functions/v1/${edgeFunctionName}/study-plan/${planId}/tasks/${taskIndex}/complete`,
    {
      method: 'PATCH',
      headers,
      body: JSON.stringify({ completed }),
    }
  );

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to update task: ${error}`);
  }

  return response.json();
}

export interface UpdateStudyPlanRequest {
  userId: string;
  action: 'reduce_hours' | 'increase_hours' | 'extend_timeline' | 'shorten_timeline' | 'add_rest_days' | 'reduce_rest_days';
  params: {
    hoursPerDay?: string;
    totalDays?: number;
    additionalDays?: number;
    reduceDays?: number;
    studyDays?: string[];
  };
}

export interface UpdateStudyPlanResponse {
  success: boolean;
  message: string;
  planId: string;
}

/**
 * Update a study plan based on user feedback
 */
export async function updateStudyPlan(
  accessToken: string | null,
  request: UpdateStudyPlanRequest
): Promise<UpdateStudyPlanResponse> {
  // const API_BASE = (import.meta as any).env?.VITE_API_BASE || "http://localhost:8000";
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`;
  }

  const response = await fetch(
    `${API_BASE}/study-plan/update`,
    {
      method: 'POST',
      headers,
      body: JSON.stringify({
        user_id: request.userId,
        action: request.action,
        params: request.params,
      }),
    }
  );

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to update study plan: ${error}`);
  }

  return response.json();
}

