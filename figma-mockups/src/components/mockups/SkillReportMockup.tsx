import { Card } from '../ui/card';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Button } from '../ui/button';
import { Separator } from '../ui/separator';
import { TrendingUp, Target, Award, Clock, ExternalLink, CheckCircle2, XCircle, MessageCircle } from 'lucide-react';

const mockReportData = {
  matchScore: 78,
  hardSkills: {
    existing: [
      { name: 'JavaScript', level: 'Advanced' },
      { name: 'React', level: 'Advanced' },
      { name: 'Node.js', level: 'Intermediate' },
      { name: 'Python', level: 'Intermediate' },
      { name: 'SQL', level: 'Intermediate' },
      { name: 'Git', level: 'Advanced' },
    ],
    missing: [
      {
        name: 'TypeScript',
        resources: [
          { title: 'Understanding TypeScript (Udemy)', url: 'https://www.udemy.com/course/understanding-typescript/', hours: 15 },
          { title: 'TypeScript Official Docs', url: 'https://www.typescriptlang.org/docs/', hours: 10 }
        ]
      },
      {
        name: 'Docker',
        resources: [
          { title: 'Docker Mastery (Udemy)', url: 'https://www.udemy.com/course/docker-mastery/', hours: 19 },
          { title: 'Docker Official Getting Started', url: 'https://docs.docker.com/get-started/', hours: 5 }
        ]
      },
      {
        name: 'AWS',
        resources: [
          { title: 'AWS Certified Solutions Architect', url: 'https://aws.amazon.com/training/', hours: 40 },
          { title: 'AWS Cloud Practitioner Essentials', url: 'https://explore.skillbuilder.aws/learn', hours: 6 }
        ]
      },
    ]
  },
  softSkills: {
    existing: [
      { name: 'Team Collaboration' },
      { name: 'Problem Solving' },
      { name: 'Communication' },
      { name: 'Time Management' },
    ],
    missing: [
      {
        name: 'Leadership',
        resources: [
          { title: 'Leadership Principles (Coursera)', url: 'https://www.coursera.org/learn/leadership-principles', hours: 15 },
          { title: 'Developing Leadership Skills', url: 'https://www.linkedin.com/learning/topics/leadership', hours: 12 }
        ]
      },
      {
        name: 'Strategic Thinking',
        resources: [
          { title: 'Strategic Thinking (LinkedIn Learning)', url: 'https://www.linkedin.com/learning/topics/strategic-thinking', hours: 8 }
        ]
      },
    ]
  },
  totalLearningHours: 130
};

export function SkillReportMockup() {
  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBg = (score: number) => {
    if (score >= 80) return 'bg-green-100';
    if (score >= 60) return 'bg-yellow-100';
    return 'bg-red-100';
  };

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-pink-600 rounded-2xl p-8 text-white">
        <h1 className="text-3xl mb-2">Skill Gap Analysis Report</h1>
        <p className="text-purple-100">Comprehensive analysis of your skills vs. job requirements</p>
      </div>

      {/* Match Score */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className={`${getScoreBg(mockReportData.matchScore)} p-3 rounded-xl`}>
              <TrendingUp className={`w-6 h-6 ${getScoreColor(mockReportData.matchScore)}`} />
            </div>
            <div>
              <h2 className="text-slate-900 text-xl">Overall Match Score</h2>
              <p className="text-slate-600 text-sm">How well you match the job requirements</p>
            </div>
          </div>
          <div className={`text-5xl ${getScoreColor(mockReportData.matchScore)}`}>
            {mockReportData.matchScore}%
          </div>
        </div>
        <Progress value={mockReportData.matchScore} className="h-3" />
        <p className="text-slate-600 text-sm mt-4">
          Good match with room for improvement in some areas.
        </p>
      </Card>

      {/* Hard Skills */}
      <Card className="p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="bg-blue-100 p-3 rounded-xl">
            <Target className="w-6 h-6 text-blue-600" />
          </div>
          <div>
            <h2 className="text-slate-900 text-xl">Hard Skills</h2>
            <p className="text-slate-600 text-sm">Technical and job-specific competencies</p>
          </div>
        </div>

        <div className="space-y-6">
          {/* Existing Hard Skills */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <CheckCircle2 className="w-5 h-5 text-green-600" />
              <h3 className="text-slate-900">Skills You Have</h3>
            </div>
            <div className="flex flex-wrap gap-2">
              {mockReportData.hardSkills.existing.map((skill, index) => (
                <Badge
                  key={index}
                  className="bg-green-100 text-green-700 hover:bg-green-200"
                >
                  {skill.name} • {skill.level}
                </Badge>
              ))}
            </div>
          </div>

          <Separator />

          {/* Missing Hard Skills */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <XCircle className="w-5 h-5 text-red-600" />
              <h3 className="text-slate-900">Skills to Develop</h3>
            </div>
            <div className="space-y-4">
              {mockReportData.hardSkills.missing.map((skill, index) => (
                <div key={index} className="bg-slate-50 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-slate-900">{skill.name}</h4>
                    <Badge variant="outline" className="text-red-600 border-red-300">
                      Missing
                    </Badge>
                  </div>
                  {skill.resources && skill.resources.length > 0 && (
                    <div className="space-y-2">
                      <p className="text-slate-600 text-sm mb-2">Recommended Resources:</p>
                      {skill.resources.map((resource, rIndex) => (
                        <div
                          key={rIndex}
                          className="flex items-center justify-between bg-white rounded-lg p-3 border border-slate-200"
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
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </Card>

      {/* Soft Skills */}
      <Card className="p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="bg-purple-100 p-3 rounded-xl">
            <Award className="w-6 h-6 text-purple-600" />
          </div>
          <div>
            <h2 className="text-slate-900 text-xl">Soft Skills</h2>
            <p className="text-slate-600 text-sm">Interpersonal and transferable skills</p>
          </div>
        </div>

        <div className="space-y-6">
          {/* Existing Soft Skills */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <CheckCircle2 className="w-5 h-5 text-green-600" />
              <h3 className="text-slate-900">Skills You Have</h3>
            </div>
            <div className="flex flex-wrap gap-2">
              {mockReportData.softSkills.existing.map((skill, index) => (
                <Badge
                  key={index}
                  className="bg-purple-100 text-purple-700 hover:bg-purple-200"
                >
                  {skill.name}
                </Badge>
              ))}
            </div>
          </div>

          <Separator />

          {/* Missing Soft Skills */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <XCircle className="w-5 h-5 text-red-600" />
              <h3 className="text-slate-900">Skills to Develop</h3>
            </div>
            <div className="flex flex-wrap gap-2">
              {mockReportData.softSkills.missing.map((skill, index) => (
                <Badge
                  key={index}
                  variant="outline"
                  className="text-red-600 border-red-300"
                >
                  {skill.name}
                </Badge>
              ))}
            </div>
          </div>
        </div>
      </Card>

      {/* Behavioral Questions / Interview Prep */}
      <Card className="p-6 bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200">
        <div className="flex items-center gap-3 mb-6">
          <div className="bg-blue-100 p-3 rounded-xl">
            <MessageCircle className="w-6 h-6 text-blue-600" />
          </div>
          <div>
            <h2 className="text-slate-900 text-xl">Behavioral Questions to Practice</h2>
            <p className="text-slate-600 text-sm">Interview preparation for soft skills assessment</p>
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <p className="text-slate-700 mb-2">
              Develop your soft skills and prepare for behavioral interviews with these curated resources:
            </p>
            <p className="text-slate-500 text-sm italic">
              Note: Preparation time varies based on your own pace and experience level.
            </p>
          </div>
          
          <div className="bg-white rounded-lg p-4 border border-blue-200">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <h3 className="text-slate-900 mb-2">Exponent - Behavioral Interview Prep</h3>
                <p className="text-slate-600 text-sm mb-3">
                  Practice common behavioral questions for Leadership, Strategic Thinking, and other soft skills with expert feedback and frameworks.
                </p>
                <div className="flex flex-wrap gap-2">
                  {mockReportData.softSkills.missing.map((skill, index) => (
                    <Badge key={index} className="bg-blue-100 text-blue-700 text-xs">
                      {skill.name}
                    </Badge>
                  ))}
                </div>
              </div>
              <Button
                onClick={() => window.open('https://www.tryexponent.com/courses/behavioral', '_blank')}
                className="bg-blue-600 hover:bg-blue-700 gap-2 whitespace-nowrap"
              >
                Visit Exponent
                <ExternalLink className="w-4 h-4" />
              </Button>
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-3">
            <div className="bg-white rounded-lg p-3 border border-slate-200">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                <p className="text-slate-900 text-sm">STAR Method Framework</p>
              </div>
              <p className="text-slate-600 text-xs">
                Structure your answers effectively
              </p>
            </div>
            <div className="bg-white rounded-lg p-3 border border-slate-200">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                <p className="text-slate-900 text-sm">Practice Questions Library</p>
              </div>
              <p className="text-slate-600 text-xs">
                200+ behavioral questions by skill
              </p>
            </div>
            <div className="bg-white rounded-lg p-3 border border-slate-200">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                <p className="text-slate-900 text-sm">Expert Video Examples</p>
              </div>
              <p className="text-slate-600 text-xs">
                Learn from successful answers
              </p>
            </div>
            <div className="bg-white rounded-lg p-3 border border-slate-200">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                <p className="text-slate-900 text-sm">Mock Interview Practice</p>
              </div>
              <p className="text-slate-600 text-xs">
                Simulate real interview scenarios
              </p>
            </div>
          </div>
        </div>
      </Card>

      {/* Learning Summary */}
      <Card className="p-6 bg-gradient-to-br from-purple-50 to-pink-50 border-purple-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-slate-900 text-lg mb-2">Estimated Learning Time</h3>
            <p className="text-slate-600 text-sm">
              Total time to acquire missing skills based on recommended resources
            </p>
          </div>
          <div className="text-right">
            <div className="text-4xl text-purple-600 mb-1">
              {mockReportData.totalLearningHours}
            </div>
            <div className="text-slate-600 text-sm">hours</div>
          </div>
        </div>
      </Card>
    </div>
  );
}
