import { useState, useEffect } from "react";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "./components/ui/tabs";
import { Switch } from "./components/ui/switch";
import { Label } from "./components/ui/label";

// Mockup components
import { LoginPageMockup } from "./components/mockups/LoginPageMockup";
import { UploadPageMockup } from "./components/mockups/UploadPageMockup";
import { ChatbotPageMockup } from "./components/mockups/ChatbotPageMockup";
import { SkillReportMockup } from "./components/mockups/SkillReportMockup";

// Real components (for production)
import { LoginPage } from "./components/LoginPage";
import { UploadPage } from "./components/UploadPage";
import { ChatbotPage } from "./components/ChatbotPage";
import { createClient } from "./utils/supabase/client";
import { Toaster } from "./components/ui/sonner";

// Set to true when ready to use real authentication
const USE_REAL_AUTH = false;

type AppState = "login" | "upload" | "chat";

export default function App() {
  const [mockupMode, setMockupMode] = useState(true);
  const [appState, setAppState] = useState<AppState>("login");
  const [accessToken, setAccessToken] = useState<string>("");
  const [analysisId, setAnalysisId] = useState<string>("");

  useEffect(() => {
    if (USE_REAL_AUTH && !mockupMode) {
      // Check for existing session on mount
      const checkSession = async () => {
        const supabase = createClient();
        const {
          data: { session },
        } = await supabase.auth.getSession();

        if (session?.access_token) {
          setAccessToken(session.access_token);
          setAppState("upload");
        }
      };

      checkSession();

      // Listen for auth state changes (OAuth redirect)
      const supabase = createClient();
      const {
        data: { subscription },
      } = supabase.auth.onAuthStateChange((_event, session) => {
        if (session?.access_token) {
          setAccessToken(session.access_token);
          setAppState("upload");
        }
      });

      return () => {
        subscription.unsubscribe();
      };
    }
  }, [mockupMode]);

  const handleLoginSuccess = (token: string) => {
    setAccessToken(token);
    setAppState("upload");
  };

  const handleAnalysisComplete = (id: string) => {
    setAnalysisId(id);
    setAppState("chat");
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

  // Mockup mode - show tabbed interface
  if (mockupMode) {
    return (
      <div className="min-h-screen bg-slate-100">
        <div className="bg-white border-b border-slate-200 p-4">
          <div className="container mx-auto">
            <div className="flex items-center justify-between mb-2">
              <h1 className="text-slate-900 text-xl">
                SkillMiner - Figma Mockups
              </h1>
              <div className="flex items-center gap-3">
                <Label
                  htmlFor="mode-toggle"
                  className="text-sm text-slate-600"
                >
                  Mockup Mode
                </Label>
                <Switch
                  id="mode-toggle"
                  checked={mockupMode}
                  onCheckedChange={setMockupMode}
                />
              </div>
            </div>
            <p className="text-slate-600 text-sm">
              Browse and customize each page design. Switch
              between tabs to view different screens.
            </p>
          </div>
        </div>

        <Tabs defaultValue="login" className="w-full">
          <div className="bg-white border-b border-slate-200 sticky top-0 z-10">
            <div className="container mx-auto px-4">
              <TabsList className="w-full justify-start h-auto p-0 bg-transparent">
                <TabsTrigger
                  value="login"
                  className="rounded-none border-b-2 border-transparent data-[state=active]:border-purple-600 data-[state=active]:bg-transparent"
                >
                  1. Login Page
                </TabsTrigger>
                <TabsTrigger
                  value="upload"
                  className="rounded-none border-b-2 border-transparent data-[state=active]:border-purple-600 data-[state=active]:bg-transparent"
                >
                  2. Upload Page
                </TabsTrigger>
                <TabsTrigger
                  value="chatbot"
                  className="rounded-none border-b-2 border-transparent data-[state=active]:border-purple-600 data-[state=active]:bg-transparent"
                >
                  3. Chatbot Interface
                </TabsTrigger>
                <TabsTrigger
                  value="report"
                  className="rounded-none border-b-2 border-transparent data-[state=active]:border-purple-600 data-[state=active]:bg-transparent"
                >
                  4. Skill Report
                </TabsTrigger>
              </TabsList>
            </div>
          </div>

          <TabsContent value="login" className="m-0">
            <LoginPageMockup />
          </TabsContent>

          <TabsContent value="upload" className="m-0">
            <UploadPageMockup />
          </TabsContent>

          <TabsContent value="chatbot" className="m-0">
            <ChatbotPageMockup />
          </TabsContent>

          <TabsContent
            value="report"
            className="m-0 bg-slate-50 min-h-screen"
          >
            <SkillReportMockup />
          </TabsContent>
        </Tabs>
      </div>
    );
  }

  // Real app mode - show actual authentication flow
  return (
    <>
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
      {appState === "chat" && (
        <ChatbotPage
          accessToken={accessToken}
          analysisId={analysisId}
          onLogout={handleLogout}
        />
      )}
      <Toaster />
    </>
  );
}