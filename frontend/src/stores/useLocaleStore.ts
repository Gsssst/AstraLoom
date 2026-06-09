import { create } from 'zustand';
import { DEFAULT_LANGUAGE, normalizeLanguage, translate, type Language, type MessageKey } from '../i18n';

interface LocaleState {
  language: Language;
  setLanguage: (language: Language) => void;
  t: (key: MessageKey, params?: Record<string, string | number>) => string;
}

const STORAGE_KEY = 'uiLanguage';

const initialLanguage = normalizeLanguage(localStorage.getItem(STORAGE_KEY) || DEFAULT_LANGUAGE);

export const useLocaleStore = create<LocaleState>((set, get) => ({
  language: initialLanguage,
  setLanguage: (language) => {
    localStorage.setItem(STORAGE_KEY, language);
    document.documentElement.lang = language === 'en' ? 'en' : 'zh-CN';
    set({ language });
  },
  t: (key, params) => translate(get().language, key, params),
}));

document.documentElement.lang = initialLanguage === 'en' ? 'en' : 'zh-CN';
