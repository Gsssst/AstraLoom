import type { AxiosError } from 'axios';

type ApiErrorOptions = {
  fallback?: string;
  action?: string;
};

export type ApiErrorCategory = 'timeout' | 'network' | 'auth' | 'permission' | 'validation' | 'conflict' | 'upstream' | 'server' | 'unknown';
export type ApiErrorSeverity = 'info' | 'warning' | 'error';

export type ApiErrorDetails = {
  message: string;
  category: ApiErrorCategory;
  severity: ApiErrorSeverity;
  retryable: boolean;
  recovery: string;
  status?: number;
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

const isNetworkMessage = (message?: string) => {
  const lower = (message || '').toLowerCase();
  return lower.includes('network') || lower.includes('failed to fetch');
};

const detailsForStatus = (status: number, message: string, options: ApiErrorOptions = {}): ApiErrorDetails => {
  if (status === 401) {
    return {
      message,
      category: 'auth',
      severity: 'warning',
      retryable: false,
      recovery: '请重新登录后再执行此操作。',
      status,
    };
  }
  if (status === 403) {
    return {
      message,
      category: 'permission',
      severity: 'warning',
      retryable: false,
      recovery: '当前账号权限不足，如需继续请切换账号或联系管理员。',
      status,
    };
  }
  if (status === 400 || status === 422 || status === 413) {
    return {
      message,
      category: 'validation',
      severity: 'warning',
      retryable: false,
      recovery: '请检查表单内容、文件大小或必填项后再提交。',
      status,
    };
  }
  if (status === 409) {
    return {
      message,
      category: 'conflict',
      severity: 'warning',
      retryable: true,
      recovery: '当前数据状态可能已变化，请刷新页面或重新选择后再试。',
      status,
    };
  }
  if (status === 429 || status === 504) {
    return {
      message,
      category: 'timeout',
      severity: 'warning',
      retryable: true,
      recovery: '请求可能仍在排队或超时，请稍等片刻后重试。',
      status,
    };
  }
  if (status === 502 || status === 503) {
    return {
      message,
      category: 'upstream',
      severity: 'error',
      retryable: true,
      recovery: '上游服务暂时不可用，请检查服务端配置或稍后重试。',
      status,
    };
  }
  if (status >= 500) {
    return {
      message,
      category: 'server',
      severity: 'error',
      retryable: true,
      recovery: '服务器处理失败，请查看后端日志或稍后重试。',
      status,
    };
  }
  return {
    message,
    category: 'unknown',
    severity: 'warning',
    retryable: true,
    recovery: options.fallback || '请检查当前操作条件后重试。',
    status,
  };
};

const applyAction = (details: ApiErrorDetails, action?: string): ApiErrorDetails => ({
  ...details,
  message: withAction(details.message, action),
});

export const getApiErrorDetails = (error: unknown, options: ApiErrorOptions = {}): ApiErrorDetails => {
  const fallback = options.fallback || '操作失败，请稍后重试';
  const err = error as Partial<AxiosError> & { code?: string; message?: string };
  const status = err.response?.status;
  const parsed = responseMessage(err.response?.data);
  const message = parsed || (status && STATUS_MESSAGES[status]) || (err.message && err.message !== 'fail' ? err.message : fallback);

  if (err.code === 'ECONNABORTED') {
    return applyAction({
      message: '请求超时，请稍后重试',
      category: 'timeout',
      severity: 'warning',
      retryable: true,
      recovery: '请求耗时过长，建议稍后重试；如果持续发生，请检查后端或模型服务是否阻塞。',
      status,
    }, options.action);
  }

  if (!err.response && isNetworkMessage(err.message)) {
    return applyAction({
      message: '网络连接失败，请检查服务是否可用后重试',
      category: 'network',
      severity: 'error',
      retryable: true,
      recovery: '请确认前端、后端服务和网络连接正常，然后重新尝试。',
    }, options.action);
  }

  if (status) {
    return applyAction(detailsForStatus(status, message, options), options.action);
  }

  return applyAction({
    message,
    category: 'unknown',
    severity: 'warning',
    retryable: true,
    recovery: '请检查当前操作条件后重试；如果持续失败，请查看控制台或后端日志。',
  }, options.action);
};

export const getApiErrorMessage = (error: unknown, options: ApiErrorOptions = {}): string => {
  return getApiErrorDetails(error, options).message;
};

export const getHttpErrorDetails = (status: number, data?: unknown, options: ApiErrorOptions = {}): ApiErrorDetails => {
  const fallback = options.fallback || '操作失败，请稍后重试';
  const parsed = responseMessage(data);
  const message = parsed || STATUS_MESSAGES[status] || fallback;
  return applyAction(detailsForStatus(status, message, options), options.action);
};

export const getHttpErrorMessage = (status: number, data?: unknown, options: ApiErrorOptions = {}): string => {
  return getHttpErrorDetails(status, data, options).message;
};

export const formatApiError = getApiErrorMessage;
