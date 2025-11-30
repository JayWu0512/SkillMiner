// src/App.tsx
import React, { useEffect, useState, useCallback } from "react";
import { BrowserRouter } from "react-router-dom";

import { LoginPage } from "./components/pages/LoginPage";
import { UploadPage } from "./components/pages/UploadPage";
import { ChatbotPage } from "./components/pages/ChatbotPage";
import { MainDashboard } from "./components/pages/MainDashboardPage";
import { StudyPlan } from "./components/pages/StudyPlanPage";
import { CodingPractice } from "./components/pages/CodingPracticePage";
import { InterviewPractice } from "./components/pages/InterviewPracticePage";
import { Profile } from "./components/pages/ProfilePage";
import { Resume } from "./components/pages/ResumePage";
import { SkillReport } from "./components/pages/SkillReportPage";

import { Header } from "./components/features/Header";
import { Toaster } from "./components/ui/sonner";
import { PersistentChatbot } from "./components/features/PersistentChatbot";

import { createClient } from "./utils/supabase/client";
import {
  getStudyPlan,
  type StudyPlan as StudyPlanData,
} from "./services/studyPlan";

type Nullable<T> = T | null;

type AuthUser = {
  id: string;
  email: string | null;
};

const USE_REAL_AUTH = true as const;

// ⭐ 單一 supabase client，避免到處 new
const supabase = createClient();

type AppState =
  | "login"
  | "upload"
  | "dashboard"
  | "plan"
  | "coding"
  | "interview"
  | "profile"
  | "resume"
  | "report"
  | "chat";

type HeaderNavKey =
  | "today"
  | "study-plan"
  | "practice"
  | "coding-practice"
  | "interview-practice"
  | "profile"
  | "settings";

export default function App() {
  const [appState, setAppState] = useState<AppState>("login");
  const [accessToken, setAccessToken] = useState<string>("");
  const [analysisId, setAnalysisId] = useState<string>("");
  const [authUser, setAuthUser] = useState<AuthUser | null>(null);
  const [currentPlanId, setCurrentPlanId] = useState<string | null>(() => {
    if (typeof window === "undefined") return null;
    return window.localStorage.getItem("currentStudyPlanId");
  });
  const [activeStudyPlan, setActiveStudyPlan] =
    useState<Nullable<StudyPlanData>>(null);

  // ---- localStorage 同步 ----
  useEffect(() => {
    if (typeof window === "undefined") return;
    if (currentPlanId) {
      window.localStorage.setItem("currentStudyPlanId", currentPlanId);
    } else {
      window.localStorage.removeItem("currentStudyPlanId");
    }
  }, [currentPlanId]);

  const handlePlanUpdate = useCallback((plan: Nullable<StudyPlanData>) => {
    setActiveStudyPlan(plan);
  }, []);

  // ---- 從 chatbot 更新 study plan ----
  useEffect(() => {
    if (typeof window === "undefined") return;
    const handleStudyPlanUpdate = (event: Event) => {
      const detail = (event as CustomEvent<StudyPlanData>).detail;
      if (!detail || !detail.id) return;
      setCurrentPlanId(detail.id);
      handlePlanUpdate(detail);
    };
    window.addEventListener(
      "studyPlanUpdatedFromChat",
      handleStudyPlanUpdate as EventListener
    );
    return () => {
      window.removeEventListener(
        "studyPlanUpdatedFromChat",
        handleStudyPlanUpdate as EventListener
      );
    };
  }, [handlePlanUpdate]);

  const fetchAndStorePlan = async (
    planId: string,
    tokenOverride?: string | null
  ) => {
    try {
      const plan = await getStudyPlan(
        tokenOverride ?? accessToken ?? null,
        planId
      );
      handlePlanUpdate(plan);
      return plan;
    } catch (error) {
      console.error("[App] Failed to fetch study plan:", error);
      handlePlanUpdate(null);
      throw error;
    }
  };

  // ---- 根據歷史決定要去 plan / upload / dashboard ----
  async function routeByHistory(uid: string, tokenOverride?: string) {
    try {
      const { data: userRes } = await supabase.auth.getUser();
      console.log("[auth] user.id =", userRes?.user?.id);

      // 1) 先看有沒有最新的 study_plan
      const { data: latestPlanRowsRaw, error: latestPlanError } = await supabase
        .from("study_plans")
        .select("id")
        .eq("user_id", uid)
        .order("created_at", { ascending: false })
        .limit(1);

      const latestPlanRows =
        (latestPlanRowsRaw as Array<{ id: string }> | null) ?? null;

      if (!latestPlanError && latestPlanRows && latestPlanRows.length > 0) {
        const latestPlanId = latestPlanRows?.[0]?.id;
        if (latestPlanId) {
          setCurrentPlanId(latestPlanId);
          try {
            await fetchAndStorePlan(latestPlanId, tokenOverride);
          } catch (planError) {
            console.warn(
              "[routeByHistory] Latest study plan retrieval failed:",
              planError
            );
          }
          setAppState("plan");
          return;
        }
      } else if (latestPlanError) {
        console.warn(
          "[routeByHistory] failed to fetch latest study plan:",
          latestPlanError
        );
        if (currentPlanId) {
          try {
            await fetchAndStorePlan(currentPlanId, tokenOverride);
            setAppState("plan");
            return;
          } catch (planError) {
            console.warn(
              "[routeByHistory] Stored study plan retrieval failed:",
              planError
            );
          }
        }
      }

      // 2) 沒有 plan，就看有沒有任何 skill_analyses
      const q1 = await supabase
        .from("skill_analyses")
        .select("id, user_id, resume_text")
        .eq("user_id", uid)
        .limit(1);

      if (q1.error) {
        setCurrentPlanId(null);
        handlePlanUpdate(null);
        setAppState("upload");
        return;
      }

      // 有 analysis 但沒 plan，就回 dashboard
      setCurrentPlanId(null);
      handlePlanUpdate(null);
      setAppState("dashboard");
    } catch (err) {
      console.error("[routeByHistory] unexpected error:", err);
      setCurrentPlanId(null);
      handlePlanUpdate(null);
      setAppState("dashboard");
    }
  }

  // ---- 初始化 & auth 監聽 ----
  useEffect(() => {
    if (!USE_REAL_AUTH) return;

    const init = async () => {
      try {
        const {
          data: { session },
        } = await supabase.auth.getSession();

        if (session?.access_token && session?.user?.id) {
          setAccessToken(session.access_token);
          setAuthUser({
            id: session.user.id,
            email: session.user.email ?? null,
          });

          // 先給一個穩定畫面，不要被 DB call 卡住
          setAppState("dashboard");

          // 背景決定要不要跳到 plan / upload
          void routeByHistory(session.user.id, session.access_token);
        } else {
          setAuthUser(null);
          setAppState("login");
        }
      } catch (err) {
        console.error("[App init] getSession failed:", err);
        setAuthUser(null);
        setAppState("login");
      }
    };

    void init();

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (event, session) => {
      if (event === "SIGNED_IN" && session?.access_token && session.user) {
        setAccessToken(session.access_token);
        setAuthUser({
          id: session.user.id,
          email: session.user.email ?? null,
        });
        // 只在真正 SIGNED_IN 時重新 route
        setAppState("dashboard");
        void routeByHistory(session.user.id, session.access_token);
      } else if (event === "SIGNED_OUT") {
        setAuthUser(null);
        setAppState("login");
      } else {
        // TOKEN_REFRESHED 等其他事件就不要亂動目前頁面
        return;
      }
    });

    return () => {
      subscription.unsubscribe();
    };
  }, []); // ⭐ 不依賴 routeByHistory，避免每次 render 重跑

  // ---- Handlers ----
  const handleLoginSuccess = (token: string) => {
    setAccessToken(token);
  };

  const handleAnalysisComplete = (id: string) => {
    setAnalysisId(id);
    setAppState("report");
  };

  const handleLogout = () => {
    setAccessToken("");
    setAnalysisId("");
    setCurrentPlanId(null);
    setAuthUser(null);
    handlePlanUpdate(null);
    setAppState("login");

    if (USE_REAL_AUTH) {
      supabase.auth.signOut().catch((e) => {
        console.error("[App] supabase signOut failed:", e);
      });
    }
  };

  const mapHeaderKeyToState = (key: HeaderNavKey): AppState => {
    switch (key) {
      case "today":
        return "dashboard";
      case "study-plan":
        return "plan";
      case "coding-practice":
        return "coding";
      case "interview-practice":
        return "interview";
      case "profile":
        return "profile";
      case "settings":
        return "dashboard";
      default:
        return "dashboard";
    }
  };

  const handleStudyPlanGenerated = (planId?: string) => {
    if (planId) {
      setCurrentPlanId(planId);
      fetchAndStorePlan(planId).catch((err) => {
        console.warn(
          "[App] Failed to refresh study plan after generation:",
          err
        );
      });
    }
    setAppState("plan");
  };

  const headerActive: "today" | "study-plan" | "practice" | "profile" | "resume" =
    appState === "dashboard"
      ? "today"
      : appState === "plan"
      ? "study-plan"
      : appState === "coding" || appState === "interview"
      ? "practice"
      : appState === "profile"
      ? "profile"
      : appState === "resume"
      ? "resume"
      : "today";

  return (
    <BrowserRouter>
      {appState !== "login" && appState !== "upload" && (
        <Header
          activePage={headerActive}
          onNavigate={(key) =>
            setAppState(mapHeaderKeyToState(key as HeaderNavKey))
          }
          onLogout={handleLogout}
        />
      )}

      {appState === "login" && (
        <LoginPage onLoginSuccess={handleLoginSuccess} />
      )}

      {appState === "upload" && (
        <UploadPage
          accessToken={accessToken}
          onAnalysisComplete={handleAnalysisComplete}
          onLogout={handleLogout}
        />
      )}

      {appState === "dashboard" && (
        <MainDashboard
          onNavigate={(p: string) => {
            if (p === "report") setAppState("report");
            if (p === "coding") setAppState("coding");
            if (p === "interview") setAppState("interview");
            if (p === "plan") setAppState("plan");
            if (p === "profile") setAppState("profile");
            if (p === "resume") setAppState("resume");
          }}
        />
      )}

      {appState === "plan" && (
        <StudyPlan
          planId={currentPlanId ?? undefined}
          accessToken={accessToken}
          initialPlan={activeStudyPlan ?? undefined}
          onPlanUpdate={handlePlanUpdate}
          onNavigate={(p: string) =>
            p === "dashboard" && setAppState("dashboard")
          }
        />
      )}

      {appState === "coding" && (
        <CodingPractice
          onNavigate={(p: string) =>
            p === "dashboard" && setAppState("dashboard")
          }
        />
      )}

      {appState === "interview" && (
        <InterviewPractice
          onNavigate={(p: string) =>
            p === "dashboard" && setAppState("dashboard")
          }
        />
      )}

      {appState === "profile" && (
        <Profile
          user={authUser}
          onNavigate={(p: string) => {
            if (p === "dashboard") setAppState("dashboard");
            if (p === "resume") setAppState("resume");
            if (p === "report") setAppState("report");
          }}
        />
      )}

      {appState === "resume" && (
        <Resume
          onNavigate={(p) => {
            if (p === "dashboard") setAppState("dashboard");
            if (p === "upload") setAppState("upload"); // Re-analyze
          }}
        />
      )}

      {appState === "report" && (
        <SkillReport
          analysisId={analysisId}
          accessToken={accessToken}
          onGenerateStudyPlan={handleStudyPlanGenerated}
        />
      )}

      {appState === "chat" && (
        <ChatbotPage
          accessToken={accessToken}
          analysisId={analysisId}
          onLogout={handleLogout}
        />
      )}

      {appState !== "login" && appState !== "upload" && (
        <div className="fixed bottom-6 right-6 z-[9999] pointer-events-auto">
          <PersistentChatbot />
        </div>
      )}

      <Toaster />
    </BrowserRouter>
  );
}
