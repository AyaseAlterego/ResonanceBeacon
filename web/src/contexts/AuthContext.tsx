import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';

interface AuthContextType {
  apiKey: string | null;
  isAuthenticated: boolean;
  login: (key: string) => Promise<boolean>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [apiKey, setApiKey] = useState<string | null>(() => localStorage.getItem('hermes_api_key'));

  const login = useCallback(async (key: string): Promise<boolean> => {
    try {
      const apiBase = import.meta.env.VITE_API_BASE || '';
      const res = await fetch(`${apiBase}/健康/健康`, {
        headers: { 'Authorization': `Bearer ${key}` }
      });
      if (res.ok) {
        setApiKey(key);
        localStorage.setItem('hermes_api_key', key);
        return true;
      }
      return false;
    } catch {
      return false;
    }
  }, []);

  const logout = useCallback(() => {
    setApiKey(null);
    localStorage.removeItem('hermes_api_key');
  }, []);

  return (
    <AuthContext.Provider value={{ apiKey, isAuthenticated: !!apiKey, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
