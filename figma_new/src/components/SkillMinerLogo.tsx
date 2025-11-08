import { Brain } from "lucide-react";

interface SkillMinerLogoProps {
  className?: string;
  variant?: "default" | "compact";
}

export const SkillMinerLogo = ({ className = "", variant = "compact" }: SkillMinerLogoProps) => {
  if (variant === "default") {
    // Full login page version
    return (
      <div className={`flex flex-col items-center ${className}`}>
        <div className="bg-gradient-to-br from-purple-500 to-pink-500 p-3 rounded-2xl mb-4">
          <Brain className="w-10 h-10 text-white" />
        </div>
        <h1 className="text-white text-3xl mb-2">SkillMiner</h1>
        <p className="text-slate-400 text-center">
          AI-powered skill gap analysis and career recommendations
        </p>
      </div>
    );
  }

  // Compact version for headers
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div className="bg-gradient-to-br from-purple-500 to-pink-500 p-2 rounded-xl">
        <Brain className="w-6 h-6 text-white" />
      </div>
      <div>
        <h1 className="text-xl text-slate-900">
          SkillMiner
        </h1>
        <p className="text-xs text-slate-500">AI-Powered Career Builder</p>
      </div>
    </div>
  );
};
