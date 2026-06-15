import { create } from 'zustand';
import api from '../services/api';
import { getApiErrorMessage } from '../services/apiError';

interface Message {
  id?: string;
  role: string;
  content: string;
  references?: {
    title: string;
    arxiv_id?: string | null;
    year?: number | null;
    similarity?: number;
    url?: string;
    source?: string;
    provider?: string;
  }[];
  created_at?: string;
  _streaming?: boolean;
  reasoning?: string;
  thinking_started_at?: number;
  _reasoningStreaming?: boolean;
  research_scout?: {
    enabled?: boolean;
    query?: string;
    candidate_count?: number;
    candidates?: any[];
  };
}

interface Session {
  id: string;
  title: string;
  rag_enabled: boolean;
  message_count: number;
  last_message: string | null;
  created_at: string;
  updated_at: string;
}

interface ChatSessionState {
  sessions: Session[];
  currentSessionId: string | null;
  messages: Message[];
  loading: boolean;
  sending: boolean;
  drawerOpen: boolean;

  loadSessions: () => Promise<void>;
  createSession: () => Promise<string>;
  selectSession: (id: string) => Promise<void>;
  deleteSession: (id: string) => Promise<void>;
  sendMessage: (content: string) => Promise<void>;
  toggleRag: (enabled: boolean) => Promise<void>;
  setDrawerOpen: (open: boolean) => void;
}

export const useChatSessionStore = create<ChatSessionState>((set, get) => ({
  sessions: [],
  currentSessionId: null,
  messages: [],
  loading: false,
  sending: false,
  drawerOpen: false,

  loadSessions: async () => {
    set({ loading: true });
    try {
      const res = await api.get('/chat-sessions/');
      set({ sessions: res.data, loading: false });
    } catch (error) {
      set({ loading: false });
      throw error;
    }
  },

  createSession: async () => {
    try {
      const res = await api.post('/chat-sessions/', { title: '新对话', rag_enabled: true });
      const session = res.data;
      set(s => ({
        sessions: [session, ...s.sessions],
        currentSessionId: session.id,
        messages: [],
      }));
      return session.id;
    } catch (error) {
      throw error;
    }
  },

  selectSession: async (id: string) => {
    set({ currentSessionId: id, loading: true });
    try {
      const res = await api.get(`/chat-sessions/${id}/messages`);
      set({ messages: res.data, loading: false });
    } catch (error) {
      set({ loading: false });
      throw error;
    }
  },

  deleteSession: async (id: string) => {
    try {
      await api.delete(`/chat-sessions/${id}`);
      set(s => {
        const sessions = s.sessions.filter(sess => sess.id !== id);
        const currentSessionId = s.currentSessionId === id
          ? (sessions[0]?.id || null)
          : s.currentSessionId;
        return { sessions, currentSessionId };
      });
      // 如果切换了会话，加载新会话的消息
      const { currentSessionId } = get();
      if (currentSessionId && currentSessionId !== id) {
        get().selectSession(currentSessionId);
      } else {
        set({ messages: [] });
      }
    } catch (error) {
      throw error;
    }
  },

  sendMessage: async (content: string) => {
    const { currentSessionId } = get();
    if (!currentSessionId) return;

    set({ sending: true });
    try {
      const res = await api.post(`/chat-sessions/${currentSessionId}/send`, { content });
      const { message, reply, session_title } = res.data;
      set(s => ({
        messages: [...s.messages, message, reply],
        sessions: s.sessions.map(sess =>
          sess.id === currentSessionId
            ? { ...sess, title: session_title, message_count: sess.message_count + 2, last_message: reply.content?.slice(0, 100) }
            : sess
        ),
      }));
    } catch (e: any) {
      const errMsg = getApiErrorMessage(e, { fallback: '发送失败' });
      set(s => ({
        messages: [...s.messages, { role: 'assistant', content: `❌ ${errMsg}` }],
      }));
    }
    finally { set({ sending: false }); }
  },

  toggleRag: async (enabled: boolean) => {
    const { currentSessionId } = get();
    if (!currentSessionId) return;
    set(s => ({
      sessions: s.sessions.map(sess =>
        sess.id === currentSessionId ? { ...sess, rag_enabled: enabled } : sess
      ),
    }));
  },

  setDrawerOpen: (open: boolean) => set({ drawerOpen: open }),
}));
