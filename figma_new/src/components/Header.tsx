// src/components/Header.tsx
import { Brain, Calendar, Code, ChevronDown, User, LogOut } from "lucide-react";
import { Button } from "./ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu";

interface HeaderProps {
  activePage?: "today" | "study-plan" | "practice" | "profile" | "resume";
  onNavigate?: (page: string) => void;
  onLogout?: () => void;
}

export const Header = ({ activePage, onNavigate, onLogout }: HeaderProps) => {
  return (
    <header className="bg-white border-b border-slate-200 px-6 py-3">
      <div className="flex items-center justify-between">
        {/* Left side - Logo and Navigation */}
        <div className="flex items-center gap-8">
          <div className="flex items-center gap-2">
            <div className="bg-gradient-to-br from-purple-500 to-pink-500 p-2 rounded-xl">
              <Brain className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl text-slate-900 font-semibold">SkillMiner</h1>
              <p className="text-xs text-slate-500">AI-Powered Career Builder</p>
            </div>
          </div>

          <nav className="flex items-center gap-2">
            <Button
              variant="ghost"
              className={`gap-2 ${activePage === "today" ? "text-purple-600 bg-purple-50" : "text-slate-600 hover:text-slate-900"}`}
              onClick={() => onNavigate?.("today")}
            >
              <div className="w-5 h-5 rounded-full border-2 border-current flex items-center justify-center">
                <div className="w-1.5 h-1.5 rounded-full bg-current" />
              </div>
              Today
            </Button>

            <Button
              variant="ghost"
              className={`gap-2 ${activePage === "study-plan" ? "text-purple-600 bg-purple-50" : "text-slate-600 hover:text-slate-900"}`}
              onClick={() => onNavigate?.("study-plan")}
            >
              <Calendar className="w-5 h-5" />
              Study Plan
            </Button>

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  className={`gap-2 ${activePage === "practice" ? "text-purple-600 bg-purple-50" : "text-slate-600 hover:text-slate-900"}`}
                >
                  <Code className="w-5 h-5" />
                  Practice
                  <ChevronDown className="w-4 h-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start">
                <DropdownMenuItem onClick={() => onNavigate?.("coding-practice")}>
                  Coding Practice
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => onNavigate?.("interview-practice")}>
                  Interview Practice
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </nav>
        </div>

        {/* Right side - User actions */}
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            className="text-slate-600 hover:text-slate-900"
            onClick={() => onNavigate?.("profile")}
          >
            <User className="w-5 h-5" />
          </Button>

          {/* 🔴 Logout */}
          <Button
            variant="ghost"
            size="icon"
            className="text-red-600 hover:text-red-700"
            onClick={() => onLogout?.()} 
            title="Logout"
          >
            <LogOut className="w-5 h-5" />
          </Button>
        </div>
      </div>
    </header>
  );
};
