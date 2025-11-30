import React, { useEffect, useMemo, useState } from "react";
import {
  Calendar,
  Target,
  Flame,
  Trophy,
  BookOpen,
  Code,
  MessageSquare,
  User,
  FileText,
  ChevronRight,
} from "lucide-react";
import { Card } from "../ui/card";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { Progress } from "../ui/progress";
import { Checkbox } from "../ui/checkbox";

import { createClient } from "../../utils/supabase/client";
import {
  getStudyPlan,
  type StudyPlan as StudyPlanType,
  type DailyTask as StudyPlanDailyTask,
} from "../../services/studyPlan";

type MockupPage =
  | "login"
  | "upload"
  | "report"
  | "dashboard"
  | "plan"
  | "coding"
  | "interview"
  | "profile"
  | "resume";

interface MainDashboardProps {
  onNavigate?: (page: MockupPage) => void;
  accessToken?: string | null;
}

/** UI shape for today's tasks */
interface TodayTask {
  id: string;
  title: string;
  topic: string;
  estMinutes: number;
  xp: number;
  completed: boolean;
  type: "study" | "practice" | "interview" | "reflection";
}

/** Helper: parse "2h", "90m" → minutes (fallback 60) */
const parseEstTimeToMinutes = (estTime?: string | null): number => {
  if (!estTime) return 60;
  const v = estTime.trim().toLowerCase();

  const hMatch = v.match(/([\d.]+)\s*h/);
  if (hMatch) {
    const hours = parseFloat(hMatch[1]);
    if (!Number.isNaN(hours)) return Math.round(hours * 60);
  }

  const mMatch = v.match(/(\d+)\s*m/);
  if (mMatch) {
    const minutes = parseInt(mMatch[1], 10);
    if (!Number.isNaN(minutes)) return minutes;
  }

  const numMatch = v.match(/(\d+)/);
  if (numMatch) {
    const minutes = parseInt(numMatch[1], 10);
    if (!Number.isNaN(minutes)) return minutes;
  }

  return 60;
};

const DAY_LABELS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"] as const;

const toLocalDate = (isoDate: string | undefined | null) => {
  if (!isoDate) return null;
  const parts = isoDate.split("-").map((part) => Number.parseInt(part, 10));
  if (parts.length !== 3 || parts.some((value) => Number.isNaN(value))) {
    return null;
  }
  const [year, month, day] = parts;
  return new Date(year, month - 1, day);
};

const supabase = createClient();

export function MainDashboard({ onNavigate, accessToken }: MainDashboardProps) {
  const [studyPlan, setStudyPlan] = useState<StudyPlanType | null>(null);
  const [isLoadingPlan, setIsLoadingPlan] = useState(false);
  const [planError, setPlanError] = useState<string | null>(null);

  // -------- fetch latest study plan for current user ----------
  useEffect(() => {
    let cancelled = false;

    const loadLatestPlan = async () => {
      setIsLoadingPlan(true);
      setPlanError(null);

      try {
        // 1. access token (if parent didn't pass one, get from session)
        let token: string | null = accessToken || null;

        if (!token) {
          const {
            data: { session },
          } = await supabase.auth.getSession();
          token = session?.access_token || null;
        }

        // 2. get auth user
        const {
          data: { user },
          error: userError,
        } = await supabase.auth.getUser();

        if (userError) throw userError;
        if (!user) throw new Error("You must be logged in.");

        // 3. find latest study_plan.id for this user
        const { data: latestRow, error: latestError } = await supabase
          .from("study_plans")
          .select("id, created_at")
          .eq("user_id", user.id)
          .order("created_at", { ascending: false })
          .limit(1)
          .maybeSingle();

        if (latestError) throw latestError;
        if (!latestRow) {
          throw new Error(
            "You do not have any study plan yet. Please generate one from the report page."
          );
        }

        const planId = (latestRow as { id: string }).id;

        // 4. call edge function to get full plan
        const plan = await getStudyPlan(token, planId);

        if (!cancelled) {
          setStudyPlan(plan);
        }
      } catch (e: any) {
        if (!cancelled) {
          console.error("Failed to load latest study plan:", e);
          setStudyPlan(null);
          setPlanError(
            e?.message ??
              "Unable to load your study plan. Please try again later."
          );
        }
      } finally {
        if (!cancelled) setIsLoadingPlan(false);
      }
    };

    loadLatestPlan();

    return () => {
      cancelled = true;
    };
  }, [accessToken]);

  // -------- derive "all tasks with fullDate" from studyPlan ----------
  const allTasksWithDate = useMemo(
    () =>
      studyPlan
        ? studyPlan.planData.tasks.map(
            (task: StudyPlanDailyTask, index: number) => {
              let fullDate: Date | null = null;
              const planStartDate = toLocalDate(studyPlan.startDate);

              // 1) if task has fullDate string
              if ((task as any).fullDate) {
                const parsed = toLocalDate((task as any).fullDate as string);
                if (parsed && !Number.isNaN(parsed.getTime())) {
                  fullDate = parsed;
                }
              }

              // 2) else derive from startDate + index
              if (!fullDate && planStartDate) {
                fullDate = new Date(planStartDate);
                fullDate.setDate(planStartDate.getDate() + index);
              }

              // 3) fallback: try parsing like "Nov 30"
              if (!fullDate && task.date) {
                const dateMatch = task.date.match(/(\w+)\s+(\d+)/);
                if (dateMatch) {
                  const monthNames = [
                    "Jan",
                    "Feb",
                    "Mar",
                    "Apr",
                    "May",
                    "Jun",
                    "Jul",
                    "Aug",
                    "Sep",
                    "Oct",
                    "Nov",
                    "Dec",
                  ];
                  const month = monthNames.indexOf(dateMatch[1]);
                  const day = parseInt(dateMatch[2], 10);
                  const year = planStartDate
                    ? planStartDate.getFullYear()
                    : new Date().getFullYear();
                  fullDate = new Date(year, month, day);
                }
              }

              // 4) final fallback: today + index
              if (!fullDate) {
                fullDate = new Date();
                fullDate.setDate(fullDate.getDate() + index);
              }

              const displayDate =
                task.date ??
                fullDate.toLocaleDateString("en-US", {
                  month: "short",
                  day: "numeric",
                });
              const dayLabel = DAY_LABELS[fullDate.getDay()];

              return {
                ...task,
                fullDate,
                displayDate,
                dayLabel,
              } as StudyPlanDailyTask & {
                fullDate: Date;
                displayDate: string;
                dayLabel: string;
              };
            }
          )
        : [],
    [studyPlan]
  );

  // -------- filter today's tasks from study plan ----------
  const todayTasks: TodayTask[] = useMemo(() => {
    if (!studyPlan) return [];

    const today = new Date();
    const tYear = today.getFullYear();
    const tMonth = today.getMonth();
    const tDate = today.getDate();

    return allTasksWithDate
      .filter((task) => {
        const d = task.fullDate;
        return (
          d.getFullYear() === tYear &&
          d.getMonth() === tMonth &&
          d.getDate() === tDate &&
          !(task as any).isRestDay // skip rest days
        );
      })
      .map((task, idx) => ({
        id: `${idx}`,
        title: task.task,
        topic: task.theme,
        estMinutes: parseEstTimeToMinutes(task.estTime),
        xp: task.xp,
        completed: !!task.completed,
        // for now everything is "study"; later you can map by theme/type
        type: "study" as const,
      }));
  }, [allTasksWithDate, studyPlan]);

  const totalXPToday = todayTasks.reduce((sum, task) => sum + task.xp, 0);
  const earnedXP = todayTasks
    .filter((t) => t.completed)
    .reduce((sum, task) => sum + task.xp, 0);
  const xpProgress =
    totalXPToday > 0 ? (earnedXP / totalXPToday) * 100 : 0;

  const todayLabel = (() => {
    const d = new Date();
    return d.toLocaleDateString("en-US", {
      weekday: "long",
      month: "short",
      day: "numeric",
    });
  })();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="container mx-auto px-6 py-8">
        <div className="grid grid-cols-12 gap-6">
          {/* Left Sidebar - Quick Links */}
          <div className="col-span-3">
            <Card className="p-6">
              <h3 className="text-slate-900 mb-4">Quick Access</h3>
              <div className="space-y-2">
                <Button
                  variant="ghost"
                  className="w-full justify-start"
                  onClick={() => onNavigate?.("profile")}
                >
                  <User className="w-4 h-4 mr-2" />
                  Profile
                </Button>
                <Button
                  variant="ghost"
                  className="w-full justify-start"
                  onClick={() => onNavigate?.("resume")}
                >
                  <FileText className="w-4 h-4 mr-2" />
                  Resume
                </Button>
                <Button
                  variant="ghost"
                  className="w-full justify-start"
                  onClick={() => onNavigate?.("report")}
                >
                  <Target className="w-4 h-4 mr-2" />
                  Skill Report
                </Button>
                <Button
                  variant="ghost"
                  className="w-full justify-start"
                  onClick={() => onNavigate?.("plan")}
                >
                  <Calendar className="w-4 h-4 mr-2" />
                  Study Plan
                </Button>
              </div>
            </Card>
          </div>

          {/* Center - Today's Tasks */}
          <div className="col-span-6">
            <div className="mb-6">
              <h1 className="text-3xl text-slate-900 mb-2">Today, {todayLabel}</h1>
              {isLoadingPlan ? (
                <p className="text-slate-600">
                  Loading your study plan tasks...
                </p>
              ) : planError ? (
                <p className="text-red-600 text-sm">{planError}</p>
              ) : todayTasks.length > 0 ? (
                <p className="text-slate-600">
                  You have{" "}
                  {todayTasks.filter((t) => !t.completed).length} tasks to
                  complete today
                </p>
              ) : (
                <p className="text-slate-600">
                  No specific tasks scheduled for today in your study plan.
                </p>
              )}
            </div>

            {/* Daily Tasks */}
            <div className="space-y-4">
              {todayTasks.map((task) => (
                <Card
                  key={task.id}
                  className={`p-6 ${
                    task.completed ? "bg-slate-50 opacity-75" : "bg-white"
                  }`}
                >
                  <div className="flex items-start gap-4">
                    {/* TODO: wire this up to updateTaskCompletion if you want checkbox to sync */}
                    <Checkbox checked={task.completed} className="mt-1" />
                    <div className="flex-1">
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <h3
                            className={`text-lg ${
                              task.completed
                                ? "line-through text-slate-500"
                                : "text-slate-900"
                            }`}
                          >
                            {task.title}
                          </h3>
                          <p className="text-sm text-slate-600">
                            {task.topic}
                          </p>
                        </div>
                        <Badge className="bg-purple-100 text-purple-700">
                          {task.xp} XP
                        </Badge>
                      </div>

                      <div className="flex items-center gap-4 text-sm text-slate-600">
                        <span>⏱️ {task.estMinutes} min</span>
                        <span>•</span>
                        <span className="capitalize">{task.type}</span>
                      </div>

                      {!task.completed && (
                        <div className="flex gap-2 mt-4">
                          <Button className="bg-purple-600 hover:bg-purple-700">
                            Start Task
                          </Button>
                          <Button variant="outline">Reschedule</Button>
                        </div>
                      )}
                    </div>
                  </div>
                </Card>
              ))}
            </div>

            {/* Completed Banner */}
            {todayTasks.length > 0 &&
              todayTasks.every((t) => t.completed) && (
                <Card className="p-6 mt-6 bg-gradient-to-r from-green-50 to-emerald-50 border-green-200">
                  <div className="flex items-center gap-4">
                    <div className="bg-green-100 p-3 rounded-full">
                      <Trophy className="w-6 h-6 text-green-600" />
                    </div>
                    <div>
                      <h3 className="text-green-900">
                        All done for today! 🎉
                      </h3>
                      <p className="text-sm text-green-700">
                        You've earned {totalXPToday} XP and maintained your
                        streak!
                      </p>
                    </div>
                  </div>
                </Card>
              )}

            {/* 如果完全沒有 study plan，可以引導去生成 */}
            {!isLoadingPlan && !studyPlan && planError && (
              <Card className="p-6 mt-6 bg-red-50 border border-red-200">
                <h3 className="text-red-700 mb-2">
                  We couldn&apos;t find a study plan for you
                </h3>
                <p className="text-sm text-red-600 mb-4">
                  {planError}
                </p>
                <Button
                  className="bg-red-600 hover:bg-red-700"
                  onClick={() => onNavigate?.("report")}
                >
                  Generate from Skill Report
                </Button>
              </Card>
            )}
          </div>

          {/* Right Sidebar - Insights */}
          <div className="col-span-3">
            {/* XP Progress */}
            <Card className="p-6 mb-6 bg-gradient-to-br from-purple-50 to-indigo-50 border-purple-200">
              <div className="flex items-center gap-3 mb-4">
                <div className="bg-purple-100 p-3 rounded-xl">
                  <Trophy className="w-6 h-6 text-purple-600" />
                </div>
                <div>
                  <h3 className="text-slate-900">Today&apos;s XP</h3>
                  <p className="text-2xl text-purple-600">
                    {earnedXP} / {totalXPToday || 0}
                  </p>
                </div>
              </div>
              <Progress value={xpProgress} className="h-2" />
            </Card>

            {/* Streak */}
            <Card className="p-6 mb-6 bg-gradient-to-br from-orange-50 to-red-50 border-orange-200">
              <div className="flex items-center gap-3 mb-2">
                <div className="bg-orange-100 p-3 rounded-xl">
                  <Flame className="w-6 h-6 text-orange-600" />
                </div>
                <div>
                  <h3 className="text-slate-900">Current Streak</h3>
                  <p className="text-3xl text-orange-600">7 days</p>
                </div>
              </div>
              <p className="text-sm text-orange-700 mt-4">
                🛡️ You have 1 streak shield available
              </p>
            </Card>

            {/* Readiness */}
            <Card className="p-6 mb-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="bg-blue-100 p-3 rounded-xl">
                  <Target className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <h3 className="text-slate-900">Readiness</h3>
                  <p className="text-2xl text-blue-600">
                    {studyPlan ? `${studyPlan.metadata.progress}%` : "34%"}
                  </p>
                </div>
              </div>
              <Progress
                value={studyPlan ? studyPlan.metadata.progress : 34}
                className="h-2 mb-2"
              />
              <p className="text-sm text-slate-600">
                {studyPlan
                  ? `On track for Data Analyst role by ${new Date(
                      studyPlan.endDate
                    ).toLocaleDateString("en-US", {
                      month: "short",
                      day: "numeric",
                      year: "numeric",
                    })}`
                  : "On track for Data Analyst role in 52 days"}
              </p>
            </Card>

            {/* Recent Badges */}
            <Card className="p-6">
              <h3 className="text-slate-900 mb-4">Recent Badges</h3>
              <div className="space-y-3">
                <div className="flex items-center gap-3 p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                  <div className="text-2xl">🏆</div>
                  <div>
                    <div className="text-sm text-slate-900">7-Day Streak</div>
                    <div className="text-xs text-slate-600">Earned today</div>
                  </div>
                </div>
                <div className="flex items-center gap-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
                  <div className="text-2xl">📚</div>
                  <div>
                    <div className="text-sm text-slate-900">SQL Starter</div>
                    <div className="text-xs text-slate-600">2 days ago</div>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
