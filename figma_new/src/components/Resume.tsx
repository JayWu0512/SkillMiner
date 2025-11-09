import { Upload, FileText, Download, Trash2, Check, Clock, Plus } from 'lucide-react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';

interface ResumeVersion {
  id: string;
  name: string;
  uploadDate: string;
  isActive: boolean;
  fileSize: string;
}

const resumeVersions: ResumeVersion[] = [
  { id: '3', name: 'Resume_DataAnalyst_v3.pdf', uploadDate: 'Nov 8, 2024', isActive: true, fileSize: '124 KB' },
  { id: '2', name: 'Resume_DataAnalyst_v2.pdf', uploadDate: 'Nov 1, 2024', isActive: false, fileSize: '118 KB' },
  { id: '1', name: 'Resume_Marketing.pdf', uploadDate: 'Oct 15, 2024', isActive: false, fileSize: '112 KB' },
];

type MockupPage = "login" | "upload" | "report" | "dashboard" | "plan" | "coding" | "interview" | "profile" | "resume";

interface ResumeMockupProps {
  onNavigate?: (page: MockupPage) => void;
}

export function ResumeMockup({ onNavigate }: ResumeMockupProps) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-6">
        <div className="container mx-auto">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl text-slate-900 mb-2">Resume Management</h1>
              <p className="text-slate-600">Manage and track different versions of your resume</p>
            </div>
            <Button className="bg-purple-600 hover:bg-purple-700">
              <Upload className="w-4 h-4 mr-2" />
              Upload New Version
            </Button>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-6 py-8">
        <div className="grid grid-cols-12 gap-6">
          {/* Main Content - Resume Versions */}
          <div className="col-span-8">
            <Card className="p-6 mb-6">
              <h2 className="text-xl text-slate-900 mb-4">Resume Versions</h2>
              <p className="text-slate-600 mb-6">
                Keep track of different versions of your resume. The active resume is used for skill analysis and job matching.
              </p>

              <div className="space-y-3">
                {resumeVersions.map((resume) => (
                  <Card key={resume.id} className={`p-5 ${resume.isActive ? 'border-2 border-purple-300 bg-purple-50' : ''}`}>
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-4 flex-1">
                        <div className={`p-3 rounded-lg ${resume.isActive ? 'bg-purple-100' : 'bg-slate-100'}`}>
                          <FileText className={`w-6 h-6 ${resume.isActive ? 'text-purple-600' : 'text-slate-600'}`} />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <h3 className="text-slate-900">{resume.name}</h3>
                            {resume.isActive && (
                              <Badge className="bg-purple-600">
                                <Check className="w-3 h-3 mr-1" />
                                Active
                              </Badge>
                            )}
                          </div>
                          <div className="flex items-center gap-4 text-sm text-slate-600">
                            <span className="flex items-center gap-1">
                              <Clock className="w-4 h-4" />
                              {resume.uploadDate}
                            </span>
                            <span>•</span>
                            <span>{resume.fileSize}</span>
                          </div>
                        </div>
                      </div>

                      <div className="flex gap-2">
                        {!resume.isActive && (
                          <Button variant="outline" size="sm">
                            Set as Active
                          </Button>
                        )}
                        <Button variant="outline" size="sm">
                          <Download className="w-4 h-4" />
                        </Button>
                        {!resume.isActive && (
                          <Button variant="outline" size="sm" className="text-red-600 hover:text-red-700">
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        )}
                      </div>
                    </div>

                    {resume.isActive && (
                      <div className="mt-4 pt-4 border-t border-purple-200">
                        <div className="grid grid-cols-3 gap-4 text-sm">
                          <div>
                            <div className="text-slate-600 mb-1">Skills Extracted</div>
                            <div className="text-slate-900">12 skills</div>
                          </div>
                          <div>
                            <div className="text-slate-600 mb-1">Match Score</div>
                            <div className="text-purple-600">68%</div>
                          </div>
                          <div>
                            <div className="text-slate-600 mb-1">Last Analysis</div>
                            <div className="text-slate-900">Today</div>
                          </div>
                        </div>
                      </div>
                    )}
                  </Card>
                ))}
              </div>
            </Card>

            {/* Upload New Resume */}
            <Card className="p-6 bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200">
              <div className="text-center">
                <div className="bg-blue-100 p-4 rounded-full w-16 h-16 mx-auto mb-4 flex items-center justify-center">
                  <Plus className="w-8 h-8 text-blue-600" />
                </div>
                <h3 className="text-slate-900 mb-2">Upload New Resume Version</h3>
                <p className="text-sm text-slate-600 mb-6">
                  PDF or DOCX format, max 5MB. We'll analyze it automatically and update your skill profile.
                </p>
                <div className="border-2 border-dashed border-blue-300 rounded-lg p-8 bg-white">
                  <Button className="bg-blue-600 hover:bg-blue-700">
                    <Upload className="w-4 h-4 mr-2" />
                    Choose File
                  </Button>
                  <p className="text-xs text-slate-500 mt-3">or drag and drop here</p>
                </div>
              </div>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="col-span-4">
            {/* Active Resume Info */}
            <Card className="p-6 mb-6 bg-gradient-to-br from-purple-50 to-indigo-50 border-purple-200">
              <div className="flex items-center gap-3 mb-4">
                <div className="bg-purple-100 p-3 rounded-xl">
                  <FileText className="w-6 h-6 text-purple-600" />
                </div>
                <h3 className="text-slate-900">Active Resume</h3>
              </div>

              <div className="space-y-3">
                <div>
                  <div className="text-sm text-slate-600 mb-1">File Name</div>
                  <div className="text-slate-900 text-sm break-words">
                    Resume_DataAnalyst_v3.pdf
                  </div>
                </div>
                <div>
                  <div className="text-sm text-slate-600 mb-1">Uploaded</div>
                  <div className="text-slate-900 text-sm">Nov 8, 2024</div>
                </div>
                <div>
                  <div className="text-sm text-slate-600 mb-1">Skills Found</div>
                  <div className="flex flex-wrap gap-1 mt-2">
                    <Badge variant="outline" className="text-xs">Python</Badge>
                    <Badge variant="outline" className="text-xs">SQL</Badge>
                    <Badge variant="outline" className="text-xs">Excel</Badge>
                    <Badge variant="outline" className="text-xs">+9 more</Badge>
                  </div>
                </div>
              </div>

              <Button className="w-full mt-4 bg-purple-600 hover:bg-purple-700">
                View Full Analysis
              </Button>
            </Card>

            {/* Tips */}
            <Card className="p-6 mb-6 bg-gradient-to-br from-yellow-50 to-orange-50 border-yellow-200">
              <h3 className="text-slate-900 mb-3">Resume Tips</h3>
              <ul className="space-y-2 text-sm text-slate-700">
                <li>✓ Keep your resume updated with latest projects</li>
                <li>✓ Include quantifiable achievements</li>
                <li>✓ Use industry-standard skill names</li>
                <li>✓ Tailor your resume for target roles</li>
                <li>✓ Upload new versions as you learn</li>
              </ul>
            </Card>

            {/* Quick Actions */}
            <Card className="p-6">
              <h3 className="text-slate-900 mb-4">Quick Actions</h3>
              <div className="space-y-2">
                <Button variant="outline" className="w-full justify-start">
                  <FileText className="w-4 h-4 mr-2" />
                  Download Active Resume
                </Button>
                <Button variant="outline" className="w-full justify-start">
                  <Upload className="w-4 h-4 mr-2" />
                  Re-analyze Resume
                </Button>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
