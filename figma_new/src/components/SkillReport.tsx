import { useState, useEffect } from 'react';
import { Target, TrendingUp, CheckCircle, AlertCircle, Clock, Calendar, ArrowRight, Sparkles, ExternalLink, Code, BookOpen, Video, Award } from 'lucide-react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Separator } from './ui/separator';
import { projectId } from '../utils/supabase/info';

// Helper function to get learning platform recommendations based on skill name
function getPlatformLinks(skillName: string): { name: string; url: string; icon: any; type: string }[] {
  const skill = skillName.toLowerCase();
  const links: { name: string; url: string; icon: any; type: string }[] = [];

  // Programming languages
  if (skill.includes('python') || skill.includes('java') || skill.includes('javascript') || 
      skill.includes('c++') || skill.includes('ruby') || skill.includes('go') || 
      skill.includes('rust') || skill.includes('kotlin') || skill.includes('swift')) {
    links.push(
      { name: 'Codecademy', url: `https://www.codecademy.com/catalog/language/${skill.split(' ')[0]}`, icon: Code, type: 'Interactive' },
      { name: 'freeCodeCamp', url: 'https://www.freecodecamp.org/', icon: BookOpen, type: 'Free' },
      { name: 'LeetCode', url: 'https://leetcode.com/', icon: Code, type: 'Practice' }
    );
  }

  // SQL and databases
  if (skill.includes('sql') || skill.includes('database') || skill.includes('postgres') || skill.includes('mysql')) {
    links.push(
      { name: 'Mode SQL', url: 'https://mode.com/sql-tutorial/', icon: BookOpen, type: 'Tutorial' },
      { name: 'SQLZoo', url: 'https://sqlzoo.net/', icon: Code, type: 'Interactive' },
      { name: 'LeetCode SQL', url: 'https://leetcode.com/problemset/database/', icon: Code, type: 'Practice' }
    );
  }

  // Data Science & Analytics
  if (skill.includes('data') || skill.includes('analytics') || skill.includes('statistics') || skill.includes('r ')) {
    links.push(
      { name: 'DataCamp', url: 'https://www.datacamp.com/', icon: Award, type: 'Courses' },
      { name: 'Kaggle Learn', url: 'https://www.kaggle.com/learn', icon: Code, type: 'Free' },
      { name: 'Khan Academy', url: 'https://www.khanacademy.org/math/statistics-probability', icon: Video, type: 'Video' }
    );
  }

  // Excel & Spreadsheets
  if (skill.includes('excel') || skill.includes('spreadsheet') || skill.includes('sheets')) {
    links.push(
      { name: 'Excel Easy', url: 'https://www.excel-easy.com/', icon: BookOpen, type: 'Tutorial' },
      { name: 'Coursera Excel', url: 'https://www.coursera.org/courses?query=excel', icon: Video, type: 'Courses' }
    );
  }

  // Visualization tools
  if (skill.includes('tableau') || skill.includes('power bi') || skill.includes('visualization')) {
    links.push(
      { name: 'Tableau Public', url: 'https://public.tableau.com/app/resources/learn', icon: BookOpen, type: 'Free' },
      { name: 'DataCamp', url: 'https://www.datacamp.com/', icon: Award, type: 'Courses' }
    );
  }

  // Web Development
  if (skill.includes('html') || skill.includes('css') || skill.includes('react') || 
      skill.includes('vue') || skill.includes('angular') || skill.includes('web')) {
    links.push(
      { name: 'freeCodeCamp', url: 'https://www.freecodecamp.org/', icon: BookOpen, type: 'Free' },
      { name: 'Frontend Mentor', url: 'https://www.frontendmentor.io/', icon: Code, type: 'Projects' },
      { name: 'MDN Web Docs', url: 'https://developer.mozilla.org/', icon: BookOpen, type: 'Docs' }
    );
  }

  // Machine Learning & AI
  if (skill.includes('machine learning') || skill.includes('ai') || skill.includes('deep learning') || skill.includes('neural')) {
    links.push(
      { name: 'Coursera ML', url: 'https://www.coursera.org/specializations/machine-learning-introduction', icon: Video, type: 'Course' },
      { name: 'Kaggle', url: 'https://www.kaggle.com/learn', icon: Code, type: 'Practice' },
      { name: 'Fast.ai', url: 'https://www.fast.ai/', icon: Video, type: 'Free' }
    );
  }

  // Cloud & DevOps
  if (skill.includes('aws') || skill.includes('azure') || skill.includes('gcp') || 
      skill.includes('docker') || skill.includes('kubernetes') || skill.includes('cloud')) {
    links.push(
      { name: 'A Cloud Guru', url: 'https://www.pluralsight.com/cloud-guru', icon: Award, type: 'Courses' },
      { name: 'AWS Training', url: 'https://aws.amazon.com/training/', icon: BookOpen, type: 'Official' }
    );
  }

  // Design
  if (skill.includes('design') || skill.includes('ui') || skill.includes('ux') || skill.includes('figma')) {
    links.push(
      { name: 'Coursera Design', url: 'https://www.coursera.org/courses?query=ui%20ux%20design', icon: Video, type: 'Courses' },
      { name: 'Figma Learn', url: 'https://help.figma.com/hc/en-us/categories/360002051613', icon: BookOpen, type: 'Official' }
    );
  }

  // Generic fallback - always useful
  if (links.length === 0) {
    links.push(
      { name: 'Coursera', url: `https://www.coursera.org/courses?query=${encodeURIComponent(skillName)}`, icon: Video, type: 'Courses' },
      { name: 'YouTube', url: `https://www.youtube.com/results?search_query=${encodeURIComponent(skillName + ' tutorial')}`, icon: Video, type: 'Free' },
      { name: 'Udemy', url: `https://www.udemy.com/courses/search/?q=${encodeURIComponent(skillName)}`, icon: Award, type: 'Courses' }
    );
  }

  return links;
}

interface SkillData {
  name: string;
  level?: 'Beginner' | 'Intermediate' | 'Advanced' | 'Expert';
  priority?: 'High' | 'Medium' | 'Low';
  estimatedTime?: string;
  resources?: {
    title: string;
    url: string;
    hours: number;
  }[];
}

interface ReportData {
  matchScore: number;
  hardSkills: {
    existing: SkillData[];
    missing: SkillData[];
  };
  softSkills: {
    existing: SkillData[];
    missing: SkillData[];
  };
  totalLearningHours: number;
}

interface SkillReportProps {
  accessToken: string;
  analysisId: string;
}

export function SkillReport({ accessToken, analysisId }: SkillReportProps) {
  const [reportData, setReportData] = useState<ReportData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showPlanGenerator, setShowPlanGenerator] = useState(false);
  const [hoursPerDay, setHoursPerDay] = useState('2-3');
  const [timeline, setTimeline] = useState('60');
  const [studyDays, setStudyDays] = useState(['Mon', 'Tue', 'Wed', 'Thu', 'Fri']);

  useEffect(() => {
    const loadReport = async () => {
      try {
        const response = await fetch(
          `https://${projectId}.supabase.co/functions/v1/server/report/${analysisId}`,
          {
            headers: {
              'Authorization': `Bearer ${accessToken}`,
            },
          }
        );

        if (response.ok) {
          const data = await response.json();
          setReportData(data);
        }
      } catch (error) {
        console.error('Error loading report:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadReport();
  }, [analysisId, accessToken]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="w-8 h-8 border-4 border-purple-600 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  if (!reportData) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-slate-600">Failed to load report</p>
      </div>
    );
  }

  const getReadinessMessage = (score: number) => {
    if (score >= 80) return { text: "You're almost ready!", color: "text-green-600", icon: "🎯" };
    if (score >= 60) return { text: "You're on the right track!", color: "text-blue-600", icon: "🚀" };
    return { text: "Let's build your skills!", color: "text-purple-600", icon: "💪" };
  };

  const readiness = getReadinessMessage(reportData.matchScore);
  const totalExisting = reportData.hardSkills.existing.length + reportData.softSkills.existing.length;
  const totalMissing = reportData.hardSkills.missing.length + reportData.softSkills.missing.length;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 py-12">
      <div className="container mx-auto px-6 max-w-6xl">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl text-slate-900 mb-3">Your Career Readiness Report</h1>
          <p className="text-lg text-slate-600">Personalized skill gap analysis for your target role</p>
        </div>

        {/* Overall Readiness Card */}
        <Card className="p-8 mb-8 bg-gradient-to-br from-purple-50 to-indigo-50 border-purple-200">
          <div className="text-center mb-6">
            <div className="inline-flex items-center justify-center w-32 h-32 rounded-full bg-white shadow-lg mb-4">
              <div className="text-center">
                <div className="text-4xl text-purple-600 mb-1">{reportData.matchScore}%</div>
                <div className="text-xs text-slate-600">Ready</div>
              </div>
            </div>
            <h2 className={`text-2xl mb-2 ${readiness.color}`}>
              {readiness.icon} {readiness.text}
            </h2>
            <p className="text-slate-700 max-w-2xl mx-auto">
              You have a {totalExisting > 0 ? 'solid foundation with' : ''} <strong>{totalExisting} relevant skill{totalExisting !== 1 ? 's' : ''}</strong>. 
              {totalMissing > 0 && (
                <>
                  {' '}Focus on building <strong>{totalMissing} key area{totalMissing !== 1 ? 's' : ''}</strong> to become fully qualified for this role.
                </>
              )}
              {reportData.totalLearningHours > 0 && (
                <>
                  {' '}With consistent effort, you could be ready in about <strong>{Math.ceil(reportData.totalLearningHours / 14)} weeks</strong>.
                </>
              )}
            </p>
          </div>

          <div className="grid grid-cols-3 gap-6 mt-6">
            <div className="text-center p-4 bg-white rounded-lg border border-purple-200">
              <div className="text-2xl text-green-600 mb-1">{totalExisting}</div>
              <div className="text-sm text-slate-600">Skills You Have</div>
            </div>
            <div className="text-center p-4 bg-white rounded-lg border border-purple-200">
              <div className="text-2xl text-purple-600 mb-1">{totalMissing}</div>
              <div className="text-sm text-slate-600">Skills to Learn</div>
            </div>
            <div className="text-center p-4 bg-white rounded-lg border border-purple-200">
              <div className="text-2xl text-blue-600 mb-1">~{reportData.totalLearningHours}h</div>
              <div className="text-sm text-slate-600">Total Study Time</div>
            </div>
          </div>
        </Card>

        {/* Existing Skills */}
        {totalExisting > 0 && (
          <Card className="p-6 mb-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="bg-green-100 p-3 rounded-xl">
                <CheckCircle className="w-6 h-6 text-green-600" />
              </div>
              <div>
                <h2 className="text-xl text-slate-900">Your Existing Strengths</h2>
                <p className="text-sm text-slate-600">Skills you already have for this role</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              {reportData.hardSkills.existing.map((skill, idx) => (
                <div key={idx} className="flex items-center justify-between p-4 bg-slate-50 rounded-lg border border-slate-200">
                  <div>
                    <div className="text-slate-900 mb-1">{skill.name}</div>
                    {skill.level && (
                      <Badge className={
                        skill.level === 'Expert' || skill.level === 'Advanced' ? 'bg-green-100 text-green-700' :
                        skill.level === 'Intermediate' ? 'bg-blue-100 text-blue-700' :
                        'bg-yellow-100 text-yellow-700'
                      }>
                        {skill.level}
                      </Badge>
                    )}
                  </div>
                  <CheckCircle className="w-5 h-5 text-green-600" />
                </div>
              ))}
              {reportData.softSkills.existing.map((skill, idx) => (
                <div key={idx} className="flex items-center justify-between p-4 bg-slate-50 rounded-lg border border-slate-200">
                  <div>
                    <div className="text-slate-900 mb-1">{skill.name}</div>
                    {skill.level && (
                      <Badge className={
                        skill.level === 'Expert' || skill.level === 'Advanced' ? 'bg-green-100 text-green-700' :
                        skill.level === 'Intermediate' ? 'bg-blue-100 text-blue-700' :
                        'bg-yellow-100 text-yellow-700'
                      }>
                        {skill.level}
                      </Badge>
                    )}
                  </div>
                  <CheckCircle className="w-5 h-5 text-green-600" />
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Skills to Develop */}
        {totalMissing > 0 && (
          <Card className="p-6 mb-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="bg-purple-100 p-3 rounded-xl">
                <TrendingUp className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <h2 className="text-xl text-slate-900">Skills to Develop</h2>
                <p className="text-sm text-slate-600">Focus areas to reach your career goal</p>
              </div>
            </div>

            {/* Hard Skills */}
            {reportData.hardSkills.missing.length > 0 && (
              <div className="mb-6">
                <h3 className="text-slate-900 mb-4 flex items-center gap-2">
                  <Target className="w-5 h-5 text-purple-600" />
                  Technical Skills
                </h3>
                <div className="space-y-3">
                  {reportData.hardSkills.missing.map((skill, idx) => (
                    <div key={idx} className="p-4 bg-white rounded-lg border border-slate-200">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <h4 className="text-slate-900">{skill.name}</h4>
                            {skill.priority && (
                              <Badge className={
                                skill.priority === 'High' 
                                  ? 'bg-red-100 text-red-700' 
                                  : skill.priority === 'Medium'
                                  ? 'bg-orange-100 text-orange-700'
                                  : 'bg-blue-100 text-blue-700'
                              }>
                                {skill.priority} Priority
                              </Badge>
                            )}
                          </div>
                          {skill.estimatedTime && (
                            <div className="flex items-center gap-4 text-sm text-slate-600">
                              <span className="flex items-center gap-1">
                                <Clock className="w-4 h-4" />
                                {skill.estimatedTime}
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                      {skill.resources && skill.resources.length > 0 && (
                        <div className="space-y-2 mb-3">
                          <div className="text-sm text-slate-700">
                            <strong>Recommended resources:</strong>
                          </div>
                          <div className="space-y-2">
                            {skill.resources.map((resource, rIdx) => (
                              <div
                                key={rIdx}
                                className="flex items-center justify-between bg-slate-50 rounded-lg p-3 border border-slate-200"
                              >
                                <div className="flex-1">
                                  <p className="text-slate-900 text-sm">{resource.title}</p>
                                  <div className="flex items-center gap-2 mt-1">
                                    <Clock className="w-3 h-3 text-slate-400" />
                                    <span className="text-slate-500 text-xs">
                                      ~{resource.hours} hours
                                    </span>
                                  </div>
                                </div>
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  onClick={() => window.open(resource.url, '_blank')}
                                  className="gap-1"
                                >
                                  <ExternalLink className="w-4 h-4" />
                                </Button>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {/* Platform Quick Links */}
                      <div className="mt-3 pt-3 border-t border-slate-200">
                        <div className="text-xs text-slate-600 mb-2">Quick start learning:</div>
                        <div className="flex flex-wrap gap-2">
                          {getPlatformLinks(skill.name).slice(0, 3).map((platform, pIdx) => {
                            const Icon = platform.icon;
                            return (
                              <Button
                                key={pIdx}
                                size="sm"
                                variant="outline"
                                onClick={() => window.open(platform.url, '_blank')}
                                className="h-8 text-xs gap-1.5 border-purple-200 hover:bg-purple-50 hover:text-purple-700"
                              >
                                <Icon className="w-3 h-3" />
                                {platform.name}
                                <Badge variant="outline" className="ml-1 text-xs px-1 py-0 h-4 border-purple-300">
                                  {platform.type}
                                </Badge>
                              </Button>
                            );
                          })}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Soft Skills */}
            {reportData.softSkills.missing.length > 0 && (
              <div>
                <h3 className="text-slate-900 mb-4 flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-blue-600" />
                  Professional Skills
                </h3>
                <div className="space-y-3">
                  {reportData.softSkills.missing.map((skill, idx) => (
                    <div key={idx} className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <h4 className="text-slate-900">{skill.name}</h4>
                            {skill.priority && (
                              <Badge className="bg-blue-100 text-blue-700">
                                {skill.priority} Priority
                              </Badge>
                            )}
                          </div>
                          {skill.estimatedTime && (
                            <div className="text-sm text-slate-600 mb-2">{skill.estimatedTime} of practice</div>
                          )}
                          {skill.resources && skill.resources.length > 0 && (
                            <div className="space-y-2 mt-3">
                              <div className="text-sm text-slate-700">
                                <strong>Practice with:</strong>
                              </div>
                              <div className="space-y-2">
                                {skill.resources.map((resource, rIdx) => (
                                  <div
                                    key={rIdx}
                                    className="flex items-center justify-between bg-white rounded-lg p-3 border border-blue-200"
                                  >
                                    <div className="flex-1">
                                      <p className="text-slate-900 text-sm">{resource.title}</p>
                                      <div className="flex items-center gap-2 mt-1">
                                        <Clock className="w-3 h-3 text-slate-400" />
                                        <span className="text-slate-500 text-xs">
                                          ~{resource.hours} hours
                                        </span>
                                      </div>
                                    </div>
                                    <Button
                                      size="sm"
                                      variant="ghost"
                                      onClick={() => window.open(resource.url, '_blank')}
                                      className="gap-1"
                                    >
                                      <ExternalLink className="w-4 h-4" />
                                    </Button>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                          
                          {/* Platform Quick Links for Soft Skills */}
                          <div className="mt-3 pt-3 border-t border-blue-200">
                            <div className="text-xs text-slate-600 mb-2">Develop this skill:</div>
                            <div className="flex flex-wrap gap-2">
                              {/* For soft skills, show generic learning platforms */}
                              {[
                                { name: 'LinkedIn Learning', url: `https://www.linkedin.com/learning/search?keywords=${encodeURIComponent(skill.name)}`, icon: Award, type: 'Courses' },
                                { name: 'Coursera', url: `https://www.coursera.org/courses?query=${encodeURIComponent(skill.name)}`, icon: Video, type: 'Video' },
                                { name: 'YouTube', url: `https://www.youtube.com/results?search_query=${encodeURIComponent(skill.name + ' skills')}`, icon: Video, type: 'Free' }
                              ].slice(0, 3).map((platform, pIdx) => {
                                const Icon = platform.icon;
                                return (
                                  <Button
                                    key={pIdx}
                                    size="sm"
                                    variant="outline"
                                    onClick={() => window.open(platform.url, '_blank')}
                                    className="h-8 text-xs gap-1.5 border-blue-200 hover:bg-blue-50 hover:text-blue-700"
                                  >
                                    <Icon className="w-3 h-3" />
                                    {platform.name}
                                    <Badge variant="outline" className="ml-1 text-xs px-1 py-0 h-4 border-blue-300">
                                      {platform.type}
                                    </Badge>
                                  </Button>
                                );
                              })}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {/* Popular Learning Platforms Overview */}
            <div className="mt-6 p-4 bg-gradient-to-br from-slate-50 to-slate-100 rounded-lg border border-slate-200">
              <h3 className="text-slate-900 mb-3 flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-slate-600" />
                Popular Learning Platforms
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                <Button
                  variant="outline"
                  size="sm"
                  className="h-auto py-2 flex-col items-start gap-1"
                  onClick={() => window.open('https://www.coursera.org/', '_blank')}
                >
                  <span className="font-semibold">Coursera</span>
                  <span className="text-slate-500">University courses</span>
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  className="h-auto py-2 flex-col items-start gap-1"
                  onClick={() => window.open('https://www.udemy.com/', '_blank')}
                >
                  <span className="font-semibold">Udemy</span>
                  <span className="text-slate-500">Practical skills</span>
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  className="h-auto py-2 flex-col items-start gap-1"
                  onClick={() => window.open('https://www.linkedin.com/learning/', '_blank')}
                >
                  <span className="font-semibold">LinkedIn Learning</span>
                  <span className="text-slate-500">Professional dev</span>
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  className="h-auto py-2 flex-col items-start gap-1"
                  onClick={() => window.open('https://www.freecodecamp.org/', '_blank')}
                >
                  <span className="font-semibold">freeCodeCamp</span>
                  <span className="text-slate-500">Free coding</span>
                </Button>
              </div>
            </div>
          </Card>
        )}

        {/* Study Plan Generator */}
        <Card className="p-8 bg-gradient-to-br from-green-50 to-emerald-50 border-green-200">
          <div className="flex items-center gap-3 mb-6">
            <div className="bg-green-100 p-3 rounded-xl">
              <Calendar className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <h2 className="text-xl text-slate-900">Generate Your Personalized Study Plan</h2>
              <p className="text-sm text-slate-600">
                Tell us your availability and we'll create a day-by-day roadmap to reach your goal
              </p>
            </div>
          </div>

          {!showPlanGenerator ? (
            <div className="text-center">
              <Button 
                onClick={() => setShowPlanGenerator(true)}
                className="bg-green-600 hover:bg-green-700 text-white px-8 py-6 h-auto text-lg"
              >
                <Sparkles className="w-5 h-5 mr-2" />
                Create My Study Plan
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            </div>
          ) : (
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <Label htmlFor="hours-per-day">How many hours can you study per day?</Label>
                  <Select value={hoursPerDay} onValueChange={setHoursPerDay}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1-2">1-2 hours/day (Light pace)</SelectItem>
                      <SelectItem value="2-3">2-3 hours/day (Standard)</SelectItem>
                      <SelectItem value="3-4">3-4 hours/day (Intensive)</SelectItem>
                      <SelectItem value="4+">4+ hours/day (Full-time)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="timeline">When do you want to be job-ready?</Label>
                  <Select value={timeline} onValueChange={setTimeline}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="30">1 month (30 days)</SelectItem>
                      <SelectItem value="60">2 months (60 days)</SelectItem>
                      <SelectItem value="90">3 months (90 days)</SelectItem>
                      <SelectItem value="120">4 months (120 days)</SelectItem>
                      <SelectItem value="180">6 months (180 days)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div>
                <Label className="mb-3 block">Which days are you available to study?</Label>
                <div className="flex gap-2">
                  {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day) => (
                    <Button
                      key={day}
                      variant={studyDays.includes(day) ? 'default' : 'outline'}
                      className={studyDays.includes(day) ? 'bg-green-600 hover:bg-green-700' : ''}
                      onClick={() => {
                        setStudyDays(prev => 
                          prev.includes(day) 
                            ? prev.filter(d => d !== day)
                            : [...prev, day]
                        );
                      }}
                    >
                      {day}
                    </Button>
                  ))}
                </div>
              </div>

              <Separator />

              <div className="bg-white rounded-lg p-6 border border-green-300">
                <h3 className="text-slate-900 mb-4">Your Study Plan Summary</h3>
                <div className="space-y-2 text-sm text-slate-700">
                  <div className="flex justify-between">
                    <span>Daily commitment:</span>
                    <strong>{hoursPerDay} hours</strong>
                  </div>
                  <div className="flex justify-between">
                    <span>Study days per week:</span>
                    <strong>{studyDays.length} days</strong>
                  </div>
                  <div className="flex justify-between">
                    <span>Timeline:</span>
                    <strong>{timeline} days</strong>
                  </div>
                  <div className="flex justify-between">
                    <span>Target completion:</span>
                    <strong>{new Date(Date.now() + parseInt(timeline) * 24 * 60 * 60 * 1000).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</strong>
                  </div>
                  <Separator className="my-3" />
                  <div className="flex justify-between text-base">
                    <span>Expected readiness level:</span>
                    <strong className="text-green-600">95%</strong>
                  </div>
                </div>
              </div>

              <div className="flex gap-3">
                <Button 
                  onClick={() => setShowPlanGenerator(false)}
                  variant="outline"
                  className="flex-1"
                >
                  Back
                </Button>
                <Button 
                  className="flex-1 bg-green-600 hover:bg-green-700 text-white"
                >
                  <Calendar className="w-4 h-4 mr-2" />
                  Generate My {timeline}-Day Plan
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </div>
            </div>
          )}
        </Card>

        {/* Behavioral Interview Section */}
        <Card className="p-6 mt-8 bg-gradient-to-br from-blue-50 to-cyan-50 border-blue-200">
          <div className="flex items-center gap-3 mb-4">
            <div className="bg-blue-100 p-3 rounded-xl">
              <AlertCircle className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <h3 className="text-lg text-slate-900">Behavioral Questions to Practice</h3>
              <p className="text-sm text-slate-600">Prepare for common interview scenarios</p>
            </div>
          </div>

          <div className="space-y-2">
            {[
              'Tell me about yourself and your career goals',
              'Describe a time you solved a challenging problem',
              'How do you handle tight deadlines and multiple priorities?',
              'Give an example of when you had to explain complex concepts to others'
            ].map((question, idx) => (
              <div key={idx} className="p-3 bg-white rounded border border-blue-200 text-sm text-slate-700">
                {idx + 1}. {question}
              </div>
            ))}
          </div>

          <Button 
            variant="outline" 
            className="w-full mt-4 border-blue-300 text-blue-600 hover:bg-blue-50"
            onClick={() => window.open('https://www.biginterview.com/', '_blank')}
          >
            <ExternalLink className="w-4 h-4 mr-2" />
            Practice with BigInterview
          </Button>
        </Card>
      </div>
    </div>
  );
}
