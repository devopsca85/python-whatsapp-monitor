'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface User {
  id: string;
  username: string;
  role: 'admin' | 'user';
  email?: string;
  assignedServers?: string[];
  lastLogin?: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  isAdmin: boolean;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const AUTH_API_URL = process.env.NEXT_PUBLIC_AUTH_API_URL || 'http://localhost:5001';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Load token from localStorage on mount
  useEffect(() => {
    const storedToken = localStorage.getItem('auth_token');
    if (storedToken) {
      validateToken(storedToken);
    } else {
      setLoading(false);
    }
  }, []);

  // Validate token
  const validateToken = async (authToken: string) => {
    try {
      const response = await fetch(`${AUTH_API_URL}/api/auth/validate`, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setToken(authToken);
        setUser({
          id: data.user.userId,
          username: data.user.username,
          role: data.user.role,
          assignedServers: data.user.assignedServers || []
        });
      } else {
        // Token invalid, clear it
        localStorage.removeItem('auth_token');
        setToken(null);
        setUser(null);
      }
    } catch (error) {
      console.error('Token validation error:', error);
      localStorage.removeItem('auth_token');
      setToken(null);
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  // Login function
  const login = async (username: string, password: string) => {
    try {
      console.log('Attempting login to:', `${AUTH_API_URL}/api/auth/login`);
      
      const response = await fetch(`${AUTH_API_URL}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password })
      });

      console.log('Login response status:', response.status);

      if (!response.ok) {
        const error = await response.json().catch(() => ({ error: 'Network error' }));
        console.error('Login failed:', error);
        throw new Error(error.error || 'Login failed');
      }

      const data = await response.json();
      console.log('Login successful:', data);
      
      // Store token
      localStorage.setItem('auth_token', data.token);
      setToken(data.token);
      setUser(data.user);
      
    } catch (error) {
      console.error('Login error:', error);
      // Provide more helpful error message
      if (error instanceof TypeError && error.message === 'Failed to fetch') {
        throw new Error('Cannot connect to authentication server. Please check if the auth server is running.');
      }
      throw error;
    }
  };

  // Logout function
  const logout = () => {
    localStorage.removeItem('auth_token');
    setToken(null);
    setUser(null);
  };

  const value = {
    user,
    token,
    login,
    logout,
    isAuthenticated: !!user && !!token,
    isAdmin: user?.role === 'admin',
    loading
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}



