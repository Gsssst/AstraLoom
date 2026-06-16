import { useCallback, useState } from 'react';
import { message } from 'antd';
import api from '../services/api';
import { getApiErrorMessage } from '../services/apiError';

export const CHAT_ATTACHMENT_MAX_BYTES = 50 * 1024 * 1024;
export const CHAT_ATTACHMENT_MAX_MB = 50;
export const CHAT_IMAGE_OPTIMIZED_MAX_EDGE = 1600;
export const CHAT_IMAGE_OPTIMIZED_QUALITY = 0.82;
export const CHAT_ATTACHMENT_ACCEPT = 'image/*,.pdf,.docx,.doc,.pptx,.ppt';

export interface ChatAttachment {
  file: File;
  text: string;
  extracting: boolean;
  id: string;
  dataUrl?: string;
  optimizedDataUrl?: string;
  mimeType?: string;
  optimizedMimeType?: string;
  optimizationStatus?: 'pending' | 'optimized' | 'fallback';
  optimizationNote?: string;
  remembered?: boolean;
}

export interface ChatImageAttachmentPayload {
  filename: string;
  mime_type: string;
  data_url: string;
}

const createAttachmentId = () => Math.random().toString(36).slice(2);

const isImageAttachment = (file: ChatAttachment) => file.file.type.startsWith('image/');

const optimizeImageDataUrl = async (file: File): Promise<Pick<ChatAttachment, 'optimizedDataUrl' | 'optimizedMimeType' | 'optimizationStatus' | 'optimizationNote'>> => {
  if (typeof window === 'undefined' || typeof document === 'undefined' || typeof Image === 'undefined') {
    return { optimizationStatus: 'fallback', optimizationNote: '当前环境不支持图片优化' };
  }

  const objectUrl = URL.createObjectURL(file);
  try {
    const image = await new Promise<HTMLImageElement>((resolve, reject) => {
      const img = new Image();
      img.onload = () => resolve(img);
      img.onerror = () => reject(new Error('图片解码失败'));
      img.src = objectUrl;
    });
    const sourceWidth = image.naturalWidth || image.width;
    const sourceHeight = image.naturalHeight || image.height;
    if (!sourceWidth || !sourceHeight) {
      return { optimizationStatus: 'fallback', optimizationNote: '图片尺寸不可读' };
    }
    const scale = Math.min(1, CHAT_IMAGE_OPTIMIZED_MAX_EDGE / Math.max(sourceWidth, sourceHeight));
    const width = Math.max(1, Math.round(sourceWidth * scale));
    const height = Math.max(1, Math.round(sourceHeight * scale));
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext('2d');
    if (!ctx) return { optimizationStatus: 'fallback', optimizationNote: '图片优化不可用' };
    ctx.drawImage(image, 0, 0, width, height);
    const optimizedMimeType = file.type === 'image/png' ? 'image/png' : 'image/jpeg';
    const optimizedDataUrl = canvas.toDataURL(optimizedMimeType, optimizedMimeType === 'image/jpeg' ? CHAT_IMAGE_OPTIMIZED_QUALITY : undefined);
    const optimizedBytes = Math.round((optimizedDataUrl.length * 3) / 4);
    const originalKb = Math.max(1, Math.round(file.size / 1024));
    const optimizedKb = Math.max(1, Math.round(optimizedBytes / 1024));
    return {
      optimizedDataUrl,
      optimizedMimeType,
      optimizationStatus: 'optimized',
      optimizationNote: `${sourceWidth}x${sourceHeight} → ${width}x${height}，约 ${originalKb}KB → ${optimizedKb}KB`,
    };
  } catch {
    return { optimizationStatus: 'fallback', optimizationNote: '图片优化失败，使用原始载荷' };
  } finally {
    URL.revokeObjectURL(objectUrl);
  }
};

export const useChatAttachments = () => {
  const [attachedFiles, setAttachedFiles] = useState<ChatAttachment[]>([]);
  const [rememberedAttachments, setRememberedAttachments] = useState<ChatAttachment[]>([]);

  const removeAttachment = useCallback((id: string) => {
    setAttachedFiles(prev => prev.filter(file => file.id !== id));
  }, []);

  const removeRememberedAttachment = useCallback((id: string) => {
    setRememberedAttachments(prev => prev.filter(file => file.id !== id));
  }, []);

  const clearAttachments = useCallback(() => {
    setAttachedFiles([]);
  }, []);

  const clearRememberedAttachments = useCallback(() => {
    setRememberedAttachments([]);
  }, []);

  const rememberAttachments = useCallback((files: ChatAttachment[]) => {
    const readyFiles = files.filter(file => !file.extracting && (file.text || file.dataUrl));
    if (readyFiles.length === 0) return;
    setRememberedAttachments(prev => {
      const existingIds = new Set(prev.map(file => file.id));
      const next = [...prev];
      readyFiles.forEach(file => {
        if (!existingIds.has(file.id)) next.push({ ...file, remembered: true });
      });
      return next;
    });
  }, []);

  const extractFiles = useCallback(async (files: File[]) => {
    for (const file of files) {
      if (file.size > CHAT_ATTACHMENT_MAX_BYTES) {
        message.warning(`${file.name} 超过${CHAT_ATTACHMENT_MAX_MB}MB`);
        continue;
      }
      const id = createAttachmentId();
      setAttachedFiles(prev => [...prev, { file, text: '', extracting: true, id }]);
      const formData = new FormData();
      formData.append('file', file);
      try {
        const response = await api.post('/chat-sessions/extract-file', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
        const isImage = file.type.startsWith('image/');
        const optimized = isImage ? await optimizeImageDataUrl(file) : {};
        setAttachedFiles(prev => prev.map(item => item.id === id
          ? {
              ...item,
              text: response.data.extracted_text || '',
              extracting: false,
              dataUrl: response.data.data_url || undefined,
              mimeType: response.data.mime_type || undefined,
              ...optimized,
            }
          : item));
      } catch (error) {
        setAttachedFiles(prev => prev.filter(item => item.id !== id));
        message.error(getApiErrorMessage(error, { fallback: `${file.name} 解析失败` }));
      }
    }
  }, []);

  const openAttachmentPicker = useCallback(() => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = CHAT_ATTACHMENT_ACCEPT;
    input.multiple = true;
    input.onchange = async () => {
      await extractFiles(Array.from(input.files || []));
    };
    input.click();
  }, [extractFiles]);

  const readyAttachments = useCallback((files: ChatAttachment[] = attachedFiles) => (
    files.filter(file => !file.extracting && (file.text || file.dataUrl))
  ), [attachedFiles]);

  const mergedReadyAttachments = useCallback((files: ChatAttachment[] = attachedFiles) => {
    const merged: ChatAttachment[] = [];
    const seen = new Set<string>();
    [...rememberedAttachments, ...readyAttachments(files)].forEach(file => {
      if (seen.has(file.id)) return;
      seen.add(file.id);
      merged.push(file);
    });
    return merged;
  }, [attachedFiles, readyAttachments, rememberedAttachments]);

  const attachedTextContext = useCallback((files: ChatAttachment[] = attachedFiles) => (
    files
      .filter(file => !isImageAttachment(file))
      .map(file => file.text)
      .filter(Boolean)
      .join('\n\n---\n\n')
  ), [attachedFiles]);

  const imageAttachmentPayloads = useCallback((files: ChatAttachment[] = attachedFiles): ChatImageAttachmentPayload[] => (
    files
      .filter(file => isImageAttachment(file) && (file.optimizedDataUrl || file.dataUrl))
      .map(file => ({
        filename: file.file.name,
        mime_type: file.optimizedMimeType || file.mimeType || file.file.type || 'image/png',
        data_url: file.optimizedDataUrl || file.dataUrl || '',
      }))
  ), [attachedFiles]);

  const attachmentStatusLabel = useCallback((file: ChatAttachment) => {
    if (file.extracting) return '解析中';
    if (isImageAttachment(file)) {
      if (file.optimizationStatus === 'optimized') return file.remembered ? '已记忆 · 已优化' : '就绪 · 已优化';
      if (file.optimizationStatus === 'fallback') return file.remembered ? '已记忆 · 原图' : '就绪 · 原图';
      return file.dataUrl ? (file.remembered ? '已记忆' : '就绪') : '异常';
    }
    if (file.text) return file.remembered ? '已记忆' : '就绪';
    return '异常';
  }, []);

  return {
    attachedFiles,
    setAttachedFiles,
    rememberedAttachments,
    setRememberedAttachments,
    removeAttachment,
    removeRememberedAttachment,
    clearAttachments,
    clearRememberedAttachments,
    rememberAttachments,
    extractFiles,
    openAttachmentPicker,
    readyAttachments,
    mergedReadyAttachments,
    attachedTextContext,
    imageAttachmentPayloads,
    attachmentStatusLabel,
    hasExtractingAttachments: attachedFiles.some(file => file.extracting),
    hasImageAttachment: [...attachedFiles, ...rememberedAttachments].some(file => isImageAttachment(file)),
    hasRememberedAttachments: rememberedAttachments.length > 0,
  };
};

export default useChatAttachments;
