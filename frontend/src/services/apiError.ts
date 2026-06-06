import type { AxiosError } from 'axios';

type ApiErrorOptions = {
  fallback?: string;
  action?: string;
};

const STATUS_MESSAGES: Record<number, string> = {
  400: '请求参数有误，请检查后重试',
  401: '登录状态已失效，请重新登录',
  403: '当前账号没有权限执行此操作',
  404: '请求的资源不存在或已被删除',
  409: '当前状态不允许执行此操作',
  413: '上传内容过大，请压缩后重试',
  422: '提交内容校验失败，请检查输入',
  429: '请求过于频繁，请稍后重试',
  500: '服务器处理失败，请稍后重试',
  502: '上游服务暂时不可用，请稍后重试',
  503: '服务暂时不可用，请稍后重试',
  504: '请求超时，请稍后重试',
};

const isRecord = (value: unknown): value is Record<string, unknown> => (
  typeof value === 'object' && value !== null
);

const firstString = (value: unknown): string | null => {
  if (typeof value === 'string' && value.trim()) return value.trim();
  if (Array.isArray(value)) {
    for (const item of value) {
      const nested = firstString(item);
      if (nested) return nested;
    }
  }
  if (isRecord(value)) {
    for (const key of ['message', 'msg', 'detail', 'reason']) {
      const nested = firstString(value[key]);
      if (nested) return nested;
    }
  }
  return null;
};

const responseMessage = (data: unknown): string | null => {
  if (!data) return null;
  if (typeof data === 'string') return data.trim() || null;
  if (!isRecord(data)) return null;

  const envelope = data.error;
  if (isRecord(envelope)) {
    const message = firstString(envelope.message) || firstString(envelope.detail);
    if (message) return message;
  }

  const detail = data.detail;
  if (typeof detail === 'string' && detail.trim()) return detail.trim();
  const validation = firstString(detail);
  if (validation) return validation;

  return firstString(data.message);
};

const withAction = (message: string, action?: string): string => {
  if (!action) return message;
  if (message.startsWith(action)) return message;
  return `${action}：${message}`;
};

export const getApiErrorMessage = (error: unknown, options: ApiErrorOptions = {}): string => {
  const fallback = options.fallback || '操作失败，请稍后重试';
  const err = error as Partial<AxiosError> & { code?: string; message?: string };

  const data = err.response?.data;
  const parsed = responseMessage(data);
  if (parsed) return withAction(parsed, options.action);

  if (err.code === 'ECONNABORTED') {
    return withAction('请求超时，请稍后重试', options.action);
  }

  if (err.response?.status && STATUS_MESSAGES[err.response.status]) {
    return withAction(STATUS_MESSAGES[err.response.status], options.action);
  }

  if (!err.response && err.message) {
    const lower = err.message.toLowerCase();
    if (lower.includes('network') || lower.includes('failed to fetch')) {
      return withAction('网络连接失败，请检查服务是否可用后重试', options.action);
    }
  }

  if (err.message && err.message !== 'fail') {
    return withAction(err.message, options.action);
  }

  return withAction(fallback, options.action);
};

export const getHttpErrorMessage = (status: number, data?: unknown, options: ApiErrorOptions = {}): string => {
  const fallback = options.fallback || '操作失败，请稍后重试';
  const parsed = responseMessage(data);
  if (parsed) return withAction(parsed, options.action);
  if (STATUS_MESSAGES[status]) return withAction(STATUS_MESSAGES[status], options.action);
  return withAction(fallback, options.action);
};

export const formatApiError = getApiErrorMessage;
