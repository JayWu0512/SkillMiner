// components/Resume.tsx
import { useRef, useState } from "react";
import { Upload, FileText, Download, Trash2, Check, Clock, Plus } from "lucide-react";
import { Card } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { toast } from "sonner";

type MockupPage =
  | "login" | "upload" | "report" | "dashboard" | "plan"
  | "coding" | "interview" | "profile" | "resume";

interface ResumeVersion {
  id: string;
  name: string;
  uploadDate: string;
  isActive: boolean;
  fileSize: string;
  file?: File;      
  url?: string;       
}

const fmtBytes = (bytes: number) => {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
};

const todayLabel = () =>
  new Date().toLocaleString("en-US", { month: "short", day: "numeric", year: "numeric" });

interface ResumeMockupProps {
  onNavigate?: (page: MockupPage) => void;
}

export function Resume({ onNavigate }: ResumeMockupProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [versions, setVersions] = useState<ResumeVersion[]>([
    {
      id: crypto.randomUUID(),
      name: "Resume_DataAnalyst_v3.pdf",
      uploadDate: "Nov 8, 2024",
      isActive: true,
      fileSize: "124 KB",
    },
    {
      id: crypto.randomUUID(),
      name: "Resume_DataAnalyst_v2.pdf",
      uploadDate: "Nov 1, 2024",
      isActive: false,
      fileSize: "118 KB",
    },
    {
      id: crypto.randomUUID(),
      name: "Resume_Marketing.pdf",
      uploadDate: "Oct 15, 2024",
      isActive: false,
      fileSize: "112 KB",
    },
  ]);

  const active = versions.find(v => v.isActive);

  const handleFiles = (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const f = files[0];

    const okType = /pdf|docx?$/.test(f.name.toLowerCase());
    if (!okType) {
      toast.error("Only PDF or DOCX is allowed.");
      return;
    }
    if (f.size > 5 * 1024 * 1024) {
      toast.error("Max size 5MB.");
      return;
    }

    const url = URL.createObjectURL(f);
    const newItem: ResumeVersion = {
      id: crypto.randomUUID(),
      name: f.name,
      uploadDate: todayLabel(),
      isActive: true, 
      fileSize: fmtBytes(f.size),
      file: f,
      url,
    };

    setVersions(prev => [newItem, ...prev.map(p => ({ ...p, isActive: false }))]);
    toast.success("Resume uploaded (mock).");
  };

  const onChooseFile = () => fileInputRef.current?.click();

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    handleFiles(e.dataTransfer.files);
  };

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const setActive = (id: string) => {
    setVersions(prev => prev.map(v => ({ ...v, isActive: v.id === id })));
    toast.success("Set as Active.");
  };

  const removeOne = (id: string) => {
    setVersions(prev => {
      const target = prev.find(v => v.id === id);
      if (target?.isActive) {
        toast.error("Cannot delete the Active resume.");
        return prev;
      }
      if (target?.url) URL.revokeObjectURL(target.url);
      return prev.filter(v => v.id !== id);
    });
  };

  const downloadOne = (v: ResumeVersion) => {
    const url = v.url ?? URL.createObjectURL(new Blob([`Dummy file: ${v.name}`], { type: "text/plain" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = v.name;
    document.body.appendChild(a);
    a.click();
    a.remove();
    if (!v.url) URL.revokeObjectURL(url);
  };

  const reAnalyze = () => {
    toast.message("Re-analyzing (mock)…", { description: "No real API call made." });
    setTimeout(() => toast.success("Analysis complete (mock)."), 800);
  };

  const downloadActive = () => {
    if (!active) {
      toast.error("No active resume.");
      return;
    }
    downloadOne(active);
  };

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
            <Button className="bg-purple-600 hover:bg-purple-700" onClick={onChooseFile}>
              <Upload className="w-4 h-4 mr-2" />
              Upload New Version
            </Button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.doc,.docx,application/pdf"
              className="hidden"
              onChange={(e) => handleFiles(e.target.files)}
            />
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
                {versions.map((resume) => (
                  <Card key={resume.id} className={`p-5 ${resume.isActive ? "border-2 border-purple-300 bg-purple-50" : ""}`}>
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-4 flex-1">
                        <div className={`p-3 rounded-lg ${resume.isActive ? "bg-purple-100" : "bg-slate-100"}`}>
                          <FileText className={`w-6 h-6 ${resume.isActive ? "text-purple-600" : "text-slate-600"}`} />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <h3 className="text-slate-900 break-all">{resume.name}</h3>
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
                          <Button variant="outline" size="sm" onClick={() => setActive(resume.id)}>
                            Set as Active
                          </Button>
                        )}
                        <Button variant="outline" size="sm" onClick={() => downloadOne(resume)}>
                          <Download className="w-4 h-4" />
                        </Button>
                        {!resume.isActive && (
                          <Button
                            variant="outline"
                            size="sm"
                            className="text-red-600 hover:text-red-700"
                            onClick={() => removeOne(resume.id)}
                          >
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

            {/* Upload New Resume (Dropzone) */}
            <Card className="p-6 bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200">
              <div className="text-center">
                <div className="bg-blue-100 p-4 rounded-full w-16 h-16 mx-auto mb-4 flex items-center justify-center">
                  <Plus className="w-8 h-8 text-blue-600" />
                </div>
                <h3 className="text-slate-900 mb-2">Upload New Resume Version</h3>
                <p className="text-sm text-slate-600 mb-6">
                  PDF or DOCX, max 5MB. This is a mock upload (no API).
                </p>
                <div
                  className="border-2 border-dashed border-blue-300 rounded-lg p-8 bg-white"
                  onClick={onChooseFile}
                  onDrop={onDrop}
                  onDragOver={onDragOver}
                >
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
                    {active?.name ?? "—"}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-slate-600 mb-1">Uploaded</div>
                  <div className="text-slate-900 text-sm">{active?.uploadDate ?? "—"}</div>
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

              <div className="grid grid-cols-2 gap-2 mt-4">
                <Button className="bg-purple-600 hover:bg-purple-700" onClick={downloadActive}>
                  Download Active
                </Button>
                <Button variant="outline" onClick={reAnalyze}>
                  Re-analyze
                </Button>
              </div>
            </Card>

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

            <Card className="p-6">
              <h3 className="text-slate-900 mb-4">Quick Actions</h3>
              <div className="space-y-2">
                <Button variant="outline" className="w-full justify-start" onClick={downloadActive}>
                  <FileText className="w-4 h-4 mr-2" />
                  Download Active Resume
                </Button>
                <Button variant="outline" className="w-full justify-start" onClick={reAnalyze}>
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
