import { useState } from "react";
import {
  Target,
  TrendingUp,
  CheckCircle,
  AlertCircle,
  Clock,
  Calendar,
  ArrowRight,
  Sparkles,
  Loader2,
} from "lucide-react";
import { Card } from "../ui/card";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { Progress } from "../ui/progress";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../ui/select";
import { Separator } from "../ui/separator";
import { generateStudyPlan } from "../../services/studyPlan";
import { createClient } from "../../utils/supabase/client";

const existingSkills = [
  { name: "Python", level: "Intermediate", color: "blue" },
  { name: "Excel", level: "Advanced", color: "green" },
  { name: "Communication", level: "Advanced", color: "green" },
  { name: "R", level: "Beginner", color: "yellow" },
];

const missingSkills = [
  {
    name: "SQL",
    priority: "High",
    estimatedTime: "20 hours",
    resources: ["Mode SQL Tutorial", "LeetCode SQL"],
    type: "hard",
  },
  {
    name: "Tableau",
    priority: "High",
    estimatedTime: "15 hours",
    resources: ["Tableau Public Tutorials", "DataCamp"],
    type: "hard",
  },
  {
    name: "Statistics",
    priority: "Medium",
    estimatedTime: "25 hours",
    resources: ["Khan Academy", "StatQuest YouTube"],
    type: "hard",
  },
  {
    name: "Problem Solving",
    priority: "Medium",
    estimatedTime: "10 hours",
    resources: ["Practice with case studies"],
    type: "soft",
  },
];

interface SkillReportMockupProps {
  onGenerateStudyPlan?: (planId?: string) => void;
  // Optional: if provided, will use real backend
  analysisId?: string;
  accessToken?: string;
  // Optional: if provided, will use this for testing
  useBackend?: boolean;
}

export function SkillReportMockup({
  onGenerateStudyPlan,
  analysisId,
  accessToken,
  useBackend = true,
}: SkillReportMockupProps) {
  const [showPlanGenerator, setShowPlanGenerator] =
    useState(false);
  const [hoursPerDay, setHoursPerDay] = useState("2-3");
  const [timeline, setTimeline] = useState("60");
  const [studyDays, setStudyDays] = useState([
    "Mon",
    "Tue",
    "Wed",
    "Thu",
    "Fri",
  ]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const readinessScore = 68;
  const hardSkillsMissing = missingSkills.filter(
    (s) => s.type === "hard",
  );
  const softSkillsMissing = missingSkills.filter(
    (s) => s.type === "soft",
  );

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

  const handleGenerateStudyPlan = async () => {
    if (useBackend) {
      setIsGenerating(true);
      setError(null);
      
      try {
        // Try to get session token, but allow null for mockup mode
        let token: string | null = accessToken || null;
        
        if (!token) {
          try {
            const supabase = createClient();
            const { data: { session } } = await supabase.auth.getSession();
            token = session?.access_token || null;
          } catch (sessionErr) {
            console.log('No session available, proceeding without auth for mockup mode');
            token = null;
          }
        }

        // Use a mock analysisId for testing (backend will create mock analysis)
        const mockAnalysisId = `mock_analysis_${Date.now()}`;
        
        console.log('Generating study plan with:', {
          analysisId: mockAnalysisId,
          hoursPerDay,
          timeline,
          studyDays,
          hasToken: !!token
        });

        const studyPlan = await generateStudyPlan(token, {
          analysisId: mockAnalysisId,
          hoursPerDay,
          timeline,
          studyDays,
          jobDescription: "Data Analyst (Entry-Level) Position",
        });
        
        console.log('Study plan generated:', studyPlan.id);
        
        // Store planId in localStorage for StudyPlanMockup to retrieve
        localStorage.setItem('currentStudyPlanId', studyPlan.id);
        
        if (onGenerateStudyPlan) {
          onGenerateStudyPlan(studyPlan.id);
        }
      } catch (err: any) {
        console.error('Error generating study plan:', err);
        setError(err.message || 'Failed to generate study plan. Please check the console for details.');
        setIsGenerating(false);
      }
    } else {
      // Mock mode - just navigate
      if (onGenerateStudyPlan) {
        onGenerateStudyPlan();
      }
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 py-12">
      <div className="container mx-auto px-6 max-w-6xl">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl text-slate-900 mb-3">
            Your Career Readiness Report
          </h1>
          <p className="text-lg text-slate-600">
            Data Analyst (Entry-Level) Position
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
                  Ready
                </div>
              </div>
            </div>
            <h2 className={`text-2xl mb-2 ${readiness.color}`}>
              {readiness.icon} {readiness.text}
            </h2>
            <p className="text-slate-700 max-w-2xl mx-auto">
              You have a solid foundation with{" "}
              <strong>4 relevant skills</strong>. Focus on
              building <strong>4 key areas</strong> to become
              fully qualified for this role. With consistent
              effort, you could be ready in about{" "}
              <strong>2-3 months</strong>.
            </p>
          </div>

          <div className="grid grid-cols-3 gap-6 mt-6">
            <div className="text-center p-4 bg-white rounded-lg border border-purple-200">
              <div className="text-2xl text-green-600 mb-1">
                4
              </div>
              <div className="text-sm text-slate-600">
                Skills You Have
              </div>
            </div>
            <div className="text-center p-4 bg-white rounded-lg border border-purple-200">
              <div className="text-2xl text-purple-600 mb-1">
                4
              </div>
              <div className="text-sm text-slate-600">
                Skills to Learn
              </div>
            </div>
            <div className="text-center p-4 bg-white rounded-lg border border-purple-200">
              <div className="text-2xl text-blue-600 mb-1">
                ~70h
              </div>
              <div className="text-sm text-slate-600">
                Total Study Time
              </div>
            </div>
          </div>
        </Card>

        {/* Existing Skills */}
        <Card className="p-6 mb-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="bg-green-100 p-3 rounded-xl">
              <CheckCircle className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <h2 className="text-xl text-slate-900">
                Your Existing Strengths
              </h2>
              <p className="text-sm text-slate-600">
                Skills you already have for this role
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            {existingSkills.map((skill) => (
              <div
                key={skill.name}
                className="flex items-center justify-between p-4 bg-slate-50 rounded-lg border border-slate-200"
              >
                <div>
                  <div className="text-slate-900 mb-1">
                    {skill.name}
                  </div>
                  <Badge
                    className={
                      skill.color === "green"
                        ? "bg-green-100 text-green-700"
                        : skill.color === "blue"
                          ? "bg-blue-100 text-blue-700"
                          : "bg-yellow-100 text-yellow-700"
                    }
                  >
                    {skill.level}
                  </Badge>
                </div>
                <CheckCircle className="w-5 h-5 text-green-600" />
              </div>
            ))}
          </div>
        </Card>

        {/* Skills to Develop */}
        <Card className="p-6 mb-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="bg-purple-100 p-3 rounded-xl">
              <TrendingUp className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <h2 className="text-xl text-slate-900">
                Skills to Develop
              </h2>
              <p className="text-sm text-slate-600">
                Focus areas to reach your career goal
              </p>
            </div>
          </div>

          {/* Hard Skills */}
          <div className="mb-6">
            <h3 className="text-slate-900 mb-4 flex items-center gap-2">
              <Target className="w-5 h-5 text-purple-600" />
              Technical Skills
            </h3>
            <div className="space-y-3">
              {hardSkillsMissing.map((skill) => (
                <div
                  key={skill.name}
                  className="p-4 bg-white rounded-lg border border-slate-200"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="text-slate-900">
                          {skill.name}
                        </h4>
                        <Badge
                          className={
                            skill.priority === "High"
                              ? "bg-red-100 text-red-700"
                              : "bg-orange-100 text-orange-700"
                          }
                        >
                          {skill.priority} Priority
                        </Badge>
                      </div>
                      <div className="flex items-center gap-4 text-sm text-slate-600">
                        <span className="flex items-center gap-1">
                          <Clock className="w-4 h-4" />
                          {skill.estimatedTime}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="text-sm text-slate-700">
                    <strong>Recommended resources:</strong>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {skill.resources.map((resource, idx) => (
                        <Badge
                          key={idx}
                          variant="outline"
                          className="text-xs"
                        >
                          {resource}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Soft Skills */}
          <div>
            <h3 className="text-slate-900 mb-4 flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-blue-600" />
              Professional Skills
            </h3>
            <div className="space-y-3">
              {softSkillsMissing.map((skill) => (
                <div
                  key={skill.name}
                  className="p-4 bg-blue-50 rounded-lg border border-blue-200"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="text-slate-900">
                          {skill.name}
                        </h4>
                        <Badge className="bg-blue-100 text-blue-700">
                          {skill.priority} Priority
                        </Badge>
                      </div>
                      <div className="text-sm text-slate-600 mb-2">
                        {skill.estimatedTime} of practice
                      </div>
                      <div className="text-sm text-slate-700">
                        <strong>Practice with:</strong>{" "}
                        {skill.resources.join(", ")}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Card>

        {/* Study Plan Generator */}
        <Card className="p-8 bg-gradient-to-br from-green-50 to-emerald-50 border-green-200">
          <div className="flex items-center gap-3 mb-6">
            <div className="bg-green-100 p-3 rounded-xl">
              <Calendar className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <h2 className="text-xl text-slate-900">
                Generate Your Personalized Study Plan
              </h2>
              <p className="text-sm text-slate-600">
                Tell us your availability and we'll create a
                day-by-day roadmap to reach your goal
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
                    onValueChange={setHoursPerDay}
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
                  <Select
                    value={timeline}
                    onValueChange={setTimeline}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="30">
                        1 month (30 days)
                      </SelectItem>
                      <SelectItem value="60">
                        2 months (60 days)
                      </SelectItem>
                      <SelectItem value="90">
                        3 months (90 days)
                      </SelectItem>
                      <SelectItem value="120">
                        4 months (120 days)
                      </SelectItem>
                      <SelectItem value="180">
                        6 months (180 days)
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div>
                <Label className="mb-3 block">
                  Which days are you available to study?
                </Label>
                <div className="flex gap-2">
                  {[
                    "Mon",
                    "Tue",
                    "Wed",
                    "Thu",
                    "Fri",
                    "Sat",
                    "Sun",
                  ].map((day) => (
                    <Button
                      key={day}
                      variant={
                        studyDays.includes(day)
                          ? "default"
                          : "outline"
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
                            : [...prev, day],
                        );
                      }}
                    >
                      {day}
                    </Button>
                  ))}
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
                    <strong className="text-green-600">
                      95%
                    </strong>
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

        {/* Behavioral Interview Section */}
        <Card className="p-6 mt-8 bg-gradient-to-br from-blue-50 to-cyan-50 border-blue-200">
          <div className="flex items-center gap-3 mb-4">
            <div className="bg-blue-100 p-3 rounded-xl">
              <AlertCircle className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <h3 className="text-lg text-slate-900">
                Behavioral Questions to Practice
              </h3>
              <p className="text-sm text-slate-600">
                Prepare for common interview scenarios
              </p>
            </div>
          </div>

          <div className="space-y-2">
            {[
              "Tell me about yourself and your interest in data analytics",
              "Describe a time you solved a problem using data",
              "How do you handle tight deadlines and multiple priorities?",
              "Give an example of when you had to explain technical concepts to non-technical stakeholders",
            ].map((question, idx) => (
              <div
                key={idx}
                className="p-3 bg-white rounded border border-blue-200 text-sm text-slate-700"
              >
                {idx + 1}. {question}
              </div>
            ))}
          </div>

          <Button
            variant="outline"
            className="w-full mt-4 border-blue-300 text-blue-600 hover:bg-blue-50"
          >
            Practice with Exponent →
          </Button>
        </Card>
      </div>
    </div>
  );
}