import { useState, useEffect, useRef } from 'react';
import { MessageCircle, X, Minus, Send, Sparkles, Loader2, Trash2 } from 'lucide-react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Card } from '../ui/card';
import { Badge } from '../ui/badge';
import { ScrollArea, ScrollBar } from '../ui/scroll-area';
import { sendChatMessage } from '../../services/api';
import { createClient } from '../../utils/supabase/client';
import { projectId, publicAnonKey, edgeFunctionName } from '../../utils/supabase/info';


interface Message {
  role: 'user' | 'assistant';
  content: string;
  citations?: string[];
  id?: string; // Optional ID for database records
}

export function PersistentChatbot() {
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const [resumeText, setResumeText] = useState<string>('');
  const [userId, setUserId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const historyLoadedRef = useRef(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: 'Hi! I\'m your Career Assistant. I can help you with skill analysis, career recommendations, and answer questions about your resume. What would you like to know?'
    }
  ]);

  // Load user session and chat history on mount
  useEffect(() => {
    // Only load history once on initial mount
    if (historyLoadedRef.current) return;
    
    const loadUserAndHistory = async () => {
      // Show loading immediately
      setIsLoadingHistory(true);
      
      try {
        const supabase = createClient();
        const { data: { session } } = await supabase.auth.getSession();
        
        if (session?.user?.id) {
          setUserId(session.user.id);
          await loadChatHistory(session.user.id);
          historyLoadedRef.current = true;
        } else {
          setIsLoadingHistory(false);
        }
      } catch (error) {
        console.error('Error loading user session:', error);
        setIsLoadingHistory(false);
      }
    };

    loadUserAndHistory();

    // Listen for auth state changes (only for login/logout, not window open/close)
    const supabase = createClient();
    const { data: { subscription } } = supabase.auth.onAuthStateChange(async (event, session) => {
      // Only reload history on actual auth state changes (SIGNED_IN, SIGNED_OUT)
      // Ignore TOKEN_REFRESHED and other events that don't change auth state
      if (event === 'SIGNED_IN' && session?.user?.id) {
        // Only reload if history hasn't been loaded yet for this user
        // This prevents reloading when window is minimized/closed/reopened
        if (!historyLoadedRef.current) {
          setIsLoadingHistory(true);
          setUserId(session.user.id);
          await loadChatHistory(session.user.id);
          historyLoadedRef.current = true;
        }
      } else if (event === 'SIGNED_OUT') {
        setUserId(null);
        setIsLoadingHistory(false);
        historyLoadedRef.current = false;
        // Reset to default message when user logs out
        setMessages([{
          role: 'assistant',
          content: 'Hi! I\'m your Career Assistant. I can help you with skill analysis, career recommendations, and answer questions about your resume. What would you like to know?'
        }]);
      }
      // For all other events (TOKEN_REFRESHED, etc.), do nothing - preserve messages
    });

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  // Load chat history from Supabase
  const loadChatHistory = async (userId: string) => {
    try {
      const supabase = createClient();
      
      // Set a timeout to prevent hanging
      const timeoutId = setTimeout(() => {
        setIsLoadingHistory(false);
        // Show default message if loading takes too long
        setMessages([{
          role: 'assistant',
          content: 'Hi! I\'m your Career Assistant. I can help you with skill analysis, career recommendations, and answer questions about your resume. What would you like to know?'
        }]);
      }, 3000); // 3 second timeout
      
      const { data, error } = await supabase
        .from('chat_messages')
        .select('*')
        .eq('user_id', userId)
        .order('created_at', { ascending: true })
        .limit(100); // Limit to 100 messages for faster loading

      clearTimeout(timeoutId);

      if (error) {
        console.error('Error loading chat history:', error);
        setIsLoadingHistory(false);
        // Show default message on error
        setMessages([{
          role: 'assistant',
          content: 'Hi! I\'m your Career Assistant. I can help you with skill analysis, career recommendations, and answer questions about your resume. What would you like to know?'
        }]);
        return;
      }

      if (data && data.length > 0) {
        const loadedMessages: Message[] = data.map((msg: any) => ({
          role: msg.role as 'user' | 'assistant',
          content: msg.content,
          citations: msg.citations && Array.isArray(msg.citations) ? msg.citations : [],
          id: msg.id,
        }));
        setMessages(loadedMessages);
      } else {
        // No history, keep default welcome message
        setMessages([{
          role: 'assistant',
          content: 'Hi! I\'m your Career Assistant. I can help you with skill analysis, career recommendations, and answer questions about your resume. What would you like to know?'
        }]);
      }
    } catch (error) {
      console.error('Error loading chat history:', error);
      // Show default message on error
      setMessages([{
        role: 'assistant',
        content: 'Hi! I\'m your Career Assistant. I can help you with skill analysis, career recommendations, and answer questions about your resume. What would you like to know?'
      }]);
    } finally {
      setIsLoadingHistory(false);
    }
  };

  // Save message to Supabase
  const saveMessageToDatabase = async (message: Message) => {
    if (!userId) return;

    try {
      const supabase = createClient();
      const { error } = await supabase
        .from('chat_messages')
        .insert({
          user_id: userId,
          role: message.role,
          content: message.content,
          citations: message.citations || [],
        } as any);

      if (error) {
        console.error('Error saving message to database:', error);
      }
    } catch (error) {
      console.error('Error saving message to database:', error);
    }
  };

  // Clear chat history from database and UI
  const clearChatHistory = async () => {
    // Clear UI immediately for better UX
    setMessages([{
      role: 'assistant',
      content: 'Hi! I\'m your Career Assistant. I can help you with skill analysis, career recommendations, and answer questions about your resume. What would you like to know?'
    }]);

    if (!userId) {
      // If not logged in, UI is already cleared
      return;
    }

    // Delete from database in background (non-blocking)
    try {
      const supabase = createClient();
      
      // Delete all messages for the current user
      const { error } = await supabase
        .from('chat_messages')
        .delete()
        .eq('user_id', userId);

      if (error) {
        console.error('Error clearing chat history:', error);
      }
    } catch (error) {
      console.error('Error clearing chat history:', error);
    }
  };

  // Load resume text from localStorage on mount and listen for changes
  useEffect(() => {
    const loadResumeText = () => {
      const storedResumeText = localStorage.getItem('resumeText');
      if (storedResumeText) {
        setResumeText(storedResumeText);
      }
    };

    // Load on mount
    loadResumeText();

    // Listen for storage events (when resume is uploaded on another page)
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'resumeText' && e.newValue) {
        setResumeText(e.newValue);
      }
    };

    window.addEventListener('storage', handleStorageChange);

    // Also listen for custom events (same-page updates)
    const handleCustomStorage = () => {
      loadResumeText();
    };

    window.addEventListener('resumeTextUpdated', handleCustomStorage);

    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('resumeTextUpdated', handleCustomStorage);
    };
  }, []);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (messagesEndRef.current && scrollAreaRef.current) {
      // Use setTimeout to ensure DOM is updated
      setTimeout(() => {
        // Find the Radix ScrollArea viewport element
        const scrollContainer = scrollAreaRef.current?.querySelector('[data-slot="scroll-area-viewport"]') as HTMLElement;
        if (scrollContainer) {
          scrollContainer.scrollTop = scrollContainer.scrollHeight;
        }
      }, 100);
    }
  }, [messages, isLoading]);

  const quickActions = [
    { label: 'Reschedule', icon: '📅' },
    { label: 'Harder', icon: '⬆️' },
    { label: 'Easier', icon: '⬇️' },
    { label: 'Swap Resource', icon: '🔄' },
    { label: 'Add Day Off', icon: '🏖️' },
  ];

  const handleSend = async () => {
    if (!message.trim() || isLoading) return;
    
    const userMessage = message.trim();
    const userMsgObj: Message = { role: 'user', content: userMessage };
    const updatedMessages = [...messages, userMsgObj];
    setMessages(updatedMessages);
    setMessage('');
    setIsLoading(true);
    
    // Save user message to database
    await saveMessageToDatabase(userMsgObj);
    
    try {
      console.log('Sending chat message:', userMessage);
      console.log('Resume text length:', resumeText?.length || 0);
      

      // Use the API service to send chat message
      const data = await sendChatMessage(
        userMessage,
        resumeText || undefined
      );

      console.log('✅ Chat response received:', {
        replyLength: data.reply.length,
        citationsCount: data.citations?.length || 0,
      });

      const botMessage: Message = {
        role: 'assistant',
        content: data.reply,
        citations: data.citations,
      };
      const finalMessages = [...updatedMessages, botMessage];
      setMessages(finalMessages);
      
      // Save assistant message to database
      await saveMessageToDatabase(botMessage);
    } catch (error: any) {
      console.error('Chat error:', error);
      console.error('Error details:', {
        name: error?.name,
        message: error?.message,
        stack: error?.stack,
      });
      
      const errorMessage: Message = {
        role: 'assistant',
        content: error?.message || 'Sorry, I encountered an error. Please try again or rephrase your question.'
      };
      const finalMessages = [...updatedMessages, errorMessage];
      setMessages(finalMessages);
      
      // Save error message to database
      await saveMessageToDatabase(errorMessage);
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
    <Card 
      className="fixed bottom-6 right-6 shadow-2xl border-slate-200 z-50 flex flex-col overflow-hidden"
      style={{ 
        width: '450px', 
        height: '600px', 
        maxWidth: '450px', 
        maxHeight: '600px', 
        minWidth: '450px', 
        minHeight: '600px',
        boxSizing: 'border-box'
      }}
    >
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white p-4 rounded-t-lg flex items-center justify-between flex-shrink-0" style={{ width: '100%', boxSizing: 'border-box' }}>
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
            className="text-white hover:bg-white/20 text-xs px-2"
            onClick={clearChatHistory}
            title="Start a new chat"
          >
            <Trash2 className="w-3 h-3 mr-1" />
            <span>New Chat</span>
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="text-white hover:bg-white/20"
            onClick={() => setIsMinimized(true)}
            title="Minimize"
          >
            <Minus className="w-4 h-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="text-white hover:bg-white/20"
            onClick={() => setIsOpen(false)}
            title="Close"
          >
            <X className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="p-3 border-b border-slate-200 bg-slate-50 flex-shrink-0 min-w-0" style={{ width: '100%', boxSizing: 'border-box', maxWidth: '100%' }}>
        <div className="flex flex-wrap gap-2 min-w-0" style={{ maxWidth: '100%' }}>
          {quickActions.map((action) => (
            <Badge
              key={action.label}
              variant="outline"
              className="cursor-pointer hover:bg-purple-50 hover:border-purple-300 break-words"
              onClick={() => handleQuickAction(action.label)}
            >
              <span className="mr-1">{action.icon}</span>
              {action.label}
            </Badge>
          ))}
        </div>
      </div>

      {/* Messages - Scrollable Area */}
      <div ref={scrollAreaRef} className="flex-1 min-h-0 max-h-full overflow-hidden" style={{ width: '100%', maxWidth: '100%', boxSizing: 'border-box' }}>
        <ScrollArea className="h-full w-full">
          <div className="p-4 space-y-4" style={{ minWidth: '100%', boxSizing: 'border-box', overflowX: 'auto' }}>
            {messages.map((msg, index) => (
              <div
                key={index}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                style={{ width: '100%', minWidth: 'fit-content' }}
              >
                <div
                  className={`rounded-lg p-3 ${
                    msg.role === 'user'
                      ? 'bg-purple-600 text-white'
                      : 'bg-slate-100 text-slate-900'
                  }`}
                  style={{ 
                    maxWidth: '85%', 
                    minWidth: 'fit-content',
                    whiteSpace: 'pre-wrap',
                    overflowWrap: 'normal',
                    wordBreak: 'normal'
                  }}
                >
                  <p className="text-sm" style={{ whiteSpace: 'pre-wrap', overflowWrap: 'normal', wordBreak: 'normal' }}>{msg.content}</p>
                  {/* Show citations if available */}
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-slate-300">
                      <div className="text-xs text-slate-500 mb-1">References:</div>
                      <div className="flex flex-wrap gap-1">
                        {msg.citations.map((cite, idx) => (
                          <Badge
                            key={idx}
                            variant="outline"
                            className="text-xs bg-white text-purple-700 border-purple-300 break-words max-w-full"
                            style={{ wordBreak: 'break-word', overflowWrap: 'anywhere' }}
                          >
                            <span className="break-words" style={{ wordBreak: 'break-word', overflowWrap: 'anywhere' }}>{cite}</span>
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
            {isLoadingHistory && (
              <div className="flex justify-center items-center py-8">
                <div className="flex flex-col items-center gap-2">
                  <Loader2 className="w-5 h-5 animate-spin text-purple-600" />
                  <span className="text-sm text-slate-600">Loading chat history...</span>
                </div>
              </div>
            )}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-slate-100 text-slate-900 rounded-lg p-3">
                  <Loader2 className="w-4 h-4 animate-spin" />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
          <ScrollBar orientation="horizontal" />
          <ScrollBar orientation="vertical" />
        </ScrollArea>
      </div>

      {/* Input - Always visible at bottom */}
      <div className="p-4 border-t border-slate-200 bg-white flex-shrink-0 min-w-0" style={{ width: '100%', maxWidth: '100%', boxSizing: 'border-box' }}>
        <div className="flex gap-2 min-w-0" style={{ width: '100%', maxWidth: '100%' }}>
          <Input
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && !isLoading && handleSend()}
            placeholder="Ask me anything..."
            className="flex-1 min-w-0"
            style={{ maxWidth: '100%', boxSizing: 'border-box' }}
            disabled={isLoading}
          />
          <Button
            onClick={handleSend}
            className="bg-purple-600 hover:bg-purple-700 flex-shrink-0"
            disabled={isLoading || !message.trim()}
          >
            {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          </Button>
        </div>
      </div>
    </Card>
  );
}
