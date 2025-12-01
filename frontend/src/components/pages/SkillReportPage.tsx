import { useState, useEffect } from "react";
import {
  Target,
  TrendingUp,
  CheckCircle,
  Calendar,
  ArrowRight,
  Sparkles,
  Award,
  MessageCircle,
  ExternalLink,
  X,
  Loader2,
} from "lucide-react";
import { Card } from "../ui/card";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { Separator } from "../ui/separator";
import { Label } from "../ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../ui/select";
// import { Header } from "../Header";
import { generateStudyPlan } from "../../services/studyPlan";
import { createClient } from "../../utils/supabase/client";
import { API_BASE } from '../../services/api'; 

// ===== 跟 analysis 一樣：直接寫死 API base URL =====
// const API_BASE = "http://localhost:8000";

// === helpers for mapping weekly_hours <-> hoursPerDay options ===
type HoursPerDayOption = "1-2" | "2-3" | "3-4" | "4+";

function mapWeeklyHoursToDailyOption(weekly: number | null): HoursPerDayOption {
  if (!weekly || weekly <= 10) return "1-2";
  if (weekly <= 20) return "2-3";
  if (weekly <= 28) return "3-4";
  return "4+";
}

function estimateWeeklyHours(
  hoursPerDay: HoursPerDayOption,
  daysPerWeek: number
): number {
  const mid =
    hoursPerDay === "1-2"
      ? 1.5
      : hoursPerDay === "2-3"
      ? 2.5
      : hoursPerDay === "3-4"
      ? 3.5
      : 4.5;
  return Math.round(mid * daysPerWeek);
}

interface SkillReportProps {
  onGenerateStudyPlan?: (planId?: string) => void;
  analysisId?: string;
  accessToken?: string;
  useBackend?: boolean;
}

// 從 /analysis/{id}/resources 回來的單一 resource 可能的欄位
type Resource = {
  title?: string;
  name?: string;
  full_name?: string;
  url?: string;
  link?: string;
  html_url?: string;
  repo_url?: string;
  provider?: string;
  [key: string]: any;
};

type ResourceMap = Record<string, Resource[]>;

export function SkillReport({
  onGenerateStudyPlan,
  analysisId: initialAnalysisId,
  accessToken,
  useBackend = true,
}: SkillReportProps) {
  const [showPlanGenerator, setShowPlanGenerator] = useState(false);
  const [hoursPerDay, setHoursPerDay] = useState<HoursPerDayOption>("2-3");
  const [timeline, setTimeline] = useState("60");
  const [studyDays, setStudyDays] = useState<string[]>([
    "Mon",
    "Tue",
    "Wed",
    "Thu",
    "Fri",
  ]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Local analysis state
  const [analysisId, setAnalysisId] = useState<string | undefined>(
    initialAnalysisId
  );
  const [matchScore, setMatchScore] = useState<number | null>(null);

  // dynamic skills from API / DB
  const [matchedTechnical, setMatchedTechnical] = useState<string[]>([]);
  const [matchedSoft, setMatchedSoft] = useState<string[]>([]);
  const [missingTechnical, setMissingTechnical] = useState<string[]>([]);
  const [missingSoft, setMissingSoft] = useState<string[]>([]);

  // resources 狀態
  const [techResources, setTechResources] = useState<ResourceMap>({});
  const [softResources, setSoftResources] = useState<ResourceMap>({});
  const [loadingResources, setLoadingResources] = useState(false);

  // Convert matchScore -> percentage readiness score
  const readinessScore =
    matchScore !== null
      ? matchScore <= 1
        ? Math.round(matchScore * 100) // treat as 0–1
        : Math.round(matchScore) // treat as 0–100
      : 68; // fallback if not loaded

  // ===== 1) Load weekly_hours from profiles -> map to hoursPerDay =====
  useEffect(() => {
    if (!useBackend) return;

    const loadProfilePreferences = async () => {
      try {
        const supabase = createClient();
        const {
          data: { session },
        } = await supabase.auth.getSession();

        const userId = session?.user?.id;
        if (!userId) return;

        const { data, error } = await supabase
          .from("profiles")
          .select("weekly_hours")
          .eq("id", userId)
          .maybeSingle();

        if (error) {
          console.warn("[SkillReport] Failed to load profile preferences:", error);
          return;
        }

        const row = data as { weekly_hours: number | null } | null;

        if (!row || row.weekly_hours == null) return;

        setHoursPerDay(mapWeeklyHoursToDailyOption(row.weekly_hours));
      } catch (err) {
        console.warn("[SkillReport] loadProfilePreferences error:", err);
      }
    };

    loadProfilePreferences();
  }, [useBackend]);

  // ===== 2) Auto-resolve analysisId: use prop if given, else latest from skill_analyses =====
  useEffect(() => {
    if (!useBackend) return;

    const loadLatestAnalysis = async () => {
      try {
        // If parent already provided analysisId, just use it
        if (initialAnalysisId) {
          setAnalysisId(initialAnalysisId);
          return;
        }

        const supabase = createClient();

        const {
          data: { user },
        } = await supabase.auth.getUser();

        if (!user) {
          console.warn("[SkillReport] No auth user, cannot load analysis");
          return;
        }

        const { data, error } = await supabase
          .from("skill_analyses")
          .select("id, created_at")
          .eq("user_id", user.id)
          .order("created_at", { ascending: false })
          .limit(1)
          .maybeSingle();

        if (error) {
          console.warn("[SkillReport] Failed to load latest skill analysis:", error);
          return;
        }

        const row = data as { id: string } | null;

        if (row?.id) {
          setAnalysisId(row.id);
        } else {
          console.log("[SkillReport] No skill_analyses rows found for this user");
        }
      } catch (err) {
        console.warn("[SkillReport] loadLatestAnalysis error:", err);
      }
    };

    loadLatestAnalysis();
  }, [initialAnalysisId, useBackend]);

  // ===== 3) Once we have analysisId, load match_score & skills from skill_analyses =====
  useEffect(() => {
    if (!useBackend || !analysisId) return;

    const loadAnalysisDetails = async () => {
      try {
        const supabase = createClient();
        const { data, error } = await supabase
          .from("skill_analyses")
          .select(
            "match_score, matched_skills_technical, matched_skills_soft, missing_skills_technical, missing_skills_soft"
          )
          .eq("id", analysisId)
          .maybeSingle();

        if (error) {
          console.warn("[SkillReport] Failed to load analysis details:", error);
          return;
        }

        const row = data as {
          match_score: number | null;
          matched_skills_technical: string[] | null;
          matched_skills_soft: string[] | null;
          missing_skills_technical: string[] | null;
          missing_skills_soft: string[] | null;
        } | null;

        if (!row) return;

        if (row.match_score !== null) {
          setMatchScore(row.match_score);
        } else {
          setMatchScore(null);
        }

        setMatchedTechnical(row.matched_skills_technical || []);
        setMatchedSoft(row.matched_skills_soft || []);
        setMissingTechnical(row.missing_skills_technical || []);
        setMissingSoft(row.missing_skills_soft || []);
      } catch (err) {
        console.warn("[SkillReport] loadAnalysisDetails error:", err);
      }
    };

    loadAnalysisDetails();
  }, [analysisId, useBackend]);

  // ===== 4) 有 analysisId 之後，去打 /analysis/{id}/resources 抓學習資源 =====
  useEffect(() => {
    if (!useBackend || !analysisId) return;

    const loadResources = async () => {
      try {
        setLoadingResources(true);
        const res = await fetch(
          `${API_BASE}/analysis/${analysisId}/resources`
        );
        if (!res.ok) {
          console.warn(
            "[SkillReport] Failed to fetch resources, status:",
            res.status
          );
          return;
        }

        const data: {
          technical?: ResourceMap;
          soft?: ResourceMap;
          message?: string;
        } = await res.json();

        setTechResources(data.technical || {});
        setSoftResources(data.soft || {});
      } catch (err) {
        console.warn("[SkillReport] loadResources error:", err);
      } finally {
        setLoadingResources(false);
      }
    };

    loadResources();
  }, [analysisId, useBackend]);

  const getReadinessMessage = (score: number) => {
    if (score >= 80)
      return {
        text: "You're almost ready!",
        color: "text-green-600",
        icon: "🎯",
      };
    if (score >= 60)
      return {
        text: "You're on the right track!",
        color: "text-blue-600",
        icon: "🚀",
      };
    return {
      text: "Let's build your skills!",
      color: "text-purple-600",
      icon: "💪",
    };
  };

  const readiness = getReadinessMessage(readinessScore);

  // 小 helper：從 resource 物件抓 label / url
  const getResourceLabel = (r: Resource): string =>
    r.title ||
    r.name ||
    r.full_name ||
    r.provider ||
    "View resource";

  const getResourceUrl = (r: Resource): string | undefined => {
    // 先嘗試常見欄位
    if (typeof r.url === "string") return r.url;
    if (typeof r.link === "string") return r.link;
    if (typeof r.html_url === "string") return r.html_url;
    if (typeof r.repo_url === "string") return r.repo_url;

    // fallback：從所有欄位中找第一個 http 開頭的字串
    for (const v of Object.values(r)) {
      if (typeof v === "string" && v.startsWith("http")) {
        return v;
      }
    }
    return undefined;
  };

  const handleGenerateStudyPlan = async () => {
    if (!useBackend) {
      onGenerateStudyPlan?.();
      return;
    }

    if (!analysisId) {
      setError(
        "Missing analysis data. Please upload your resume and job description again."
      );
      return;
    }

    setIsGenerating(true);
    setError(null);

    try {
      const supabase = createClient();

      let token: string | null = accessToken || null;
      let userId: string | null = null;

      if (!token) {
        try {
          const {
            data: { session },
          } = await supabase.auth.getSession();
          token = session?.access_token || null;
          userId = session?.user?.id ?? null;
        } catch (sessionErr) {
          console.log("No session available");
          token = null;
        }
      } else {
        try {
          const {
            data: { user },
          } = await supabase.auth.getUser();
          userId = user?.id ?? null;
        } catch (userErr) {
          console.log("Could not fetch auth user:", userErr);
        }
      }

      if (userId) {
        try {
          const weeklyHours = estimateWeeklyHours(hoursPerDay, studyDays.length);

          await supabase
            .from("profiles")
            .upsert(
              {
                id: userId,
                weekly_hours: weeklyHours,
              } as any
            );
        } catch (profileErr) {
          console.warn(
            "[SkillReport] Failed to sync profile preferences (weekly_hours):",
            profileErr
          );
        }
      }

      console.log("Generating study plan with:", {
        analysisId,
        hoursPerDay,
        timeline,
        studyDays,
        hasToken: !!token,
      });

      const studyPlan = await generateStudyPlan(token, {
        analysisId,
        hoursPerDay,
        timeline,
        studyDays,
        jobDescription: "",
      });

      console.log("Study plan generated:", studyPlan.id);

      localStorage.setItem("currentStudyPlanId", studyPlan.id);

      onGenerateStudyPlan?.(studyPlan.id);
    } catch (err: any) {
      console.error("Error generating study plan:", err);
      setError(
        err?.message ||
          "Failed to generate study plan. Please check the console for details."
      );
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* <Header activePage="today" /> */}
      <div className="container mx-auto px-6 max-w-6xl py-12">
        <div className="text-center mb-8">
          <h1 className="text-4xl text-slate-900 mb-3">
            Your Career Readiness Report
          </h1>
          <p className="text-lg text-slate-600">
          </p>
        </div>

        {/* Overall Readiness Card */}
        <Card className="p-8 mb-8 bg-gradient-to-br from-purple-50 to-indigo-50 border-purple-200">
          <div className="text-center mb-6">
            <div className="inline-flex items-center justify-center w-32 h-32 rounded-full bg-white shadow-lg mb-4">
              <div className="text-center">
                <div className="text-4xl text-purple-600 mb-1">
                  {readinessScore}%
                </div>
                <div className="text-xs text-slate-600">
                </div>
              </div>
            </div>
            <h2 className={`text-2xl mb-2 ${readiness.color}`}>
              {readiness.icon} {readiness.text}
            </h2>
            <p className="text-slate-700 max-w-2xl mx-auto">
              Your resume currently has a{" "}
              <strong>{readinessScore}% match</strong> to this role. Focus on
              strengthening the missing skills to become fully qualified. With
              consistent effort, you could be job-ready in about{" "}
              <strong>2-3 months</strong>.
            </p>
          </div>

          <div className="grid grid-cols-3 gap-6 mt-6">
            <div className="text-center p-4 bg-white rounded-lg border border-purple-200">
              <div className="text-2xl text-green-600 mb-1">
                {matchedTechnical.length + matchedSoft.length}
              </div>
              <div className="text-sm text-slate-600">Skills You Have</div>
            </div>
            <div className="text-center p-4 bg-white rounded-lg border border-purple-200">
              <div className="text-2xl text-purple-600 mb-1">
                {missingTechnical.length + missingSoft.length}
              </div>
              <div className="text-sm text-slate-600">Skills to Learn</div>
            </div>
            <div className="text-center p-4 bg-white rounded-lg border border-purple-200">
              <div className="text-2xl text-blue-600 mb-1">~70h</div>
              <div className="text-sm text-slate-600">Total Study Time</div>
            </div>
          </div>
        </Card>

        {/* Study Plan Generator */}
        <Card className="p-8 mb-8 bg-gradient-to-br from-green-50 to-emerald-50 border-green-200">
          <div className="flex items-center gap-3 mb-6">
            <div className="bg-green-100 p-3 rounded-xl">
              <Calendar className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <h2 className="text-xl text-slate-900">
                Generate Your Personalized Study Plan
              </h2>
              <p className="text-sm text-slate-600">
                Tell us your availability and we&apos;ll create a day-by-day
                roadmap to reach your goal
              </p>
            </div>
          </div>

          {!showPlanGenerator ? (
            <div className="text-center">
              <Button
                onClick={() => setShowPlanGenerator(true)}
                className="bg-green-600 hover:bg-green-700 text-white px-8 py-6 h-auto text-lg"
              >
                <Sparkles className="w-5 h-5 mr-2" />
                Create My Study Plan
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            </div>
          ) : (
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <Label htmlFor="hours-per-day">
                    How many hours can you study per day?
                  </Label>
                  <Select
                    value={hoursPerDay}
                    onValueChange={(v: HoursPerDayOption) =>
                      setHoursPerDay(v)
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1-2">
                        1-2 hours/day (Light pace)
                      </SelectItem>
                      <SelectItem value="2-3">
                        2-3 hours/day (Standard)
                      </SelectItem>
                      <SelectItem value="3-4">
                        3-4 hours/day (Intensive)
                      </SelectItem>
                      <SelectItem value="4+">
                        4+ hours/day (Full-time)
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="timeline">
                    When do you want to be job-ready?
                  </Label>
                  <Select value={timeline} onValueChange={setTimeline}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="30">1 month (30 days)</SelectItem>
                      <SelectItem value="60">2 months (60 days)</SelectItem>
                      <SelectItem value="90">3 months (90 days)</SelectItem>
                      <SelectItem value="120">4 months (120 days)</SelectItem>
                      <SelectItem value="180">6 months (180 days)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div>
                <Label className="mb-3 block">
                  Which days are you available to study?
                </Label>
                <div className="flex gap-2">
                  {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map(
                    (day) => (
                      <Button
                        key={day}
                        variant={
                          studyDays.includes(day) ? "default" : "outline"
                        }
                        className={
                          studyDays.includes(day)
                            ? "bg-green-600 hover:bg-green-700"
                            : ""
                        }
                        onClick={() => {
                          setStudyDays((prev) =>
                            prev.includes(day)
                              ? prev.filter((d) => d !== day)
                              : [...prev, day]
                          );
                        }}
                      >
                        {day}
                      </Button>
                    )
                  )}
                </div>
              </div>

              <Separator />

              <div className="bg-white rounded-lg p-6 border border-green-300">
                <h3 className="text-slate-900 mb-4">
                  Your Study Plan Summary
                </h3>
                <div className="space-y-2 text-sm text-slate-700">
                  <div className="flex justify-between">
                    <span>Daily commitment:</span>
                    <strong>{hoursPerDay} hours</strong>
                  </div>
                  <div className="flex justify-between">
                    <span>Study days per week:</span>
                    <strong>{studyDays.length} days</strong>
                  </div>
                  <div className="flex justify-between">
                    <span>Timeline:</span>
                    <strong>{timeline} days</strong>
                  </div>
                  <div className="flex justify-between">
                    <span>Target completion:</span>
                    <strong>Feb 10, 2025</strong>
                  </div>
                  <Separator className="my-3" />
                  <div className="flex justify-between text-base">
                    <span>Expected readiness level:</span>
                    <strong className="text-green-600">95%</strong>
                  </div>
                </div>
              </div>

              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-sm">
                  {error}
                </div>
              )}

              <div className="flex gap-3">
                <Button
                  onClick={() => {
                    setShowPlanGenerator(false);
                    setError(null);
                  }}
                  variant="outline"
                  className="flex-1"
                  disabled={isGenerating}
                >
                  Back
                </Button>
                <Button
                  className="flex-1 bg-green-600 hover:bg-green-700 text-white"
                  onClick={handleGenerateStudyPlan}
                  disabled={isGenerating}
                >
                  {isGenerating ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Generating Plan...
                    </>
                  ) : (
                    <>
                      <Calendar className="w-4 h-4 mr-2" />
                      Generate My {timeline}-Day Plan
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </>
                  )}
                </Button>
              </div>
            </div>
          )}
        </Card>

        {/* Existing Skills (Matched) */}
        <Card className="p-6 mb-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="bg-green-100 p-3 rounded-xl">
              <CheckCircle className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <h2 className="text-xl text-slate-900">Your Existing Strengths</h2>
              <p className="text-sm text-slate-600">
                Skills detected in your resume that match this role
              </p>
            </div>
          </div>

          {matchedTechnical.length === 0 && matchedSoft.length === 0 ? (
            <p className="text-sm text-slate-600">
              No skills detected yet. Try uploading a resume with more detailed
              skill descriptions.
            </p>
          ) : (
            <div className="space-y-6">
              {/* Technical */}
              {matchedTechnical.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold text-slate-900 mb-2">
                    Technical Skills
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {matchedTechnical.map((skill) => (
                      <Badge
                        key={skill}
                        className="bg-green-50 text-green-700 border border-green-200"
                      >
                        {skill}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {/* Soft */}
              {matchedSoft.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold text-slate-900 mb-2">
                    Soft Skills
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {matchedSoft.map((skill) => (
                      <Badge
                        key={skill}
                        className="bg-blue-50 text-blue-700 border border-blue-200"
                      >
                        {skill}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </Card>

        {/* Skills to Develop (Missing + Resources) */}
        <Card className="p-6 mb-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="bg-purple-100 p-3 rounded-xl">
              <TrendingUp className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <h2 className="text-xl text-slate-900">Skills to Develop</h2>
              <p className="text-sm text-slate-600">
                Focus areas to reach your career goal
              </p>
            </div>
          </div>

          {/* Technical Skills to Develop */}
          <div className="mb-6">
            <h3 className="text-slate-900 mb-4 flex items-center gap-2">
              <Target className="w-5 h-5 text-purple-600" />
              Technical Skills
            </h3>

            {missingTechnical.length === 0 ? (
              <p className="text-sm text-slate-600">
                No missing technical skills detected for this job description.
              </p>
            ) : (
              <div className="space-y-3">
                {missingTechnical.map((skill) => {
                  const resources = techResources[skill] || [];
                  return (
                    <div
                      key={skill}
                      className="p-4 bg-white rounded-lg border border-slate-200"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-slate-900 font-medium">
                          {skill}
                        </span>
                        <Badge className="bg-red-50 text-red-700 border border-red-200">
                          Missing
                        </Badge>
                      </div>

                      {loadingResources && resources.length === 0 ? (
                        <p className="text-xs text-slate-500">
                          Loading learning resources...
                        </p>
                      ) : resources.length === 0 ? (
                        <p className="text-xs text-slate-500">
                          No curated resources yet for this skill.
                        </p>
                      ) : (
                        <div className="mt-2 flex flex-wrap gap-2">
                          {resources.map((r, idx) => {
                            const label = getResourceLabel(r);
                            const url = getResourceUrl(r);
                            if (!url) {
                              return (
                                <Badge
                                  key={idx}
                                  variant="outline"
                                  className="text-xs"
                                >
                                  {label}
                                </Badge>
                              );
                            }
                            return (
                              <a
                                key={idx}
                                href={url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-block"
                              >
                                <Badge
                                  variant="outline"
                                  className="text-xs cursor-pointer hover:bg-purple-50 hover:border-purple-300 transition-colors"
                                >
                                  {label} →
                                </Badge>
                              </a>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Soft Skills */}
          <div>
            <div className="flex items-center gap-3 mb-4">
              <div className="bg-purple-100 p-2 rounded-lg">
                <Award className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <h3 className="text-lg text-slate-900">Soft Skills</h3>
                <p className="text-sm text-slate-600">
                  Interpersonal and transferable skills
                </p>
              </div>
            </div>

            {/* Skills You Have (from matchedSoft) */}
            <div className="mb-4">
              <div className="flex items-center gap-2 mb-3">
                <CheckCircle className="w-4 h-4 text-green-600" />
                <h4 className="text-sm text-slate-900">Skills You Have</h4>
              </div>
              {matchedSoft.length === 0 ? (
                <p className="text-xs text-slate-500">
                  No soft skills detected yet.
                </p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {matchedSoft.map((skill) => (
                    <Badge
                      key={skill}
                      className="bg-purple-50 text-purple-700 border border-purple-200 hover:bg-purple-100"
                    >
                      {skill}
                    </Badge>
                  ))}
                </div>
              )}
            </div>

            {/* Skills to Develop (from missingSoft + resources) */}
            <div>
              <div className="flex items-center gap-2 mb-3">
                <X className="w-4 h-4 text-red-600" />
                <h4 className="text-sm text-slate-900">Skills to Develop</h4>
              </div>
              {missingSoft.length === 0 ? (
                <p className="text-xs text-slate-500">
                  No missing soft skills detected for this role.
                </p>
              ) : (
                <div className="space-y-3">
                  {missingSoft.map((skill) => {
                    const resources = softResources[skill] || [];
                    return (
                      <div
                        key={skill}
                        className="p-4 bg-white rounded-lg border border-slate-200"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-slate-900 font-medium">
                            {skill}
                          </span>
                          <Badge className="bg-red-50 text-red-700 border border-red-200">
                            Missing
                          </Badge>
                        </div>

                        {loadingResources && resources.length === 0 ? (
                          <p className="text-xs text-slate-500">
                            Loading learning resources...
                          </p>
                        ) : resources.length === 0 ? (
                          <p className="text-xs text-slate-500">
                            No curated resources yet for this skill.
                          </p>
                        ) : (
                          <div className="mt-2 flex flex-wrap gap-2">
                            {resources.map((r, idx) => {
                              const label = getResourceLabel(r);
                              const url = getResourceUrl(r);
                              if (!url) {
                                return (
                                  <Badge
                                    key={idx}
                                    variant="outline"
                                    className="text-xs"
                                  >
                                    {label}
                                  </Badge>
                                );
                              }
                              return (
                                <a
                                  key={idx}
                                  href={url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="inline-block"
                                >
                                  <Badge
                                    variant="outline"
                                    className="text-xs cursor-pointer hover:bg-blue-50 hover:border-blue-300 transition-colors"
                                  >
                                    {label} →
                                  </Badge>
                                </a>
                              );
                            })}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </Card>

        {/* Behavioral Questions to Practice */}
        <Card className="p-6 mb-8 bg-gradient-to-br from-blue-50 to-cyan-50 border-blue-200">
          <div className="flex items-center gap-3 mb-4">
            <div className="bg-blue-100 p-2 rounded-lg">
              <MessageCircle className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h3 className="text-lg text-slate-900">
                Behavioral Questions to Practice
              </h3>
              <p className="text-sm text-slate-600">
                Interview preparation for soft skills assessment
              </p>
            </div>
          </div>

          <p className="text-sm text-slate-700 mb-2">
            Develop your soft skills and prepare for behavioral interviews with
            these curated resources:
          </p>
          <p className="text-sm text-slate-500 italic mb-4">
            Note: Preparation time varies based on your own pace and experience
            level.
          </p>

          {/* Exponent Card */}
          <div className="bg-white rounded-lg p-4 border border-slate-200 mb-4">
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1">
                <h4 className="text-slate-900 mb-1">
                  Exponent - Behavioral Interview Prep
                </h4>
                <p className="text-sm text-slate-600 mb-3">
                  Practice common behavioral questions for leadership, strategic
                  thinking, communication, and other soft skills with expert
                  feedback and frameworks.
                </p>
                <div className="flex flex-wrap gap-2">
                  {(missingSoft.length > 0
                    ? missingSoft.slice(0, 4)
                    : ["Leadership", "Strategic Thinking", "Communication"]
                  ).map((skill) => (
                    <Badge
                      key={skill}
                      className="bg-blue-50 text-blue-700 border border-blue-200"
                    >
                      {skill}
                    </Badge>
                  ))}
                </div>
              </div>
              <a
                href="https://www.tryexponent.com/"
                target="_blank"
                rel="noopener noreferrer"
                className="ml-4"
              >
                <Button className="bg-blue-600 hover:bg-blue-700 text-white">
                  Visit Exponent
                  <ExternalLink className="w-4 h-4 ml-2" />
                </Button>
              </a>
            </div>
          </div>

          {/* Features Grid */}
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-white rounded-lg p-3 border border-slate-200">
              <div className="flex items-start gap-2">
                <div className="w-2 h-2 rounded-full bg-blue-600 mt-1.5 flex-shrink-0" />
                <div>
                  <h5 className="text-sm text-slate-900 mb-0.5">
                    STAR Method Framework
                  </h5>
                  <p className="text-xs text-slate-600">
                    Structure your answers effectively
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg p-3 border border-slate-200">
              <div className="flex items-start gap-2">
                <div className="w-2 h-2 rounded-full bg-blue-600 mt-1.5 flex-shrink-0" />
                <div>
                  <h5 className="text-sm text-slate-900 mb-0.5">
                    Practice Questions Library
                  </h5>
                  <p className="text-xs text-slate-600">
                    200+ behavioral questions by skill
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg p-3 border border-slate-200">
              <div className="flex items-start gap-2">
                <div className="w-2 h-2 rounded-full bg-blue-600 mt-1.5 flex-shrink-0" />
                <div>
                  <h5 className="text-sm text-slate-900 mb-0.5">
                    Expert Video Examples
                  </h5>
                  <p className="text-xs text-slate-600">
                    Learn from successful answers
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg p-3 border border-slate-200">
              <div className="flex items-start gap-2">
                <div className="w-2 h-2 rounded-full bg-blue-600 mt-1.5 flex-shrink-0" />
                <div>
                  <h5 className="text-sm text-slate-900 mb-0.5">
                    Mock Interview Practice
                  </h5>
                  <p className="text-xs text-slate-600">
                    Simulate real interview scenarios
                  </p>
                </div>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
