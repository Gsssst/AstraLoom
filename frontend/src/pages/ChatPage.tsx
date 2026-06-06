import React, { useEffect, useRef, useState } from 'react';
import { Input, Button, Tag, Typography, Space, Empty, message, List, Popconfirm, Avatar, Tooltip, theme, Image, Select, Skeleton, Dropdown, Drawer, Grid, Modal } from 'antd';
import {
  SendOutlined, PlusOutlined, DeleteOutlined, UserOutlined, RobotOutlined,
  MenuOutlined, LoadingOutlined, UploadOutlined, FilePdfOutlined, CloseOutlined,
  CopyOutlined, RedoOutlined, EditOutlined, SearchOutlined, MoreOutlined,
  DatabaseOutlined, GlobalOutlined, ExportOutlined, MessageOutlined,
  BulbOutlined, FileTextOutlined, ExperimentOutlined, SwapOutlined,
  HighlightOutlined, EyeOutlined, ClockCircleOutlined,
} from '@ant-design/icons';
import { useChatSessionStore } from '../stores/useChatSessionStore';
import { useThemeStore } from '../stores/useThemeStore';
import api from '../services/api';
import { getApiErrorMessage, getHttpErrorMessage } from '../services/apiError';
import Markdown from '../components/Markdown';
import ThinkingPanel from '../components/ThinkingPanel';

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

interface AttachedFile {
  file: File;
  text: string;
  extracting: boolean;
  id: string;
  dataUrl?: string;
  mimeType?: string;
}

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

interface StreamMetaContent {
  references?: any[];
  model?: ChatModelMetadata;
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

const ChatPage: React.FC = () => {
  const { token } = theme.useToken();
  const screens = Grid.useBreakpoint();
  const isMobile = !screens.md;
  const { sessions, currentSessionId, messages, loading, sending, drawerOpen, loadSessions, createSession, selectSession, deleteSession, toggleRag, setDrawerOpen } = useChatSessionStore();

  const [input, setInput] = useState('');
  const [attachedFiles, setAttachedFiles] = useState<AttachedFile[]>([]);
  const [searchDepth, setSearchDepth] = useState<'quick' | 'standard' | 'deep'>('standard');
  const [webSearch, setWebSearch] = useState(false);
  const [convSearch, setConvSearch] = useState('');
  const [pendingMsg, setPendingMsg] = useState<string | null>(null);
  const [streamStatus, setStreamStatus] = useState<string | null>(null);
  const [activeModelInfo, setActiveModelInfo] = useState<ChatModelMetadata | null>(null);
  const [sendStartedAt, setSendStartedAt] = useState<number | null>(null);
  const [firstTokenAt, setFirstTokenAt] = useState<number | null>(null);
  const [elapsedMs, setElapsedMs] = useState(0);
  const showThinking = useThemeStore((s) => s.showThinking ?? false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const sendLock = useRef(false);
  const isAuthenticated = !!localStorage.getItem('access_token');
  const currentSession = sessions.find(s => s.id === currentSessionId);
  const ragEnabled = currentSession?.rag_enabled ?? true;
  const retrievalStrategy = webSearch && ragEnabled
    ? '混合检索'
    : webSearch
      ? '联网检索'
      : ragEnabled
        ? '知识库检索'
        : '直接对话';
  const modelDisplay = activeModelInfo?.label || activeModelInfo?.model || '当前模型';
  const modelDetail = activeModelInfo
    ? `${activeModelInfo.provider || 'provider'} / ${activeModelInfo.model || activeModelInfo.label || 'model'}`
    : '发送消息后显示当前模型';
  const hasImageAttachment = attachedFiles.some(file => file.file.type.startsWith('image/'));
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
  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, pendingMsg]);
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

  const appendStreamingReply = (content: string, references: any[] = []) => {
    useChatSessionStore.setState(s => {
      const msgs = [...s.messages];
      const last = msgs[msgs.length - 1];
      if (last?.role === 'assistant' && last._streaming) {
        msgs[msgs.length - 1] = { ...last, content: `${last.content}${content}`, references, _reasoningStreaming: false };
      } else {
        msgs.push({ role: 'assistant', content, references, _streaming: true, created_at: new Date().toISOString() });
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
  const consumeChatStream = async (response: Response) => {
    const reader = response.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let finished = false;
    let references: any[] = [];

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
          if (event.content.model) setActiveModelInfo(event.content.model);
        } else if (event.type === 'reasoning' && typeof event.content === 'string') {
          markFirstToken();
          appendStreamingReasoning(event.content);
        } else if ((event.type === 'content' || event.type === 'error') && typeof event.content === 'string') {
          markFirstToken();
          appendStreamingReply(event.content, references);
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
    useChatSessionStore.setState(s => ({
      messages: s.messages.map(m => m._streaming ? { ...m, _streaming: false, _reasoningStreaming: false } : m),
    }));
  };

  const handleSend = async () => {
    if (sendLock.current || (!input.trim() && attachedFiles.length === 0) || sending) return;
    if (!isAuthenticated) { message.warning('请先登录'); return; }
    if (attachedFiles.some(f => f.extracting)) { message.warning('文件还在解析中...'); return; }
    let sid = currentSessionId; if (!sid) { sid = await createSession(); if (!sid) { message.error('创建对话失败：请稍后重试'); return; } }
    sendLock.current = true;
    setSendStartedAt(Date.now());
    setFirstTokenAt(null);
    setElapsedMs(0);
    setStreamStatus(webSearch ? '正在检索知识库与网络来源...' : ragEnabled ? '正在检索知识库...' : '正在生成回答...');
    const text = input.trim(); setInput('');

    if (attachedFiles.length > 0) {
      const files = [...attachedFiles]; setAttachedFiles([]);
      const fileNames = files.map(f => f.file.name).join(', ');
      const allText = files
        .filter(f => !f.file.type.startsWith('image/'))
        .map(f => f.text)
        .filter(Boolean)
        .join('\n\n---\n\n');
      const imageAttachments = files
        .filter(f => f.file.type.startsWith('image/') && f.dataUrl)
        .map(f => ({ filename: f.file.name, mime_type: f.mimeType || f.file.type || 'image/png', data_url: f.dataUrl }));
      const icons = files.map(f => f.file.type.startsWith('image/') ? '🖼️' : '📄').join('');
      useChatSessionStore.setState(s => ({ messages: [...s.messages, { role: 'user', content: `${icons} ${fileNames}${text ? '\n' + text : ''}`, created_at: new Date().toISOString() }], sending: true }));
      try {
        const t = localStorage.getItem('access_token');
        const prompt = text || `请分析文件: ${fileNames}`;
        const r = await fetch(`/api/chat-sessions/${sid}/send-stream`, { method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${t}` }, body: JSON.stringify({ content: prompt, rag_enabled: ragEnabled, extra_context: allText || undefined, attachments: imageAttachments, web_search: webSearch, search_depth: searchDepth, show_thinking: showThinking }) });
        if (!r.ok) throw new Error(await parseStreamError(r, '上传发送失败'));
        await consumeChatStream(r);
      } catch (e: any) { appendAssistantError(getApiErrorMessage(e, { fallback: '上传发送失败' })); }
      finally { resetStreamProgress(); sendLock.current = false; useChatSessionStore.setState({ sending: false }); }
      return;
    }

    useChatSessionStore.setState(s => ({ messages: [...s.messages, { role: 'user', content: text, created_at: new Date().toISOString() }], sending: true }));
    try {
      const t = localStorage.getItem('access_token');
      const r = await fetch(`/api/chat-sessions/${sid}/send-stream`, { method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${t}` }, body: JSON.stringify({ content: text, rag_enabled: ragEnabled, web_search: webSearch, search_depth: searchDepth, show_thinking: showThinking }) });
      if (!r.ok) throw new Error(await parseStreamError(r, '发送失败'));
      await consumeChatStream(r);
    } catch (e: any) { appendAssistantError(getApiErrorMessage(e, { fallback: '发送失败' })); }
    finally { resetStreamProgress(); sendLock.current = false; useChatSessionStore.setState({ sending: false }); }
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
    const nextWebSearch = !webSearch;
    setWebSearch(nextWebSearch);
    if (nextWebSearch && searchDepth !== 'deep') {
      setSearchDepth('deep');
      message.info('已开启联网增强，并自动切换为深度检索');
    }
  };
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
          <div className="chat-toolbar-actions" style={{ fontSize: 13, fontWeight: 500 }}>
            <div className="chat-model-status">
              <Tooltip title={modelDetail}>
                <span className="chat-model-badge">
                  <RobotOutlined />
                  <span>{modelDisplay}</span>
                </span>
              </Tooltip>
              <Tooltip title={ragEnabled ? '知识库检索开启' : '知识库检索关闭'}>
                <span className={`chat-status-chip ${ragEnabled ? 'is-active' : ''}`}><DatabaseOutlined />知识库</span>
              </Tooltip>
              <Tooltip title={webSearch ? '联网增强开启' : '联网增强关闭'}>
                <span className={`chat-status-chip ${webSearch ? 'is-active' : ''}`}><GlobalOutlined />联网</span>
              </Tooltip>
              <Tooltip title={activeModelInfo?.capabilities?.thinking ? '当前模型支持思考展示' : '当前模型不支持思考展示'}>
                <span className={`chat-status-chip ${activeModelInfo?.capabilities?.thinking ? 'is-active' : ''}`}><BulbOutlined />思考</span>
              </Tooltip>
              <Tooltip title={activeModelInfo?.capabilities?.vision ? '当前模型支持图片输入' : hasImageAttachment ? '当前模型不支持图片输入' : '当前模型未标记为视觉模型'}>
                <span className={`chat-status-chip ${activeModelInfo?.capabilities?.vision ? 'is-active' : ''}`}><EyeOutlined />视觉</span>
              </Tooltip>
            </div>
            <Text className="chat-retrieval-strategy">{retrievalStrategy}</Text>
            <Button className={`chat-control-pill ${ragEnabled ? 'is-active' : ''}`} type="text" size="small" icon={<DatabaseOutlined />} onClick={() => handleToggleRag(!ragEnabled)}>知识库</Button>
            <Tooltip title="联网增强可以和知识库同时使用">
              <Button className={`chat-control-pill ${webSearch ? 'is-active' : ''}`} type="text" size="small" icon={<GlobalOutlined />} onClick={handleWebSearchToggle}>联网增强</Button>
            </Tooltip>
            <Select className="chat-depth-select" size="small" value={searchDepth} onChange={setSearchDepth} variant="borderless" style={{ width: 68, fontSize: 13 }} options={[{ value: 'quick', label: '快速' }, { value: 'standard', label: '标准' }, { value: 'deep', label: '深度' }]} />
            <Button className="chat-control-pill" type="text" size="small" icon={<ExportOutlined />} onClick={handleExport}>导出</Button>
            <Input className="chat-toolbar-search" size="small" prefix={<SearchOutlined />} placeholder="搜索..." value={convSearch} onChange={e => setConvSearch(e.target.value)} style={{ width: 120 }} allowClear />
          </div>
        </div>
        <div className="chat-message-list" style={{ flex: 1, overflowY: 'auto', padding: '24px 20px', background: token.colorBgLayout }}>
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
                <div key={idx} style={{ display: 'flex', gap: 10, marginBottom: 24, flexDirection: msg.role === 'user' ? 'row-reverse' : 'row', alignItems: 'flex-start' }}>
                  <Avatar size={32} icon={msg.role === 'user' ? <UserOutlined /> : <RobotOutlined />} style={{ flexShrink: 0, background: msg.role === 'user' ? 'linear-gradient(135deg,#667eea,#764ba2)' : 'linear-gradient(135deg,#12c2e9,#c471ed)' }} />
                  <div style={{ maxWidth: '72%' }}>
                    {msg.role === 'assistant' && msg.reasoning && (
                      <ThinkingPanel reasoningText={msg.reasoning} isStreaming={!!msg._reasoningStreaming} startTime={msg.thinking_started_at} />
                    )}
                    {(msg.role === 'user' || msg.content) && (
                      <div style={{ padding: '12px 16px', borderRadius: msg.role === 'user' ? '16px 4px 16px 16px' : '4px 16px 16px 16px', background: msg.role === 'user' ? 'linear-gradient(135deg,#667eea,#764ba2)' : token.colorBgElevated, color: msg.role === 'user' ? '#fff' : token.colorText, boxShadow: msg.role === 'user' ? '0 2px 12px rgba(102,126,234,.3)' : `0 1px 4px ${token.colorFillSecondary}`, border: msg.role === 'user' ? 'none' : `1px solid ${token.colorBorderSecondary}`, lineHeight: 1.7, fontSize: 14 }}>
                        {msg.role === 'user' ? <div style={{ whiteSpace: 'pre-wrap', color: '#fff' }}>{msg.content}</div> : <Markdown content={msg.content} />}
                      </div>
                    )}
                    <div style={{ display: 'flex', gap: 4, marginTop: 4, paddingLeft: 4, justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
                      {!msg._streaming && <Button type="text" size="small" icon={<span>💬</span>} onClick={() => setInput(`> ${msg.content.slice(0, 100)}${msg.content.length > 100 ? '...' : ''}\n\n`)} title="引用回复" style={{ fontSize: 11, color: token.colorTextQuaternary }} />}
                      {msg.role === 'user' && <Button type="text" size="small" icon={<EditOutlined />} onClick={() => setInput(msg.content)} style={{ fontSize: 11, color: token.colorTextQuaternary }} />}
                      {!msg._streaming && msg.id && <Popconfirm title="删除此消息？" onConfirm={async () => { if (!msg.id || !currentSessionId) return; try { await api.delete(`/chat-sessions/${currentSessionId}/messages/${msg.id}`); useChatSessionStore.setState(s => ({ messages: s.messages.filter(m => m.id !== msg.id) })); } catch (error) { message.error(getApiErrorMessage(error, { fallback: '删除消息失败' })); } }}><Button type="text" size="small" icon={<DeleteOutlined />} style={{ fontSize: 11, color: '#ff4d4f40' }} /></Popconfirm>}
                      {msg.role === 'assistant' && !msg._streaming && <><Button type="text" size="small" icon={<CopyOutlined />} onClick={() => { navigator.clipboard.writeText(msg.content); message.success('已复制'); }} style={{ fontSize: 11, color: token.colorTextQuaternary }}>复制</Button>
                      <Dropdown menu={{ items: [
                        { key: 'balanced', label: '🔄 平衡', onClick: () => { handleToggleRag(true); setInput('请重新回答'); setTimeout(()=>handleSend(),100); } },
                        { key: 'creative', label: '💡 创意', onClick: () => { handleToggleRag(true); setInput('请用更有创意的角度回答'); setTimeout(()=>handleSend(),100); } },
                        { key: 'precise', label: '🎯 精确', onClick: () => { handleToggleRag(true); setInput('请精确严谨地重新回答'); setTimeout(()=>handleSend(),100); } },
                        { key: 'norag', label: '🧠 纯模型', onClick: () => { handleToggleRag(false); setInput('请重新回答'); setTimeout(()=>handleSend(),100); } },
                      ]}} trigger={['click']}>
                        <Button type="text" size="small" icon={<RedoOutlined />} style={{ fontSize: 11, color: token.colorTextQuaternary }}>重新生成</Button>
                      </Dropdown>
                      <Button type="text" size="small" onClick={async () => { if (msg.id) try { await api.post('/chat/feedback', { message_id: msg.id, rating: 'like' }); message.success('已反馈'); } catch (error) { message.error(getApiErrorMessage(error, { fallback: '反馈提交失败' })); } }} style={{ fontSize: 11, color: token.colorTextQuaternary }}>👍</Button>
                      <Button type="text" size="small" onClick={async () => { if (msg.id) try { await api.post('/chat/feedback', { message_id: msg.id, rating: 'dislike' }); message.success('已反馈'); } catch (error) { message.error(getApiErrorMessage(error, { fallback: '反馈提交失败' })); } }} style={{ fontSize: 11, color: token.colorTextQuaternary }}>👎</Button></>}
                    </div>
                    {msg.references && msg.references.length > 0 && <div style={{ marginTop: 8, padding: '8px 12px', background: token.colorBgElevated, borderRadius: 12, border: `1px solid ${token.colorBorderSecondary}` }}><Text type="secondary" style={{ fontSize: 11 }}>📎 引用：</Text>{(msg.references as any[]).map((ref: any, ri: number) => <Tag key={`${ref.url || ref.arxiv_id || ref.title}-${ri}`} color={ref.source === 'web' ? 'cyan' : 'geekblue'} style={{ marginTop: 4, cursor: ref.url || ref.arxiv_id ? 'pointer' : 'default', borderRadius: 8 }} onClick={() => { if (ref.url) window.open(ref.url, '_blank', 'noopener,noreferrer'); else if (ref.arxiv_id) window.open(`https://arxiv.org/abs/${ref.arxiv_id.replace(/v\d+$/, '')}`, '_blank', 'noopener,noreferrer'); }}>[{ri + 1}] {ref.source === 'web' ? '网页 · ' : ''}{ref.title?.slice(0, 40)}{ref.title?.length > 40 ? '...' : ''}{ref.year ? ` (${ref.year})` : ''}</Tag>)}</div>}
                    <div style={{ fontSize: 11, color: token.colorTextQuaternary, marginTop: 4, textAlign: msg.role === 'user' ? 'right' : 'left', padding: '0 4px' }}>{msg.created_at ? new Date(msg.created_at).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) : ''}</div>
                  </div>
                </div>
              ))}
              {pendingMsg && <div style={{ display: 'flex', gap: 10, marginBottom: 24, flexDirection: 'row-reverse' }}><Avatar size={32} icon={<UserOutlined />} style={{ background: 'linear-gradient(135deg,#667eea,#764ba2)' }} /><div style={{ maxWidth: '72%', padding: '12px 16px', borderRadius: '16px 4px 16px 16px', background: 'linear-gradient(135deg,#667eea,#764ba2)', color: '#fff', boxShadow: '0 2px 12px rgba(102,126,234,.3)', lineHeight: 1.7, fontSize: 14 }}>{pendingMsg}</div></div>}
              {sending && <div style={{ display: 'flex', gap: 10, marginBottom: 24 }}><Avatar size={32} icon={<RobotOutlined />} style={{ background: 'linear-gradient(135deg,#12c2e9,#c471ed)' }} /><div className="chat-stream-status" style={{ background: token.colorBgElevated, border: `1px solid ${token.colorBorderSecondary}` }}><Space size={8} align="start"><Space size={5} style={{ paddingTop: 5 }}>{[0, 0.2, 0.4].map((d, i) => <div key={i} style={{ width: 7, height: 7, borderRadius: '50%', background: '#c471ed', animation: `bounce 1.4s infinite ease-in-out ${d}s` }} />)}</Space><div className="chat-stream-status-copy">{streamPhaseLabel && <span className="chat-stream-phase"><ClockCircleOutlined />{streamPhaseLabel}</span>}<Text type="secondary" className="chat-stream-status-text">{streamStatus || '正在等待模型响应...'}</Text></div></Space></div></div>}
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
                    <span className="chat-attachment-name">{af.extracting ? '解析中' : af.text ? '就绪' : '异常'} · {af.file.name}</span>
                    <Button className="chat-attachment-remove" type="text" size="small" icon={<CloseOutlined />} onClick={() => setAttachedFiles(prev => prev.filter(f => f.id !== af.id))} />
                  </div>
                ))}
              </div>
            )}
            <div className="chat-editor">
              <Tooltip title="上传论文或图片"><Button className="chat-upload-button chat-tool-button" type="text" icon={<UploadOutlined />} onClick={() => { const el = document.createElement('input'); el.type = 'file'; el.accept = 'image/*,.pdf'; el.multiple = true; el.onchange = async () => { for (const f of Array.from(el.files || [])) { if (f.size > 10 * 1024 * 1024) { message.warning(`${f.name} 超过10MB`); continue; } const id = Math.random().toString(36).slice(2); setAttachedFiles(prev => [...prev, { file: f, text: '', extracting: true, id }]); const fd = new FormData(); fd.append('file', f); try { const res = await api.post('/chat-sessions/extract-file', fd, { headers: { 'Content-Type': 'multipart/form-data' } }); setAttachedFiles(prev => prev.map(p => p.id === id ? { ...p, text: res.data.extracted_text || '', extracting: false, dataUrl: res.data.data_url || undefined, mimeType: res.data.mime_type || undefined } : p)); } catch (error) { setAttachedFiles(prev => prev.filter(p => p.id !== id)); message.error(getApiErrorMessage(error, { fallback: `${f.name} 解析失败` })); } } }; el.click(); }} /></Tooltip>
              <div className="chat-input-wrap"><Input.TextArea className="chat-input" value={input} onChange={e => setInput(e.target.value)} onPressEnter={e => { if (!e.shiftKey) { e.preventDefault(); handleSend(); } }} placeholder={ragEnabled ? '输入消息，Enter 发送，Shift+Enter 换行' : '输入消息...'} autoSize={{ minRows: 1, maxRows: 5 }} /></div>
              <Tooltip title="发送"><Button className="chat-send-button chat-tool-button" type="primary" shape="circle" icon={sending ? <LoadingOutlined /> : <SendOutlined />} onClick={handleSend} loading={sending} disabled={!input.trim() && attachedFiles.length === 0} /></Tooltip>
            </div>
          </div>
        </div>
      </div>
      <style>{'@keyframes bounce{0%,80%,100%{transform:scale(.6);opacity:.4}40%{transform:scale(1);opacity:1}}'}</style>
    </div>
  );
};

export default ChatPage;
