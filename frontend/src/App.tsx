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

// Single supabase client
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

  // ---------- Save the last visited page to localStorage ----------
  useEffect(() => {
    if (typeof window === "undefined") return;
    if (appState === "login" || appState === "upload") return;
    window.localStorage.setItem("lastAppState", appState);
  }, [appState]);

  // ---------- Sync currentPlanId to localStorage ----------
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

  // ---------- Update study plan from chatbot ----------
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

  // ---------- Fetch latest study_plan in background, don't change appState ----------
  async function routeByHistory(uid: string, tokenOverride?: string) {
    try {
      console.log("[routeByHistory] uid =", uid);

      const { data: latestPlanRowsRaw, error: latestPlanError } = await supabase
        .from("study_plans")
        .select("id")
        .eq("user_id", uid)
        .order("created_at", { ascending: false })
        .limit(1);

      const latestPlanRows =
        (latestPlanRowsRaw as Array<{ id: string }> | null) ?? null;

      if (!latestPlanError && latestPlanRows && latestPlanRows.length > 0) {
        const latestPlanId = latestPlanRows[0].id;
        if (latestPlanId) {
          setCurrentPlanId(latestPlanId);
          try {
            await fetchAndStorePlan(latestPlanId, tokenOverride);
          } catch (planError) {
            console.warn(
              "[routeByHistory] latest study plan retrieval failed:",
              planError
            );
          }
          return;
        }
      }

      if (latestPlanError) {
        console.warn(
          "[routeByHistory] failed to fetch latest study plan:",
          latestPlanError
        );
      }

      // skill_analyses is currently only for informational purposes
      const skillRes = await supabase
        .from("skill_analyses")
        .select("id")
        .eq("user_id", uid)
        .limit(1);

      if (skillRes.error) {
        console.warn(
          "[routeByHistory] skill_analyses query error:",
          skillRes.error
        );
      }
    } catch (err) {
      console.error("[routeByHistory] unexpected error:", err);
    }
  }

  // ---------- Initialize & auth listener ----------
  useEffect(() => {
    if (!USE_REAL_AUTH) {
      setAppState("login");
      return;
    }

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

          console.log("[auth] user.id =", session.user.id);

          // 1️⃣ Has session, first check lastAppState
          let initial: AppState = "dashboard";
          if (typeof window !== "undefined") {
            const saved = window.localStorage.getItem(
              "lastAppState"
            ) as AppState | null;
            if (
              saved &&
              saved !== "login" &&
              saved !== "upload" &&
              saved !== "chat"
            ) {
              initial = saved;
            }
          }
          setAppState(initial);

          // 2️⃣ Fetch latest study_plan in background, fill into state
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
    } = supabase.auth.onAuthStateChange((event, session) => {
      // Only handle data updates for SIGNED_IN / SIGNED_OUT, don't change appState
      if (event === "SIGNED_IN" && session?.access_token && session.user) {
        console.log("[auth] onAuth SIGNED_IN", session.user.id);
        setAccessToken(session.access_token);
        setAuthUser({
          id: session.user.id,
          email: session.user.email ?? null,
        });
        void routeByHistory(session.user.id, session.access_token);
      } else if (event === "SIGNED_OUT") {
        console.log("[auth] onAuth SIGNED_OUT");
        setAuthUser(null);
        setCurrentPlanId(null);
        handlePlanUpdate(null);
        setAppState("login");
        if (typeof window !== "undefined") {
          window.localStorage.removeItem("lastAppState");
          window.localStorage.removeItem("currentStudyPlanId");
        }
      } else {
        // TOKEN_REFRESHED / INITIAL_SESSION etc. don't change the screen at all
        return;
      }
    });

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  // ---------- Handlers ----------
  const handleLoginSuccess = (token: string) => {
    // After LoginPage login success, automatically navigate to dashboard
    setAccessToken(token);
    setAppState("dashboard");
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

    if (typeof window !== "undefined") {
      window.localStorage.removeItem("lastAppState");
      window.localStorage.removeItem("currentStudyPlanId");
    }

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
          onNavigate={(p: string) => {
            if (p === "dashboard") {
              setAppState("dashboard");
            }
            if (p === "skill-report" || p === "report") {
              setAppState("report");
            }
          }}
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
