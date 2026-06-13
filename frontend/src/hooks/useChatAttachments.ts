import { useCallback, useState } from 'react';
import { message } from 'antd';
import api from '../services/api';
import { getApiErrorMessage } from '../services/apiError';

export const CHAT_ATTACHMENT_MAX_BYTES = 50 * 1024 * 1024;
export const CHAT_ATTACHMENT_MAX_MB = 50;

export interface ChatAttachment {
  file: File;
  text: string;
  extracting: boolean;
  id: string;
  dataUrl?: string;
  mimeType?: string;
}

export interface ChatImageAttachmentPayload {
  filename: string;
  mime_type: string;
  data_url: string;
}

const createAttachmentId = () => Math.random().toString(36).slice(2);

export const useChatAttachments = () => {
  const [attachedFiles, setAttachedFiles] = useState<ChatAttachment[]>([]);

  const removeAttachment = useCallback((id: string) => {
    setAttachedFiles(prev => prev.filter(file => file.id !== id));
  }, []);

  const clearAttachments = useCallback(() => {
    setAttachedFiles([]);
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
        setAttachedFiles(prev => prev.map(item => item.id === id
          ? {
              ...item,
              text: response.data.extracted_text || '',
              extracting: false,
              dataUrl: response.data.data_url || undefined,
              mimeType: response.data.mime_type || undefined,
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
    input.accept = 'image/*,.pdf';
    input.multiple = true;
    input.onchange = async () => {
      await extractFiles(Array.from(input.files || []));
    };
    input.click();
  }, [extractFiles]);

  const attachedTextContext = useCallback((files: ChatAttachment[] = attachedFiles) => (
    files
      .filter(file => !file.file.type.startsWith('image/'))
      .map(file => file.text)
      .filter(Boolean)
      .join('\n\n---\n\n')
  ), [attachedFiles]);

  const imageAttachmentPayloads = useCallback((files: ChatAttachment[] = attachedFiles): ChatImageAttachmentPayload[] => (
    files
      .filter(file => file.file.type.startsWith('image/') && file.dataUrl)
      .map(file => ({
        filename: file.file.name,
        mime_type: file.mimeType || file.file.type || 'image/png',
        data_url: file.dataUrl || '',
      }))
  ), [attachedFiles]);

  return {
    attachedFiles,
    setAttachedFiles,
    removeAttachment,
    clearAttachments,
    extractFiles,
    openAttachmentPicker,
    attachedTextContext,
    imageAttachmentPayloads,
    hasExtractingAttachments: attachedFiles.some(file => file.extracting),
    hasImageAttachment: attachedFiles.some(file => file.file.type.startsWith('image/')),
  };
};

export default useChatAttachments;
