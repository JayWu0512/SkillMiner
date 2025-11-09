import { useState, useRef, useEffect } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Brain, Send, Menu, FileText, LogOut, MessageSquare } from 'lucide-react';
import { SkillReport } from './SkillReport';
import { projectId, publicAnonKey, edgeFunctionName } from '../utils/supabase/info';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface ChatbotPageProps {
  accessToken: string;
  analysisId: string;
  onLogout: () => void;
}

export function ChatbotPage({ accessToken, analysisId, onLogout }: ChatbotPageProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [showReport, setShowReport] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Load initial welcome message and analysis summary
    const loadInitialData = async () => {
      try {
        const response = await fetch(
          `https://${projectId}.supabase.co/functions/v1/${edgeFunctionName}/analysis/${analysisId}`,
          {
            headers: {
              'Authorization': `Bearer ${accessToken}`,
            },
          }
        );

        if (response.ok) {
          const data = await response.json();
          setMessages([
            {
              id: '1',
              role: 'assistant',
              content: `Hello! I've analyzed your resume against the job description. Your overall match score is **${data.matchScore}%**.\n\nI found ${data.matchingSkills} matching skills and ${data.missingSkills} skills you could develop. Would you like me to explain the results or help you create a learning plan?`,
              timestamp: new Date(),
            },
          ]);
        }
      } catch (error) {
        console.error('Error loading initial data:', error);
      }
    };

    loadInitialData();
  }, [analysisId, accessToken]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isSending) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsSending(true);

    try {
      const response = await fetch(
        `https://${projectId}.supabase.co/functions/v1/${edgeFunctionName}/chat`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            analysisId,
            message: input,
          }),
        }
      );

      if (response.ok) {
        const data = await response.json();
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: data.response,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, assistantMessage]);
      } else {
        throw new Error('Failed to get response');
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex h-screen bg-slate-50">
      {/* Sidebar */}
      <div
        className={`${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        } fixed lg:relative lg:translate-x-0 z-30 w-72 bg-white border-r border-slate-200 h-full transition-transform duration-300`}
      >
        <div className="p-4 border-b border-slate-200">
          <div className="flex items-center gap-2 mb-4">
            <div className="bg-gradient-to-br from-purple-500 to-pink-500 p-2 rounded-lg">
              <Brain className="w-5 h-5 text-white" />
            </div>
            <h2 className="text-slate-900">SkillMiner</h2>
          </div>
          <Button
            onClick={() => setShowReport(!showReport)}
            className="w-full justify-start gap-2 bg-purple-50 text-purple-700 hover:bg-purple-100"
          >
            <FileText className="w-4 h-4" />
            {showReport ? 'Back to Chat' : 'View Full Report'}
          </Button>
        </div>

        <div className="p-4 space-y-2">
          <div className="text-slate-500 text-sm mb-2">Quick Actions</div>
          <Button
            variant="ghost"
            className="w-full justify-start text-sm"
            onClick={() => setInput('Tell me about the missing hard skills')}
          >
            💼 Missing Hard Skills
          </Button>
          <Button
            variant="ghost"
            className="w-full justify-start text-sm"
            onClick={() => setInput('What soft skills should I develop?')}
          >
            🤝 Soft Skills Gap
          </Button>
          <Button
            variant="ghost"
            className="w-full justify-start text-sm"
            onClick={() => setInput('Create a learning plan for me')}
          >
            📚 Learning Plan
          </Button>
          <Button
            variant="ghost"
            className="w-full justify-start text-sm"
            onClick={() => setInput('How can I improve my resume?')}
          >
            ✍️ Resume Tips
          </Button>
        </div>

        <div className="absolute bottom-4 left-4 right-4">
          <Button
            variant="outline"
            onClick={onLogout}
            className="w-full gap-2"
          >
            <LogOut className="w-4 h-4" />
            Logout
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b border-slate-200 px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="lg:hidden"
            >
              <Menu className="w-5 h-5" />
            </Button>
            <MessageSquare className="w-5 h-5 text-purple-500" />
            <h1 className="text-slate-900">Career Assistant</h1>
          </div>
        </div>

        {/* Content Area */}
        {showReport ? (
          <div className="flex-1 overflow-y-auto">
            <SkillReport accessToken={accessToken} analysisId={analysisId} />
          </div>
        ) : (
          <>
            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${
                    message.role === 'user' ? 'justify-end' : 'justify-start'
                  }`}
                >
                  <div
                    className={`max-w-2xl rounded-2xl px-4 py-3 ${
                      message.role === 'user'
                        ? 'bg-purple-600 text-white'
                        : 'bg-white border border-slate-200 text-slate-900'
                    }`}
                  >
                    <div
                      className="whitespace-pre-wrap"
                      dangerouslySetInnerHTML={{
                        __html: message.content.replace(
                          /\*\*(.*?)\*\*/g,
                          '<strong>$1</strong>'
                        ),
                      }}
                    />
                  </div>
                </div>
              ))}
              {isSending && (
                <div className="flex justify-start">
                  <div className="bg-white border border-slate-200 rounded-2xl px-4 py-3">
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce delay-100"></div>
                      <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce delay-200"></div>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="bg-white border-t border-slate-200 p-4">
              <div className="max-w-4xl mx-auto flex gap-2">
                <Input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask me anything about your skills, career path, or learning recommendations..."
                  className="flex-1"
                  disabled={isSending}
                />
                <Button
                  onClick={handleSend}
                  disabled={!input.trim() || isSending}
                  className="bg-purple-600 hover:bg-purple-700"
                >
                  <Send className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-20 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
}
