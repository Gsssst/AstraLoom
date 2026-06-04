import { create } from 'zustand';
import { theme as antdTheme } from 'antd';

const { defaultAlgorithm, darkAlgorithm } = antdTheme;

export interface ThemePreset {
  id: string;
  name: string;
  icon: string;
  algorithm: any;
  token: {
    colorPrimary: string;
    colorBgLayout?: string;
    borderRadius?: number;
    colorBgContainer?: string;
    colorTextBase?: string;
  };
}

export const THEME_PRESETS: ThemePreset[] = [
  {
    id: 'light',
    name: '极简白',
    icon: '☀️',
    algorithm: defaultAlgorithm,
    token: { colorPrimary: '#1677ff', borderRadius: 6 },
  },
  {
    id: 'dark',
    name: '暗夜黑',
    icon: '🌙',
    algorithm: darkAlgorithm,
    token: { colorPrimary: '#1677ff', borderRadius: 6 },
  },
  {
    id: 'ocean',
    name: '深海蓝',
    icon: '🌊',
    algorithm: defaultAlgorithm,
    token: { colorPrimary: '#0ea5e9', borderRadius: 8, colorBgLayout: '#f0f9ff' },
  },
  {
    id: 'forest',
    name: '竹林绿',
    icon: '🎋',
    algorithm: defaultAlgorithm,
    token: { colorPrimary: '#10b981', borderRadius: 8, colorBgLayout: '#f0fdf4' },
  },
  {
    id: 'sunset',
    name: '日落橙',
    icon: '🌅',
    algorithm: defaultAlgorithm,
    token: { colorPrimary: '#f97316', borderRadius: 8, colorBgLayout: '#fff7ed' },
  },
  {
    id: 'lavender',
    name: '薰衣草紫',
    icon: '💜',
    algorithm: defaultAlgorithm,
    token: { colorPrimary: '#8b5cf6', borderRadius: 8, colorBgLayout: '#faf5ff' },
  },
];

interface ThemeState {
  current: ThemePreset;
  showThinking: boolean;
  setTheme: (id: string) => void;
  setShowThinking: (show: boolean) => void;
}

export const useThemeStore = create<ThemeState>((set) => {
  const savedId = localStorage.getItem('theme') || 'light';
  const preset = THEME_PRESETS.find(t => t.id === savedId) || THEME_PRESETS[0];
  const savedThinking = localStorage.getItem('showThinking') === 'true';

  return {
    current: preset,
    showThinking: savedThinking,
    setTheme: (id: string) => {
      const theme = THEME_PRESETS.find(t => t.id === id) || THEME_PRESETS[0];
      localStorage.setItem('theme', id);
      set({ current: theme });
    },
    setShowThinking: (show: boolean) => {
      localStorage.setItem('showThinking', String(show));
      set({ showThinking: show });
    },
  };
});
