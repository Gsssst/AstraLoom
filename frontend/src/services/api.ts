import axios from 'axios';
import type { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';

const api: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// 请求拦截器 —— 自动附加 Authorization
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('access_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let isRefreshing = false;
let refreshPromise: Promise<any> | null = null;

// 统一响应拦截器
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const config = error.config as any;
    if (!config) return Promise.reject(error);

    // 1. 网络错误/超时 → 重试 1 次
    if (!config._retry && !error.response) {
      config._retry = true;
      await new Promise(r => setTimeout(r, 1000));
      return api(config);
    }

    // 2. 401 → 刷新 Token
    if (error.response?.status === 401 && !config._retryRefresh) {
      const url = config.url || '';
      if (url.includes('/auth/login') || url.includes('/auth/register') || url.includes('/auth/refresh')) {
        return Promise.reject(error);
      }

      config._retryRefresh = true;
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        localStorage.removeItem('access_token');
        return Promise.reject(error);
      }

      if (!isRefreshing) {
        isRefreshing = true;
        refreshPromise = axios.post('/api/auth/refresh', { refresh_token: refreshToken })
          .then(res => {
            localStorage.setItem('access_token', res.data.access_token);
            localStorage.setItem('refresh_token', res.data.refresh_token);
            isRefreshing = false;
            refreshPromise = null;
            return res.data.access_token;
          })
          .catch(() => {
            isRefreshing = false;
            refreshPromise = null;
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            throw error;
          });
      }

      try {
        const newToken = await refreshPromise;
        config.headers.Authorization = `Bearer ${newToken}`;
        return api(config);
      } catch {
        return Promise.reject(error);
      }
    }

    return Promise.reject(error);
  }
);

export default api;
