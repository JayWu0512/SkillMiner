/// <reference types="vite/client" />

/**
 * API Service for SkillMiner Backend
 * Handles all communication with the FastAPI backend
 */

export const API_BASE =
  (import.meta.env.VITE_API_URL ?? "http://localhost:8000").trim();

// Types for API responses
export interface UploadResponse {
  text: string;
  status: string;
  message: string;
}

export interface ChatRequest {
  message: string;
  resume_text?: string;
}

export interface ChatResponse {
  reply: string;
  citations: string[];
}

export interface HealthResponse {
  status: string;
}

/**
 * Build headers for API requests
 */
function buildHeaders(accessToken?: string, json = false): Record<string, string> {
  const headers: Record<string, string> = {};
  
  if (json) {
    headers["Content-Type"] = "application/json";
  }
  
  if (accessToken && accessToken !== "dev-local-token") {
    headers["Authorization"] = `Bearer ${accessToken}`;
  }
  
  return headers;
}

/**
 * Check if backend is healthy and accessible
 */
export async function checkHealth(): Promise<HealthResponse> {
  const url = `${API_BASE}/health`;
  console.log('[API] Health check URL:', url);
  console.log('[API] API_BASE value:', API_BASE);
  console.log('[API] Current origin:', window.location.origin);
  
  try {
    const response = await fetch(url, {
      method: "GET",
      mode: "cors",
      credentials: "omit", // Changed from "include" to avoid CORS issues
    });

    console.log('[API] Health check response status:', response.status);
    console.log('[API] Health check response headers:', Object.fromEntries(response.headers.entries()));

    if (!response.ok) {
      const errorText = await response.text().catch(() => 'No error details');
      throw new Error(`Health check failed: ${response.status} ${response.statusText}. Details: ${errorText}`);
    }

    const data = await response.json();
    console.log('[API] Health check success:', data);
    return data;
  } catch (error: any) {
    console.error('[API] Health check error:', error);
    console.error('[API] Error type:', error?.constructor?.name);
    console.error('[API] Error name:', error?.name);
    console.error('[API] Error message:', error?.message);
    console.error('[API] API_BASE:', API_BASE);
    console.error('[API] Full URL:', url);
    
    // Provide more helpful error message
    if (error?.message?.includes('Failed to fetch') || error?.name === 'TypeError') {
      throw new Error(`Network error: Cannot connect to ${url}. Make sure the backend is running on port 8000.`);
    }
    throw error;
  }
}

/**
 * Upload a resume file (PDF)
 * @param file - The PDF file to upload
 * @param accessToken - Optional authentication token
 * @returns The extracted text from the resume
 */
export async function uploadResume(
  file: File,
  accessToken?: string
): Promise<UploadResponse> {
  // Validate file type
  if (file.type !== "application/pdf" && !file.name.endsWith(".pdf")) {
    throw new Error("Only PDF files are supported");
  }

  // Validate file size (10MB limit)
  const maxSize = 10 * 1024 * 1024; // 10MB
  if (file.size > maxSize) {
    throw new Error("File size exceeds 10MB limit");
  }

  // Create FormData
  const formData = new FormData();
  formData.append("file", file);

  // Build headers (don't set Content-Type for FormData - browser will set it with boundary)
  const headers = buildHeaders(accessToken, false);

  // Make request
  const url = `${API_BASE}/upload`;
  console.log('[API] Upload URL:', url);
  console.log('[API] File:', file.name, 'Size:', file.size, 'Type:', file.type);
  
  const response = await fetch(url, {
    method: "POST",
    headers: headers,
    credentials: "omit", // Changed from "include" to avoid CORS issues
    mode: "cors",
    body: formData,
  });

  // Handle errors
  if (!response.ok) {
    let errorMessage = `Upload failed with status ${response.status}`;
    
    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorData.message || errorMessage;
    } catch {
      // If response is not JSON, use status text
      errorMessage = response.statusText || errorMessage;
    }
    
    throw new Error(errorMessage);
  }

  // Parse response
  const data = await response.json() as UploadResponse;
  
  // Validate response
  if (!data.text) {
    throw new Error("Resume text not returned from server");
  }

  return data;
}

/**
 * Send a chat message with RAG
 * @param message - The user's message
 * @param resumeText - Optional resume text for context
 * @param accessToken - Optional authentication token
 * @returns The AI response with citations
 */
export async function sendChatMessage(
  message: string,
  resumeText?: string,
  accessToken?: string
): Promise<ChatResponse> {
  // Validate message
  if (!message || !message.trim()) {
    throw new Error("Message cannot be empty");
  }

  // Build request body
  const body: ChatRequest = {
    message: message.trim(),
    resume_text: resumeText || undefined,
  };

  // Build headers
  const headers = buildHeaders(accessToken, true);

  // Make request
  const url = `${API_BASE}/chat`;
  console.log('[API] Chat URL:', url);
  
  const response = await fetch(url, {
    method: "POST",
    headers: headers,
    credentials: "omit", // Changed from "include" to avoid CORS issues
    mode: "cors",
    body: JSON.stringify(body),
  });

  // Handle errors
  if (!response.ok) {
    let errorMessage = `Chat request failed with status ${response.status}`;
    
    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorData.message || errorMessage;
    } catch {
      errorMessage = response.statusText || errorMessage;
    }
    
    throw new Error(errorMessage);
  }

  // Parse response
  const data = await response.json() as ChatResponse;
  
  // Validate response
  if (!data.reply) {
    throw new Error("Reply not returned from server");
  }

  return data;
}

/**
 * Get API base URL
 */
export function getApiBase(): string {
  return API_BASE;
}

