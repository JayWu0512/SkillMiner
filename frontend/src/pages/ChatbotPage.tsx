// src/pages/ChatbotPage.tsx
import { useEffect, useRef, useState } from "react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Brain, FileText, LogOut, Menu, MessageSquare, Send } from "lucide-react";
import { createClient } from "../utils/supabase/client";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

interface ChatbotPageProps {
  accessToken: string;
  analysisId: string;
  onLogout: () => void;
}

const API_BASE = import.meta.env.VITE_API_BASE as string;
const DEV_TOKEN = "dev-local-token";

// Helper to build request headers
function buildHeaders(accessToken: string, json = false) {
  const headers: Record<string, string> = {};
  if (json) headers["Content-Type"] = "application/json";
  if (accessToken && accessToken !== DEV_TOKEN) {
    headers["Authorization"] = `Bearer ${accessToken}`;
  }
  return headers;
}

export function ChatbotPage({ accessToken, analysisId, onLogout }: ChatbotPageProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [showReport, setShowReport] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // --- Handle user logout ---
  const handleLogout = async () => {
    setIsLoggingOut(true);
    try {
      const supabase = createClient();
      await supabase.auth.signOut();
      onLogout();
    } catch (e: any) {
      console.error("Logout error:", e);
    } finally {
      setIsLoggingOut(false);
    }
  };

  // --- Load analysis summary when analysisId changes ---
  useEffect(() => {
    const loadAnalysis = async () => {
      try {
        const res = await fetch(`${API_BASE}/analysis/${analysisId}`, {
          headers: buildHeaders(accessToken, false),
          credentials: "include",
        });
        if (res.ok) {
          const data = await res.json();
          setMessages([
            {
              id: "welcome",
              role: "assistant",
              content: `Hello! I've analyzed your resume. Match score: **${data.matchScore}%**. Missing skills: ${data.missingSkills}.`,
              timestamp: new Date(),
            },
          ]);
        }
      } catch (e) {
        console.error("Load analysis error:", e);
      }
    };
    if (analysisId) loadAnalysis();
  }, [analysisId, accessToken]);

  // --- Auto-scroll to bottom on new message ---
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // --- Handle user send message ---
  const handleSend = async () => {
    if (!input.trim() || isSending) return;

    const userMessage: Message = {
      id: `${Date.now()}`,
      role: "user",
      content: input,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsSending(true);
    setInput("");

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: buildHeaders(accessToken, true),
        credentials: "include",
        body: JSON.stringify({ analysisId, message: userMessage.content }),
      });

      if (!res.ok) throw new Error("Chat request failed");

      const data = await res.json();
      const botMessage: Message = {
        id: `${Date.now() + 1}`,
        role: "assistant",
        content: data.response,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, botMessage]);
    } catch (e) {
      console.error("Chat error:", e);
      setMessages((prev) => [
        ...prev,
        {
          id: `${Date.now() + 2}`,
          role: "assistant",
          content: "Sorry, something went wrong. Please try again.",
          timestamp: new Date(),
        },
      ]);
    } finally {
      setIsSending(false);
    }
  };

  // --- Allow Enter key to send ---
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex h-screen bg-slate-50">
      {/* --- Sidebar --- */}
      <div
        className={`${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        } fixed lg:relative lg:translate-x-0 z-30 w-72 bg-white border-r border-slate-200 h-full transition-transform duration-300`}
      >
        <div className="p-4 border-b border-slate-200">
          <div className="flex items-center gap-2 mb-4">
            <div className="bg-gradient-to-br from-purple-500 to-pink-500 p-2 rounded-lg">
              <Brain className="w-5 h-5 text-white" />
            </div>
            <h2 className="text-slate-900">SkillMiner</h2>
          </div>

          <Button
            onClick={() => setShowReport(!showReport)}
            className="w-full justify-start gap-2 bg-purple-50 text-purple-700 hover:bg-purple-100"
          >
            <FileText className="w-4 h-4" />
            {showReport ? "Back to Chat" : "View Full Report"}
          </Button>
        </div>

        {/* --- Logout Button --- */}
        <div className="absolute bottom-4 left-4 right-4">
          <Button
            variant="outline"
            onClick={handleLogout}
            disabled={isLoggingOut}
            className="w-full gap-2"
          >
            {isLoggingOut ? (
              <>
                <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                Logging out...
              </>
            ) : (
              <>
                <LogOut className="w-4 h-4" />
                Logout
              </>
            )}
          </Button>
        </div>
      </div>

      {/* --- Main Chat Area --- */}
      <div className="flex-1 flex flex-col">
        <div className="bg-white border-b border-slate-200 px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="lg:hidden"
            >
              <Menu className="w-5 h-5" />
            </Button>
            <MessageSquare className="w-5 h-5 text-purple-500" />
            <h1 className="text-slate-900">Career Assistant</h1>
          </div>
        </div>

        {/* --- Chat View --- */}
        {!showReport ? (
          <>
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((m) => (
                <div
                  key={m.id}
                  className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`max-w-2xl rounded-2xl px-4 py-3 ${
                      m.role === "user"
                        ? "bg-purple-600 text-white"
                        : "bg-white border border-slate-200 text-slate-900"
                    }`}
                  >
                    <div
                      className="whitespace-pre-wrap"
                      dangerouslySetInnerHTML={{
                        __html: m.content.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>"),
                      }}
                    />
                  </div>
                </div>
              ))}

              {/* Typing dots animation */}
              {isSending && (
                <div className="flex justify-start">
                  <div className="bg-white border border-slate-200 rounded-2xl px-4 py-3">
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" />
                      <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce delay-100" />
                      <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce delay-200" />
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* --- Input Bar --- */}
            <div className="bg-white border-t border-slate-200 p-4">
              <div className="max-w-4xl mx-auto flex gap-2">
                <Input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask me anything about your skills, career path, or learning recommendations..."
                  className="flex-1"
                  disabled={isSending}
                />
                <Button
                  onClick={handleSend}
                  disabled={!input.trim() || isSending}
                  className="bg-purple-600 hover:bg-purple-700"
                >
                  <Send className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </>
        ) : (
          // --- Placeholder for report view ---
          <div className="flex-1 overflow-y-auto p-6 text-slate-600">
            <p>Still updating!</p>
          </div>
        )}
      </div>
    </div>
  );
}
