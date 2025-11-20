import { User, Clock, Target, Calendar, Sparkles, Save, Edit2 } from 'lucide-react';
import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Switch } from '../ui/switch';
import { Badge } from '../ui/badge';
// import { Header } from './Header';

type MockupPage = "login" | "upload" | "report" | "dashboard" | "plan" | "coding" | "interview" | "profile" | "resume";

interface ProfileMockupProps {
  onNavigate?: (page: MockupPage) => void;
}

export function Profile({ onNavigate }: ProfileMockupProps) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* <Header 
        activePage="profile" 
        onNavigate={(page) => {
          const pageMap: Record<string, MockupPage> = {
            'today': 'dashboard',
            'study-plan': 'plan',
            'coding-practice': 'coding',
            'interview-practice': 'interview',
            'profile': 'profile'
          };
          onNavigate?.(pageMap[page] || 'profile');
        }}
        onLogout={() => onNavigate?.('login')}
      /> */}

      {/* Page Header */}
      <div className="bg-white border-b border-slate-200 px-6 py-6">
        <div className="container mx-auto">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl text-slate-900 mb-2">Profile Settings</h1>
              <p className="text-slate-600">Manage your account and study preferences</p>
            </div>
            <Button className="bg-purple-600 hover:bg-purple-700">
              <Save className="w-4 h-4 mr-2" />
              Save Changes
            </Button>
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
                    <Input id="name" defaultValue="Alex Johnson" />
                  </div>
                  <div>
                    <Label htmlFor="email">Email</Label>
                    <Input id="email" type="email" defaultValue="alex.johnson@email.com" disabled />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="timezone">Timezone</Label>
                    <Select defaultValue="pst">
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="pst">Pacific Time (PST)</SelectItem>
                        <SelectItem value="mst">Mountain Time (MST)</SelectItem>
                        <SelectItem value="cst">Central Time (CST)</SelectItem>
                        <SelectItem value="est">Eastern Time (EST)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor="location">Location</Label>
                    <Input id="location" defaultValue="San Francisco, CA" />
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
                  <Input id="target-role" defaultValue="Data Analyst (Entry-Level)" />
                </div>

                <div>
                  <Label htmlFor="current-role">Current Role/Background</Label>
                  <Input id="current-role" defaultValue="Marketing Coordinator" />
                </div>

                <div>
                  <Label htmlFor="motivation">What's your motivation for this transition?</Label>
                  <Textarea
                    id="motivation"
                    defaultValue="I want to leverage my analytical skills in a more technical role and work with data to drive business decisions."
                    className="min-h-[100px]"
                  />
                </div>

                <div>
                  <Label htmlFor="target-date">Target Job Search Date</Label>
                  <Input id="target-date" type="date" defaultValue="2025-03-01" />
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
                  <Select defaultValue="15">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="5">5-10 hours/week (Light)</SelectItem>
                      <SelectItem value="15">15-20 hours/week (Standard)</SelectItem>
                      <SelectItem value="25">25-30 hours/week (Intensive)</SelectItem>
                      <SelectItem value="35">35+ hours/week (Full-time)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label>Available Days</Label>
                  <div className="grid grid-cols-7 gap-2 mt-2">
                    {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day) => (
                      <div key={day} className="flex items-center justify-center">
                        <Button
                          variant={['Mon', 'Tue', 'Wed', 'Fri', 'Sat'].includes(day) ? 'default' : 'outline'}
                          className={['Mon', 'Tue', 'Wed', 'Fri', 'Sat'].includes(day) ? 'bg-purple-600' : ''}
                          size="sm"
                        >
                          {day}
                        </Button>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="pref-time">Preferred Study Time</Label>
                    <Select defaultValue="evening">
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="morning">Morning (6am-12pm)</SelectItem>
                        <SelectItem value="afternoon">Afternoon (12pm-6pm)</SelectItem>
                        <SelectItem value="evening">Evening (6pm-12am)</SelectItem>
                        <SelectItem value="flexible">Flexible</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor="difficulty">Preferred Difficulty</Label>
                    <Select defaultValue="progressive">
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="gentle">Gentle (Slower pace)</SelectItem>
                        <SelectItem value="progressive">Progressive (Standard)</SelectItem>
                        <SelectItem value="challenging">Challenging (Fast pace)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div>
                  <Label>Learning Style Preferences</Label>
                  <div className="flex flex-wrap gap-2 mt-2">
                    <Badge variant="outline" className="cursor-pointer bg-purple-50 border-purple-300">
                      ✓ Video Tutorials
                    </Badge>
                    <Badge variant="outline" className="cursor-pointer bg-purple-50 border-purple-300">
                      ✓ Interactive Coding
                    </Badge>
                    <Badge variant="outline" className="cursor-pointer">
                      Reading Materials
                    </Badge>
                    <Badge variant="outline" className="cursor-pointer bg-purple-50 border-purple-300">
                      ✓ Practice Projects
                    </Badge>
                    <Badge variant="outline" className="cursor-pointer">
                      Podcasts
                    </Badge>
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
                  <Input id="assistant-name" defaultValue="Study Assistant" />
                  <p className="text-sm text-slate-500 mt-1">Personalize your AI helper</p>
                </div>

                <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
                  <div>
                    <div className="text-slate-900 mb-1">Enable proactive suggestions</div>
                    <div className="text-sm text-slate-600">
                      Let your assistant suggest adjustments to your study plan
                    </div>
                  </div>
                  <Switch defaultChecked />
                </div>

                <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
                  <div>
                    <div className="text-slate-900 mb-1">Daily reminders</div>
                    <div className="text-sm text-slate-600">
                      Get notifications for scheduled tasks
                    </div>
                  </div>
                  <Switch defaultChecked />
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
                  AJ
                </div>
                <h3 className="text-xl text-slate-900 mb-1">Alex Johnson</h3>
                <p className="text-sm text-slate-600">Member since Nov 2024</p>
              </div>

              <div className="space-y-3 pt-4 border-t border-purple-200">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-600">Current Streak</span>
                  <span className="text-purple-600">7 days 🔥</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-600">Total XP</span>
                  <span className="text-purple-600">220 XP</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-600">Badges Earned</span>
                  <span className="text-purple-600">2</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-600">Readiness</span>
                  <span className="text-purple-600">34%</span>
                </div>
              </div>
            </Card>

            {/* Quick Actions */}
            <Card className="p-6 mb-6">
              <h3 className="text-slate-900 mb-4">Quick Actions</h3>
              <div className="space-y-2">
                <Button variant="outline" className="w-full justify-start">
                  <Edit2 className="w-4 h-4 mr-2" />
                  Update Resume
                </Button>
                <Button variant="outline" className="w-full justify-start">
                  <Target className="w-4 h-4 mr-2" />
                  View Skill Report
                </Button>
                <Button variant="outline" className="w-full justify-start">
                  <Calendar className="w-4 h-4 mr-2" />
                  Regenerate Plan
                </Button>
              </div>
            </Card>

            {/* Danger Zone */}
            <Card className="p-6 border-red-200">
              <h3 className="text-red-900 mb-4">Danger Zone</h3>
              <div className="space-y-2">
                <Button variant="outline" className="w-full justify-start text-red-600 border-red-200 hover:bg-red-50">
                  Reset Study Plan
                </Button>
                <Button variant="outline" className="w-full justify-start text-red-600 border-red-200 hover:bg-red-50">
                  Delete Account
                </Button>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
