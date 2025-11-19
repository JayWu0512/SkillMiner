import { useState, useEffect } from 'react';
import { Button } from '../ui/button';
import { Textarea } from '../ui/textarea';
import { Card } from '../ui/card';
import { uploadResume, checkHealth, getApiBase } from '../../services/api';
import { Upload, FileText, Sparkles, LogOut, Loader2 } from 'lucide-react';
import { SkillMinerLogo } from '../SkillMinerLogo';

interface UploadPageMockupProps {
  onAnalysisComplete?: () => void;
}

export function UploadPageMockup({ onAnalysisComplete }: UploadPageMockupProps) {
  const [jobDescription, setJobDescription] = useState('');
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState('');
  const [backendStatus, setBackendStatus] = useState<'checking' | 'connected' | 'disconnected'>('checking');

  // Test backend connection on component mount
  useEffect(() => {
    const testConnection = async () => {
      const apiBase = getApiBase();
      console.log('[UploadPage] API_BASE from getApiBase():', apiBase);
      console.log('[UploadPage] VITE_API_BASE from env:', import.meta.env.VITE_API_BASE);
      
      if (!apiBase || apiBase === 'undefined' || apiBase === '') {
        console.warn('⚠️ API_BASE not configured');
        setBackendStatus('disconnected');
        return;
      }
      
      try {
        console.log('[UploadPage] Testing backend connection to:', `${apiBase}/health`);
        const result = await checkHealth();
        console.log('[UploadPage] ✅ Backend connection test passed:', result);
        setBackendStatus('connected');
      } catch (err: any) {
        console.error('[UploadPage] ❌ Backend connection test failed:', err);
        console.error('[UploadPage] Error details:', {
          name: err?.name,
          message: err?.message,
          stack: err?.stack,
        });
        setBackendStatus('disconnected');
      }
    };
    
    testConnection();
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Backend only supports PDF files
    if (file.type === 'application/pdf' || file.name.endsWith('.pdf')) {
      setResumeFile(file);
      setError('');
    } else {
      setError('Please upload a PDF file (backend only supports PDF format)');
      setResumeFile(null);
    }
  };

  const handleAnalyze = async () => {
    if (!resumeFile) {
      setError('Please upload your resume');
      return;
    }

    setIsUploading(true);
    setError(''); // Clear any previous errors

    try {
      const apiBase = getApiBase();
      if (!apiBase || apiBase === 'undefined' || apiBase === '') {
        throw new Error('API base URL is not configured. Please check your .env file and restart the dev server.');
      }

      // Re-check backend connection before upload
      try {
        await checkHealth();
        setBackendStatus('connected');
      } catch (healthErr) {
        console.warn('Backend health check failed before upload:', healthErr);
        setBackendStatus('disconnected');
        throw new Error('Backend is not responding. Please ensure the backend is running on http://localhost:8000');
      }

      console.log('=== Upload Debug Info ===');
      console.log('API_BASE:', apiBase);
      console.log('File:', resumeFile.name, 'Type:', resumeFile.type, 'Size:', resumeFile.size);

      // Upload resume to backend
      const data = await uploadResume(resumeFile);
      
      console.log('✅ Upload successful! Text length:', data.text.length);
      console.log('Status:', data.status);
      console.log('Message:', data.message);
      
      // Clear any errors on success
      setError('');
      
      // Store resume text in localStorage for chatbot access
      localStorage.setItem('resumeText', data.text);
      if (jobDescription.trim()) {
        localStorage.setItem('jobDescription', jobDescription);
      }
      
      // Dispatch custom event to notify other components
      window.dispatchEvent(new Event('resumeTextUpdated'));
      
      // Call completion callback
      if (onAnalysisComplete) {
        onAnalysisComplete();
      }
    } catch (err: any) {
      console.error('=== Upload Error Details ===');
      console.error('Error:', err);
      console.error('Error name:', err?.name);
      console.error('Error message:', err?.message);
      
      const isNetworkError = 
        err?.name === 'TypeError' || 
        err?.name === 'NetworkError' ||
        err?.message?.includes('fetch') || 
        err?.message?.includes('Failed to fetch') ||
        err?.message?.includes('Backend is not responding');
      
      if (isNetworkError) {
        const apiBase = getApiBase();
        setBackendStatus('disconnected');
        setError(`Cannot connect to backend at ${apiBase || 'http://localhost:8000'}. Please ensure the backend is running.`);
      } else {
        setError(err?.message || 'Failed to upload resume. Please try again.');
      }
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-purple-50">
      {/* Simple Header with Logo and Logout */}
      <header className="bg-white border-b border-slate-200 px-6 py-4">
        <div className="container mx-auto flex items-center justify-between">
          <SkillMinerLogo />
          <Button variant="outline" className="gap-2">
            <LogOut className="w-4 h-4" />
            Logout
          </Button>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8 max-w-4xl">

        <div className="bg-white rounded-2xl shadow-lg border border-slate-200 p-8 mb-6">
          <div className="flex items-center gap-3 mb-6">
            <Sparkles className="w-6 h-6 text-purple-500" />
            <h2 className="text-slate-900 text-xl">Start Your Analysis</h2>
          </div>
          
          <p className="text-slate-600 mb-8">
            Upload your resume and paste the job description to get personalized skill gap analysis and recommendations.
          </p>

          {/* Backend connection status - only show if no error */}
          {!error && (
            <>
              {backendStatus === 'checking' && (
                <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg mb-4">
                  <p className="text-blue-600 text-sm">Checking backend connection...</p>
                </div>
              )}
              {backendStatus === 'connected' && (
                <div className="p-3 bg-green-50 border border-green-200 rounded-lg mb-4">
                  <p className="text-green-600 text-sm">✅ Backend connected</p>
                </div>
              )}
              {backendStatus === 'disconnected' && (
                <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg mb-4">
                  <p className="text-yellow-600 text-sm">⚠️ Backend connection issue. Check console (F12) for details.</p>
                </div>
              )}
            </>
          )}

          {/* Error message - takes priority over status */}
          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg mb-4">
              <p className="text-red-600 font-medium">{error}</p>
              {error.includes('Cannot connect') && (
                <p className="text-red-500 text-sm mt-2">
                  Troubleshooting: Check that the backend is running with: <code className="bg-red-100 px-2 py-1 rounded">cd backend && uvicorn src.api.main:app --reload --port 8000</code>
                </p>
              )}
            </div>
          )}

          <div className="space-y-6">
            <div>
              <label className="block text-slate-700 mb-2">
                Job Description *
              </label>
              <Textarea
                placeholder="Paste the job description here..."
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                className="min-h-[200px] resize-none"
              />
            </div>

            <div>
              <label className="block text-slate-700 mb-2">
                Resume (PDF) *
              </label>
              <div className="relative">
                <input
                  type="file"
                  id="resume-upload"
                  accept=".pdf"
                  onChange={handleFileChange}
                  className="hidden"
                />
                <label
                  htmlFor="resume-upload"
                  className="flex items-center justify-center gap-3 border-2 border-dashed border-slate-300 hover:border-purple-400 rounded-xl p-8 cursor-pointer transition-colors bg-slate-50 hover:bg-purple-50"
                >
                  {resumeFile ? (
                    <>
                      <FileText className="w-6 h-6 text-purple-500" />
                      <span className="text-slate-700">{resumeFile.name}</span>
                    </>
                  ) : (
                    <>
                      <Upload className="w-6 h-6 text-slate-400" />
                      <span className="text-slate-600">Click to upload your resume</span>
                    </>
                  )}
                </label>
              </div>
            </div>

            <Button
              disabled={!resumeFile || isUploading}
              className="w-full h-12 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white rounded-xl"
              onClick={handleAnalyze}
            >
              {isUploading ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  Uploading...
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5 mr-2" />
                  Analyze My Skills
                </>
              )}
            </Button>
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-4">
          <Card className="p-4 bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
            <div className="text-purple-600 mb-2">📊</div>
            <h3 className="text-slate-900 mb-1">Skill Matching</h3>
            <p className="text-slate-600 text-sm">Compare your skills against job requirements</p>
          </Card>
          <Card className="p-4 bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
            <div className="text-blue-600 mb-2">🎯</div>
            <h3 className="text-slate-900 mb-1">Gap Analysis</h3>
            <p className="text-slate-600 text-sm">Identify missing skills and knowledge areas</p>
          </Card>
          <Card className="p-4 bg-gradient-to-br from-pink-50 to-pink-100 border-pink-200">
            <div className="text-pink-600 mb-2">📚</div>
            <h3 className="text-slate-900 mb-1">Learning Path</h3>
            <p className="text-slate-600 text-sm">Get personalized resources and timelines</p>
          </Card>
        </div>
      </div>
    </div>
  );
}
