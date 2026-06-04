import { create } from 'zustand';
import api from '../services/api';

export interface User {
  id: string;
  username: string;
  email: string;
  role: string;
  is_active: boolean;
  avatar?: string;
  display_name?: string;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  fetchUser: () => Promise<void>;
  updateUser: (updates: Partial<User>) => void;
}

const hasToken = () => !!localStorage.getItem('access_token');

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: hasToken(),
  isLoading: false,

  login: async (username: string, password: string) => {
    set({ isLoading: true });
    try {
      const response = await api.post('/auth/login', { username, password });
      const { access_token, refresh_token } = response.data;
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      const userRes = await api.get('/auth/me');
      set({ user: userRes.data, isAuthenticated: true, isLoading: false });
    } catch (error: any) {
      set({ isLoading: false });
      const msg = error.response?.data?.detail || '登录失败';
      throw new Error(msg);
    }
  },

  register: async (username: string, email: string, password: string) => {
    set({ isLoading: true });
    try {
      const response = await api.post('/auth/register', { username, email, password });
      const { access_token, refresh_token } = response.data;
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      const userRes = await api.get('/auth/me');
      set({ user: userRes.data, isAuthenticated: true, isLoading: false });
    } catch (error: any) {
      set({ isLoading: false });
      const msg = error.response?.data?.detail || '注册失败';
      throw new Error(msg);
    }
  },

  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    set({ user: null, isAuthenticated: false });
  },

  updateUser: (updates: Partial<User>) => {
    set((state) => ({
      user: state.user ? { ...state.user, ...updates } : null,
    }));
  },

  fetchUser: async () => {
    if (!hasToken()) {
      set({ user: null, isAuthenticated: false });
      return;
    }
    // 延迟一小段时间，避免后端还在启动时请求失败
    await new Promise(r => setTimeout(r, 300));
    try {
      const res = await api.get('/auth/me');
      set({ user: res.data, isAuthenticated: true });
    } catch {
      // Token 过期，尝试用 refresh_token 刷新
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const refreshRes = await api.post('/auth/refresh', { refresh_token: refreshToken });
          localStorage.setItem('access_token', refreshRes.data.access_token);
          localStorage.setItem('refresh_token', refreshRes.data.refresh_token);
          const userRes = await api.get('/auth/me');
          set({ user: userRes.data, isAuthenticated: true });
          return;
        } catch {
          // 刷新失败
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          set({ user: null, isAuthenticated: false });
          return;
        }
      }
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      set({ user: null, isAuthenticated: false });
    }
  },
}));
