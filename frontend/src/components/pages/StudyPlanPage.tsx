// src/components/pages/StudyPlanPage.tsx
import React, { useState, useEffect } from "react";
import {
  Calendar,
  Download,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  Target,
  Clock,
  Trophy,
  Loader2,
  AlertCircle,
} from "lucide-react";
import { Card } from "../ui/card";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../ui/dialog";
import {
  getStudyPlan,
  updateTaskCompletion,
  type StudyPlan as StudyPlanType,
  type DailyTask as StudyPlanDailyTask,
} from "../../services/studyPlan";
import { createClient } from "../../utils/supabase/client";

const DAY_LABELS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"] as const;
const normalizeDayKey = (day: string) => day.slice(0, 3).toLowerCase();

const toLocalDate = (isoDate: string | undefined | null) => {
  if (!isoDate) return null;
  const parts = isoDate.split("-").map((part) => Number.parseInt(part, 10));
  if (parts.length !== 3 || parts.some((value) => Number.isNaN(value))) {
    return null;
  }
  const [year, month, day] = parts;
  return new Date(year, month - 1, day);
};

// ------- Supabase 連線（跟 Profile 一樣用單一 client） -------
const supabase = createClient();

// ------- DB row 型別：對應 public.study_plans 的欄位 -------
type DBStudyPlanRow = {
  id: string;
  user_id: string;
  analysis_id: string;
  status: string;
  created_at: string;
  updated_at: string;
  start_date: string;
  end_date: string;
  total_days: number;
  hours_per_day: string;
  study_days: string[];
  plan_data: any;
  metadata: any;
};

// 把 DB 的 snake_case row 轉成前端 StudyPlanType
const mapDBRowToStudyPlan = (row: DBStudyPlanRow): StudyPlanType => {
  return {
    id: row.id,
    userId: row.user_id,
    analysisId: row.analysis_id,
    status: row.status,
    createdAt: row.created_at,
    updatedAt: row.updated_at,
    startDate: row.start_date,
    endDate: row.end_date,
    totalDays: row.total_days,
    hoursPerDay: row.hours_per_day,
    studyDays: row.study_days,
    planData: row.plan_data,
    metadata: row.metadata,
  };
};

interface DailyTask {
  date: string;
  dayOfWeek: string;
  theme: string;
  task: string;
  resources: string;
  estTime: string;
  xp: number;
  completed?: boolean;
  isRestDay?: boolean;
  color?: string;
}

// ------- mock 資料：完全沒有 study plan 時才會用 -------

// 一週 mock
const generateWeekData = (weekOffset: number): DailyTask[] => {
  const startDate = new Date(2024, 10, 11); // Nov 11, 2024
  startDate.setDate(startDate.getDate() + weekOffset * 7);

  const weekData: Array<Omit<DailyTask, "date" | "dayOfWeek">> = [
    {
      theme: "Orientation",
      task: "Review Skill Report + Install Jupyter/VSCode",
      resources: "SkillMiner Docs",
      estTime: "1h",
      xp: 20,
    },
    {
      theme: "Python Basics",
      task: "Variables, data types, loops",
      resources: "Kaggle Python 101",
      estTime: "2h",
      xp: 40,
    },
    {
      theme: "Python Practice",
      task: "10 Easy LeetCode Python problems",
      resources: "LeetCode",
      estTime: "2h",
      xp: 60,
    },
    {
      theme: "Statistics",
      task: "Mean, median, mode, standard deviation",
      resources: "Khan Academy",
      estTime: "2h",
      xp: 50,
    },
    {
      theme: "SQL Basics",
      task: "SELECT, WHERE, ORDER BY",
      resources: "Mode SQL Tutorial",
      estTime: "2h",
      xp: 50,
    },
    {
      theme: "Weekend Challenge",
      task: "Build a small CSV data summary (Pandas)",
      resources: "SkillMiner Notebook",
      estTime: "3h",
      xp: 70,
    },
    {
      theme: "Reflection",
      task: "Review week + write summary in chatbot",
      resources: "Chatbot Prompt",
      estTime: "1h",
      xp: 30,
    },
  ];

  const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

  return weekData.map((data, index) => {
    const date = new Date(startDate);
    date.setDate(date.getDate() + index);

    return {
      date: date.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
      }),
      dayOfWeek: days[index],
      ...data,
      completed: weekOffset === 0 && index < 3,
      isRestDay: false,
    };
  });
};

// 60 天 mock
const generateAllTasks = (): (DailyTask & { fullDate: Date })[] => {
  const startDate = new Date(2024, 10, 11); // Nov 11, 2024
  const allTasks: Array<DailyTask & { fullDate: Date }> = [];

  const taskTemplates = [
    {
      theme: "Orientation",
      task: "Review Skill Report + Install Jupyter/VSCode",
      resources: "SkillMiner Docs",
      estTime: "1h",
      xp: 20,
      color: "purple",
    },
    {
      theme: "Python Basics",
      task: "Variables, data types, loops",
      resources: "Kaggle Python 101",
      estTime: "2h",
      xp: 40,
      color: "blue",
    },
    {
      theme: "Python Practice",
      task: "10 Easy LeetCode Python problems",
      resources: "LeetCode",
      estTime: "2h",
      xp: 60,
      color: "blue",
    },
    {
      theme: "Statistics",
      task: "Mean, median, mode, standard deviation",
      resources: "Khan Academy",
      estTime: "2h",
      xp: 50,
      color: "green",
    },
    {
      theme: "SQL Basics",
      task: "SELECT, WHERE, ORDER BY",
      resources: "Mode SQL Tutorial",
      estTime: "2h",
      xp: 50,
      color: "orange",
    },
    {
      theme: "Weekend Challenge",
      task: "Build a small CSV data summary (Pandas)",
      resources: "SkillMiner Notebook",
      estTime: "3h",
      xp: 70,
      color: "purple",
    },
    {
      theme: "Reflection",
      task: "Review week + write summary in chatbot",
      resources: "Chatbot Prompt",
      estTime: "1h",
      xp: 30,
      color: "gray",
    },
  ];

  const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

  for (let i = 0; i < 60; i++) {
    const currentDate = new Date(startDate);
    currentDate.setDate(startDate.getDate() + i);

    const templateIndex = i % 7;
    const task = taskTemplates[templateIndex];

    allTasks.push({
      fullDate: currentDate,
      date: currentDate.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
      }),
      dayOfWeek:
        days[currentDate.getDay() === 0 ? 6 : currentDate.getDay() - 1],
      ...task,
      completed: i < 3,
      isRestDay: false,
    });
  }

  return allTasks;
};

// 月曆 mock
const generateMonthData = (monthOffset: number) => {
  const baseDate = new Date(2024, 10, 1); // Nov 1, 2024
  baseDate.setMonth(baseDate.getMonth() + monthOffset);

  const year = baseDate.getFullYear();
  const month = baseDate.getMonth();

  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);

  const firstDayOfWeek = firstDay.getDay();
  const daysFromPrevMonth = firstDayOfWeek;

  const startDate = new Date(firstDay);
  startDate.setDate(startDate.getDate() - daysFromPrevMonth);

  const calendarDays: Array<{
    date: Date;
    dayNumber: number;
    isCurrentMonth: boolean;
    isToday: boolean;
  }> = [];

  for (let i = 0; i < 42; i++) {
    const currentDate = new Date(startDate);
    currentDate.setDate(startDate.getDate() + i);

    calendarDays.push({
      date: currentDate,
      dayNumber: currentDate.getDate(),
      isCurrentMonth: currentDate.getMonth() === month,
      isToday:
        currentDate.getDate() === new Date(2024, 10, 11).getDate() &&
        currentDate.getMonth() === new Date(2024, 10, 11).getMonth() &&
        currentDate.getFullYear() === new Date(2024, 10, 11).getFullYear(),
    });
  }

  return {
    year,
    month,
    monthName: firstDay.toLocaleDateString("en-US", {
      month: "long",
      year: "numeric",
    }),
    calendarDays,
  };
};

interface StudyPlanProps {
  onNavigate?: (page: string) => void;

  /** 可以給特定 planId；如果沒給，就會用 user_id 抓最新一筆 */
  planId?: string;
  accessToken?: string;
  initialPlan?: StudyPlanType | null;
  onPlanUpdate?: (plan: StudyPlanType | null) => void;
}

export function StudyPlan({
  onNavigate,
  planId,
  accessToken,
  initialPlan,
  onPlanUpdate,
}: StudyPlanProps) {
  const [viewMode, setViewMode] = useState<"calendar" | "list" | "month">(
    "calendar"
  );
  const [currentWeek, setCurrentWeek] = useState(0);
  const [currentMonthOffset, setCurrentMonthOffset] = useState(0);
  const [studyPlan, setStudyPlan] = useState<StudyPlanType | null>(
    initialPlan ?? null
  );
  const [isLoading, setIsLoading] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [retryKey, setRetryKey] = useState(0);

  // ------------ 用 user_id 找最新的 plan_id，再跑 study plan service -------------
  useEffect(() => {
    let isCancelled = false;

    const fetchStudyPlan = async () => {
      setIsLoading(true);
      setLoadError(null);

      try {
        // 1. 先拿 access token（優先用外面傳進來的）
        let token: string | null = accessToken || null;

        if (!token) {
          try {
            const {
              data: { session },
            } = await supabase.auth.getSession();
            token = session?.access_token || null;
          } catch {
            token = null;
          }
        }

        // 2. 先決定要用的 planId
        let effectivePlanId = planId;

        if (!effectivePlanId) {
          // 如果外面沒有給 planId，就用 user_id 去 study_plans 找最新一筆
          const {
            data: { user },
            error: userError,
          } = await supabase.auth.getUser();

          if (userError) throw userError;
          if (!user) {
            throw new Error("You must be logged in to view your study plan.");
          }

          const { data, error } = await supabase
            .from("study_plans")
            .select("id, created_at")
            .eq("user_id", user.id)
            .order("created_at", { ascending: false })
            .limit(1)
            .maybeSingle();

          if (error) {
            throw error;
          }

          if (!data) {
            // 這裡就是真正查不到任何 plan 的情況
            throw new Error(
              "You do not have any study plan yet. Please generate one from the report page."
            );
          }

          effectivePlanId = (data as { id: string }).id;
        }

        // 3. 用找到的 planId 去 call 既有的 study plan service（edge function）
        const plan = await getStudyPlan(token, effectivePlanId);

        if (!isCancelled) {
          setStudyPlan(plan);
          onPlanUpdate?.(plan);
        }
      } catch (error: any) {
        if (!isCancelled) {
          console.error("Error fetching study plan:", error);
          setStudyPlan(null);

          const msg =
            error?.message && /study plan/i.test(error.message)
              ? `Unable to load your study plan: ${error.message}`
              : error?.message
              ? `Unable to load your study plan: ${error.message}`
              : "Unable to load your study plan.";

          setLoadError(msg);
          onPlanUpdate?.(null);
        }
      } finally {
        if (!isCancelled) setIsLoading(false);
      }
    };

    fetchStudyPlan();

    return () => {
      isCancelled = true;
    };
  }, [planId, accessToken, onPlanUpdate, retryKey]);

  // ---- 監聽從 Chatbot 發出的 studyPlanUpdatedFromChat 事件 ----
  useEffect(() => {
    if (typeof window === "undefined") return;

    const handleUpdatedPlan = (event: Event) => {
      const updated = (event as CustomEvent<StudyPlanType>).detail;
      if (!updated) return;
      if (planId && updated.id !== planId) return;
      setStudyPlan(updated);
      onPlanUpdate?.(updated);
    };

    window.addEventListener(
      "studyPlanUpdatedFromChat",
      handleUpdatedPlan as EventListener
    );

    return () => {
      window.removeEventListener(
        "studyPlanUpdatedFromChat",
        handleUpdatedPlan as EventListener
      );
    };
  }, [planId, onPlanUpdate]);

  // ----------------- 根據 study plan 產出 task 資料 -----------------
  const planStudyDays = studyPlan?.studyDays ?? [];
  const planStudyDaySet = new Set(planStudyDays.map(normalizeDayKey));
  const hasStudyDayFilter = planStudyDaySet.size > 0;
  const planStartDate = toLocalDate(studyPlan?.startDate ?? undefined);
  const totalWeeks = studyPlan ? Math.ceil(studyPlan.totalDays / 7) : 8; // mock default

  const allTasks: Array<DailyTask & { fullDate: Date }> = studyPlan
    ? studyPlan.planData.tasks.map(
        (task: StudyPlanDailyTask, index: number) => {
          let fullDate: Date | null = null;

          if ((task as any).fullDate) {
            const parsed = toLocalDate((task as any).fullDate as string);
            if (parsed && !Number.isNaN(parsed.getTime())) fullDate = parsed;
          }

          if (!fullDate && planStartDate) {
            fullDate = new Date(planStartDate);
            fullDate.setDate(planStartDate.getDate() + index);
          }

          if (!fullDate) {
            const dateMatch = task.date?.match(/(\w+)\s+(\d+)/);
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
            } else {
              fullDate = new Date();
              fullDate.setDate(fullDate.getDate() + index);
            }
          }

          const resolvedDate = fullDate ?? new Date();
          const displayDate =
            task.date ??
            resolvedDate.toLocaleDateString("en-US", {
              month: "short",
              day: "numeric",
            });
          const dayLabel = DAY_LABELS[resolvedDate.getDay()];
          const displayDay = dayLabel === "Sun" ? "Sun" : dayLabel;
          const normalizedDay = normalizeDayKey(displayDay);

          const isRestDay =
            task.isRestDay ??
            (hasStudyDayFilter && !planStudyDaySet.has(normalizedDay));

          if (isRestDay) {
            return {
              date: displayDate,
              dayOfWeek: displayDay,
              theme: "Rest & Recharge",
              task: "Take a break—no study scheduled.",
              resources: "",
              estTime: "0h",
              xp: 0,
              completed: false,
              fullDate: resolvedDate,
              isRestDay: true,
            };
          }

          return {
            date: displayDate,
            dayOfWeek: task.dayOfWeek ?? displayDay,
            theme: task.theme,
            task: task.task,
            resources: task.resources,
            estTime: task.estTime,
            xp: task.xp,
            completed: task.completed || false,
            fullDate: resolvedDate,
            isRestDay: false,
            color: (task as any).color,
          };
        }
      )
    : generateAllTasks();

  const currentWeekData = studyPlan
    ? allTasks
        .slice(currentWeek * 7, (currentWeek + 1) * 7)
        .map((task) => ({
          date: task.date,
          dayOfWeek: task.dayOfWeek,
          theme: task.theme,
          task: task.task,
          resources: task.resources,
          estTime: task.estTime,
          xp: task.xp,
          completed: task.completed || false,
          isRestDay: task.isRestDay ?? false,
        }))
    : generateWeekData(currentWeek);

  const startDate = currentWeekData[0]?.date || "";
  const endDate = currentWeekData[6]?.date || "";

  const monthData = generateMonthData(currentMonthOffset);

  const weeksPhases =
    studyPlan && studyPlan.planData?.phases
      ? studyPlan.planData.phases.map((phase: any) => ({
          range: phase.range,
          label: phase.label,
          color: phase.color,
        }))
      : [
          { range: [0, 1], label: "Foundations", color: "purple" },
          { range: [2, 3], label: "Visualization & EDA", color: "blue" },
          { range: [4, 5], label: "Advanced Topics", color: "orange" },
          { range: [6, 7], label: "Portfolio & Interview", color: "green" },
        ];

  const getTasksForDate = (date: Date) => {
    return allTasks.filter((task) => {
      const taskDate =
        task.fullDate instanceof Date ? task.fullDate : new Date(task.fullDate);
      return (
        taskDate.getDate() === date.getDate() &&
        taskDate.getMonth() === date.getMonth() &&
        taskDate.getFullYear() === date.getFullYear()
      );
    });
  };

  // 勾選完成（改成用 studyPlan.id，跟 user_id 無關）
  const handleTaskComplete = async (
    taskIndex: number,
    completed: boolean
  ) => {
    if (!studyPlan) return;
    if (studyPlan.planData.tasks[taskIndex]?.isRestDay) return;

    const currentPlanId = studyPlan.id;

    try {
      let token: string | null = accessToken || null;

      if (!token) {
        try {
          const {
            data: { session },
          } = await supabase.auth.getSession();
          token = session?.access_token || null;
        } catch {
          token = null;
        }
      }

      try {
        const updatedPlan = await updateTaskCompletion(
          token,
          currentPlanId,
          taskIndex,
          completed
        );
        setStudyPlan(updatedPlan);
        onPlanUpdate?.(updatedPlan);
      } catch (updateErr) {
        console.error("Error updating task, updating locally:", updateErr);

        const updatedTasks = [...studyPlan.planData.tasks];
        updatedTasks[taskIndex].completed = completed;

        const locallyUpdatedPlan: StudyPlanType = {
          ...studyPlan,
          planData: {
            ...studyPlan.planData,
            tasks: updatedTasks,
          },
        };

        setStudyPlan(locallyUpdatedPlan);
        onPlanUpdate?.(locallyUpdatedPlan);
      }
    } catch (error) {
      console.error("Error updating task completion:", error);
    }
  };

  // ---------------------- loading / error UI ----------------------
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-purple-600" />
          <p className="text-slate-600">Loading your study plan...</p>
        </div>
      </div>
    );
  }

  // 不管有沒有 planId，只要 loadError 有值就顯示錯誤（例如：沒有 study plan）
  if (loadError) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center px-6">
        <Card className="max-w-lg w-full p-6 border border-red-200 bg-red-50">
          <div className="flex items-start gap-3">
            <div className="bg-red-100 p-2 rounded-full">
              <AlertCircle className="w-5 h-5 text-red-600" />
            </div>
            <div>
              <h2 className="text-xl text-red-700 mb-2">
                We couldn&apos;t load your study plan
              </h2>
              <p className="text-sm text-red-600 mb-4">{loadError}</p>
              <div className="flex gap-3">
                <Button
                  variant="outline"
                  onClick={() => onNavigate?.("dashboard")}
                >
                  Go to Dashboard
                </Button>
                <Button
                  onClick={() => setRetryKey((prev) => prev + 1)}
                  className="bg-red-600 hover:bg-red-700"
                >
                  Try Again
                </Button>
              </div>
            </div>
          </div>
        </Card>
      </div>
    );
  }

  const currentPhase = weeksPhases.find(
    (phase) => currentWeek >= phase.range[0] && currentWeek <= phase.range[1]
  );

  const isUsingMockData = !studyPlan;

  // --------------------------- main UI ---------------------------
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* 頁面 header */}
      <div className="bg-white border-b border-slate-200">
        <div className="container mx-auto px-6 py-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl text-slate-900 mb-2">Study Plan</h1>
              <p className="text-slate-600">
                {studyPlan
                  ? `Data Analyst Role • ${studyPlan.totalDays}-day timeline • Target: ${new Date(
                      studyPlan.endDate
                    ).toLocaleDateString("en-US", {
                      month: "short",
                      day: "numeric",
                      year: "numeric",
                    })}`
                  : isUsingMockData
                  ? "Data Analyst Role • 60-day timeline • Target: Feb 10, 2025"
                  : "Fetching your personalized study plan..."}
              </p>
            </div>
            <div className="flex gap-3">
              <Dialog>
                <DialogTrigger asChild>
                  <Button className="bg-green-600 hover:bg-green-700">
                    <Download className="w-4 h-4 mr-2" />
                    Export to Calendar
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Export Your Study Plan</DialogTitle>
                    <DialogDescription>
                      Choose how you&apos;d like to sync your study plan with
                      your calendar
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 mt-4">
                    <Card className="p-4 border-2 border-purple-200 hover:border-purple-400 cursor-pointer">
                      <div className="flex items-start gap-3">
                        <div className="bg-purple-100 p-2 rounded">
                          <Calendar className="w-5 h-5 text-purple-600" />
                        </div>
                        <div>
                          <h3 className="text-slate-900 mb-1">
                            Google Calendar
                          </h3>
                          <p className="text-sm text-slate-600">
                            Real-time sync with automatic updates (requires
                            OAuth)
                          </p>
                        </div>
                      </div>
                    </Card>
                    <Card className="p-4 border-2 border-blue-200 hover:border-blue-400 cursor-pointer">
                      <div className="flex items-start gap-3">
                        <div className="bg-blue-100 p-2 rounded">
                          <Calendar className="w-5 h-5 text-blue-600" />
                        </div>
                        <div>
                          <h3 className="text-slate-900 mb-1">
                            Outlook Calendar
                          </h3>
                          <p className="text-sm text-slate-600">
                            Real-time sync with automatic updates (requires
                            OAuth)
                          </p>
                        </div>
                      </div>
                    </Card>
                    <Card className="p-4 border-2 border-slate-200 hover:border-slate-400 cursor-pointer">
                      <div className="flex items-start gap-3">
                        <div className="bg-slate-100 p-2 rounded">
                          <Download className="w-5 h-5 text-slate-600" />
                        </div>
                        <div>
                          <h3 className="text-slate-900 mb-1">
                            ICS File (One-time)
                          </h3>
                          <p className="text-sm text-slate-600">
                            Download .ics file to import into any calendar app
                          </p>
                        </div>
                      </div>
                    </Card>
                  </div>
                </DialogContent>
              </Dialog>
              <Button variant="outline">
                <RefreshCw className="w-4 h-4 mr-2" />
                Regenerate Plan
              </Button>
            </div>
          </div>

          {/* Stats row */}
          <div className="grid grid-cols-4 gap-4">
            <Card className="p-4">
              <div className="flex items-center gap-3">
                <div className="bg-purple-100 p-2 rounded">
                  <Target className="w-5 h-5 text-purple-600" />
                </div>
                <div>
                  <div className="text-sm text-slate-600">Progress</div>
                  <div className="text-xl text-slate-900">
                    {studyPlan ? `${studyPlan.metadata.progress}%` : "34%"}
                  </div>
                </div>
              </div>
            </Card>
            <Card className="p-4">
              <div className="flex items-center gap-3">
                <div className="bg-blue-100 p-2 rounded">
                  <Clock className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <div className="text-sm text-slate-600">Days Remaining</div>
                  <div className="text-xl text-slate-900">
                    {studyPlan
                      ? Math.max(
                          0,
                          Math.ceil(
                            (new Date(studyPlan.endDate).getTime() -
                              new Date().getTime()) /
                              (1000 * 60 * 60 * 24)
                          )
                        )
                      : "52"}
                  </div>
                </div>
              </div>
            </Card>
            <Card className="p-4">
              <div className="flex items-center gap-3">
                <div className="bg-green-100 p-2 rounded">
                  <Trophy className="w-5 h-5 text-green-600" />
                </div>
                <div>
                  <div className="text-sm text-slate-600">Total XP</div>
                  <div className="text-xl text-slate-900">
                    {studyPlan
                      ? `${
                          studyPlan.planData.tasks
                            .filter((t) => t.completed)
                            .reduce((sum, t) => sum + t.xp, 0)
                        } / ${studyPlan.metadata.totalXP}`
                      : "220 / 650"}
                  </div>
                </div>
              </div>
            </Card>
            <Card className="p-4">
              <div className="flex items-center gap-3">
                <div className="bg-orange-100 p-2 rounded">
                  <Calendar className="w-5 h-5 text-orange-600" />
                </div>
                <div>
                  <div className="text-sm text-slate-600">Current Week</div>
                  <div className="text-xl text-slate-900">
                    {currentWeek + 1} / {totalWeeks}
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="container mx-auto px-6 py-8">
        <Tabs
          value={viewMode}
          onValueChange={(v) =>
            setViewMode(v as "calendar" | "list" | "month")
          }
        >
          <TabsList className="mb-6">
            <TabsTrigger value="calendar">Week View</TabsTrigger>
            <TabsTrigger value="month">Month View</TabsTrigger>
            <TabsTrigger value="list">List View</TabsTrigger>
          </TabsList>

          {/* Week view */}
          <TabsContent value="calendar">
            <div className="flex items-center justify-between mb-6">
              <Button
                variant="outline"
                onClick={() =>
                  setCurrentWeek((prev) => Math.max(0, prev - 1))
                }
                disabled={currentWeek === 0}
              >
                <ChevronLeft className="w-4 h-4 mr-2" />
                Previous Week
              </Button>
              <div className="text-center">
                <h2 className="text-xl text-slate-900">
                  Week {currentWeek + 1}: {currentPhase?.label}
                </h2>
                <p className="text-sm text-slate-600">
                  {startDate} - {endDate}
                </p>
              </div>
              <Button
                variant="outline"
                onClick={() =>
                  setCurrentWeek((prev) =>
                    Math.min(totalWeeks - 1, prev + 1)
                  )
                }
                disabled={currentWeek === totalWeeks - 1}
              >
                Next Week
                <ChevronRight className="w-4 h-4 ml-2" />
              </Button>
            </div>

            {/* Weekly grid */}
            <div className="grid grid-cols-7 gap-4">
              {currentWeekData.map((task) => (
                <Card
                  key={task.dayOfWeek + task.date}
                  className={`p-4 ${
                    task.isRestDay
                      ? "bg-slate-50 border-dashed border-slate-300 text-slate-500"
                      : task.completed
                      ? "bg-green-50 border-green-300"
                      : task.dayOfWeek === "Fri" && currentWeek === 0
                      ? "border-2 border-purple-300 bg-purple-50"
                      : ""
                  }`}
                >
                  <div className="mb-3">
                    <div className="text-sm text-slate-500 mb-1">
                      {task.dayOfWeek}
                    </div>
                    <div
                      className={`text-lg mb-1 ${
                        task.isRestDay ? "text-slate-500" : "text-slate-900"
                      }`}
                    >
                      {task.date}
                    </div>
                    <div
                      className={`text-xs ${
                        task.isRestDay ? "text-slate-500" : "text-slate-600"
                      }`}
                    >
                      {task.isRestDay ? "Rest Day" : task.theme}
                    </div>
                  </div>

                  {task.isRestDay ? (
                    <div className="text-sm text-slate-500">
                      Recharge and enjoy your day off.
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <div className="bg-white rounded p-2 border border-slate-200">
                        <div className="text-xs text-slate-900 mb-1 line-clamp-2">
                          {task.task}
                        </div>
                        <div className="flex items-center gap-1 text-xs text-slate-500">
                          <Clock className="w-3 h-3" />
                          {task.estTime}
                        </div>
                        {task.resources && (
                          <div className="mt-1 text-xs text-slate-500">
                            📚 {task.resources}
                          </div>
                        )}
                      </div>
                      <Badge
                        className={`w-full justify-center text-xs ${
                          task.completed
                            ? "bg-green-600"
                            : "bg-purple-100 text-purple-700"
                        }`}
                      >
                        {task.completed ? "✓ Completed" : `${task.xp} XP`}
                      </Badge>
                      {studyPlan && (
                        <Button
                          size="sm"
                          variant={task.completed ? "outline" : "default"}
                          className="w-full text-xs"
                          onClick={() => {
                            const idx =
                              studyPlan.planData.tasks.findIndex(
                                (t) =>
                                  t.date === task.date &&
                                  (t as any).dayOfWeek === task.dayOfWeek
                              );
                            if (idx !== -1) {
                              handleTaskComplete(idx, !task.completed);
                            }
                          }}
                        >
                          {task.completed ? "Mark Incomplete" : "Mark Complete"}
                        </Button>
                      )}
                    </div>
                  )}
                </Card>
              ))}
            </div>

            {/* Week summary */}
            <Card className="p-6 mt-6 bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-slate-900 mb-2">
                    Week {currentWeek + 1} Summary
                  </h3>
                  <p className="text-sm text-slate-600">
                    Focus: {currentPhase?.label} • Total Time: ~14 hours • Total
                    XP: 320
                  </p>
                </div>
                <Button className="bg-blue-600 hover:bg-blue-700">
                  View Week Details
                </Button>
              </div>
            </Card>
          </TabsContent>

          {/* Month view */}
          <TabsContent value="month">
            <div className="flex items-center justify-between mb-6">
              <Button
                variant="outline"
                onClick={() =>
                  setCurrentMonthOffset((prev) => prev - 1)
                }
              >
                <ChevronLeft className="w-4 h-4 mr-2" />
                Previous Month
              </Button>
              <div className="text-center">
                <h2 className="text-xl text-slate-900">
                  {monthData.monthName}
                </h2>
              </div>
              <Button
                variant="outline"
                onClick={() =>
                  setCurrentMonthOffset((prev) => prev + 1)
                }
              >
                Next Month
                <ChevronRight className="w-4 h-4 ml-2" />
              </Button>
            </div>

            <Card className="overflow-hidden">
              <div className="grid grid-cols-7 bg-slate-50 border-b border-slate-200">
                {["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"].map(
                  (day) => (
                    <div
                      key={day}
                      className="p-3 text-center text-xs text-slate-600 border-r border-slate-200 last:border-r-0"
                    >
                      {day}
                    </div>
                  )
                )}
              </div>

              <div className="grid grid-cols-7">
                {monthData.calendarDays.map((day, index) => {
                  const tasksForDay = getTasksForDate(day.date);
                  const studyTasksForDay = tasksForDay.filter(
                    (t) => !t.isRestDay
                  );
                  const hasRestOnly =
                    studyTasksForDay.length === 0 &&
                    tasksForDay.some((t) => t.isRestDay);

                  return (
                    <div
                      key={index}
                      className={`min-h-[120px] p-2 border-r border-b border-slate-200 ${
                        !day.isCurrentMonth
                          ? "bg-slate-50"
                          : "bg-white"
                      } ${day.isToday ? "bg-blue-50" : ""}`}
                    >
                      <div
                        className={`text-sm mb-2 ${
                          !day.isCurrentMonth
                            ? "text-slate-400"
                            : day.isToday
                            ? "bg-blue-600 text-white w-7 h-7 rounded-full flex items-center justify-center"
                            : "text-slate-700"
                        }`}
                      >
                        {day.dayNumber}
                      </div>
                      <div className="space-y-1">
                        {studyTasksForDay.slice(0, 2).map((task, i2) => (
                          <div
                            key={i2}
                            className={`text-xs px-2 py-1 rounded truncate ${
                              task.completed
                                ? "bg-green-500 text-white"
                                : task.color === "purple"
                                ? "bg-purple-500 text-white"
                                : task.color === "blue"
                                ? "bg-blue-500 text-white"
                                : task.color === "green"
                                ? "bg-green-500 text-white"
                                : task.color === "orange"
                                ? "bg-orange-500 text-white"
                                : "bg-slate-500 text-white"
                            }`}
                          >
                            {task.theme}
                          </div>
                        ))}
                        {studyTasksForDay.length > 2 && (
                          <div className="text-xs text-slate-500 px-2">
                            +{studyTasksForDay.length - 2} more
                          </div>
                        )}
                        {hasRestOnly && (
                          <div className="text-xs text-slate-400 px-2 italic">
                            Rest day
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </Card>

            <Card className="p-6 mt-6 bg-gradient-to-r from-purple-50 to-pink-50 border-purple-200">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-slate-900 mb-2">Month Summary</h3>
                  <p className="text-sm text-slate-600">
                    {
                      allTasks.filter(
                        (t) =>
                          t.fullDate.getMonth() === monthData.month &&
                          t.fullDate.getFullYear() === monthData.year
                      ).length
                    }{" "}
                    tasks scheduled • Track your progress daily
                  </p>
                </div>
                <div className="flex gap-3">
                  <div className="flex items-center gap-2 text-sm">
                    <div className="w-4 h-4 bg-green-500 rounded" />
                    <span className="text-slate-600">Completed</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <div className="w-4 h-4 bg-purple-500 rounded" />
                    <span className="text-slate-600">Foundations</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <div className="w-4 h-4 bg-blue-500 rounded" />
                    <span className="text-slate-600">Technical</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <div className="w-4 h-4 bg-orange-500 rounded" />
                    <span className="text-slate-600">Practice</span>
                  </div>
                </div>
              </div>
            </Card>
          </TabsContent>

          {/* List view */}
          <TabsContent value="list">
            <div className="space-y-3">
              {currentWeekData.map((task) => (
                <Card
                  key={task.dayOfWeek + task.date}
                  className={`p-5 hover:shadow-md transition-shadow ${
                    task.completed ? "bg-green-50 border-green-200" : ""
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <Badge variant="outline">
                          {task.dayOfWeek}, {task.date}
                        </Badge>
                        <h3
                          className={`text-slate-900 ${
                            task.isRestDay ? "text-slate-500" : ""
                          }`}
                        >
                          {task.isRestDay ? "Rest Day" : task.theme}
                        </h3>
                        {task.completed && !task.isRestDay && (
                          <Badge className="bg-green-600">✓ Completed</Badge>
                        )}
                      </div>
                      <p
                        className={`mb-3 ${
                          task.isRestDay
                            ? "text-slate-500 italic"
                            : "text-slate-700"
                        }`}
                      >
                        {task.isRestDay
                          ? "Recharge day — no study session planned."
                          : task.task}
                      </p>
                      {!task.isRestDay && (
                        <div className="flex items-center gap-4 text-sm text-slate-600">
                          <span className="flex items-center gap-1">
                            <Clock className="w-4 h-4" />
                            {task.estTime}
                          </span>
                          <span>•</span>
                          <span>📚 {task.resources}</span>
                        </div>
                      )}
                    </div>
                    <div className="flex flex-col items-end gap-2">
                      {!task.isRestDay && (
                        <Badge className="bg-purple-100 text-purple-700">
                          {task.xp} XP
                        </Badge>
                      )}
                      {!task.completed && !task.isRestDay && (
                        <Button
                          size="sm"
                          className="bg-purple-600 hover:bg-purple-700"
                        >
                          Start
                        </Button>
                      )}
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </TabsContent>
        </Tabs>

        {/* Phase overview */}
        <Card className="p-6 mt-8 bg-gradient-to-r from-purple-50 to-pink-50 border-purple-200">
          <h3 className="text-slate-900 mb-4">Study Plan Phases</h3>
          <div className="grid grid-cols-4 gap-4">
            {weeksPhases.map((phase, index) => (
              <div
                key={index}
                className={`bg-white rounded-lg p-4 border-2 ${
                  currentWeek >= phase.range[0] && currentWeek <= phase.range[1]
                    ? "border-purple-400 shadow-md"
                    : "border-slate-200"
                }`}
              >
                <div
                  className={`mb-2 ${
                    currentWeek >= phase.range[0] &&
                    currentWeek <= phase.range[1]
                      ? "text-purple-600"
                      : "text-slate-400"
                  }`}
                >
                  Phase {index + 1}
                </div>
                <div
                  className={`text-sm mb-1 ${
                    currentWeek >= phase.range[0] &&
                    currentWeek <= phase.range[1]
                      ? "text-slate-900"
                      : "text-slate-600"
                  }`}
                >
                  Weeks {phase.range[0] + 1}-{phase.range[1] + 1}:{" "}
                  {phase.label}
                </div>
                <div className="text-xs text-slate-500 mt-1">
                  {index === 0 && "Python, SQL, Statistics basics"}
                  {index === 1 && "Matplotlib, Tableau, EDA"}
                  {index === 2 && "A/B Testing, Regression"}
                  {index === 3 && "Projects, Interviews"}
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
