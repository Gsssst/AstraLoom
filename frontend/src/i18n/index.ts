import enUS from 'antd/locale/en_US';
import zhCN from 'antd/locale/zh_CN';
import { messages, type Language, type MessageKey } from './messages';

export type { Language, MessageKey };

export const DEFAULT_LANGUAGE: Language = 'zh';
export const SUPPORTED_LANGUAGES: Language[] = ['zh', 'en'];

export const antdLocales = {
  zh: zhCN,
  en: enUS,
} as const;

export const normalizeLanguage = (value: string | null | undefined): Language => (
  value === 'en' || value === 'zh' ? value : DEFAULT_LANGUAGE
);

export const translate = (
  language: Language,
  key: MessageKey,
  params?: Record<string, string | number>,
) => {
  let text: string = messages[language][key] || messages[DEFAULT_LANGUAGE][key] || key;
  if (params) {
    Object.entries(params).forEach(([name, value]) => {
      text = text.replaceAll(`{${name}}`, String(value));
    });
  }
  return text;
};

export { messages };
