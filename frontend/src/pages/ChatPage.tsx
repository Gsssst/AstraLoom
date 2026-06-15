import React, { useEffect, useRef, useState } from 'react';
import { Input, Button, Tag, Typography, Space, Empty, message, List, Popconfirm, Avatar, Tooltip, theme, Image, Select, Skeleton, Dropdown, Drawer, Grid, Modal, Popover } from 'antd';
import {
  SendOutlined, PlusOutlined, DeleteOutlined, UserOutlined, RobotOutlined,
  MenuOutlined, UploadOutlined, FilePdfOutlined, CloseOutlined,
  CopyOutlined, RedoOutlined, EditOutlined, SearchOutlined, MoreOutlined,
  DatabaseOutlined, GlobalOutlined, ExportOutlined, MessageOutlined,
  BulbOutlined, FileTextOutlined, ExperimentOutlined, SwapOutlined,
  HighlightOutlined, EyeOutlined, ClockCircleOutlined, StopOutlined,
  InfoCircleOutlined, CloudDownloadOutlined, CheckCircleOutlined,
} from '@ant-design/icons';
import { useChatSessionStore } from '../stores/useChatSessionStore';
import { useThemeStore } from '../stores/useThemeStore';
import api from '../services/api';
import { getApiErrorMessage, getHttpErrorMessage } from '../services/apiError';
import Markdown from '../components/Markdown';
import ThinkingPanel from '../components/ThinkingPanel';
import useChatAutoScroll from '../hooks/useChatAutoScroll';
import useChatAttachments from '../hooks/useChatAttachments';

const { Text } = Typography;

const emptySuggestions = [
  { icon: <MessageOutlined />, label: '提问讨论', text: '请帮我分析当前研究问题，并给出可以继续深入的方向' },
  { icon: <FileTextOutlined />, label: '上传论文', text: '请帮我总结上传论文的核心贡献、方法和实验结果' },
  { icon: <SearchOutlined />, label: '检索知识库', text: '请从知识库中检索与我的研究问题最相关的论文' },
  { icon: <BulbOutlined />, label: '脑暴灵感', text: '请基于当前研究方向提出三个值得验证的新想法' },
];

const promptShortcuts = [
  { icon: <FileTextOutlined />, label: '总结论文', text: '请总结这篇论文的核心贡献、方法和实验结果' },
  { icon: <ExperimentOutlined />, label: '找研究 Gap', text: '基于以上论文，请分析当前研究存在哪些未解决的问题和研究空白' },
  { icon: <SwapOutlined />, label: '对比方法', text: '请对比分析以下论文的方法、数据集和实验结果' },
  { icon: <BulbOutlined />, label: '生成 Idea', text: '基于这些论文，请提出3个创新性的研究想法' },
  { icon: <HighlightOutlined />, label: '润色文本', text: '请将以下文本润色为学术风格：' },
];

interface ChatModelMetadata {
  provider?: string;
  label?: string;
  model?: string;
  configured?: boolean;
  capabilities?: {
    rag?: boolean;
    web_search?: boolean;
    thinking?: boolean;
    vision?: boolean;
  };
  search_depth?: string;
  image_attachments?: number;
}

type ChatAssistantMode = 'general' | 'research_scout';

interface ResearchScoutCandidate {
  rank: number;
  title: string;
  authors?: string[];
  abstract?: string;
  year?: number | null;
  source?: string;
  source_url?: string | null;
  pdf_url?: string | null;
  arxiv_id?: string | null;
  doi?: string | null;
  citation_count?: number;
  remote_id?: string;
  ingest_token?: string;
  why_interesting?: string;
  why_useful?: string;
  caveat?: string;
}

interface ResearchScoutPayload {
  enabled?: boolean;
  query?: string;
  candidate_count?: number;
  candidates?: ResearchScoutCandidate[];
}

interface StreamMetaContent {
  references?: any[];
  model?: ChatModelMetadata;
  research_scout?: ResearchScoutPayload | null;
}

const formatSessionTime = (value: string) => {
  const date = new Date(value);
  const now = new Date();
  const sameDay = date.toDateString() === now.toDateString();
  return sameDay
    ? date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    : date.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' });
};

const appendAssistantError = (content: string) => {
  useChatSessionStore.setState(s => ({
    messages: [...s.messages, { role: 'assistant', content: `❌ ${content}`, created_at: new Date().toISOString() }],
  }));
};

const parseStreamError = async (response: Response, fallback: string) => {
  let data: unknown;
  try {
    data = await response.clone().json();
  } catch {
    try { data = await response.clone().text(); } catch { data = undefined; }
  }
  return getHttpErrorMessage(response.status, data, { fallback });
};

const formatElapsed = (ms: number) => {
  const seconds = Math.max(0, ms) / 1000;
  if (seconds < 10) return `${seconds.toFixed(1)}s`;
  return `${Math.round(seconds)}s`;
};

const referenceTooltip = (ref: any) => {
  if (ref.source === 'web') {
    return `网页检索来源：${ref.provider || 'unknown'}；查询：${ref.retrieval_query || ref.query || 'unknown'}`;
  }
  if (ref.source === 'research_scout') {
    return `论文猎手候选：${ref.provider || 'scholarly'}；${ref.why_useful || '可作为后续阅读候选'}`;
  }
  return ref.arxiv_id ? `知识库论文：${ref.arxiv_id}` : '知识库检索来源';
};

const referenceLabel = (ref: any) => {
  const title = ref.title || ref.url || ref.arxiv_id || '未命名来源';
  const source = ref.source === 'web' ? '网页来源' : ref.source === 'research_scout' ? '论文猎手' : '知识库';
  const provider = ref.source === 'web' && ref.provider ? ` · ${ref.provider}` : '';
  const scoutProvider = ref.source === 'research_scout' && ref.provider ? ` · ${ref.provider}` : '';
  const year = ref.year ? ` (${ref.year})` : '';
  return `${source}${provider}${scoutProvider} · ${title.slice(0, 40)}${title.length > 40 ? '...' : ''}${year}`;
};

const ChatPage: React.FC = () => {
  const { token } = theme.useToken();
  const screens = Grid.useBreakpoint();
  const isMobile = !screens.md;
  const { sessions, currentSessionId, messages, loading, sending, drawerOpen, loadSessions, createSession, selectSession, deleteSession, toggleRag, setDrawerOpen } = useChatSessionStore();

  const [input, setInput] = useState('');
  const {
    attachedFiles,
    setAttachedFiles,
    rememberedAttachments,
    removeAttachment,
    removeRememberedAttachment,
    openAttachmentPicker,
    rememberAttachments,
    mergedReadyAttachments,
    attachedTextContext,
    imageAttachmentPayloads,
    attachmentStatusLabel,
    hasExtractingAttachments,
    hasImageAttachment,
  } = useChatAttachments();
  const [searchDepth, setSearchDepth] = useState<'quick' | 'standard' | 'deep'>('standard');
  const [webSearch, setWebSearch] = useState(false);
  const [assistantMode, setAssistantMode] = useState<ChatAssistantMode>('general');
  const [convSearch, setConvSearch] = useState('');
  const [pendingMsg, setPendingMsg] = useState<string | null>(null);
  const [streamStatus, setStreamStatus] = useState<string | null>(null);
  const [activeModelInfo, setActiveModelInfo] = useState<ChatModelMetadata | null>(null);
  const [sendStartedAt, setSendStartedAt] = useState<number | null>(null);
  const [firstTokenAt, setFirstTokenAt] = useState<number | null>(null);
  const [elapsedMs, setElapsedMs] = useState(0);
  const [ingestingScoutKeys, setIngestingScoutKeys] = useState<Set<string>>(new Set());
  const [ingestedScoutKeys, setIngestedScoutKeys] = useState<Set<string>>(new Set());
  const showThinking = useThemeStore((s) => s.showThinking ?? false);
  const {
    scrollContainerRef: chatScrollRef,
    scrollEndRef: messagesEndRef,
    scrollToBottomIfFollowing,
    enableFollowOutput,
  } = useChatAutoScroll();
  const sendLock = useRef(false);
  const abortControllerRef = useRef<AbortController | null>(null);
  const cancelRequestedRef = useRef(false);
  const isAuthenticated = !!localStorage.getItem('access_token');
  const currentSession = sessions.find(s => s.id === currentSessionId);
  const ragEnabled = currentSession?.rag_enabled ?? true;
  const modelDisplay = activeModelInfo?.label || activeModelInfo?.model || '当前模型';
  const modelDetail = activeModelInfo
    ? `${activeModelInfo.provider || 'provider'} / ${activeModelInfo.model || activeModelInfo.label || 'model'}`
    : '发送消息后显示当前模型';
  const generationElapsedMs = firstTokenAt && sendStartedAt
    ? Math.max(0, elapsedMs - (firstTokenAt - sendStartedAt))
    : 0;
  const streamPhaseLabel = sending && sendStartedAt
    ? firstTokenAt
      ? `生成中 ${formatElapsed(generationElapsedMs)}`
      : streamStatus?.startsWith('正在检索')
        ? `检索中 ${formatElapsed(elapsedMs)}`
        : `等待首段 ${formatElapsed(elapsedMs)}`
    : null;

  const [initDone, setInitDone] = useState(false);
  const [initLoading, setInitLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated || initDone) return;
    setInitDone(true);
    (async () => {
      try { await loadSessions(); const s = useChatSessionStore.getState(); if (s.sessions.length === 0) await createSession(); else if (!s.currentSessionId) await selectSession(s.sessions[0].id); }
      catch (error) { message.error(getApiErrorMessage(error, { fallback: '对话记录加载失败' })); } finally { setInitLoading(false); }
    })();
  }, [isAuthenticated, initDone]);
  useEffect(() => { scrollToBottomIfFollowing(); }, [messages, pendingMsg, scrollToBottomIfFollowing]);
  useEffect(() => { setDrawerOpen(!isMobile); }, [isMobile, setDrawerOpen]);
  useEffect(() => {
    if (!sending || !sendStartedAt) {
      setElapsedMs(0);
      return;
    }
    const tick = () => setElapsedMs(Date.now() - sendStartedAt);
    tick();
    const timer = window.setInterval(tick, 250);
    return () => window.clearInterval(timer);
  }, [sending, sendStartedAt]);

  const appendStreamingReply = (content: string, references: any[] = [], researchScout?: ResearchScoutPayload | null) => {
    useChatSessionStore.setState(s => {
      const msgs = [...s.messages];
      const last = msgs[msgs.length - 1];
      if (last?.role === 'assistant' && last._streaming) {
        msgs[msgs.length - 1] = { ...last, content: `${last.content}${content}`, references, research_scout: researchScout || last.research_scout, _reasoningStreaming: false };
      } else {
        msgs.push({ role: 'assistant', content, references, research_scout: researchScout || undefined, _streaming: true, created_at: new Date().toISOString() });
      }
      return { messages: msgs };
    });
  };
  const appendStreamingReasoning = (content: string) => {
    useChatSessionStore.setState(s => {
      const msgs = [...s.messages];
      const last = msgs[msgs.length - 1];
      if (last?.role === 'assistant' && last._streaming) {
        msgs[msgs.length - 1] = {
          ...last,
          reasoning: `${last.reasoning || ''}${content}`,
          _reasoningStreaming: true,
          thinking_started_at: last.thinking_started_at || Date.now(),
        };
      } else {
        msgs.push({
          role: 'assistant',
          content: '',
          reasoning: content,
          _streaming: true,
          _reasoningStreaming: true,
          thinking_started_at: Date.now(),
          created_at: new Date().toISOString(),
        });
      }
      return { messages: msgs };
    });
  };
  const markFirstToken = () => {
    setFirstTokenAt(prev => prev ?? Date.now());
  };
  const resetStreamProgress = () => {
    setPendingMsg(null);
    setStreamStatus(null);
    setSendStartedAt(null);
    setFirstTokenAt(null);
    setElapsedMs(0);
  };
  const finishStreamingMessages = () => {
    useChatSessionStore.setState(s => ({
      messages: s.messages.map(m => m._streaming ? { ...m, _streaming: false, _reasoningStreaming: false } : m),
    }));
  };
  const handleStopGeneration = () => {
    if (!sending || !abortControllerRef.current) return;
    cancelRequestedRef.current = true;
    setStreamStatus('已停止生成');
    abortControllerRef.current.abort();
    finishStreamingMessages();
    sendLock.current = false;
    useChatSessionStore.setState({ sending: false });
    resetStreamProgress();
  };
  const consumeChatStream = async (response: Response) => {
    const reader = response.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let finished = false;
    let references: any[] = [];
    let researchScout: ResearchScoutPayload | null = null;

    const handleFrame = (frame: string) => {
      const data = frame
        .split('\n')
        .filter(line => line.startsWith('data: '))
        .map(line => line.slice(6))
        .join('\n');
      if (!data) return false;
      if (data === '[DONE]') return true;

      try {
        const event = JSON.parse(data) as { type?: string; content?: string | StreamMetaContent };
        if (event.type === 'status') {
          setStreamStatus(typeof event.content === 'string' ? event.content : '正在生成回答...');
        } else if (event.type === 'meta' && event.content && typeof event.content === 'object') {
          references = event.content.references || [];
          researchScout = event.content.research_scout || null;
          if (event.content.model) setActiveModelInfo(event.content.model);
        } else if (event.type === 'reasoning' && typeof event.content === 'string') {
          markFirstToken();
          appendStreamingReasoning(event.content);
        } else if ((event.type === 'content' || event.type === 'error') && typeof event.content === 'string') {
          markFirstToken();
          appendStreamingReply(event.content, references, researchScout);
        } else if (event.type === 'done') {
          return true;
        }
      } catch {
        appendStreamingReply(data);
      }
      return false;
    };

    while (!finished) {
      const { done, value } = await reader.read();
      buffer += decoder.decode(value, { stream: !done }).replace(/\r\n/g, '\n');
      const frames = buffer.split('\n\n');
      buffer = frames.pop() || '';
      for (const frame of frames) {
        if (handleFrame(frame)) {
          finished = true;
          break;
        }
      }
      if (done) {
        if (buffer && handleFrame(buffer)) finished = true;
        break;
      }
    }
    finishStreamingMessages();
  };

  const handleSend = async (overrideContent?: string) => {
    const hasOverride = typeof overrideContent === 'string';
    const text = (hasOverride ? overrideContent : input).trim();
    const readyAttachmentContext = mergedReadyAttachments();
    if (sendLock.current || (!text && readyAttachmentContext.length === 0) || sending) return;
    if (!isAuthenticated) { message.warning('请先登录'); return; }
    if (hasExtractingAttachments) { message.warning('文件还在解析中...'); return; }
    let sid = currentSessionId; if (!sid) { sid = await createSession(); if (!sid) { message.error('创建对话失败：请稍后重试'); return; } }
    sendLock.current = true;
    cancelRequestedRef.current = false;
    const controller = new AbortController();
    const effectiveWebSearch = assistantMode === 'research_scout' || webSearch;
    const effectiveSearchDepth = assistantMode === 'research_scout' ? 'deep' : searchDepth;
    abortControllerRef.current = controller;
    setSendStartedAt(Date.now());
    setFirstTokenAt(null);
    setElapsedMs(0);
    setStreamStatus(assistantMode === 'research_scout' ? '论文猎手正在联网检索学术来源...' : effectiveWebSearch ? '正在检索知识库与网络来源...' : ragEnabled ? '正在检索知识库...' : '正在生成回答...');
    if (!hasOverride) setInput('');
    enableFollowOutput();

    if (readyAttachmentContext.length > 0) {
      const currentFiles = [...attachedFiles];
      setAttachedFiles([]);
      const fileNames = readyAttachmentContext.map(f => f.file.name).join(', ');
      const allText = attachedTextContext(readyAttachmentContext);
      const imageAttachments = imageAttachmentPayloads(readyAttachmentContext);
      const icons = readyAttachmentContext.map(f => f.file.type.startsWith('image/') ? '🖼️' : '📄').join('');
      const userContent = currentFiles.length > 0
        ? `${icons} ${fileNames}${text ? '\n' + text : ''}`
        : text;
      useChatSessionStore.setState(s => ({ messages: [...s.messages, { role: 'user', content: userContent || `继续基于附件提问: ${fileNames}`, created_at: new Date().toISOString() }], sending: true }));
      try {
        const t = localStorage.getItem('access_token');
        const prompt = text || `请分析文件: ${fileNames}`;
        const r = await fetch(`/api/chat-sessions/${sid}/send-stream`, { method: 'POST', signal: controller.signal, headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${t}` }, body: JSON.stringify({ content: prompt, rag_enabled: ragEnabled, extra_context: allText || undefined, attachments: imageAttachments, web_search: effectiveWebSearch, search_depth: effectiveSearchDepth, show_thinking: showThinking, assistant_mode: assistantMode }) });
        if (!r.ok) throw new Error(await parseStreamError(r, '上传发送失败'));
        await consumeChatStream(r);
        rememberAttachments(currentFiles);
      } catch (e: any) {
        if (currentFiles.length > 0) setAttachedFiles(currentFiles);
        if (!cancelRequestedRef.current && e?.name !== 'AbortError') appendAssistantError(getApiErrorMessage(e, { fallback: '上传发送失败' }));
      }
      finally { finishStreamingMessages(); resetStreamProgress(); abortControllerRef.current = null; cancelRequestedRef.current = false; sendLock.current = false; useChatSessionStore.setState({ sending: false }); }
      return;
    }

    useChatSessionStore.setState(s => ({ messages: [...s.messages, { role: 'user', content: text, created_at: new Date().toISOString() }], sending: true }));
    try {
      const t = localStorage.getItem('access_token');
      const r = await fetch(`/api/chat-sessions/${sid}/send-stream`, { method: 'POST', signal: controller.signal, headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${t}` }, body: JSON.stringify({ content: text, rag_enabled: ragEnabled, web_search: effectiveWebSearch, search_depth: effectiveSearchDepth, show_thinking: showThinking, assistant_mode: assistantMode }) });
      if (!r.ok) throw new Error(await parseStreamError(r, '发送失败'));
      await consumeChatStream(r);
    } catch (e: any) { if (!cancelRequestedRef.current && e?.name !== 'AbortError') appendAssistantError(getApiErrorMessage(e, { fallback: '发送失败' })); }
    finally { finishStreamingMessages(); resetStreamProgress(); abortControllerRef.current = null; cancelRequestedRef.current = false; sendLock.current = false; useChatSessionStore.setState({ sending: false }); }
  };

  const filteredMessages = convSearch ? messages.filter(m => m.content.toLowerCase().includes(convSearch.toLowerCase())) : messages;
  const handleCreateSession = async () => {
    try {
      await createSession();
      if (isMobile) setDrawerOpen(false);
    } catch (error) {
      message.error(getApiErrorMessage(error, { fallback: '创建对话失败' }));
    }
  };
  const handleSelectSession = async (id: string) => {
    try {
      await selectSession(id);
      if (isMobile) setDrawerOpen(false);
    } catch (error) {
      message.error(getApiErrorMessage(error, { fallback: '加载会话失败' }));
    }
  };
  const handleToggleRag = async (enabled: boolean) => {
    try {
      await toggleRag(enabled);
    } catch (error) {
      message.error(getApiErrorMessage(error, { fallback: '知识库模式切换失败' }));
    }
  };
  const handleExport = () => {
    const text = messages.map(m => `### ${m.role === 'user' ? '用户' : 'AI'}\n\n${m.content}\n\n`).join('---\n\n');
    const blob = new Blob([text], { type: 'text/markdown' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `chat_${new Date().toISOString().slice(0, 10)}.md`;
    link.click();
  };
  const handleClearMessages = () => {
    if (!currentSessionId) return;
    Modal.confirm({
      title: '清空当前对话？',
      content: '清空后将无法恢复当前会话中的消息。',
      okText: '确认清空',
      cancelText: '取消',
      okButtonProps: { danger: true },
      onOk: async () => {
        try {
          await api.delete(`/chat-sessions/${currentSessionId}/messages`);
          useChatSessionStore.setState({ messages: [] });
          message.success('已清空当前对话');
        } catch (error) {
          message.error(getApiErrorMessage(error, { fallback: '清空失败' }));
        }
      },
    });
  };
  const handleWebSearchToggle = () => {
    if (assistantMode === 'research_scout' && webSearch) {
      message.info('论文猎手会自动联网检索学术来源，已保持开启');
      return;
    }
    const nextWebSearch = !webSearch;
    setWebSearch(nextWebSearch);
    if (nextWebSearch && searchDepth !== 'deep') {
      setSearchDepth('deep');
      message.info('已开启联网增强，并自动切换为深度检索');
    }
  };
  const handleAssistantModeChange = (mode: ChatAssistantMode) => {
    setAssistantMode(mode);
    if (mode === 'research_scout') {
      if (!webSearch) setWebSearch(true);
      if (searchDepth !== 'deep') setSearchDepth('deep');
      message.info('已切换到论文猎手，并自动开启联网深度学术检索');
    }
  };
  const researchScoutAutoWeb = assistantMode === 'research_scout';
  const effectiveWebSearchActive = researchScoutAutoWeb || webSearch;
  const scoutCandidateKey = (paper: ResearchScoutCandidate) => `${paper.source || 'unknown'}:${paper.remote_id || paper.arxiv_id || paper.doi || paper.title}`;
  const handleResearchScoutIngest = async (paper: ResearchScoutCandidate) => {
    const source = paper.source;
    const remoteId = paper.remote_id || paper.arxiv_id || paper.doi || paper.source_url || paper.title;
    const supportedSources = new Set(['arxiv', 'semantic_scholar', 'openalex', 'google_scholar']);
    if (!source || !remoteId || !supportedSources.has(source)) {
      message.warning('这条候选缺少可安全入库的学术源标识，请先打开来源确认');
      return;
    }
    const key = scoutCandidateKey(paper);
    setIngestingScoutKeys(prev => new Set(prev).add(key));
    try {
      const response = await api.post('/papers/ingest-personal', {
        source,
        remote_id: remoteId,
        remote_ingest_token: paper.ingest_token,
        auto_download: false,
      });
      setIngestedScoutKeys(prev => new Set(prev).add(key));
      const skipped = Number(response.data?.skipped || 0);
      message.success(skipped ? '这篇论文已在库中，已为你保存到个人论文库' : '已加入你的论文库');
    } catch (error) {
      message.error(getApiErrorMessage(error, { fallback: '加入论文库失败' }));
    } finally {
      setIngestingScoutKeys(prev => { const next = new Set(prev); next.delete(key); return next; });
    }
  };
  const statusRows = [
    { key: 'assistant-mode', icon: <ExperimentOutlined />, label: '助手模式', active: assistantMode === 'research_scout', detail: assistantMode === 'research_scout' ? '论文猎手：自动联网检索并推荐有用论文' : '普通对话：通用科研问答' },
    { key: 'rag', icon: <DatabaseOutlined />, label: '知识库', active: ragEnabled, detail: ragEnabled ? '参与当前回答检索' : '当前为纯模型或网络回答' },
    { key: 'web', icon: <GlobalOutlined />, label: '联网', active: effectiveWebSearchActive, detail: researchScoutAutoWeb ? '论文猎手已自动启用深度学术联网检索' : webSearch ? `启用${searchDepth === 'deep' ? '深度' : searchDepth === 'quick' ? '快速' : '标准'}联网增强` : '不检索网络来源' },
    { key: 'thinking', icon: <BulbOutlined />, label: '思考', active: !!activeModelInfo?.capabilities?.thinking, detail: activeModelInfo?.capabilities?.thinking ? '当前模型可返回思考摘要' : '当前模型未声明思考展示能力' },
    { key: 'vision', icon: <EyeOutlined />, label: '视觉', active: !!activeModelInfo?.capabilities?.vision, detail: activeModelInfo?.capabilities?.vision ? '当前模型可接收图片输入' : hasImageAttachment ? '当前模型未声明图片输入能力' : '未检测到视觉能力标记' },
  ];
  const statusPopoverContent = (
    <div className="chat-status-popover">
      <div className="chat-status-popover-head">
        <Text strong>{modelDisplay}</Text>
        <Text type="secondary">{modelDetail}</Text>
      </div>
      <div className="chat-status-popover-list">
        {statusRows.map(item => (
          <div className="chat-status-popover-row" key={item.key}>
            <span className={`chat-status-row-icon ${item.active ? 'is-active' : ''}`}>{item.icon}</span>
            <div className="chat-status-row-copy">
              <Text strong>{item.label}</Text>
              <Text type="secondary">{item.detail}</Text>
            </div>
            <span className={`chat-status-row-state ${item.active ? 'is-active' : ''}`}>{item.active ? '开启' : '关闭'}</span>
          </div>
        ))}
      </div>
    </div>
  );
  const searchPopoverContent = (
    <div className="chat-toolbar-search-panel">
      <Input
        size="middle"
        prefix={<SearchOutlined />}
        placeholder="搜索当前对话"
        value={convSearch}
        onChange={e => setConvSearch(e.target.value)}
        allowClear
      />
      <Text type="secondary">
        {convSearch ? `已筛选 ${filteredMessages.length}/${messages.length} 条消息` : '输入关键词后只显示匹配消息'}
      </Text>
    </div>
  );
  const researchScoutSourceLabel = (source?: string) => ({
    arxiv: 'arXiv',
    semantic_scholar: 'Semantic Scholar',
    openalex: 'OpenAlex',
    google_scholar: 'Google Scholar',
  }[source || ''] || source || '学术来源');
  const continueScoutSearch = (query: string, flavor: string) => {
    setAssistantMode('research_scout');
    setWebSearch(true);
    setSearchDepth('deep');
    setInput(`请继续用论文猎手模式找 ${flavor} 类型的论文，主题是：${query}`);
  };
  const renderResearchScoutCards = (msg: any) => {
    const candidates = msg.research_scout?.candidates || [];
    if (!candidates.length) return null;
    const query = msg.research_scout?.query || '当前研究主题';
    return (
      <div className="research-scout-cards">
        <div className="research-scout-header">
          <Space size={6}>
            <ExperimentOutlined />
            <Text strong>论文猎手候选</Text>
          </Space>
          <Space size={6} wrap>
            <Text type="secondary">{msg.research_scout?.candidate_count || candidates.length} 篇 · {query}</Text>
            {['baseline', 'survey', 'latest', 'counterexample'].map(flavor => (
              <Button key={flavor} size="small" type="text" className="research-scout-refine-button" onClick={() => continueScoutSearch(query, flavor)}>
                继续找 {flavor}
              </Button>
            ))}
          </Space>
        </div>
        <div className="research-scout-grid">
          {candidates.slice(0, 6).map((paper: ResearchScoutCandidate) => {
            const key = scoutCandidateKey(paper);
            const ingested = ingestedScoutKeys.has(key);
            return (
              <div className="research-scout-card" key={key}>
                <div className="research-scout-card-title">
                  <Tag color="geekblue">#{paper.rank}</Tag>
                  <Text strong ellipsis={{ tooltip: paper.title }}>{paper.title}</Text>
                </div>
                <Space wrap size={4} className="research-scout-meta">
                  {paper.year && <Tag color="blue">{paper.year}</Tag>}
                  <Tag color="purple">{researchScoutSourceLabel(paper.source)}</Tag>
                  {!!paper.citation_count && <Tag color="gold">引用 {paper.citation_count}</Tag>}
                  {paper.pdf_url && <Tag color="green">PDF</Tag>}
                  {ingested && <Tag color="success" icon={<CheckCircleOutlined />}>已入库</Tag>}
                </Space>
                {paper.authors?.length ? <Text type="secondary" className="research-scout-authors" ellipsis>{paper.authors.join(', ')}</Text> : null}
                <Text className="research-scout-rationale">{paper.why_interesting}</Text>
                <Text type="secondary" className="research-scout-useful">{paper.why_useful}</Text>
                {paper.abstract && <Text type="secondary" className="research-scout-abstract">{paper.abstract.slice(0, 220)}{paper.abstract.length > 220 ? '...' : ''}</Text>}
                <Space wrap size={6} className="research-scout-actions">
                  <Button
                    size="small"
                    type={ingested ? 'default' : 'primary'}
                    icon={ingested ? <CheckCircleOutlined /> : <CloudDownloadOutlined />}
                    loading={ingestingScoutKeys.has(key)}
                    disabled={ingested}
                    onClick={() => handleResearchScoutIngest(paper)}
                  >
                    {ingested ? '已入库' : '加入论文库'}
                  </Button>
                  {paper.source_url && <Button size="small" onClick={() => window.open(paper.source_url || '', '_blank', 'noopener,noreferrer')}>来源</Button>}
                  {paper.pdf_url && <Button size="small" onClick={() => window.open(paper.pdf_url || '', '_blank', 'noopener,noreferrer')}>PDF</Button>}
                  <Button size="small" type="text" onClick={() => setInput(`请围绕这篇论文继续分析：${paper.title}\n\n重点说明它和我的研究方向有什么关系，适合作为 baseline、inspiration 还是 related work。`)}>
                    继续分析
                  </Button>
                </Space>
              </div>
            );
          })}
        </div>
      </div>
    );
  };
  const toolbarMenuItems = [
    { key: 'export', icon: <ExportOutlined />, label: '导出对话', onClick: handleExport },
    ...(currentSessionId ? [{ key: 'clear', icon: <DeleteOutlined />, label: '清空当前对话', danger: true, onClick: handleClearMessages }] : []),
  ];
  const sessionList = (
    <>
      <div className="chat-session-create"><Button type="primary" icon={<PlusOutlined />} block onClick={handleCreateSession}>
        <span style={{ fontSize: 14 }}>新对话</span>
      </Button></div>
      <div className="chat-session-scroll">
        <List loading={loading} dataSource={sessions} split={false} renderItem={s => {
          const isActive = s.id === currentSessionId;
          return (
            <div className={`chat-session-item ${isActive ? 'is-active' : ''}`} onClick={() => handleSelectSession(s.id)}>
              <div className="chat-session-heading">
                <Text strong={isActive} ellipsis className="chat-session-title" style={{ fontSize: 13 }}>{s.title}</Text>
                <Popconfirm title="删除？" onConfirm={async e => { e?.stopPropagation(); try { await deleteSession(s.id); } catch (error) { message.error(getApiErrorMessage(error, { fallback: '删除会话失败' })); } }}>
                  <Button className="chat-session-delete" type="text" size="small" icon={<DeleteOutlined style={{ fontSize: 12 }} />} onClick={e => e.stopPropagation()} />
                </Popconfirm>
              </div>
              <div className="chat-session-meta">
                <Text type="secondary" ellipsis className="chat-session-preview" style={{ fontSize: 11 }}>{s.last_message || '还没有消息'}</Text>
                <Text type="secondary" className="chat-session-time" style={{ fontSize: 10 }}>{formatSessionTime(s.updated_at || s.created_at)}</Text>
              </div>
            </div>
          );
        }} />
      </div>
    </>
  );
  if (!isAuthenticated) return <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 'calc(100vh - 200px)' }}><Empty description="请先登录后使用对话功能" /></div>;
  if (initLoading && sessions.length === 0) return <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 'calc(100vh - 200px)' }}><Skeleton active paragraph={{ rows: 6 }} style={{ padding: 40 }} /></div>;

  return (
    <div className="chat-workspace" style={{ background: token.colorBgLayout }}>
      <Drawer className="chat-session-drawer" title="对话记录" placement="left" width={280} open={isMobile && drawerOpen} onClose={() => setDrawerOpen(false)}>
        {sessionList}
      </Drawer>
      {!isMobile && <div className="chat-session-sidebar" style={{ width: drawerOpen ? 260 : 0, overflow: 'hidden', transition: 'width 0.25s', borderRight: drawerOpen ? `1px solid ${token.colorBorderSecondary}` : 'none', background: '#fafbfc', flexShrink: 0 }}>
        {sessionList}
      </div>}
      <div className="chat-main" style={{ flex: 1, display: 'flex', flexDirection: 'column', background: token.colorBgContainer, marginLeft: 1 }}>
        <div className="chat-toolbar" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 20px', borderBottom: `1px solid ${token.colorBorderSecondary}`, background: token.colorBgLayout }}>
          <Space size={4} className="chat-toolbar-title">
            <Button type="text" icon={<MenuOutlined />} onClick={() => setDrawerOpen(!drawerOpen)} />
            <Text strong className="chat-toolbar-title-text">{currentSession?.title || '新对话'}</Text>
            {currentSessionId && (
              <Dropdown
                menu={{ items: [{ key: 'clear', icon: <DeleteOutlined />, label: '清空当前对话', danger: true, onClick: handleClearMessages }] }}
                trigger={['click']}
              >
                <Button type="text" size="small" icon={<MoreOutlined />} title="更多操作" />
              </Dropdown>
            )}
          </Space>
          <div className="chat-toolbar-actions">
            <Select
              className="chat-assistant-mode-select"
              size="small"
              value={assistantMode}
              onChange={handleAssistantModeChange}
              options={[
                { value: 'general', label: '普通对话' },
                { value: 'research_scout', label: '论文猎手' },
              ]}
            />
            <Tooltip title={modelDetail}>
              <span className="chat-model-badge">
                <RobotOutlined />
                <span>{modelDisplay}</span>
              </span>
            </Tooltip>
            <div className="chat-toolbar-primary-controls">
              <Button className={`chat-control-pill ${ragEnabled ? 'is-active' : ''}`} type="text" size="small" icon={<DatabaseOutlined />} onClick={() => handleToggleRag(!ragEnabled)}>
                <span className="chat-control-label">知识库</span>
              </Button>
              <Tooltip title={researchScoutAutoWeb ? '论文猎手会自动联网检索 arXiv、Semantic Scholar、OpenAlex 等学术来源' : '联网增强可以和知识库同时使用'}>
                <Button className={`chat-control-pill ${effectiveWebSearchActive ? 'is-active' : ''}`} type="text" size="small" icon={<GlobalOutlined />} onClick={handleWebSearchToggle}>
                  <span className="chat-control-label">联网</span>
                </Button>
              </Tooltip>
              <Select className="chat-depth-select" size="small" value={searchDepth} onChange={setSearchDepth} variant="borderless" options={[{ value: 'quick', label: '快速' }, { value: 'standard', label: '标准' }, { value: 'deep', label: '深度' }]} />
            </div>
            <Popover content={statusPopoverContent} trigger="click" placement="bottomRight">
              <Button className="chat-icon-pill" type="text" size="small" icon={<InfoCircleOutlined />}>
                <span className="chat-control-label">状态</span>
              </Button>
            </Popover>
            <Popover content={searchPopoverContent} trigger="click" placement="bottomRight">
              <Button className={`chat-icon-pill ${convSearch ? 'is-active' : ''}`} type="text" size="small" icon={<SearchOutlined />} />
            </Popover>
            <Dropdown menu={{ items: toolbarMenuItems }} trigger={['click']}>
              <Button className="chat-icon-pill" type="text" size="small" icon={<MoreOutlined />} title="更多操作" />
            </Dropdown>
          </div>
        </div>
        <div ref={chatScrollRef} className="chat-message-list" style={{ flex: 1, overflowY: 'auto', padding: '24px 20px', background: token.colorBgLayout }}>
          {messages.length === 0 && !pendingMsg ? (
            <div className="chat-empty-state">
              <div className="chat-empty-logo">✦</div>
              <div className="chat-empty-title">AI 科研搭子</div>
              <div className="chat-empty-description">基于知识库论文的智能问答助手</div>
              <div className="chat-empty-hint">输入问题或上传论文，开始你的研究探索</div>
              <div className="chat-empty-suggestions">
                {emptySuggestions.map(item => (
                  <button className="chat-empty-suggestion" type="button" key={item.label} onClick={() => setInput(item.text)}>
                    {item.icon}
                    <span>{item.label}</span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <>
              {filteredMessages.map((msg, idx) => (
                <div key={idx} className={`chat-message-row ${msg.role === 'user' ? 'is-user' : 'is-assistant'}`}>
                  <Avatar className="chat-message-avatar" size={30} icon={msg.role === 'user' ? <UserOutlined /> : <RobotOutlined />} />
                  <div className={`chat-message-body ${msg.role === 'user' ? 'is-user' : 'is-assistant'}`}>
                    {msg.role === 'assistant' && msg.reasoning && (
                      <ThinkingPanel reasoningText={msg.reasoning} isStreaming={!!msg._reasoningStreaming} startTime={msg.thinking_started_at} />
                    )}
                    {(msg.role === 'user' || msg.content) && (
                      <div className={`chat-message-bubble ${msg.role === 'user' ? 'is-user' : 'is-assistant'}`}>
                        {msg.role === 'user' ? <div style={{ whiteSpace: 'pre-wrap', color: '#fff' }}>{msg.content}</div> : <Markdown content={msg.content} />}
                      </div>
                    )}
                    {msg.role === 'assistant' && renderResearchScoutCards(msg)}
                    <div style={{ display: 'flex', gap: 4, marginTop: 4, paddingLeft: 4, justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
                      {!msg._streaming && <Button type="text" size="small" icon={<span>💬</span>} onClick={() => setInput(`> ${msg.content.slice(0, 100)}${msg.content.length > 100 ? '...' : ''}\n\n`)} title="引用回复" style={{ fontSize: 11, color: token.colorTextQuaternary }} />}
                      {msg.role === 'user' && <Button type="text" size="small" icon={<EditOutlined />} onClick={() => setInput(msg.content)} style={{ fontSize: 11, color: token.colorTextQuaternary }} />}
                      {!msg._streaming && msg.id && <Popconfirm title="删除此消息？" onConfirm={async () => { if (!msg.id || !currentSessionId) return; try { await api.delete(`/chat-sessions/${currentSessionId}/messages/${msg.id}`); useChatSessionStore.setState(s => ({ messages: s.messages.filter(m => m.id !== msg.id) })); } catch (error) { message.error(getApiErrorMessage(error, { fallback: '删除消息失败' })); } }}><Button type="text" size="small" icon={<DeleteOutlined />} style={{ fontSize: 11, color: '#ff4d4f40' }} /></Popconfirm>}
                      {msg.role === 'assistant' && !msg._streaming && <><Button type="text" size="small" icon={<CopyOutlined />} onClick={() => { navigator.clipboard.writeText(msg.content); message.success('已复制'); }} style={{ fontSize: 11, color: token.colorTextQuaternary }}>复制</Button>
                      <Dropdown menu={{ items: [
                        { key: 'balanced', label: '🔄 平衡', onClick: () => { handleToggleRag(true); handleSend('请重新回答'); } },
                        { key: 'creative', label: '💡 创意', onClick: () => { handleToggleRag(true); handleSend('请用更有创意的角度回答'); } },
                        { key: 'precise', label: '🎯 精确', onClick: () => { handleToggleRag(true); handleSend('请精确严谨地重新回答'); } },
                        { key: 'norag', label: '🧠 纯模型', onClick: () => { handleToggleRag(false); handleSend('请重新回答'); } },
                      ]}} trigger={['click']}>
                        <Button type="text" size="small" icon={<RedoOutlined />} style={{ fontSize: 11, color: token.colorTextQuaternary }}>重新生成</Button>
                      </Dropdown>
                      <Button type="text" size="small" onClick={async () => { if (msg.id) try { await api.post('/chat/feedback', { message_id: msg.id, rating: 'like' }); message.success('已反馈'); } catch (error) { message.error(getApiErrorMessage(error, { fallback: '反馈提交失败' })); } }} style={{ fontSize: 11, color: token.colorTextQuaternary }}>👍</Button>
                      <Button type="text" size="small" onClick={async () => { if (msg.id) try { await api.post('/chat/feedback', { message_id: msg.id, rating: 'dislike' }); message.success('已反馈'); } catch (error) { message.error(getApiErrorMessage(error, { fallback: '反馈提交失败' })); } }} style={{ fontSize: 11, color: token.colorTextQuaternary }}>👎</Button></>}
                    </div>
                    {msg.references && msg.references.length > 0 && <div className="chat-reference-strip"><Text type="secondary" style={{ fontSize: 11 }}>检索来源：</Text>{(msg.references as any[]).map((ref: any, ri: number) => <Tooltip key={`${ref.url || ref.arxiv_id || ref.title}-${ri}`} title={referenceTooltip(ref)}><Tag color={ref.source === 'web' ? 'cyan' : ref.source === 'research_scout' ? 'purple' : 'geekblue'} style={{ marginTop: 4, cursor: ref.url || ref.pdf_url || ref.arxiv_id ? 'pointer' : 'default', borderRadius: 8 }} onClick={() => { if (ref.url) window.open(ref.url, '_blank', 'noopener,noreferrer'); else if (ref.pdf_url) window.open(ref.pdf_url, '_blank', 'noopener,noreferrer'); else if (ref.arxiv_id) window.open(`https://arxiv.org/abs/${ref.arxiv_id.replace(/v\d+$/, '')}`, '_blank', 'noopener,noreferrer'); }}>[{ri + 1}] {referenceLabel(ref)}</Tag></Tooltip>)}</div>}
                    <div style={{ fontSize: 11, color: token.colorTextQuaternary, marginTop: 4, textAlign: msg.role === 'user' ? 'right' : 'left', padding: '0 4px' }}>{msg.created_at ? new Date(msg.created_at).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) : ''}</div>
                  </div>
                </div>
              ))}
              {pendingMsg && <div className="chat-message-row is-user"><Avatar className="chat-message-avatar" size={30} icon={<UserOutlined />} /><div className="chat-message-body is-user"><div className="chat-message-bubble is-user">{pendingMsg}</div></div></div>}
              {sending && <div className="chat-message-row is-assistant"><Avatar className="chat-message-avatar" size={30} icon={<RobotOutlined />} /><div className="chat-message-body is-assistant"><div className="chat-stream-status"><Space size={8} align="start"><Space size={5} style={{ paddingTop: 5 }}>{[0, 0.2, 0.4].map((d, i) => <div key={i} style={{ width: 7, height: 7, borderRadius: '50%', background: '#c471ed', animation: `bounce 1.4s infinite ease-in-out ${d}s` }} />)}</Space><div className="chat-stream-status-copy">{streamPhaseLabel && <span className="chat-stream-phase"><ClockCircleOutlined />{streamPhaseLabel}</span>}<Text type="secondary" className="chat-stream-status-text">{streamStatus || '正在等待模型响应...'}</Text></div><Button className="chat-stop-inline-button" type="text" size="small" icon={<StopOutlined />} onClick={handleStopGeneration}>停止</Button></Space></div></div></div>}
            </>
          )}
          <div ref={messagesEndRef} />
        </div>
        <div className="chat-composer">
          <div className="chat-composer-panel">
            <div className="chat-prompt-shortcuts">
              {promptShortcuts.map(item => (
                <button className="chat-prompt-chip" type="button" key={item.label} onClick={() => setInput(prev => prev ? `${prev}\n${item.text}` : item.text)}>
                  {item.icon}
                  <span>{item.label}</span>
                </button>
              ))}
            </div>
            {attachedFiles.length > 0 && (
              <div className="chat-attachments">
                {attachedFiles.map(af => (
                  <div key={af.id} className="chat-attachment-chip">
                    {af.file.type.startsWith('image/')
                      ? <Image className="chat-attachment-thumb" src={URL.createObjectURL(af.file)} width={32} height={32} preview={false} />
                      : <span className="chat-attachment-file-icon"><FilePdfOutlined /></span>}
                    <span className="chat-attachment-name">{attachmentStatusLabel(af)} · {af.file.name}</span>
                    <Button className="chat-attachment-remove" type="text" size="small" icon={<CloseOutlined />} onClick={() => removeAttachment(af.id)} />
                  </div>
                ))}
              </div>
            )}
            {rememberedAttachments.length > 0 && (
              <div className="chat-attachments chat-remembered-attachments">
                {rememberedAttachments.map(af => (
                  <div key={af.id} className="chat-attachment-chip">
                    {af.file.type.startsWith('image/')
                      ? <Image className="chat-attachment-thumb" src={af.optimizedDataUrl || af.dataUrl || URL.createObjectURL(af.file)} width={32} height={32} preview={false} />
                      : <span className="chat-attachment-file-icon"><FilePdfOutlined /></span>}
                    <span className="chat-attachment-name">{attachmentStatusLabel(af)} · {af.file.name}</span>
                    <Button className="chat-attachment-remove" type="text" size="small" icon={<CloseOutlined />} onClick={() => removeRememberedAttachment(af.id)} />
                  </div>
                ))}
              </div>
            )}
            <div className="chat-editor">
              <Tooltip title="上传论文或图片"><Button className="chat-upload-button chat-tool-button" type="text" icon={<UploadOutlined />} onClick={openAttachmentPicker} /></Tooltip>
              <div className="chat-input-wrap"><Input.TextArea className="chat-input" value={input} onChange={e => setInput(e.target.value)} onPressEnter={e => { if (!e.shiftKey) { e.preventDefault(); handleSend(); } }} placeholder={ragEnabled ? '输入消息，Enter 发送，Shift+Enter 换行' : '输入消息...'} autoSize={{ minRows: 1, maxRows: 5 }} /></div>
              {sending ? (
                <Tooltip title="停止生成"><Button className="chat-stop-button chat-tool-button" type="text" icon={<StopOutlined />} onClick={handleStopGeneration} /></Tooltip>
              ) : (
                <Tooltip title="发送"><Button className="chat-send-button chat-tool-button" type="primary" shape="circle" icon={<SendOutlined />} onClick={() => handleSend()} disabled={!input.trim() && attachedFiles.length === 0 && rememberedAttachments.length === 0} /></Tooltip>
              )}
            </div>
          </div>
        </div>
      </div>
      <style>{'@keyframes bounce{0%,80%,100%{transform:scale(.6);opacity:.4}40%{transform:scale(1);opacity:1}}'}</style>
    </div>
  );
};

export default ChatPage;
