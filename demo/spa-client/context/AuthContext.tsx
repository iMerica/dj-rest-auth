'use client';

import api from '@/lib/api';
import { deleteCookie, setCookie } from 'cookies-next';
import { useRouter } from 'next/navigation';
import React, { createContext, useContext, useEffect, useState } from 'react';

interface User {
  pk: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (data: any) => Promise<void>;
  logout: () => void;
  register: (data: any) => Promise<void>;
  checkAuth: () => Promise<void>;
  verifyMfa: (code: string, ephemeralToken: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  const checkAuth = async () => {
    try {
      const response = await api.get('/dj-rest-auth/user/');
      setUser(response.data);
    } catch (error) {
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkAuth();
  }, []);

  const login = async (data: any) => {
    try {
      const response = await api.post('/dj-rest-auth/login/', data);
      if (response.data.mfa_required) {
        router.push(`/mfa/verify?token=${response.data.ephemeral_token}`);
        return;
      }
      if (response.data.key) {
        setCookie('auth_token', response.data.key);
        await checkAuth();
        router.push('/');
      }
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  };

  const verifyMfa = async (code: string, ephemeralToken: string) => {
    try {
      const response = await api.post('/dj-rest-auth/mfa/verify/', {
        code,
        ephemeral_token: ephemeralToken,
      });
      if (response.data.key) {
        setCookie('auth_token', response.data.key);
        await checkAuth();
        router.push('/');
      }
    } catch (error) {
      console.error('MFA verify failed:', error);
      throw error;
    }
  };

  const logout = async () => {
    try {
      await api.post('/dj-rest-auth/logout/');
    } catch (error) {
      console.error('Logout failed', error);
    } finally {
      deleteCookie('auth_token');
      setUser(null);
      router.push('/login');
    }
  };

  const register = async (data: any) => {
    try {
      const response = await api.post('/dj-rest-auth/registration/', data);
      if (response.data.key) {
        setCookie('auth_token', response.data.key);
        await checkAuth();
        router.push('/');
      }
    } catch (error) {
      console.error('Registration failed:', error);
      throw error;
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, register, checkAuth, verifyMfa }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
