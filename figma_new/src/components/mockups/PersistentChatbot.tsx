import { useState } from 'react';
import { MessageCircle, X, Minus, Send, Sparkles, Loader2 } from 'lucide-react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Card } from '../ui/card';
import { Badge } from '../ui/badge';
import { ScrollArea } from '../ui/scroll-area';
import { projectId, publicAnonKey, edgeFunctionName } from '../../utils/supabase/info';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export function PersistentChatbot() {
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: 'Hi! I\'m your Study Assistant. I can help you reschedule tasks, explain topics, adjust difficulty, or start a mock interview. What would you like to do?'
    }
  ]);

  const quickActions = [
    { label: 'Reschedule', icon: '📅' },
    { label: 'Harder', icon: '⬆️' },
    { label: 'Easier', icon: '⬇️' },
    { label: 'Swap Resource', icon: '🔄' },
    { label: 'Add Day Off', icon: '🏖️' },
  ];

  const handleSend = async () => {
    if (!message.trim() || isLoading) return;
    
    const userMessage = message;
    const updatedMessages = [...messages, { role: 'user' as const, content: userMessage }];
    setMessages(updatedMessages);
    setMessage('');
    setIsLoading(true);
    
    try {
      // Get analysis ID from localStorage if available
      const analysisId = localStorage.getItem('currentAnalysisId');
      
      const response = await fetch(`https://${projectId}.supabase.co/functions/v1/${edgeFunctionName}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${publicAnonKey}`
        },
        body: JSON.stringify({
          message: userMessage,
          messages: updatedMessages.slice(0, -1), // Send conversation history without the last user message
          analysisId
        })
      });

      if (!response.ok) {
        throw new Error('Failed to get response from chatbot');
      }

      const data = await response.json();
      setMessages([...updatedMessages, { role: 'assistant', content: data.response }]);
    } catch (error) {
      console.error('Chat error:', error);
      setMessages([...updatedMessages, { 
        role: 'assistant', 
        content: 'Sorry, I encountered an error. Please try again or rephrase your question.' 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickAction = (action: string) => {
    setMessages([...messages,
      { role: 'user', content: action },
      { role: 'assistant', content: `Processing "${action}" request... (Mockup mode)` }
    ]);
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-full p-4 shadow-lg hover:shadow-xl transition-all z-50 group"
      >
        <MessageCircle className="w-6 h-6" />
        <div className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
          1
        </div>
        <div className="absolute bottom-full right-0 mb-2 hidden group-hover:block">
          <div className="bg-slate-900 text-white text-sm px-3 py-2 rounded-lg whitespace-nowrap">
            Your Study Assistant
          </div>
        </div>
      </button>
    );
  }

  if (isMinimized) {
    return (
      <div className="fixed bottom-6 right-6 bg-white rounded-lg shadow-xl border border-slate-200 p-4 z-50 w-80">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="bg-gradient-to-r from-purple-600 to-indigo-600 rounded-full p-2">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <span className="text-slate-900">Study Assistant</span>
          </div>
          <div className="flex gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsMinimized(false)}
            >
              <MessageCircle className="w-4 h-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsOpen(false)}
            >
              <X className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <Card className="fixed bottom-6 right-6 w-96 h-[600px] shadow-2xl border-slate-200 z-50 flex flex-col">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white p-4 rounded-t-lg flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5" />
          <div>
            <h3 className="font-medium">Your Study Assistant</h3>
            <p className="text-xs text-purple-100">Always here to help</p>
          </div>
        </div>
        <div className="flex gap-1">
          <Button
            variant="ghost"
            size="sm"
            className="text-white hover:bg-white/20"
            onClick={() => setIsMinimized(true)}
          >
            <Minus className="w-4 h-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="text-white hover:bg-white/20"
            onClick={() => setIsOpen(false)}
          >
            <X className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="p-3 border-b border-slate-200 bg-slate-50">
        <div className="flex flex-wrap gap-2">
          {quickActions.map((action) => (
            <Badge
              key={action.label}
              variant="outline"
              className="cursor-pointer hover:bg-purple-50 hover:border-purple-300"
              onClick={() => handleQuickAction(action.label)}
            >
              <span className="mr-1">{action.icon}</span>
              {action.label}
            </Badge>
          ))}
        </div>
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-lg p-3 ${
                  msg.role === 'user'
                    ? 'bg-purple-600 text-white'
                    : 'bg-slate-100 text-slate-900'
                }`}
              >
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-slate-100 text-slate-900 rounded-lg p-3">
                <Loader2 className="w-4 h-4 animate-spin" />
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Input */}
      <div className="p-4 border-t border-slate-200">
        <div className="flex gap-2">
          <Input
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && !isLoading && handleSend()}
            placeholder="Ask me anything..."
            className="flex-1"
            disabled={isLoading}
          />
          <Button
            onClick={handleSend}
            className="bg-purple-600 hover:bg-purple-700"
            disabled={isLoading || !message.trim()}
          >
            {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          </Button>
        </div>
      </div>
    </Card>
  );
}
