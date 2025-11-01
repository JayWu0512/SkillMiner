import { useState, useEffect } from 'react';
import { Card } from './ui/card';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { Button } from './ui/button';
import { Separator } from './ui/separator';
import { TrendingUp, Target, Award, Clock, ExternalLink, CheckCircle2, XCircle } from 'lucide-react';
import { projectId } from '../utils/supabase/info';

interface SkillData {
  name: string;
  level?: 'Beginner' | 'Intermediate' | 'Advanced' | 'Expert';
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

  useEffect(() => {
    const loadReport = async () => {
      try {
        const response = await fetch(
          `https://${projectId}.supabase.co/functions/v1/make-server-b8961ff5/report/${analysisId}`,
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
            <div className={`${getScoreBg(reportData.matchScore)} p-3 rounded-xl`}>
              <TrendingUp className={`w-6 h-6 ${getScoreColor(reportData.matchScore)}`} />
            </div>
            <div>
              <h2 className="text-slate-900 text-xl">Overall Match Score</h2>
              <p className="text-slate-600 text-sm">How well you match the job requirements</p>
            </div>
          </div>
          <div className={`text-5xl ${getScoreColor(reportData.matchScore)}`}>
            {reportData.matchScore}%
          </div>
        </div>
        <Progress value={reportData.matchScore} className="h-3" />
        <p className="text-slate-600 text-sm mt-4">
          {reportData.matchScore >= 80
            ? 'Excellent match! You have most of the required skills.'
            : reportData.matchScore >= 60
            ? 'Good match with room for improvement in some areas.'
            : 'Some skill gaps identified. Focus on developing missing skills.'}
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
              {reportData.hardSkills.existing.map((skill, index) => (
                <Badge
                  key={index}
                  className="bg-green-100 text-green-700 hover:bg-green-200"
                >
                  {skill.name}
                  {skill.level && ` • ${skill.level}`}
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
              {reportData.hardSkills.missing.map((skill, index) => (
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
              {reportData.softSkills.existing.map((skill, index) => (
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
            <div className="space-y-4">
              {reportData.softSkills.missing.map((skill, index) => (
                <div key={index} className="bg-slate-50 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-slate-900">{skill.name}</h4>
                    <Badge variant="outline" className="text-red-600 border-red-300">
                      To Develop
                    </Badge>
                  </div>
                  {skill.resources && skill.resources.length > 0 && (
                    <div className="space-y-2">
                      <p className="text-slate-600 text-sm mb-2">Development Resources:</p>
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
              {reportData.totalLearningHours}
            </div>
            <div className="text-slate-600 text-sm">hours</div>
          </div>
        </div>
      </Card>
    </div>
  );
}
