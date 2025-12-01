// src/components/pages/ProfilePage.tsx
import React, { useEffect, useState } from "react";
import {
  User,
  Clock,
  Target,
  Calendar,
  Sparkles,
  Save,
  Edit2,
} from "lucide-react";

import { Card } from "../ui/card";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { Textarea } from "../ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../ui/select";
import { Switch } from "../ui/switch";
import { Badge } from "../ui/badge";

import { createClient } from "../../utils/supabase/client";

/** DB row shape from `profiles` table */
type DBProfileRow = {
  id: string;
  full_name: string | null;
  timezone: string | null;
  location: string | null;

  target_role: string | null;
  current_role: string | null;
  motivation: string | null;
  target_job_date: string | null;

  weekly_hours: number | null;
  preferred_study_time: string | null;
  preferred_difficulty: string | null;

  learning_styles: any | null; // jsonb
  assistant_name: string | null;
  proactive_suggestions: boolean | null;
  daily_reminders: boolean | null;

  current_streak: number | null;
  total_xp: number | null;
  badges_earned: number | null;
  readiness: number | null;
};

type LearningStyles = {
  days: string[];
  modes: string[];
};

/** Frontend state shape */
type ProfileState = {
  id: string;
  full_name: string;
  timezone: string | null;
  location: string | null;

  target_role: string | null;
  current_role: string | null;
  motivation: string | null;
  target_job_date: string | null;

  weekly_hours: number | null;
  preferred_study_time: string | null;
  preferred_difficulty: string | null;

  learning_styles: LearningStyles | null;
  assistant_name: string | null;
  proactive_suggestions: boolean | null;
  daily_reminders: boolean | null;

  current_streak: number | null;
  total_xp: number | null;
  badges_earned: number | null;
  readiness: number | null;
};

export interface ProfileProps {
  user?: { id: string; email: string | null } | null;
  onNavigate?: (page: string) => void;
}

// Default Study Preferences
const DEFAULT_DAYS: string[] = ["Mon", "Tue", "Wed", "Thu", "Fri"];
const DEFAULT_MODES: string[] = [
  "Video Tutorials",
  "Interactive Coding",
  "Practice Projects",
];

const supabase = createClient();

export const Profile: React.FC<ProfileProps> = ({ user, onNavigate }) => {
  // First create a default profile from user, so the page has content initially and doesn't get stuck on Loading
  const [profile, setProfile] = useState<ProfileState | null>(() => {
    if (!user) return null;
    return {
      id: user.id,
      full_name: user.email ?? "",
      timezone: "pst",
      location: "",

      target_role: "",
      current_role: "",
      motivation: "",
      target_job_date: null,

      weekly_hours: 15,
      preferred_study_time: "evening",
      preferred_difficulty: "progressive",

      learning_styles: {
        days: DEFAULT_DAYS,
        modes: DEFAULT_MODES,
      },
      assistant_name: "Study Assistant",
      proactive_suggestions: true,
      daily_reminders: true,

      current_streak: 0,
      total_xp: 0,
      badges_earned: 0,
      readiness: 0,
    };
  });

  const [authEmail, setAuthEmail] = useState<string>(user?.email ?? "");
  const [loading, setLoading] = useState(false); // Only used to control internal state, no longer controls the entire page Loading screen
  const [saving, setSaving] = useState(false);

  // Update a single profile field
  const updateProfile = <K extends keyof ProfileState>(
    key: K,
    value: ProfileState[K]
  ) => {
    setProfile((prev) => (prev ? { ...prev, [key]: value } : prev));
  };

  // toggle available days
  const toggleDay = (day: string) => {
    setProfile((prev) => {
      if (!prev) return prev;
      const ls: LearningStyles = prev.learning_styles ?? {
        days: [],
        modes: [],
      };
      const set = new Set(ls.days);
      if (set.has(day)) set.delete(day);
      else set.add(day);
      return {
        ...prev,
        learning_styles: { ...ls, days: Array.from(set) },
      };
    });
  };

  // toggle learning styles
  const toggleMode = (mode: string) => {
    setProfile((prev) => {
      if (!prev) return prev;
      const ls: LearningStyles = prev.learning_styles ?? {
        days: [],
        modes: [],
      };
      const set = new Set(ls.modes);
      if (set.has(mode)) set.delete(mode);
      else set.add(mode);
      return {
        ...prev,
        learning_styles: { ...ls, modes: Array.from(set) },
      };
    });
  };

  useEffect(() => {
    let cancelled = false;

    const loadProfile = async () => {
      if (!user) {
        setProfile(null);
        setAuthEmail("");
        return;
      }

      setLoading(true);

      try {
        setAuthEmail(user.email ?? "");

        const { data, error } = await supabase
          .from("profiles")
          .select("*")
          .eq("id", user.id)
          .maybeSingle();

        if (cancelled) return;

        if (error) {
          console.error("Error loading profile", error);
        }

        const row = data as DBProfileRow | null;

        const rawLS = (row?.learning_styles ?? null) as any;
        const ls: LearningStyles = {
          days:
            Array.isArray(rawLS?.days) && rawLS.days.length > 0
              ? rawLS.days
              : DEFAULT_DAYS,
          modes:
            Array.isArray(rawLS?.modes) && rawLS.modes.length > 0
              ? rawLS.modes
              : DEFAULT_MODES,
        };

        // Has DB row
        if (row) {
          const uiProfile: ProfileState = {
            id: row.id,
            full_name: row.full_name ?? user.email ?? "",
            timezone: row.timezone ?? "pst",
            location: row.location ?? "",

            target_role: row.target_role,
            current_role: row.current_role,
            motivation: row.motivation,
            target_job_date: row.target_job_date,

            weekly_hours: row.weekly_hours ?? 15,
            preferred_study_time: row.preferred_study_time ?? "evening",
            preferred_difficulty: row.preferred_difficulty ?? "progressive",

            learning_styles: ls,
            assistant_name: row.assistant_name ?? "Study Assistant",
            proactive_suggestions: row.proactive_suggestions ?? true,
            daily_reminders: row.daily_reminders ?? true,

            current_streak: row.current_streak ?? 0,
            total_xp: row.total_xp ?? 0,
            badges_earned: row.badges_earned ?? 0,
            readiness: row.readiness ?? 0,
          };

          setProfile(uiProfile);
        } else {
          // No DB row, keep the initial default (the one from useState above)
          setProfile((prev) => {
            if (prev) return prev;
            return {
              id: user.id,
              full_name: user.email ?? "",
              timezone: "pst",
              location: "",

              target_role: "",
              current_role: "",
              motivation: "",
              target_job_date: null,

              weekly_hours: 15,
              preferred_study_time: "evening",
              preferred_difficulty: "progressive",

              learning_styles: {
                days: DEFAULT_DAYS,
                modes: DEFAULT_MODES,
              },
              assistant_name: "Study Assistant",
              proactive_suggestions: true,
              daily_reminders: true,

              current_streak: 0,
              total_xp: 0,
              badges_earned: 0,
              readiness: 0,
            };
          });
        }
      } catch (e) {
        console.error("loadProfile failed:", e);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    // Only depend on user here, no longer depend on supabase (already made a single instance above)
    loadProfile();

    return () => {
      cancelled = true;
    };
  }, [user]);

  const handleSave = async () => {
    if (!profile) return;
    setSaving(true);

    const { error } = await supabase
      .from("profiles")
      .upsert(profile as any); // Directly upsert the entire profile

    if (error) {
      console.error("Error saving profile:", error);
    }

    setSaving(false);
  };

  // If there's no user at all (theoretically your app won't render this page before login)
  if (!user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center">
        <div className="text-slate-600 text-lg">
          Please log in to view your profile.
        </div>
      </div>
    );
  }

  if (!profile) {
    // Unexpected error case, show a message
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center">
        <div className="text-slate-600 text-lg">
          Failed to load profile. Please refresh or try again.
        </div>
      </div>
    );
  }

  const selectedDays = profile.learning_styles?.days ?? DEFAULT_DAYS;
  const selectedModes = profile.learning_styles?.modes ?? DEFAULT_MODES;

  const initials =
    profile.full_name
      .split(" ")
      .filter((s) => s.length > 0)
      .map((s) => s[0])
      .join("")
      .toUpperCase() || "U";

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Page Header */}
      <div className="bg-white border-b border-slate-200 px-6 py-6">
        <div className="container mx-auto">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl text-slate-900 mb-2">Profile Settings</h1>
              <p className="text-slate-600">
                Manage your account and study preferences
                {loading && (
                  <span className="ml-2 text-xs text-slate-400">
                    (Refreshing...)
                  </span>
                )}
              </p>
            </div>
            <div className="flex gap-3">
              {onNavigate && (
                <Button
                  variant="outline"
                  onClick={() => onNavigate("dashboard")}
                >
                  Back to Dashboard
                </Button>
              )}
              <Button
                className="bg-purple-600 hover:bg-purple-700"
                onClick={handleSave}
                disabled={saving}
              >
                <Save className="w-4 h-4 mr-2" />
                {saving ? "Saving..." : "Save Changes"}
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-6 py-8">
        <div className="grid grid-cols-12 gap-6">
          {/* Main Content */}
          <div className="col-span-8">
            {/* Basic Info */}
            <Card className="p-6 mb-6">
              <div className="flex items-center gap-3 mb-6">
                <div className="bg-purple-100 p-3 rounded-xl">
                  <User className="w-6 h-6 text-purple-600" />
                </div>
                <h2 className="text-xl text-slate-900">Basic Information</h2>
              </div>

              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="name">Full Name</Label>
                    <Input
                      id="name"
                      value={profile.full_name}
                      onChange={(e) =>
                        updateProfile("full_name", e.target.value)
                      }
                    />
                  </div>
                  <div>
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      type="email"
                      value={authEmail}
                      disabled
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="timezone">Timezone</Label>
                    <Select
                      value={profile.timezone ?? "pst"}
                      onValueChange={(v) => updateProfile("timezone", v)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="pst">Pacific Time (PST)</SelectItem>
                        <SelectItem value="mst">
                          Mountain Time (MST)
                        </SelectItem>
                        <SelectItem value="cst">
                          Central Time (CST)
                        </SelectItem>
                        <SelectItem value="est">
                          Eastern Time (EST)
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor="location">Location</Label>
                    <Input
                      id="location"
                      value={profile.location ?? ""}
                      onChange={(e) =>
                        updateProfile("location", e.target.value)
                      }
                    />
                  </div>
                </div>
              </div>
            </Card>

            {/* Career Goals */}
            <Card className="p-6 mb-6">
              <div className="flex items-center gap-3 mb-6">
                <div className="bg-blue-100 p-3 rounded-xl">
                  <Target className="w-6 h-6 text-blue-600" />
                </div>
                <h2 className="text-xl text-slate-900">Career Goals</h2>
              </div>

              <div className="space-y-4">
                <div>
                  <Label htmlFor="target-role">Target Role</Label>
                  <Input
                    id="target-role"
                    value={profile.target_role ?? ""}
                    onChange={(e) =>
                      updateProfile("target_role", e.target.value)
                    }
                  />
                </div>

                <div>
                  <Label htmlFor="current-role">
                    Current Role/Background
                  </Label>
                  <Input
                    id="current-role"
                    value={profile.current_role ?? ""}
                    onChange={(e) =>
                      updateProfile("current_role", e.target.value)
                    }
                  />
                </div>

                <div>
                  <Label htmlFor="motivation">
                    What's your motivation for this transition?
                  </Label>
                  <Textarea
                    id="motivation"
                    className="min-h-[100px]"
                    value={profile.motivation ?? ""}
                    onChange={(e) =>
                      updateProfile("motivation", e.target.value)
                    }
                  />
                </div>

                <div>
                  <Label htmlFor="target-date">Target Job Search Date</Label>
                  <Input
                    id="target-date"
                    type="date"
                    value={profile.target_job_date ?? ""}
                    onChange={(e) =>
                      updateProfile("target_job_date", e.target.value)
                    }
                  />
                </div>
              </div>
            </Card>

            {/* Study Preferences */}
            <Card className="p-6 mb-6">
              <div className="flex items-center gap-3 mb-6">
                <div className="bg-green-100 p-3 rounded-xl">
                  <Clock className="w-6 h-6 text-green-600" />
                </div>
                <h2 className="text-xl text-slate-900">Study Preferences</h2>
              </div>

              <div className="space-y-4">
                <div>
                  <Label htmlFor="weekly-hours">Weekly Study Hours</Label>
                  <Select
                    value={(profile.weekly_hours ?? 15).toString()}
                    onValueChange={(v) =>
                      updateProfile("weekly_hours", parseInt(v, 10))
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="5">
                        5-10 hours/week (Light)
                      </SelectItem>
                      <SelectItem value="15">
                        15-20 hours/week (Standard)
                      </SelectItem>
                      <SelectItem value="25">
                        25-30 hours/week (Intensive)
                      </SelectItem>
                      <SelectItem value="35">
                        35+ hours/week (Full-time)
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label>Available Days</Label>
                  <div className="grid grid-cols-7 gap-2 mt-2">
                    {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map(
                      (day) => {
                        const active = selectedDays.includes(day);
                        return (
                          <div
                            key={day}
                            className="flex items-center justify-center"
                          >
                            <Button
                              type="button"
                              variant={active ? "default" : "outline"}
                              className={active ? "bg-purple-600" : ""}
                              size="sm"
                              onClick={() => toggleDay(day)}
                            >
                              {day}
                            </Button>
                          </div>
                        );
                      }
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="pref-time">Preferred Study Time</Label>
                    <Select
                      value={profile.preferred_study_time ?? "evening"}
                      onValueChange={(v) =>
                        updateProfile("preferred_study_time", v)
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="morning">
                          Morning (6am-12pm)
                        </SelectItem>
                        <SelectItem value="afternoon">
                          Afternoon (12pm-6pm)
                        </SelectItem>
                        <SelectItem value="evening">
                          Evening (6pm-12am)
                        </SelectItem>
                        <SelectItem value="flexible">Flexible</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor="difficulty">Preferred Difficulty</Label>
                    <Select
                      value={profile.preferred_difficulty ?? "progressive"}
                      onValueChange={(v) =>
                        updateProfile("preferred_difficulty", v)
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="gentle">
                          Gentle (Slower pace)
                        </SelectItem>
                        <SelectItem value="progressive">
                          Progressive (Standard)
                        </SelectItem>
                        <SelectItem value="challenging">
                          Challenging (Fast pace)
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div>
                  <Label>Learning Style Preferences</Label>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {[
                      "Video Tutorials",
                      "Interactive Coding",
                      "Reading Materials",
                      "Practice Projects",
                      "Podcasts",
                    ].map((mode) => {
                      const active = selectedModes.includes(mode);
                      return (
                        <Badge
                          key={mode}
                          variant="outline"
                          className={
                            "cursor-pointer" +
                            (active
                              ? " bg-purple-50 border-purple-300"
                              : "")
                          }
                          onClick={() => toggleMode(mode)}
                        >
                          {active ? "✓ " : ""}
                          {mode}
                        </Badge>
                      );
                    })}
                  </div>
                </div>
              </div>
            </Card>

            {/* Assistant Settings */}
            <Card className="p-6">
              <div className="flex items-center gap-3 mb-6">
                <div className="bg-indigo-100 p-3 rounded-xl">
                  <Sparkles className="w-6 h-6 text-indigo-600" />
                </div>
                <h2 className="text-xl text-slate-900">Study Assistant</h2>
              </div>

              <div className="space-y-4">
                <div>
                  <Label htmlFor="assistant-name">Assistant Name</Label>
                  <Input
                    id="assistant-name"
                    value={profile.assistant_name ?? ""}
                    onChange={(e) =>
                      updateProfile("assistant_name", e.target.value)
                    }
                  />
                  <p className="text-sm text-slate-500 mt-1">
                    Personalize your AI helper
                  </p>
                </div>

                <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
                  <div>
                    <div className="text-slate-900 mb-1">
                      Enable proactive suggestions
                    </div>
                    <div className="text-sm text-slate-600">
                      Let your assistant suggest adjustments to your study plan
                    </div>
                  </div>
                  <Switch
                    checked={!!profile.proactive_suggestions}
                    onCheckedChange={(checked) =>
                      updateProfile("proactive_suggestions", checked)
                    }
                  />
                </div>

                <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
                  <div>
                    <div className="text-slate-900 mb-1">Daily reminders</div>
                    <div className="text-sm text-slate-600">
                      Get notifications for scheduled tasks
                    </div>
                  </div>
                  <Switch
                    checked={!!profile.daily_reminders}
                    onCheckedChange={(checked) =>
                      updateProfile("daily_reminders", checked)
                    }
                  />
                </div>
              </div>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="col-span-4">
            {/* Profile Summary */}
            <Card className="p-6 mb-6 bg-gradient-to-br from-purple-50 to-indigo-50 border-purple-200">
              <div className="text-center mb-4">
                <div className="w-24 h-24 bg-gradient-to-br from-purple-600 to-indigo-600 rounded-full mx-auto mb-4 flex items-center justify-center text-white text-3xl">
                  {initials}
                </div>
                <h3 className="text-xl text-slate-900 mb-1">
                  {profile.full_name || authEmail}
                </h3>
                <p className="text-sm text-slate-600">Member</p>
              </div>
            </Card>

            {/* Quick Actions */}
            <Card className="p-6 mb-6">
              <h3 className="text-slate-900 mb-4">Quick Actions</h3>
              <div className="space-y-2">
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => onNavigate?.("resume")}
                >
                  <Edit2 className="w-4 h-4 mr-2" />
                  Update Resume
                </Button>
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => onNavigate?.("report")}
                >
                  <Target className="w-4 h-4 mr-2" />
                  View Skill Report
                </Button>
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => onNavigate?.("report")}
                >
                  <Calendar className="w-4 h-4 mr-2" />
                  Regenerate Plan
                </Button>
              </div>
            </Card>

            {/* Danger Zone */}
            <Card className="p-6 border-red-200">
              <h3 className="text-red-900 mb-4">Danger Zone</h3>
              <div className="space-y-2">
                <Button
                  variant="outline"
                  className="w-full justify-start text-red-600 border-red-200 hover:bg-red-50"
                >
                  Reset Study Plan
                </Button>
                <Button
                  variant="outline"
                  className="w-full justify-start text-red-600 border-red-200 hover:bg-red-50"
                >
                  Delete Account
                </Button>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Profile;
