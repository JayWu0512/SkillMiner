import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
import { Card } from './ui/card';
import { Brain, Upload, FileText, Sparkles, LogOut } from 'lucide-react';
import { createClient } from '../utils/supabase/client'; 
import { projectId, publicAnonKey, edgeFunctionName } from '../utils/supabase/info';

interface UploadPageProps {
  accessToken: string;
  onAnalysisComplete: (analysisId: string) => void;
  onLogout: () => void;
}

export function UploadPage({ accessToken, onAnalysisComplete, onLogout }: UploadPageProps) {
  const [userId, setUserId] = useState<string>('');
  const [jobDescription, setJobDescription] = useState('');
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate(); 

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const supabase = createClient();
        const { data: { session } } = await supabase.auth.getSession();
        if (session?.user?.id) {
          setUserId(session.user.id);
          console.log('[UploadPage] user_id loaded:', session.user.id);
        } else {
          console.warn('[UploadPage] No active Supabase session');
        }
      } catch (err) {
        console.error('[UploadPage] Error fetching user:', err);
      }
    };
    fetchUser();
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const isPdf = file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf');
      if (isPdf) {
        setResumeFile(file);
        setError('');
      } else {
        setError('Only PDF files are supported.');
        setResumeFile(null);
      }
    }
  };

  const handleAnalyze = async () => {
    if (!jobDescription.trim()) {
      setError('Please enter a job description');
      return;
    }
    if (!resumeFile) {
      setError('Please upload your resume (PDF)');
      return;
    }
    if (!userId?.trim()) {
      setError('Missing user id (please log in again)');
      return;
    }

    setIsAnalyzing(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('file', resumeFile);
      formData.append('job_description', jobDescription);
      formData.append('user_id', userId);

      const response = await fetch(`http://localhost:8000/analysis`, {
        method: 'POST',
        // headers: { Authorization: `Bearer ${accessToken}` }, // optional
        body: formData,
      });

      if (!response.ok) {
        let message = 'Analysis failed';
        const text = await response.text();
        try {
          const err = JSON.parse(text);
          message = err?.detail || message;
        } catch {
          message = text || message;
        }
        throw new Error(message);
      }

      const result: { analysis_id: string; user_id: string; match_score: number } = await response.json();
      onAnalysisComplete(result.analysis_id);

      navigate('/SkillReportMockup');
    } catch (err: any) {
      console.error('Analysis error:', err);
      setError(err.message || 'Failed to analyze. Please try again.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-purple-50">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <div className="bg-gradient-to-br from-purple-500 to-pink-500 p-2 rounded-xl">
              <Brain className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-slate-900 text-2xl">SkillMiner</h1>
              <p className="text-slate-600 text-sm">AI-Powered Career Analysis</p>
            </div>
          </div>
          <Button variant="outline" onClick={onLogout} className="gap-2">
            <LogOut className="w-4 h-4" />
            Logout
          </Button>
        </div>

        <div className="bg-white rounded-2xl shadow-lg border border-slate-200 p-8 mb-6">
          <div className="flex items-center gap-3 mb-6">
            <Sparkles className="w-6 h-6 text-purple-500" />
            <h2 className="text-slate-900 text-xl">Start Your Analysis</h2>
          </div>

          <p className="text-slate-600 mb-8">
            Upload your resume and paste the job description to get personalized skill gap analysis and recommendations.
          </p>

          <div className="space-y-6">
            <div>
              <label className="block text-slate-700 mb-2">Job Description *</label>
              <Textarea
                placeholder="Paste the job description here..."
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                className="min-h-[200px] resize-none"
              />
            </div>

            <div>
              <label className="block text-slate-700 mb-2">Resume (PDF only) *</label>
              <div className="relative">
                <input
                  type="file"
                  id="resume-upload"
                  accept=".pdf,application/pdf"
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
                      <span className="text-slate-600">Click to upload your resume (PDF)</span>
                    </>
                  )}
                </label>
              </div>
            </div>

            {error && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-red-600">{error}</p>
              </div>
            )}

            <Button
              onClick={handleAnalyze}
              disabled={isAnalyzing || !jobDescription.trim() || !resumeFile}
              className="w-full h-12 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white rounded-xl"
            >
              {isAnalyzing ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                  Analyzing...
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
