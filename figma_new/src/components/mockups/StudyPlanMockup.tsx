import { useState } from 'react';
import { Calendar, Download, RefreshCw, ChevronLeft, ChevronRight, Target, Clock, Trophy } from 'lucide-react';
import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '../ui/dialog';

interface DailyTask {
  date: string;
  dayOfWeek: string;
  theme: string;
  task: string;
  resources: string;
  estTime: string;
  xp: number;
  completed?: boolean;
}

// Generate dates starting from Nov 11, 2024 (Monday)
const generateWeekData = (weekOffset: number): DailyTask[] => {
  const startDate = new Date(2024, 10, 11); // Nov 11, 2024
  startDate.setDate(startDate.getDate() + (weekOffset * 7));
  
  const weekData = [
    { theme: 'Orientation', task: 'Review Skill Report + Install Jupyter/VSCode', resources: 'SkillMiner Docs', estTime: '1h', xp: 20 },
    { theme: 'Python Basics', task: 'Variables, data types, loops', resources: 'Kaggle Python 101', estTime: '2h', xp: 40 },
    { theme: 'Python Practice', task: '10 Easy LeetCode Python problems', resources: 'LeetCode', estTime: '2h', xp: 60 },
    { theme: 'Statistics', task: 'Mean, median, mode, standard deviation', resources: 'Khan Academy', estTime: '2h', xp: 50 },
    { theme: 'SQL Basics', task: 'SELECT, WHERE, ORDER BY', resources: 'Mode SQL Tutorial', estTime: '2h', xp: 50 },
    { theme: 'Weekend Challenge', task: 'Build a small CSV data summary (Pandas)', resources: 'SkillMiner Notebook', estTime: '3h', xp: 70 },
    { theme: 'Reflection', task: 'Review week + write summary in chatbot', resources: 'Chatbot Prompt', estTime: '1h', xp: 30 },
  ];

  const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  
  return weekData.map((data, index) => {
    const date = new Date(startDate);
    date.setDate(date.getDate() + index);
    
    return {
      date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      dayOfWeek: days[index],
      ...data,
      completed: weekOffset === 0 && index < 3 // Mark first 3 days of current week as completed
    };
  });
};

// Generate all study plan tasks (60 days)
const generateAllTasks = (): (DailyTask & { fullDate: Date })[] => {
  const startDate = new Date(2024, 10, 11); // Nov 11, 2024
  const allTasks = [];
  
  const taskTemplates = [
    { theme: 'Orientation', task: 'Review Skill Report + Install Jupyter/VSCode', resources: 'SkillMiner Docs', estTime: '1h', xp: 20, color: 'purple' },
    { theme: 'Python Basics', task: 'Variables, data types, loops', resources: 'Kaggle Python 101', estTime: '2h', xp: 40, color: 'blue' },
    { theme: 'Python Practice', task: '10 Easy LeetCode Python problems', resources: 'LeetCode', estTime: '2h', xp: 60, color: 'blue' },
    { theme: 'Statistics', task: 'Mean, median, mode, standard deviation', resources: 'Khan Academy', estTime: '2h', xp: 50, color: 'green' },
    { theme: 'SQL Basics', task: 'SELECT, WHERE, ORDER BY', resources: 'Mode SQL Tutorial', estTime: '2h', xp: 50, color: 'orange' },
    { theme: 'Weekend Challenge', task: 'Build a small CSV data summary (Pandas)', resources: 'SkillMiner Notebook', estTime: '3h', xp: 70, color: 'purple' },
    { theme: 'Reflection', task: 'Review week + write summary in chatbot', resources: 'Chatbot Prompt', estTime: '1h', xp: 30, color: 'gray' },
  ];

  const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  
  for (let i = 0; i < 60; i++) {
    const currentDate = new Date(startDate);
    currentDate.setDate(startDate.getDate() + i);
    
    const templateIndex = i % 7;
    const task = taskTemplates[templateIndex];
    
    allTasks.push({
      fullDate: currentDate,
      date: currentDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      dayOfWeek: days[currentDate.getDay() === 0 ? 6 : currentDate.getDay() - 1],
      ...task,
      completed: i < 3 // First 3 days completed
    });
  }
  
  return allTasks;
};

// Generate month calendar data
const generateMonthData = (monthOffset: number) => {
  const baseDate = new Date(2024, 10, 1); // Nov 1, 2024
  baseDate.setMonth(baseDate.getMonth() + monthOffset);
  
  const year = baseDate.getFullYear();
  const month = baseDate.getMonth();
  
  // Get first day of month and last day of month
  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);
  
  // Get day of week for first day (0 = Sunday, 1 = Monday, etc.)
  const firstDayOfWeek = firstDay.getDay();
  
  // Calculate how many days from previous month to show
  const daysFromPrevMonth = firstDayOfWeek;
  
  // Calculate start date (including prev month overflow)
  const startDate = new Date(firstDay);
  startDate.setDate(startDate.getDate() - daysFromPrevMonth);
  
  // Generate 42 days (6 weeks) for calendar grid
  const calendarDays = [];
  for (let i = 0; i < 42; i++) {
    const currentDate = new Date(startDate);
    currentDate.setDate(startDate.getDate() + i);
    
    calendarDays.push({
      date: currentDate,
      dayNumber: currentDate.getDate(),
      isCurrentMonth: currentDate.getMonth() === month,
      isToday: 
        currentDate.getDate() === new Date(2024, 10, 11).getDate() &&
        currentDate.getMonth() === new Date(2024, 10, 11).getMonth() &&
        currentDate.getFullYear() === new Date(2024, 10, 11).getFullYear()
    });
  }
  
  return {
    year,
    month,
    monthName: firstDay.toLocaleDateString('en-US', { month: 'long', year: 'numeric' }),
    calendarDays
  };
};

export function StudyPlanMockup() {
  const [viewMode, setViewMode] = useState<'calendar' | 'list' | 'month'>('calendar');
  const [currentWeek, setCurrentWeek] = useState(0);
  const [currentMonthOffset, setCurrentMonthOffset] = useState(0);

  const totalWeeks = 8; // 2 months = ~8 weeks
  const currentWeekData = generateWeekData(currentWeek);
  const startDate = currentWeekData[0].date;
  const endDate = currentWeekData[6].date;
  
  // Month view data
  const monthData = generateMonthData(currentMonthOffset);
  const allTasks = generateAllTasks();
  
  // Get tasks for a specific date
  const getTasksForDate = (date: Date) => {
    return allTasks.filter(task => 
      task.fullDate.getDate() === date.getDate() &&
      task.fullDate.getMonth() === date.getMonth() &&
      task.fullDate.getFullYear() === date.getFullYear()
    );
  };

  const weeksPhases = [
    { range: [0, 1], label: 'Foundations', color: 'purple' },
    { range: [2, 3], label: 'Visualization & EDA', color: 'blue' },
    { range: [4, 5], label: 'Advanced Topics', color: 'orange' },
    { range: [6, 7], label: 'Portfolio & Interview', color: 'green' },
  ];

  const currentPhase = weeksPhases.find(phase => 
    currentWeek >= phase.range[0] && currentWeek <= phase.range[1]
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <header className="bg-white border-b border-slate-200">
        <div className="container mx-auto px-6 py-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl text-slate-900 mb-2">Study Plan</h1>
              <p className="text-slate-600">Data Analyst Role • 60-day timeline • Target: Feb 10, 2025</p>
            </div>
            <div className="flex gap-3">
              <Dialog>
                <DialogTrigger asChild>
                  <Button className="bg-green-600 hover:bg-green-700">
                    <Download className="w-4 h-4 mr-2" />
                    Export to Calendar
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Export Your Study Plan</DialogTitle>
                    <DialogDescription>
                      Choose how you'd like to sync your study plan with your calendar
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 mt-4">
                    <Card className="p-4 border-2 border-purple-200 hover:border-purple-400 cursor-pointer">
                      <div className="flex items-start gap-3">
                        <div className="bg-purple-100 p-2 rounded">
                          <Calendar className="w-5 h-5 text-purple-600" />
                        </div>
                        <div>
                          <h3 className="text-slate-900 mb-1">Google Calendar</h3>
                          <p className="text-sm text-slate-600">
                            Real-time sync with automatic updates (requires OAuth)
                          </p>
                        </div>
                      </div>
                    </Card>
                    <Card className="p-4 border-2 border-blue-200 hover:border-blue-400 cursor-pointer">
                      <div className="flex items-start gap-3">
                        <div className="bg-blue-100 p-2 rounded">
                          <Calendar className="w-5 h-5 text-blue-600" />
                        </div>
                        <div>
                          <h3 className="text-slate-900 mb-1">Outlook Calendar</h3>
                          <p className="text-sm text-slate-600">
                            Real-time sync with automatic updates (requires OAuth)
                          </p>
                        </div>
                      </div>
                    </Card>
                    <Card className="p-4 border-2 border-slate-200 hover:border-slate-400 cursor-pointer">
                      <div className="flex items-start gap-3">
                        <div className="bg-slate-100 p-2 rounded">
                          <Download className="w-5 h-5 text-slate-600" />
                        </div>
                        <div>
                          <h3 className="text-slate-900 mb-1">ICS File (One-time)</h3>
                          <p className="text-sm text-slate-600">
                            Download .ics file to import into any calendar app
                          </p>
                        </div>
                      </div>
                    </Card>
                  </div>
                </DialogContent>
              </Dialog>
              <Button variant="outline">
                <RefreshCw className="w-4 h-4 mr-2" />
                Regenerate Plan
              </Button>
            </div>
          </div>

          {/* Stats Row */}
          <div className="grid grid-cols-4 gap-4">
            <Card className="p-4">
              <div className="flex items-center gap-3">
                <div className="bg-purple-100 p-2 rounded">
                  <Target className="w-5 h-5 text-purple-600" />
                </div>
                <div>
                  <div className="text-sm text-slate-600">Progress</div>
                  <div className="text-xl text-slate-900">34%</div>
                </div>
              </div>
            </Card>
            <Card className="p-4">
              <div className="flex items-center gap-3">
                <div className="bg-blue-100 p-2 rounded">
                  <Clock className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <div className="text-sm text-slate-600">Days Remaining</div>
                  <div className="text-xl text-slate-900">52</div>
                </div>
              </div>
            </Card>
            <Card className="p-4">
              <div className="flex items-center gap-3">
                <div className="bg-green-100 p-2 rounded">
                  <Trophy className="w-5 h-5 text-green-600" />
                </div>
                <div>
                  <div className="text-sm text-slate-600">Total XP</div>
                  <div className="text-xl text-slate-900">220 / 650</div>
                </div>
              </div>
            </Card>
            <Card className="p-4">
              <div className="flex items-center gap-3">
                <div className="bg-orange-100 p-2 rounded">
                  <Calendar className="w-5 h-5 text-orange-600" />
                </div>
                <div>
                  <div className="text-sm text-slate-600">Current Week</div>
                  <div className="text-xl text-slate-900">{currentWeek + 1} / {totalWeeks}</div>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="container mx-auto px-6 py-8">
        <Tabs value={viewMode} onValueChange={(v) => setViewMode(v as 'calendar' | 'list' | 'month')}>
          <TabsList className="mb-6">
            <TabsTrigger value="calendar">Week View</TabsTrigger>
            <TabsTrigger value="month">Month View</TabsTrigger>
            <TabsTrigger value="list">List View</TabsTrigger>
          </TabsList>

          <TabsContent value="calendar">
            {/* Week Navigation */}
            <div className="flex items-center justify-between mb-6">
              <Button
                variant="outline"
                onClick={() => setCurrentWeek(Math.max(0, currentWeek - 1))}
                disabled={currentWeek === 0}
              >
                <ChevronLeft className="w-4 h-4 mr-2" />
                Previous Week
              </Button>
              <div className="text-center">
                <h2 className="text-xl text-slate-900">Week {currentWeek + 1}: {currentPhase?.label}</h2>
                <p className="text-sm text-slate-600">{startDate} - {endDate}</p>
              </div>
              <Button
                variant="outline"
                onClick={() => setCurrentWeek(Math.min(totalWeeks - 1, currentWeek + 1))}
                disabled={currentWeek === totalWeeks - 1}
              >
                Next Week
                <ChevronRight className="w-4 h-4 ml-2" />
              </Button>
            </div>

            {/* Calendar Grid - One Week */}
            <div className="grid grid-cols-7 gap-4">
              {currentWeekData.map((task) => (
                <Card 
                  key={task.date} 
                  className={`p-4 ${
                    task.completed 
                      ? 'bg-green-50 border-green-300' 
                      : task.dayOfWeek === 'Fri' && currentWeek === 0
                      ? 'border-2 border-purple-300 bg-purple-50' 
                      : ''
                  }`}
                >
                  <div className="mb-3">
                    <div className="text-sm text-slate-500 mb-1">{task.dayOfWeek}</div>
                    <div className="text-lg text-slate-900 mb-1">{task.date}</div>
                    <div className="text-xs text-slate-600">{task.theme}</div>
                  </div>
                  <div className="space-y-2">
                    <div className="bg-white rounded p-2 border border-slate-200">
                      <div className="text-xs text-slate-900 mb-1 line-clamp-2">{task.task}</div>
                      <div className="flex items-center gap-1 text-xs text-slate-500">
                        <Clock className="w-3 h-3" />
                        {task.estTime}
                      </div>
                    </div>
                    <Badge className={`w-full justify-center text-xs ${
                      task.completed 
                        ? 'bg-green-600' 
                        : 'bg-purple-100 text-purple-700'
                    }`}>
                      {task.completed ? '✓ Completed' : `${task.xp} XP`}
                    </Badge>
                  </div>
                </Card>
              ))}
            </div>

            {/* Week Summary */}
            <Card className="p-6 mt-6 bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-slate-900 mb-2">Week {currentWeek + 1} Summary</h3>
                  <p className="text-sm text-slate-600">
                    Focus: {currentPhase?.label} • Total Time: ~14 hours • Total XP: 320
                  </p>
                </div>
                <Button className="bg-blue-600 hover:bg-blue-700">
                  View Week Details
                </Button>
              </div>
            </Card>
          </TabsContent>

          <TabsContent value="month">
            {/* Month Navigation */}
            <div className="flex items-center justify-between mb-6">
              <Button
                variant="outline"
                onClick={() => setCurrentMonthOffset(currentMonthOffset - 1)}
              >
                <ChevronLeft className="w-4 h-4 mr-2" />
                Previous Month
              </Button>
              <div className="text-center">
                <h2 className="text-xl text-slate-900">{monthData.monthName}</h2>
              </div>
              <Button
                variant="outline"
                onClick={() => setCurrentMonthOffset(currentMonthOffset + 1)}
              >
                Next Month
                <ChevronRight className="w-4 h-4 ml-2" />
              </Button>
            </div>

            {/* Month Calendar Grid */}
            <Card className="overflow-hidden">
              {/* Day Headers */}
              <div className="grid grid-cols-7 bg-slate-50 border-b border-slate-200">
                {['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'].map((day) => (
                  <div key={day} className="p-3 text-center text-xs text-slate-600 border-r border-slate-200 last:border-r-0">
                    {day}
                  </div>
                ))}
              </div>

              {/* Calendar Days */}
              <div className="grid grid-cols-7">
                {monthData.calendarDays.map((day, index) => {
                  const tasksForDay = getTasksForDate(day.date);
                  
                  return (
                    <div
                      key={index}
                      className={`min-h-[120px] p-2 border-r border-b border-slate-200 ${
                        !day.isCurrentMonth ? 'bg-slate-50' : 'bg-white'
                      } ${day.isToday ? 'bg-blue-50' : ''}`}
                    >
                      <div className={`text-sm mb-2 ${
                        !day.isCurrentMonth ? 'text-slate-400' : 
                        day.isToday ? 'bg-blue-600 text-white w-7 h-7 rounded-full flex items-center justify-center' : 
                        'text-slate-700'
                      }`}>
                        {day.dayNumber}
                      </div>
                      
                      <div className="space-y-1">
                        {tasksForDay.slice(0, 2).map((task, taskIndex) => (
                          <div
                            key={taskIndex}
                            className={`text-xs px-2 py-1 rounded truncate ${
                              task.completed 
                                ? 'bg-green-500 text-white' 
                                : task.color === 'purple' ? 'bg-purple-500 text-white' :
                                  task.color === 'blue' ? 'bg-blue-500 text-white' :
                                  task.color === 'green' ? 'bg-green-500 text-white' :
                                  task.color === 'orange' ? 'bg-orange-500 text-white' :
                                  'bg-slate-500 text-white'
                            }`}
                          >
                            {task.theme}
                          </div>
                        ))}
                        {tasksForDay.length > 2 && (
                          <div className="text-xs text-slate-500 px-2">
                            +{tasksForDay.length - 2} more
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </Card>

            {/* Month Summary */}
            <Card className="p-6 mt-6 bg-gradient-to-r from-purple-50 to-pink-50 border-purple-200">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-slate-900 mb-2">Month Summary</h3>
                  <p className="text-sm text-slate-600">
                    {allTasks.filter(t => 
                      t.fullDate.getMonth() === monthData.month && 
                      t.fullDate.getFullYear() === monthData.year
                    ).length} tasks scheduled • Track your progress daily
                  </p>
                </div>
                <div className="flex gap-3">
                  <div className="flex items-center gap-2 text-sm">
                    <div className="w-4 h-4 bg-green-500 rounded"></div>
                    <span className="text-slate-600">Completed</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <div className="w-4 h-4 bg-purple-500 rounded"></div>
                    <span className="text-slate-600">Foundations</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <div className="w-4 h-4 bg-blue-500 rounded"></div>
                    <span className="text-slate-600">Technical</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <div className="w-4 h-4 bg-orange-500 rounded"></div>
                    <span className="text-slate-600">Practice</span>
                  </div>
                </div>
              </div>
            </Card>
          </TabsContent>

          <TabsContent value="list">
            <div className="space-y-3">
              {currentWeekData.map((task) => (
                <Card key={task.date} className={`p-5 hover:shadow-md transition-shadow ${
                  task.completed ? 'bg-green-50 border-green-200' : ''
                }`}>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <Badge variant="outline">{task.dayOfWeek}, {task.date}</Badge>
                        <h3 className="text-slate-900">{task.theme}</h3>
                        {task.completed && (
                          <Badge className="bg-green-600">✓ Completed</Badge>
                        )}
                      </div>
                      <p className="text-slate-700 mb-3">{task.task}</p>
                      <div className="flex items-center gap-4 text-sm text-slate-600">
                        <span className="flex items-center gap-1">
                          <Clock className="w-4 h-4" />
                          {task.estTime}
                        </span>
                        <span>•</span>
                        <span>📚 {task.resources}</span>
                      </div>
                    </div>
                    <div className="flex flex-col items-end gap-2">
                      <Badge className="bg-purple-100 text-purple-700">
                        {task.xp} XP
                      </Badge>
                      {!task.completed && (
                        <Button size="sm" className="bg-purple-600 hover:bg-purple-700">
                          Start
                        </Button>
                      )}
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </TabsContent>
        </Tabs>

        {/* Phase Overview */}
        <Card className="p-6 mt-8 bg-gradient-to-r from-purple-50 to-pink-50 border-purple-200">
          <h3 className="text-slate-900 mb-4">Study Plan Phases</h3>
          <div className="grid grid-cols-4 gap-4">
            {weeksPhases.map((phase, index) => (
              <div 
                key={index}
                className={`bg-white rounded-lg p-4 border-2 ${
                  currentWeek >= phase.range[0] && currentWeek <= phase.range[1]
                    ? 'border-purple-400 shadow-md'
                    : 'border-slate-200'
                }`}
              >
                <div className={`mb-2 ${
                  currentWeek >= phase.range[0] && currentWeek <= phase.range[1]
                    ? 'text-purple-600'
                    : 'text-slate-400'
                }`}>
                  Phase {index + 1}
                </div>
                <div className={`text-sm mb-1 ${
                  currentWeek >= phase.range[0] && currentWeek <= phase.range[1]
                    ? 'text-slate-900'
                    : 'text-slate-600'
                }`}>
                  Weeks {phase.range[0] + 1}-{phase.range[1] + 1}: {phase.label}
                </div>
                <div className="text-xs text-slate-500 mt-1">
                  {index === 0 && 'Python, SQL, Statistics basics'}
                  {index === 1 && 'Matplotlib, Tableau, EDA'}
                  {index === 2 && 'A/B Testing, Regression'}
                  {index === 3 && 'Projects, Interviews'}
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
