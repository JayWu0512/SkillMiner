// src/App.tsx
import { useState } from "react";
import { LoginPage } from "./pages/LoginPage";
import { UploadPage } from "./pages/UploadPage";
import { ChatbotPage } from "./pages/ChatbotPage";
import { Toaster } from "./components/ui/sonner";

type AppState = "login" | "upload" | "chat";

// Read flags from .env (Vite exposes variables prefixed with VITE_)
const DEV_BYPASS_AUTH =
  import.meta.env.VITE_DEV_BYPASS_AUTH === "true";
// Optional: "login" | "upload" | "chat"
const DEV_START_STAGE =
  (import.meta.env.VITE_DEV_START_STAGE as AppState | undefined);

/** 
 * Resolve the initial app state from env flags.
 * If bypass is enabled and a start stage is provided, use it.
 * Otherwise:
 *   - bypass only => go to "upload"
 *   - normal => go to "login"
 */
function resolveInitialState(): AppState {
  if (DEV_BYPASS_AUTH) {
    return DEV_START_STAGE ?? "upload";
  }
  return "login";
}

/**
 * Provide a dev-friendly default access token.
 * Real auth flow will overwrite this via handleLoginSuccess.
 */
function resolveInitialToken(initialState: AppState): string {
  // If you need a token only when calling APIs, keep a mocked token in dev.
  return DEV_BYPASS_AUTH ? "dev-local-token" : "";
}

/**
 * Provide a dev-friendly analysisId if starting at "chat".
 * ChatbotPage typically requires analysisId to fetch conversation context.
 */
function resolveInitialAnalysisId(initialState: AppState): string {
  return initialState === "chat" ? "dev-analysis-id" : "";
}

export default function App() {
  // Initial state derived from env
  const initialState = resolveInitialState();

  // App FSM state
  const [appState, setAppState] = useState<AppState>(initialState);

  // Auth token (dev can skip real login)
  const [accessToken, setAccessToken] = useState<string>(
    resolveInitialToken(initialState)
  );

  // Analysis ID passed to ChatbotPage
  const [analysisId, setAnalysisId] = useState<string>(
    resolveInitialAnalysisId(initialState)
  );

  // Called by LoginPage after successful auth
  const handleLoginSuccess = (token: string) => {
    // Save token and move to upload page
    setAccessToken(token);
    setAppState("upload");
  };

  // Called by UploadPage after the backend creates an analysis
  const handleAnalysisComplete = (id: string) => {
    // Save analysis id and move to chat page
    setAnalysisId(id);
    setAppState("chat");
  };

  // Called by UploadPage/ChatbotPage logout button
  const handleLogout = () => {
    // Clear session state
    setAccessToken("");
    setAnalysisId("");

    // In dev, return to the configured start stage; otherwise go back to login
    setAppState(DEV_BYPASS_AUTH ? (DEV_START_STAGE ?? "upload") : "login");
  };

  return (
    <>
      {/* Render login only if not bypassing and we are on "login" */}
      {!DEV_BYPASS_AUTH && appState === "login" && (
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
