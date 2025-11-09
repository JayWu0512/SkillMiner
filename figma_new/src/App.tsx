// src/App.tsx
import { useEffect, useState } from "react";
import { BrowserRouter } from "react-router-dom";

import { LoginPage } from "./components/LoginPage";
import { UploadPage } from "./components/UploadPage";
import { ChatbotPage } from "./components/ChatbotPage";
import { MainDashboard } from "./components/MainDashboard";
import { StudyPlanMockup as StudyPlan } from "./components/mockups/StudyPlanMockup";
import { CodingPractice } from "./components/CodingPractice";
import { InterviewPractice } from "./components/InterviewPractice";
import { Profile } from "./components/Profile";
import { Resume } from "./components/Resume";
import { SkillReportMockup as SkillReport } from "./components/mockups/SkillReportMockup";

// ---- Global UI ----
import { Header } from "./components/Header";
import { Toaster } from "./components/ui/sonner";
import { PersistentChatbot } from "./components/mockups/PersistentChatbot";

// ---- Supabase ----
import { createClient } from "./utils/supabase/client";

// === CONFIG ===
const USE_REAL_AUTH = true as const;

// App state
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

  const routeByHistory = async (uid: string) => {
    const supabase = createClient();

    const { data: userRes } = await supabase.auth.getUser();
    console.log("[auth] user.id =", userRes?.user?.id);

    const q1 = await supabase
      .from("skill_analyses")
      .select("id, user_id, resume_text")
      .eq("user_id", uid)
      .limit(1);
    // console.log("[q1] error =", q1.error, "rows =", q1.data?.length, q1.data);

    let hasAny = false;
    if (!q1.error && q1.data && q1.data.length > 0) {
      const q2 = await supabase
        .from("skill_analyses")
        .select("id")
        .eq("user_id", uid)
        .not("resume_text", "is", null)
        .neq("resume_text", "")
        .limit(1);
      // console.log("[q2] error =", q2.error, "rows =", q2.data?.length);
      hasAny = !q2.error && !!q2.data && q2.data.length > 0;
    }

    if (q1.error) {
      // console.error("[routeByHistory] Q1 failed:", q1.error);
      setAppState("upload");
      return;
    }

    setAppState(hasAny ? "dashboard" : "upload");
  };

  useEffect(() => {
    if (!USE_REAL_AUTH) return;

    const init = async () => {
      const supabase = createClient();
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (session?.access_token && session?.user?.id) {
        setAccessToken(session.access_token);
        await routeByHistory(session.user.id);
      } else {
        setAppState("login");
      }
    };

    init();

    const supabase = createClient();
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (_evt, session) => {
      if (session?.access_token && session?.user?.id) {
        setAccessToken(session.access_token);
        await routeByHistory(session.user.id);
      } else {
        setAppState("login");
      }
    });

    return () => subscription.unsubscribe();
  }, []);

  // === Handlers ===
  const handleLoginSuccess = (token: string) => {
    setAccessToken(token);
  };

  const handleAnalysisComplete = (id: string) => {
    setAnalysisId(id);
    setAppState("report");
  };

  const handleLogout = async () => {
    if (USE_REAL_AUTH) {
      const supabase = createClient();
      await supabase.auth.signOut();
    }
    setAccessToken("");
    setAnalysisId("");
    setAppState("login");
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
          onNavigate={(key) => setAppState(mapHeaderKeyToState(key as HeaderNavKey))}
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
        <StudyPlan onNavigate={(p: string) => p === "dashboard" && setAppState("dashboard")} />
      )}

      {appState === "coding" && (
        <CodingPractice onNavigate={(p: string) => p === "dashboard" && setAppState("dashboard")} />
      )}

      {appState === "interview" && (
        <InterviewPractice onNavigate={(p: string) => p === "dashboard" && setAppState("dashboard")} />
      )}

      {appState === "profile" && (
        <Profile onNavigate={(p: string) => p === "dashboard" && setAppState("dashboard")} />
      )}

      {appState === "resume" && (
        <Resume onNavigate={(p: string) => p === "dashboard" && setAppState("dashboard")} />
      )}

      {appState === "report" && (
        <SkillReport onGenerateStudyPlan={() => setAppState("dashboard")} />
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
