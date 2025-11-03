// src/pages/LoginPage.tsx
import { useEffect, useState } from 'react';
import { Button } from '../components/ui/button';
import { createClient } from '../utils/supabase/client'; // use your factory (singleton inside)
import { Brain, Github } from 'lucide-react';

interface LoginPageProps {
  onLoginSuccess: (accessToken: string) => void;
}

const APP_URL = import.meta.env.VITE_APP_BASE_URL as string; // from .env

export function LoginPage({ onLoginSuccess }: LoginPageProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  // --- Auto check session or OAuth callback ---
  useEffect(() => {
    const supabase = createClient();

    const init = async () => {
      const { data, error } = await supabase.auth.getSession();
      if (error) {
        console.error('getSession error:', error);
      }
      if (data?.session?.access_token) {
        onLoginSuccess(data.session.access_token);
      }
    };
    init();

    // Subscribe to auth state changes
    const { data: sub } = supabase.auth.onAuthStateChange((_event, session) => {
      if (session?.access_token) {
        onLoginSuccess(session.access_token);
      }
    });

    return () => {
      sub.subscription.unsubscribe();
    };
  }, [onLoginSuccess]);

  // --- General OAuth handler (Google / GitHub) ---
  const startOAuth = async (provider: 'google' | 'github') => {
    setIsLoading(true);
    setError('');
    try {
      const supabase = createClient();
      const { error } = await supabase.auth.signInWithOAuth({
        provider,
        options: {
          redirectTo: APP_URL, // must also be whitelisted in Supabase Auth URL settings
        },
      });
      if (error) throw error;
      // Redirect happens; no need to getSession here
    } catch (err: any) {
      console.error(`${provider} login error:`, err);
      const docLink =
        provider === 'google'
          ? 'https://supabase.com/docs/guides/auth/social-login/auth-google'
          : 'https://supabase.com/docs/guides/auth/social-login/auth-github';
      setError(
        `Login failed. Please enable ${provider} OAuth in Supabase dashboard. See ${docLink}`
      );
      setIsLoading(false);
    }
  };

  // --- UI ---
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4">
      {/* background grid pattern */}
      <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAxMCAwIEwgMCAwIDAgMTAiIGZpbGw9Im5vbmUiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMC41IiBvcGFjaXR5PSIwLjEiLz48L3BhdHRlcm4+PC9kZWZzPjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9InVybCgjZ3JpZCkiLz48L3N2Zz4=')] opacity-20"></div>

      <div className="relative w-full max-w-md">
        <div className="bg-slate-800/50 backdrop-blur-xl rounded-2xl p-8 shadow-2xl border border-slate-700/50">
          {/* header */}
          <div className="flex flex-col items-center mb-8">
            <div className="bg-gradient-to-br from-purple-500 to-pink-500 p-3 rounded-2xl mb-4">
              <Brain className="w-10 h-10 text-white" />
            </div>
            <h1 className="text-white text-3xl mb-2">SkillMiner</h1>
            <p className="text-slate-400 text-center">
              AI-powered skill gap analysis and career recommendations
            </p>
          </div>

          {/* buttons */}
          <div className="space-y-4">
            <Button
              onClick={() => startOAuth('google')}
              disabled={isLoading}
              className="w-full bg-white hover:bg-gray-100 text-gray-900 h-12 rounded-xl"
            >
              <svg className="w-5 h-5 mr-3" viewBox="0 0 24 24">
                <path
                  fill="currentColor"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="currentColor"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="currentColor"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                />
                <path
                  fill="currentColor"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                />
              </svg>
              Continue with Google
            </Button>

            <Button
              onClick={() => startOAuth('github')}
              disabled={isLoading}
              className="w-full bg-slate-700 hover:bg-slate-600 text-white h-12 rounded-xl"
            >
              <Github className="w-5 h-5 mr-3" />
              Continue with GitHub
            </Button>
          </div>

          {/* error display */}
          {error && (
            <div className="mt-4 p-3 bg-red-500/10 border border-red-500/50 rounded-lg">
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}

          {/* footer */}
          <div className="mt-8 pt-6 border-t border-slate-700">
            <p className="text-slate-500 text-sm text-center">
              By continuing, you agree to our Terms of Service and Privacy Policy
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
