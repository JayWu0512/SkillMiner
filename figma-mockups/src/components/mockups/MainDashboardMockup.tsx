import { Calendar, Target, Flame, Trophy, BookOpen, Code, MessageSquare, User, FileText, ChevronRight } from 'lucide-react';
import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Checkbox } from '../ui/checkbox';
import { Header } from '../Header';

interface TodayTask {
  id: string;
  title: string;
  topic: string;
  estMinutes: number;
  xp: number;
  completed: boolean;
  type: 'study' | 'practice' | 'interview' | 'reflection';
}

const todayTasks: TodayTask[] = [
  { id: '1', title: 'SQL Joins Practice', topic: 'SQL', estMinutes: 120, xp: 50, completed: false, type: 'practice' },
  { id: '2', title: 'Applied Project: Merge CSVs', topic: 'Pandas', estMinutes: 150, xp: 70, completed: false, type: 'study' },
  { id: '3', title: 'Statistics II: Correlation', topic: 'Statistics', estMinutes: 120, xp: 50, completed: true, type: 'study' },
];

const weekCalendar = [
  { day: 'Mon', date: 4, tasks: 2, isToday: false },
  { day: 'Tue', date: 5, tasks: 3, isToday: false },
  { day: 'Wed', date: 6, tasks: 2, isToday: false },
  { day: 'Thu', date: 7, tasks: 3, isToday: false },
  { day: 'Fri', date: 8, tasks: 2, isToday: true },
  { day: 'Sat', date: 9, tasks: 1, isToday: false },
  { day: 'Sun', date: 10, tasks: 1, isToday: false },
];

type MockupPage = "login" | "upload" | "report" | "dashboard" | "plan" | "coding" | "interview" | "profile" | "resume";

interface MainDashboardMockupProps {
  onNavigate?: (page: MockupPage) => void;
}

export function MainDashboardMockup({ onNavigate }: MainDashboardMockupProps) {
  const totalXPToday = todayTasks.reduce((sum, task) => sum + task.xp, 0);
  const earnedXP = todayTasks.filter(t => t.completed).reduce((sum, task) => sum + task.xp, 0);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <Header 
        activePage="today" 
        onNavigate={(page) => {
          const pageMap: Record<string, MockupPage> = {
            'today': 'dashboard',
            'study-plan': 'plan',
            'coding-practice': 'coding',
            'interview-practice': 'interview',
            'profile': 'profile'
          };
          onNavigate?.(pageMap[page] || 'dashboard');
        }}
        onLogout={() => onNavigate?.('login')}
      />

      <div className="container mx-auto px-6 py-8">
        <div className="grid grid-cols-12 gap-6">
          {/* Left Sidebar - Quick Links */}
          <div className="col-span-3">
            <Card className="p-6">
              <h3 className="text-slate-900 mb-4">Quick Access</h3>
              <div className="space-y-2">
                <Button 
                  variant="ghost" 
                  className="w-full justify-start"
                  onClick={() => onNavigate?.("profile")}
                >
                  <User className="w-4 h-4 mr-2" />
                  Profile
                </Button>
                <Button 
                  variant="ghost" 
                  className="w-full justify-start"
                  onClick={() => onNavigate?.("resume")}
                >
                  <FileText className="w-4 h-4 mr-2" />
                  Resume
                </Button>
                <Button 
                  variant="ghost" 
                  className="w-full justify-start"
                  onClick={() => onNavigate?.("report")}
                >
                  <Target className="w-4 h-4 mr-2" />
                  Skill Report
                </Button>
              </div>
            </Card>
          </div>

          {/* Center - Today's Tasks */}
          <div className="col-span-6">
            <div className="mb-6">
              <h1 className="text-3xl text-slate-900 mb-2">Today, Friday Nov 8</h1>
              <p className="text-slate-600">You have {todayTasks.filter(t => !t.completed).length} tasks to complete today</p>
            </div>

            {/* Daily Tasks */}
            <div className="space-y-4">
              {todayTasks.map((task) => (
                <Card key={task.id} className={`p-6 ${task.completed ? 'bg-slate-50 opacity-75' : 'bg-white'}`}>
                  <div className="flex items-start gap-4">
                    <Checkbox checked={task.completed} className="mt-1" />
                    <div className="flex-1">
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <h3 className={`text-lg ${task.completed ? 'line-through text-slate-500' : 'text-slate-900'}`}>
                            {task.title}
                          </h3>
                          <p className="text-sm text-slate-600">{task.topic}</p>
                        </div>
                        <Badge className="bg-purple-100 text-purple-700">
                          {task.xp} XP
                        </Badge>
                      </div>
                      
                      <div className="flex items-center gap-4 text-sm text-slate-600">
                        <span>⏱️ {task.estMinutes} min</span>
                        <span>•</span>
                        <span className="capitalize">{task.type}</span>
                      </div>

                      {!task.completed && (
                        <div className="flex gap-2 mt-4">
                          <Button className="bg-purple-600 hover:bg-purple-700">
                            Start Task
                          </Button>
                          <Button variant="outline">
                            Reschedule
                          </Button>
                        </div>
                      )}
                    </div>
                  </div>
                </Card>
              ))}
            </div>

            {/* Completed Banner */}
            {todayTasks.every(t => t.completed) && (
              <Card className="p-6 mt-6 bg-gradient-to-r from-green-50 to-emerald-50 border-green-200">
                <div className="flex items-center gap-4">
                  <div className="bg-green-100 p-3 rounded-full">
                    <Trophy className="w-6 h-6 text-green-600" />
                  </div>
                  <div>
                    <h3 className="text-green-900">All done for today! 🎉</h3>
                    <p className="text-sm text-green-700">You've earned {totalXPToday} XP and maintained your streak!</p>
                  </div>
                </div>
              </Card>
            )}
          </div>

          {/* Right Sidebar - Insights */}
          <div className="col-span-3">
            {/* XP Progress */}
            <Card className="p-6 mb-6 bg-gradient-to-br from-purple-50 to-indigo-50 border-purple-200">
              <div className="flex items-center gap-3 mb-4">
                <div className="bg-purple-100 p-3 rounded-xl">
                  <Trophy className="w-6 h-6 text-purple-600" />
                </div>
                <div>
                  <h3 className="text-slate-900">Today's XP</h3>
                  <p className="text-2xl text-purple-600">{earnedXP} / {totalXPToday}</p>
                </div>
              </div>
              <Progress value={(earnedXP / totalXPToday) * 100} className="h-2" />
            </Card>

            {/* Streak */}
            <Card className="p-6 mb-6 bg-gradient-to-br from-orange-50 to-red-50 border-orange-200">
              <div className="flex items-center gap-3 mb-2">
                <div className="bg-orange-100 p-3 rounded-xl">
                  <Flame className="w-6 h-6 text-orange-600" />
                </div>
                <div>
                  <h3 className="text-slate-900">Current Streak</h3>
                  <p className="text-3xl text-orange-600">7 days</p>
                </div>
              </div>
              <p className="text-sm text-orange-700 mt-4">
                🛡️ You have 1 streak shield available
              </p>
            </Card>

            {/* Readiness */}
            <Card className="p-6 mb-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="bg-blue-100 p-3 rounded-xl">
                  <Target className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <h3 className="text-slate-900">Readiness</h3>
                  <p className="text-2xl text-blue-600">34%</p>
                </div>
              </div>
              <Progress value={34} className="h-2 mb-2" />
              <p className="text-sm text-slate-600">
                On track for Data Analyst role in 52 days
              </p>
            </Card>

            {/* Recent Badges */}
            <Card className="p-6">
              <h3 className="text-slate-900 mb-4">Recent Badges</h3>
              <div className="space-y-3">
                <div className="flex items-center gap-3 p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                  <div className="text-2xl">🏆</div>
                  <div>
                    <div className="text-sm text-slate-900">7-Day Streak</div>
                    <div className="text-xs text-slate-600">Earned today</div>
                  </div>
                </div>
                <div className="flex items-center gap-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
                  <div className="text-2xl">📚</div>
                  <div>
                    <div className="text-sm text-slate-900">SQL Starter</div>
                    <div className="text-xs text-slate-600">2 days ago</div>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
