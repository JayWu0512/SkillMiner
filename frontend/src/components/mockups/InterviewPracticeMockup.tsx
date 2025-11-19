import { useState } from 'react';
import { Play, Video, ArrowLeft, ChevronRight, Circle, CheckCircle2, Lightbulb } from 'lucide-react';
import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Header } from '../Header';
import { Brain } from 'lucide-react';

const behavioralQuestions = [
  { id: 1, question: 'Tell me about yourself.', completed: false },
  { id: 2, question: 'Why are you interested in this position?', completed: false },
  { id: 3, question: 'What are your strengths?', completed: false },
  { id: 4, question: 'Why do you want to work for us?', completed: false },
  { id: 5, question: 'Tell me about a time you overcame a challenge.', completed: false },
];

type MockupPage = "login" | "upload" | "report" | "dashboard" | "plan" | "coding" | "interview" | "profile" | "resume";

interface InterviewPracticeMockupProps {
  onNavigate?: (page: MockupPage) => void;
}

export function InterviewPracticeMockup({ onNavigate }: InterviewPracticeMockupProps) {
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const [recordedTime, setRecordedTime] = useState(0);
  const [showTips, setShowTips] = useState(false);
  const [questions, setQuestions] = useState(behavioralQuestions);

  const current = questions[currentQuestion];
  const completedCount = questions.filter(q => q.completed).length;

  const handleNextQuestion = () => {
    const updatedQuestions = [...questions];
    updatedQuestions[currentQuestion].completed = true;
    setQuestions(updatedQuestions);
    setIsRecording(false);
    setRecordedTime(0);
    
    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-slate-50">
      <Header 
        activePage="practice" 
        onNavigate={(page) => {
          const pageMap: Record<string, MockupPage> = {
            'today': 'dashboard',
            'study-plan': 'plan',
            'coding-practice': 'coding',
            'interview-practice': 'interview',
            'profile': 'profile'
          };
          onNavigate?.(pageMap[page] || 'interview');
        }}
        onLogout={() => onNavigate?.('login')}
      />
      <div className="flex flex-1 overflow-hidden">
        {/* Left Sidebar - Question List */}
        <div className="w-64 bg-gradient-to-b from-purple-700 to-purple-900 text-white flex flex-col">
          <div className="p-6 border-b border-purple-600">
            <Button 
              variant="ghost" 
              className="text-white hover:bg-purple-600 -ml-2 mb-4"
              onClick={() => onNavigate?.('plan')}
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Plan
            </Button>
          
          <div className="flex items-center justify-center mb-4">
            <div className="relative">
              <div className="w-24 h-24 rounded-full border-4 border-purple-400 flex items-center justify-center">
                <div className="text-center">
                  <div className="text-3xl">{completedCount}</div>
                  <div className="text-xs text-purple-200">/{questions.length}</div>
                </div>
              </div>
            </div>
          </div>

          <div className="text-center">
            <h2 className="text-lg mb-1">Behavioral Interview</h2>
            <div className="text-xs text-purple-200">Level 1</div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          <div className="space-y-2">
            {questions.map((q, index) => (
              <button
                key={q.id}
                onClick={() => setCurrentQuestion(index)}
                className={`w-full text-left p-3 rounded-lg transition-colors flex items-start gap-3 ${
                  index === currentQuestion
                    ? 'bg-purple-600 text-white'
                    : 'text-purple-100 hover:bg-purple-600/50'
                }`}
              >
                <div className="flex-shrink-0 mt-0.5">
                  {q.completed ? (
                    <CheckCircle2 className="w-4 h-4 text-green-300" />
                  ) : (
                    <Circle className="w-4 h-4" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-medium mb-1">{index + 1}.</div>
                  <div className="text-sm leading-tight">{q.question}</div>
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="p-4 border-t border-purple-600">
          <Button className="w-full bg-purple-500 hover:bg-purple-400 text-white">
            Edit Questions
          </Button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col bg-white">
        {/* Header */}
        <div className="border-b border-slate-200 px-8 py-6">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl text-purple-600">{current.question}</h1>
            <Badge variant="outline" className="text-slate-600">
              Step {currentQuestion + 1} of {questions.length}
            </Badge>
          </div>
        </div>

        {/* Content Grid */}
        <div className="flex-1 p-8">
          <div className="grid grid-cols-2 gap-6 h-full max-w-6xl mx-auto">
            {/* Left - Example Video */}
            <Card className="p-6 flex flex-col">
              <div className="flex-1 bg-slate-100 rounded-lg overflow-hidden relative flex items-center justify-center">
                {/* Video placeholder with play button */}
                <div className="absolute inset-0 bg-gradient-to-br from-purple-900 to-purple-700 flex items-center justify-center">
                  <div className="text-center text-white">
                    <div className="w-20 h-20 bg-white/20 rounded-full flex items-center justify-center mx-auto mb-4 cursor-pointer hover:bg-white/30 transition-colors">
                      <Play className="w-10 h-10 ml-1" />
                    </div>
                    <p className="text-sm">Watch example answer</p>
                  </div>
                </div>
              </div>
              
              <div className="mt-4 flex justify-between items-center">
                <div className="text-sm text-slate-600">Example Response</div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowTips(!showTips)}
                  className="border-purple-300 text-purple-600 hover:bg-purple-50"
                >
                  <Lightbulb className="w-4 h-4 mr-2" />
                  Tips
                </Button>
              </div>

              {showTips && (
                <Card className="mt-4 p-4 bg-yellow-50 border-yellow-200">
                  <h3 className="text-sm font-medium text-slate-900 mb-2">Tips for answering:</h3>
                  <ul className="text-sm text-slate-700 space-y-1">
                    <li>• Keep your answer between 1-2 minutes</li>
                    <li>• Start with your current role and background</li>
                    <li>• Highlight relevant experience and skills</li>
                    <li>• End with why you're interested in this position</li>
                  </ul>
                </Card>
              )}
            </Card>

            {/* Right - Recording Area */}
            <Card className="p-6 flex flex-col">
              <div className="flex-1 bg-slate-800 rounded-lg overflow-hidden relative flex items-center justify-center">
                {!isRecording ? (
                  <div className="text-center text-white">
                    <div className="text-lg mb-6">Record your answer for this question</div>
                    <Button
                      onClick={() => setIsRecording(true)}
                      className="bg-red-600 hover:bg-red-700 text-white px-8 py-6 h-auto text-lg rounded-full"
                    >
                      <div className="w-3 h-3 bg-white rounded-full mr-3"></div>
                      Start Recording
                    </Button>
                  </div>
                ) : (
                  <div className="text-center text-white">
                    <div className="w-4 h-4 bg-red-600 rounded-full mx-auto mb-4 animate-pulse"></div>
                    <div className="text-2xl mb-2">
                      {Math.floor(recordedTime / 60)}:{(recordedTime % 60).toString().padStart(2, '0')}
                    </div>
                    <div className="text-sm text-slate-300">Recording in progress...</div>
                    <Button
                      onClick={() => {
                        setIsRecording(false);
                        setRecordedTime(45);
                      }}
                      variant="outline"
                      className="mt-6 border-white text-white hover:bg-white/10"
                    >
                      Stop Recording
                    </Button>
                  </div>
                )}
              </div>

              {recordedTime > 0 && !isRecording && (
                <div className="mt-4">
                  <div className="flex items-center justify-between text-sm text-slate-600 mb-2">
                    <span>Your recording ({recordedTime}s)</span>
                    <button className="text-purple-600 hover:underline">Re-record</button>
                  </div>
                  <Progress value={100} className="h-2 bg-slate-200" />
                </div>
              )}
            </Card>
          </div>

          {/* Navigation Buttons */}
          <div className="flex justify-center gap-4 mt-8 max-w-6xl mx-auto">
            <Button
              variant="outline"
              size="lg"
              onClick={() => setCurrentQuestion(Math.max(0, currentQuestion - 1))}
              disabled={currentQuestion === 0}
              className="min-w-[120px]"
            >
              Back
            </Button>
            <Button
              size="lg"
              onClick={handleNextQuestion}
              disabled={!isRecording && recordedTime === 0}
              className="bg-green-600 hover:bg-green-700 text-white min-w-[160px]"
            >
              Next question
              <ChevronRight className="w-4 h-4 ml-2" />
            </Button>
          </div>

          {/* Progress Indicator */}
          <div className="mt-6 max-w-6xl mx-auto">
            <div className="flex items-center justify-center gap-2">
              {questions.map((q, index) => (
                <div
                  key={q.id}
                  className={`h-2 flex-1 max-w-[60px] rounded-full transition-colors ${
                    q.completed
                      ? 'bg-green-500'
                      : index === currentQuestion
                      ? 'bg-purple-500'
                      : 'bg-slate-200'
                  }`}
                />
              ))}
            </div>
            <div className="text-center text-sm text-slate-600 mt-2">
              {completedCount} of {questions.length} questions completed
            </div>
          </div>
        </div>
      </div>
      </div>
    </div>
  );
}
