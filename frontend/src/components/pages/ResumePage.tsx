// components/Resume.tsx
import { useEffect, useState } from "react";
import { FileText, Clock } from "lucide-react";
import { Card } from "../ui/card";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { toast } from "sonner";
import { createClient } from "../../utils/supabase/client";

type Page =
  | "login"
  | "upload"
  | "report"
  | "dashboard"
  | "plan"
  | "coding"
  | "interview"
  | "profile"
  | "resume";

interface ResumeVersion {
  id: string;
  name: string;
  uploadDate: string;
  isActive: boolean;
  fileSize: string;
  matchScore?: number | null;
  skillsExtracted?: number | null;
  createdAt?: string;
  matchedTechnical?: string[];
  matchedSoft?: string[];
}

const formatUploadDate = (d: Date) =>
  d.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });

const formatResumeName = (d: Date) => {
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  const hh = String(d.getHours()).padStart(2, "0");
  const mi = String(d.getMinutes()).padStart(2, "0");
  return `Resume_${yyyy}-${mm}-${dd}_${hh}-${mi}`;
};

const formatMatchScore = (score: number | null | undefined): string => {
  if (score == null) return "—";
  const val = score <= 1 ? Math.round(score * 100) : Math.round(score);
  return `${val}%`;
};

const isSameDay = (a: Date, b: Date) =>
  a.getFullYear() === b.getFullYear() &&
  a.getMonth() === b.getMonth() &&
  a.getDate() === b.getDate();

interface ResumeProps {
  onNavigate?: (page: Page) => void;
}

export function Resume({ onNavigate }: ResumeProps) {
  const [versions, setVersions] = useState<ResumeVersion[]>([]);
  const [loading, setLoading] = useState(false);

  // 1) Fetch the latest three entries for the current user in skill_analyses
  useEffect(() => {
    const fetchLatestAnalyses = async () => {
      try {
        setLoading(true);
        const supabase = createClient();

        const {
          data: { user },
          error: userError,
        } = await supabase.auth.getUser();

        if (userError) {
          console.warn("[Resume] auth.getUser error:", userError);
          return;
        }
        if (!user) {
          console.warn("[Resume] No auth user, cannot load skill_analyses");
          return;
        }

        const { data, error } = await supabase
          .from("skill_analyses")
          .select(
            "id, created_at, match_score, matched_skills_technical, matched_skills_soft"
          )
          .eq("user_id", user.id)
          .order("created_at", { ascending: false })
          .limit(3);

        if (error) {
          console.warn("[Resume] Failed to load skill_analyses:", error);
          toast.error("Failed to load resume analyses.");
          return;
        }

        const mapped: ResumeVersion[] =
          data?.map((row: any, idx: number) => {
            const created = row.created_at
              ? new Date(row.created_at)
              : new Date();

            const technical: string[] =
              (row.matched_skills_technical as string[] | null) ?? [];
            const soft: string[] =
              (row.matched_skills_soft as string[] | null) ?? [];

            const skillsCount = technical.length + soft.length;

            return {
              id: row.id,
              name: formatResumeName(created),
              uploadDate: formatUploadDate(created),
              isActive: idx === 0,
              fileSize: "—",
              matchScore: row.match_score ?? null,
              skillsExtracted: skillsCount,
              createdAt: row.created_at,
              matchedTechnical: technical,
              matchedSoft: soft,
            };
          }) ?? [];

        setVersions(mapped);
      } catch (err) {
        console.warn("[Resume] fetchLatestAnalyses error:", err);
        toast.error("Unexpected error while loading resumes.");
      } finally {
        setLoading(false);
      }
    };

    void fetchLatestAnalyses();
  }, []);

  const active = versions.find((v) => v.isActive);

  // Re-analyze → navigate to upload page
  const reAnalyze = () => {
    onNavigate?.("upload");
  };

  const activeMatchScore = formatMatchScore(active?.matchScore);
  const activeSkills = active?.skillsExtracted ?? "—";

  const lastAnalysisLabel = (() => {
    if (!active?.createdAt) return active?.uploadDate ?? "—";
    const created = new Date(active.createdAt);
    const today = new Date();
    return isSameDay(created, today) ? "Today" : formatUploadDate(created);
  })();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-6">
        <div className="container mx-auto">
          <h1 className="text-3xl text-slate-900 mb-2">Resume Management</h1>
          <p className="text-slate-600">
            Review your resume-based skill analyses
          </p>
        </div>
      </header>

      <div className="container mx-auto px-6 py-8">
        <div className="grid grid-cols-12 gap-6">
          {/* Left: list of resume analyses */}
          <div className="col-span-8">
            <Card className="p-6 mb-6">
              <h2 className="text-xl text-slate-900 mb-4">Resume History</h2>
              <p className="text-slate-600 mb-6">
                Showing the latest three analyses from your resume uploads.
              </p>

              {loading && versions.length === 0 ? (
                <p className="text-sm text-slate-500">Loading resume history...</p>
              ) : versions.length === 0 ? (
                <p className="text-sm text-slate-500">
                  No analyses found yet. Upload a resume and run an analysis
                  first.
                </p>
              ) : (
                <div className="space-y-3">
                  {versions.map((resume) => (
                    <Card
                      key={resume.id}
                      className={`p-5 ${
                        resume.isActive
                          ? "border-2 border-purple-300 bg-purple-50"
                          : ""
                      }`}
                    >
                      <div className="flex items-start gap-4">
                        <div
                          className={`p-3 rounded-lg ${
                            resume.isActive ? "bg-purple-100" : "bg-slate-100"
                          }`}
                        >
                          <FileText
                            className={`w-6 h-6 ${
                              resume.isActive
                                ? "text-purple-600"
                                : "text-slate-600"
                            }`}
                          />
                        </div>

                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <h3 className="text-slate-900 break-all">
                              {resume.name}
                            </h3>
                            {resume.isActive && (
                              <Badge className="bg-purple-600">Active</Badge>
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

                      {/* Summary row */}
                      <div
                        className={`mt-4 pt-4 border-t ${
                          resume.isActive ? "border-purple-200" : "border-slate-200"
                        }`}
                      >
                        <div className="grid grid-cols-2 gap-4 text-sm mb-4">
                          <div>
                            <div className="text-slate-600 mb-1">
                              Skills Extracted
                            </div>
                            <div className="text-slate-900">
                              {resume.skillsExtracted == null
                                ? "—"
                                : `${resume.skillsExtracted} skills`}
                            </div>
                          </div>
                          <div>
                            <div className="text-slate-600 mb-1">
                              Match Score
                            </div>
                            <div
                              className={
                                resume.isActive
                                  ? "text-purple-600"
                                  : "text-slate-900"
                              }
                            >
                              {formatMatchScore(resume.matchScore)}
                            </div>
                          </div>
                        </div>

                        {/* Technical Skills */}
                        {resume.matchedTechnical &&
                          resume.matchedTechnical.length > 0 && (
                            <div className="mb-3">
                              <div className="text-xs font-semibold text-slate-700 mb-1">
                                Technical Skills
                              </div>
                              <div className="flex flex-wrap gap-1">
                                {resume.matchedTechnical.map((skill) => (
                                  <Badge
                                    key={skill}
                                    className="bg-green-50 text-green-700 border border-green-200 text-xs"
                                  >
                                    {skill}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          )}

                        {/* Soft Skills */}
                        {resume.matchedSoft && resume.matchedSoft.length > 0 && (
                          <div>
                            <div className="text-xs font-semibold text-slate-700 mb-1">
                              Soft Skills
                            </div>
                            <div className="flex flex-wrap gap-1">
                              {resume.matchedSoft.map((skill) => (
                                <Badge
                                  key={skill}
                                  className="bg-blue-50 text-blue-700 border border-blue-200 text-xs"
                                >
                                  {skill}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </Card>
                  ))}
                </div>
              )}
            </Card>
          </div>

          {/* Right: Active resume summary + Re-analyze */}
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
                  <div className="text-sm text-slate-600 mb-1">
                    Last Analysis
                  </div>
                  <div className="text-slate-900 text-sm">
                    {lastAnalysisLabel}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-slate-600 mb-1">Match Score</div>
                  <div className="text-purple-700 text-sm font-medium">
                    {activeMatchScore}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-slate-600 mb-1">
                    Skills Extracted
                  </div>
                  <div className="text-slate-900 text-sm">
                    {activeSkills === "—" ? "—" : `${activeSkills} skills`}
                  </div>
                </div>
              </div>

              <Button
                variant="outline"
                className="w-full mt-6 py-3 text-base border-purple-600 text-purple-700 hover:bg-purple-100"
                onClick={reAnalyze}
              >
                Re-analyze
              </Button>
            </Card>

            <Card className="p-6 mb-6 bg-gradient-to-br from-yellow-50 to-orange-50 border-yellow-200">
              <h3 className="text-slate-900 mb-3">Resume Tips</h3>
              <ul className="space-y-2 text-sm text-slate-700">
                <li>✓ Keep your resume updated with latest projects</li>
                <li>✓ Include quantifiable achievements</li>
                <li>✓ Use industry-standard skill names</li>
                <li>✓ Tailor your resume for target roles</li>
                <li>✓ Upload new versions via the Upload page</li>
              </ul>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
