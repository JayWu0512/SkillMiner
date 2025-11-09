// src/App.tsx
import { useState, useEffect } from "react";
import { BrowserRouter } from "react-router-dom";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Switch } from "./components/ui/switch";
import { Label } from "./components/ui/label";
import { Toaster } from "./components/ui/sonner";

// === Mockups ===
import { LoginPageMockup } from "./components/mockups/LoginPageMockup";
import { UploadPageMockup } from "./components/mockups/UploadPageMockup";
import { MainDashboardMockup } from "./components/mockups/MainDashboardMockup";
import { StudyPlanMockup } from "./components/mockups/StudyPlanMockup";
import { CodingPracticeMockup } from "./components/mockups/CodingPracticeMockup";
import { InterviewPracticeMockup } from "./components/mockups/InterviewPracticeMockup";
import { ChatbotPageMockup } from "./components/mockups/ChatbotPageMockup";
import { SkillReportMockup } from "./components/mockups/SkillReportMockup";
import { ProfileMockup } from "./components/mockups/ProfileMockup";
import { ResumeMockup } from "./components/mockups/ResumeMockup";
import { PersistentChatbot } from "./components/mockups/PersistentChatbot";

// === Real components ===
import { LoginPage } from "./components/LoginPage";
import { UploadPage } from "./components/UploadPage";
import { ChatbotPage } from "./components/ChatbotPage";

import { createClient } from "./utils/supabase/client";

// === CONFIG ===
const USE_REAL_AUTH = true;

// app state types
type AppState = "login" | "upload" | "report" | "dashboard" | "chat";
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

export default function App() {
  const [mockupMode, setMockupMode] = useState(false);
  const [currentPage, setCurrentPage] = useState<MockupPage>("login");

  const [appState, setAppState] = useState<AppState>("login");
  const [accessToken, setAccessToken] = useState<string>("");
  const [analysisId, setAnalysisId] = useState<string>("");

  // 導頁：依是否已有上傳紀錄
  const routeByHistory = async (uid: string) => {
    const supabase = createClient();
    const { count, error } = await supabase
      .from("skill_analyses")
      .select("id", { count: "exact", head: true })
      .eq("user_id", uid)
      .not("resume_text", "is", null)
      .neq("resume_text", "");

    if (error) {
      console.error("[App] skill_analyses query error:", error);
      setAppState("upload");
      return;
    }
    setAppState((count ?? 0) > 0 ? "dashboard" : "upload");
  };

  useEffect(() => {
    if (USE_REAL_AUTH && !mockupMode) {
      const checkSession = async () => {
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

      checkSession();

      const supabase = createClient();
      const {
        data: { subscription },
      } = supabase.auth.onAuthStateChange(async (_event, session) => {
        if (session?.access_token && session?.user?.id) {
          setAccessToken(session.access_token);
          await routeByHistory(session.user.id);
        } else {
          setAppState("login");
        }
      });

      return () => subscription.unsubscribe();
    }
  }, [mockupMode]);

  // handlers
  const handleLoginSuccess = (token: string) => {
    setAccessToken(token);
    // 將跳轉交給 onAuthStateChange / routeByHistory
  };

  const handleAnalysisComplete = (id: string) => {
    setAnalysisId(id);
    setAppState("report");
  };

  const handleLogout = async () => {
    if (USE_REAL_AUTH && !mockupMode) {
      const supabase = createClient();
      await supabase.auth.signOut();
    }
    setAccessToken("");
    setAnalysisId("");
    setAppState("login");
  };

  // ===== Mockup mode =====
  if (mockupMode) {
    return (
      <div className="min-h-screen bg-slate-100">
        <div className="bg-white border-b border-slate-200 p-4">
          <div className="container mx-auto">
            <div className="flex items-center justify-between mb-2">
              <h1 className="text-slate-900 text-xl">SkillMiner - Figma Mockups</h1>
              <div className="flex items-center gap-3">
                <Label htmlFor="mode-toggle" className="text-sm text-slate-600">
                  Mockup Mode
                </Label>
                <Switch
                  id="mode-toggle"
                  checked={mockupMode}
                  onCheckedChange={setMockupMode}
                />
              </div>
            </div>
            <p className="text-slate-600 text-sm">Browse and customize each page design.</p>
          </div>
        </div>

        <Tabs
          value={currentPage}
          onValueChange={(v) => setCurrentPage(v as MockupPage)}
          className="w-full"
        >
          <div className="bg-white border-b border-slate-200 sticky top-0 z-10">
            <div className="container mx-auto px-4">
              <TabsList className="w-full justify-start h-auto p-0 bg-transparent overflow-x-auto">
                {[
                  "login",
                  "upload",
                  "report",
                  "dashboard",
                  "plan",
                  "coding",
                  "interview",
                  "profile",
                  "resume",
                ].map((k) => (
                  <TabsTrigger
                    key={k}
                    value={k}
                    className="rounded-none border-b-2 border-transparent data-[state=active]:border-purple-600 data-[state=active]:bg-transparent"
                  >
                    {
                      (
                        {
                          login: "Login",
                          upload: "Upload",
                          report: "Skill Report",
                          dashboard: "Dashboard",
                          plan: "Study Plan",
                          coding: "Coding Practice",
                          interview: "Interview Practice",
                          profile: "Profile",
                          resume: "Resume",
                        } as const
                      )[k as keyof typeof LABELS]
                    }
                  </TabsTrigger>
                ))}
              </TabsList>
            </div>
          </div>

          <TabsContent value="login" className="m-0">
            <LoginPageMockup onLoginSuccess={() => setCurrentPage("upload")} />
          </TabsContent>

          <TabsContent value="upload" className="m-0">
            <UploadPageMockup onAnalysisComplete={() => setCurrentPage("report")} />
          </TabsContent>

          <TabsContent value="report" className="m-0 bg-slate-50 min-h-screen">
            <SkillReportMockup onGenerateStudyPlan={() => setCurrentPage("dashboard")} />
          </TabsContent>

          <TabsContent value="dashboard" className="m-0">
            <MainDashboardMockup onNavigate={(p) => setCurrentPage(p as MockupPage)} />
            <PersistentChatbot />
          </TabsContent>

          <TabsContent value="plan" className="m-0">
            <StudyPlanMockup onNavigate={(p) => setCurrentPage(p as MockupPage)} />
            <PersistentChatbot />
          </TabsContent>

          <TabsContent value="coding" className="m-0">
            <CodingPracticeMockup onNavigate={(p) => setCurrentPage(p as MockupPage)} />
          </TabsContent>

          <TabsContent value="interview" className="m-0">
            <InterviewPracticeMockup onNavigate={(p) => setCurrentPage(p as MockupPage)} />
            <PersistentChatbot />
          </TabsContent>

          <TabsContent value="profile" className="m-0">
            <ProfileMockup onNavigate={(p) => setCurrentPage(p as MockupPage)} />
            <PersistentChatbot />
          </TabsContent>

          <TabsContent value="resume" className="m-0">
            <ResumeMockup onNavigate={(p) => setCurrentPage(p as MockupPage)} />
            <PersistentChatbot />
          </TabsContent>
        </Tabs>
      </div>
    );
  }

  // ===== Real app mode =====
  return (
    <BrowserRouter>
      {appState === "login" && <LoginPage onLoginSuccess={handleLoginSuccess} />}

      {appState === "upload" && (
        <UploadPage
          accessToken={accessToken}
          onAnalysisComplete={handleAnalysisComplete}
          onLogout={handleLogout}
        />
      )}

      {appState === "report" && (
        <SkillReportMockup onGenerateStudyPlan={() => setAppState("dashboard")} />
      )}

      {appState === "dashboard" && (
        <MainDashboardMockup
          onNavigate={(page) => {
            if (page === "report") setAppState("report");
            if (page === "coding") setAppState("dashboard");
          }}
        />
      )}

      {appState === "chat" && (
        <ChatbotPage
          accessToken={accessToken}
          analysisId={analysisId}
          onLogout={handleLogout}
        />
      )}

      {/* ✅ 除了 login 與 upload，其餘頁面都顯示浮窗 */}
      {appState !== "login" && appState !== "upload" && (
        <div className="fixed bottom-6 right-6 z-[9999]">
          <div className="pointer-events-auto">
            <PersistentChatbot />
          </div>
        </div>
      )}

      <Toaster />
    </BrowserRouter>
  );
}

// Helper label map for Tabs (kept outside component to avoid re-creation)
const LABELS = {
  login: "Login",
  upload: "Upload",
  report: "Skill Report",
  dashboard: "Dashboard",
  plan: "Study Plan",
  coding: "Coding Practice",
  interview: "Interview Practice",
  profile: "Profile",
  resume: "Resume",
} as const;
