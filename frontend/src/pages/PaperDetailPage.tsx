import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card, Button, Tag, Typography, Space, Spin, message,
  Empty, Row, Col, Divider, Input, Avatar, Grid, Select, Tooltip, Modal, Drawer, Badge,
} from 'antd';
import {
  ArrowLeftOutlined, StarFilled, TagOutlined, SendOutlined,
  LinkOutlined, BulbOutlined, ExclamationCircleOutlined, RocketOutlined,
  RobotOutlined, UserOutlined,
  MenuFoldOutlined, MenuUnfoldOutlined,
  CopyOutlined, RedoOutlined,
  DatabaseOutlined, GlobalOutlined,
  DeleteOutlined, CloseOutlined,
  PlayCircleOutlined, CheckCircleOutlined, RollbackOutlined,
  BookOutlined, NodeIndexOutlined, FileSearchOutlined,
  ToolOutlined, DownOutlined, UpOutlined,
  UploadOutlined, FilePdfOutlined,
} from '@ant-design/icons';
import api from '../services/api';
import Markdown from '../components/Markdown';
import PDFViewer from '../components/PDFViewer';
import ThinkingPanel from '../components/ThinkingPanel';
import WorkspaceResourceLinks from '../components/WorkspaceResourceLinks';
import WorkspaceIssueReporter from '../components/WorkspaceIssueReporter';
import ResearchKnowledgeGraph, { type ResearchGraphEdge, type ResearchGraphNode } from '../components/ResearchKnowledgeGraph';
import { useAuthStore } from '../stores/useAuthStore';
import { useThemeStore } from '../stores/useThemeStore';
import useChatAutoScroll from '../hooks/useChatAutoScroll';
import useChatAttachments from '../hooks/useChatAttachments';
import {
  buildResearchCitationKey,
  computeEvidenceConfidence,
  computeMetadataQuality,
  scoreGraphEdgeStrength,
} from '../services/researchAlgorithms';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

interface StructuredPdfParseStatus {
  ready: boolean;
  parser?: string | null;
  source_path?: string | null;
  page_count: number;
  parsed_at?: string | null;
  table_count: number;
  caption_count: number;
  visual_count: number;
  ocr_count: number;
  formula_count: number;
  block_count: number;
  block_counts?: Record<string, number>;
  parser_health?: {
    configured_backend?: string;
    available?: Record<string, boolean>;
    command_configured?: boolean;
    hf_endpoint?: string;
  } | null;
  last_error?: { message?: string; parser_backend?: string; failed_at?: string; [key: string]: any } | null;
}

interface PaperData {
  id: string; title: string; authors: string[]; year: number | null;
  abstract: string | null; arxiv_id: string | null; doi: string | null;
  source: string; source_url: string | null; citation_count: number;
  pdf_url?: string | null; pdf_path?: string | null;
  full_text_preview: string | null; tags: any;
  categories: { id: string; name: string }[];
  similar_papers: { id: string; title: string; year: number | null; arxiv_id: string | null; tags: any }[];
  importance_label?: PaperImportanceLabel | null;
  importance_note?: string | null;
  structured_parse_status?: StructuredPdfParseStatus | null;
  visual_evidence_status?: {
    ready: boolean;
    status?: string;
    item_count?: number;
    visual_count?: number;
    table_count?: number;
    asset_count?: number;
    failed?: boolean;
    last_error?: { message?: string; failed_at?: string; [key: string]: any } | null;
  } | null;
  processing_labels?: {
    key: string;
    label: string;
    state: string;
    ready: boolean;
    detail?: string;
    count?: number;
  }[];
  processing_timeline?: {
    key: string;
    label: string;
    state: string;
    ready: boolean;
    detail?: string;
    count?: number;
    timestamp?: string | null;
    timestamp_label?: string | null;
    failed_at?: string | null;
    error?: string | null;
    next_retry_hint?: string | null;
  }[];
  processing_status?: string | null;
  created_at: string;
}

interface PaperInsight {
  paper_id: string;
  generated_at: string;
  evidence_coverage: 'abstract_only' | 'full_text';
  contribution: string;
  reusable_methods: string;
  reproducible_experiments: string;
  limitations: string;
  research_gaps: string;
  research_fit: string;
  raw: string;
}

interface PaperChatReference {
  title: string;
  arxiv_id?: string | null;
  year?: number | null;
  similarity?: number;
  url?: string;
  source?: string;
  provider?: string;
  type?: string;
  id?: string;
  section?: string | null;
  page?: number | null;
  page_start?: number | null;
  page_end?: number | null;
  score?: number;
  snippet?: string;
  evidence_type?: string;
  parser_source?: string;
  metadata?: {
    kind?: string;
    caption?: string;
    bbox?: number[];
    confidence?: number;
    asset_path?: string;
    thumbnail_path?: string;
    asset_token?: string;
    thumbnail_token?: string;
    visual_evidence?: boolean;
    summary?: string;
    [key: string]: unknown;
  };
}

interface PaperPdfQuote {
  text: string;
  pageNumber: number;
}

type PaperSelectionSource = 'pdf' | 'content';
type PaperImportanceLabel = 'important' | 'interesting';

interface PaperSelectionMenu {
  text: string;
  x: number;
  y: number;
  source: PaperSelectionSource;
  pageNumber?: number;
}

interface PaperAnnotation {
  id: string;
  text: string;
  page: number;
  kind: string;
  note?: string | null;
  created_at: string;
}

interface ToolboxTool {
  id: string;
  name: string;
  kind: string;
  summary?: string | null;
  tags?: string[];
  papers?: Array<{ id: string; title: string; relation: string; evidence_note?: string | null }>;
}

interface PaperChatMessage {
  role: string;
  content: string;
  displayContent?: string;
  quote?: PaperPdfQuote;
  attachmentNames?: string[];
  references?: PaperChatReference[];
  evidence?: PaperChatEvidenceMeta;
  _streaming?: boolean;
  reasoning?: string;
  thinkingStartedAt?: number;
  _reasoningStreaming?: boolean;
  warning?: string;
}

interface PaperChatEvidenceMeta {
  evidence_count: number;
  evidence_coverage: number;
  evidence_insufficient: boolean;
  visual_evidence_count?: number;
  visual_evidence_available?: boolean;
  evidence_plan?: {
    intent?: string;
    strategy?: string;
    requested_sections?: string[];
    warnings?: string[];
    budgets?: Record<string, number>;
  } | null;
}

type PaperEvidenceCategory = 'paper_text' | 'table' | 'visual' | 'web' | 'related' | 'other';

interface PaperEvidenceDrawerState {
  open: boolean;
  message?: PaperChatMessage;
  index?: number;
  referenceKey?: string;
}

interface PaperReadingTemplate {
  key: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  question: string;
}

const readingStatusMeta = {
  unread: { label: '待读', icon: <RollbackOutlined /> },
  reading: { label: '阅读中', icon: <PlayCircleOutlined /> },
  completed: { label: '已完成', icon: <CheckCircleOutlined /> },
};

const paperImportanceMeta: Record<PaperImportanceLabel, { label: string; color: string; icon: React.ReactNode }> = {
  important: { label: '重点论文', color: 'volcano', icon: <ExclamationCircleOutlined /> },
  interesting: { label: '有趣论文', color: 'geekblue', icon: <RocketOutlined /> },
};

const groundingInstruction = '请严格基于这篇论文的标题、摘要、全文片段和可检索内容回答；如果论文内容不足以支持结论，请明确说明“当前论文内容不足”，不要编造。';

const paperReadingTemplates: PaperReadingTemplate[] = [
  {
    key: 'overview',
    title: '全篇速读',
    description: '贡献、方法、实验和局限一屏看懂',
    icon: <RobotOutlined />,
    question: `${groundingInstruction}\n请用结构化方式速读这篇论文，包含：1. 研究问题；2. 核心贡献；3. 方法思路；4. 实验结论；5. 局限与可追问点。`,
  },
  {
    key: 'introduction',
    title: '精读 Introduction',
    description: '背景、动机、问题定义和贡献',
    icon: <BookOutlined />,
    question: `${groundingInstruction}\n请重点检索并讲解这篇论文的 Introduction / 引言部分，按“研究背景、已有方法问题、作者动机、本文贡献、读者需要带着什么问题继续读”组织回答。`,
  },
  {
    key: 'method',
    title: '拆解 Method',
    description: '模块、流程、关键公式和设计动机',
    icon: <DatabaseOutlined />,
    question: `${groundingInstruction}\n请重点检索 Method / Approach / Methodology 相关章节，拆解这篇论文的方法：整体流程、核心模块、关键公式或算法、每个设计解决了什么问题，以及实现时最容易误解的点。`,
  },
  {
    key: 'experiments',
    title: '分析 Experiments',
    description: '数据集、指标、对比和消融结论',
    icon: <CheckCircleOutlined />,
    question: `${groundingInstruction}\n请重点检索 Experiments / Evaluation / Results 相关章节，总结实验设置、数据集、评价指标、主要对比结果、消融实验，以及实验是否足以支撑论文结论。`,
  },
  {
    key: 'gap',
    title: '找 Research Gap',
    description: '从局限中提炼后续研究方向',
    icon: <BulbOutlined />,
    question: `${groundingInstruction}\n请基于论文内容找出可以继续研究的 gap：包括论文承认的局限、实验未覆盖的场景、方法假设、可能失败案例，并给出 3 个可执行的后续研究问题。`,
  },
  {
    key: 'meeting',
    title: '生成组会提纲',
    description: '适合口头汇报的讲解顺序',
    icon: <TagOutlined />,
    question: `${groundingInstruction}\n请把这篇论文整理成中文组会汇报提纲：开场一句话、背景动机、方法主线、关键实验、优点、局限、可讨论问题。要求适合 5-8 分钟口头讲解。`,
  },
];

const paperEvidenceConfidenceMeta = {
  strong: { label: '证据较充分', color: 'green' },
  partial: { label: '部分支撑', color: 'gold' },
  weak: { label: '证据不足', color: 'orange' },
};

type ProcessingTimelineItem = NonNullable<PaperData['processing_timeline']>[number];

const formatParseTime = (value?: string | null) => {
  if (!value) return '未记录';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
};

const PDF_PANEL_MIN_PERCENT = 42;
const PDF_PANEL_MAX_PERCENT = 82;
const CHAT_COLLAPSE_THRESHOLD_PERCENT = 84;
const CHAT_REOPEN_WIDTH_PERCENT = 65;
const CONTENT_PANEL_MIN_PERCENT = 45;
const CONTENT_PANEL_MAX_PERCENT = 78;
const CONTENT_PANEL_DEFAULT_PERCENT = 65;

const PaperDetailPage: React.FC = () => {
  const { paperId } = useParams<{ paperId: string }>();
  const navigate = useNavigate();
  const [paper, setPaper] = useState<PaperData | null>(null);
  const [loading, setLoading] = useState(true);
  const [saved, setSaved] = useState(false);
  const [readStatus, setReadStatus] = useState<'unread' | 'reading' | 'completed'>('unread');
  const [readStatusUpdating, setReadStatusUpdating] = useState(false);
  const [notes, setNotes] = useState('');
  const [notesLoading, setNotesLoading] = useState(false);
  const [annotations, setAnnotations] = useState<PaperAnnotation[]>([]);
  const [paperInsight, setPaperInsight] = useState<PaperInsight | null>(null);
  const [insightLoading, setInsightLoading] = useState(false);
  const [annotationSaving, setAnnotationSaving] = useState(false);
  const [deletingAnnotationIds, setDeletingAnnotationIds] = useState<Set<string>>(new Set());
  const [parseStatus, setParseStatus] = useState<StructuredPdfParseStatus | null>(null);
  const [showPdf, setShowPdf] = useState(false);
  const [targetPdfPage, setTargetPdfPage] = useState<number | null>(null);
  const [mobilePanel, setMobilePanel] = useState<'content' | 'pdf' | 'chat'>('content');
  const [pdfPanelWidth, setPdfPanelWidth] = useState(CHAT_REOPEN_WIDTH_PERCENT);
  const [contentPanelWidth, setContentPanelWidth] = useState(CONTENT_PANEL_DEFAULT_PERCENT);
  const [chatCollapsed, setChatCollapsed] = useState(false);
  const paperBodyRef = useRef<HTMLDivElement>(null);
  const screens = Grid.useBreakpoint();
  const isMobile = !screens.md;

  // PDF 地址提前计算
  const pdfUrl = paper?.arxiv_id ? `/api/papers/pdf-proxy/${paper.arxiv_id}` : null;
  const isAuthenticated = !!localStorage.getItem('access_token');
  const isAdmin = useAuthStore((state) => state.user?.role === 'admin');

  const [selectionMenu, setSelectionMenu] = useState<PaperSelectionMenu | null>(null);
  const normalizeSelectionMenuPosition = (x: number, y: number) => {
    const menuHalfWidth = window.innerWidth < 768 ? 24 : 180;
    return {
      x: Math.min(Math.max(x, menuHalfWidth), window.innerWidth - menuHalfWidth),
      y: Math.min(Math.max(y, 72), window.innerHeight - 92),
    };
  };
  const closeSelectionMenu = () => {
    setSelectionMenu(null);
    window.getSelection()?.removeAllRanges();
  };
  useEffect(() => {
    const handleMouseUp = (event: MouseEvent) => {
      const target = event.target instanceof Element ? event.target : null;
      if (target?.closest('.paper-selection-menu')) return;
      const sel = window.getSelection();
      const text = sel?.toString().trim();
      const selectionElement = sel?.anchorNode instanceof Element ? sel.anchorNode : sel?.anchorNode?.parentElement;
      if (selectionElement?.closest('.paper-pdf-viewer')) {
        setSelectionMenu(null);
        return;
      }
      if (!selectionElement?.closest('.paper-detail-content-panel')) {
        setSelectionMenu(null);
        return;
      }
      if (text && text.length > 5 && text.length < 500) {
        const range = sel?.rangeCount ? sel.getRangeAt(0) : null;
        const rect = range?.getBoundingClientRect();
        if (rect) {
          setSelectionMenu({
            text,
            source: 'content',
            ...normalizeSelectionMenuPosition(rect.left + rect.width / 2, rect.top - 12),
          });
        }
      } else setSelectionMenu(null);
    };
    document.addEventListener('mouseup', handleMouseUp);
    return () => document.removeEventListener('mouseup', handleMouseUp);
  }, []);
  const handlePdfTextSelect = (text: string, pageNumber: number, position: { x: number; y: number }) => {
    setSelectionMenu({
      text,
      pageNumber,
      source: 'pdf',
      ...normalizeSelectionMenuPosition(position.x, position.y),
    });
  };

  // AI 问答
  const [chatMsgs, setChatMsgs] = useState<PaperChatMessage[]>([]);
  const [question, setQuestion] = useState('');
  const [pdfQuote, setPdfQuote] = useState<PaperPdfQuote | null>(null);
  const [asking, setAsking] = useState(false);
  const [askStatus, setAskStatus] = useState<string | null>(null);
  const [paperRagEnabled, setPaperRagEnabled] = useState(true);
  const [webSearch, setWebSearch] = useState(false);
  const [searchDepth, setSearchDepth] = useState<'quick' | 'standard' | 'deep'>('standard');
  const [expandedReferencePanels, setExpandedReferencePanels] = useState<Record<string, boolean>>({});
  const [evidenceDrawer, setEvidenceDrawer] = useState<PaperEvidenceDrawerState>({ open: false });
  const [tagging, setTagging] = useState(false);
  const [paperTools, setPaperTools] = useState<ToolboxTool[]>([]);
  const [availableTools, setAvailableTools] = useState<ToolboxTool[]>([]);
  const [toolLinking, setToolLinking] = useState(false);
  const [selectedToolId, setSelectedToolId] = useState<string | undefined>();
  const [toolRelation, setToolRelation] = useState('used');
  const [toolEvidenceNote, setToolEvidenceNote] = useState('');
  const showThinking = useThemeStore((s) => s.showThinking ?? false);
  const {
    attachedFiles: paperChatAttachments,
    setAttachedFiles: setPaperChatAttachments,
    rememberedAttachments: rememberedPaperChatAttachments,
    removeAttachment: removePaperChatAttachment,
    removeRememberedAttachment: removeRememberedPaperChatAttachment,
    openAttachmentPicker: openPaperChatAttachmentPicker,
    rememberAttachments: rememberPaperChatAttachments,
    mergedReadyAttachments: mergedPaperChatReadyAttachments,
    attachedTextContext: paperChatAttachmentTextContext,
    imageAttachmentPayloads: paperChatImageAttachmentPayloads,
    attachmentStatusLabel: paperChatAttachmentStatusLabel,
    hasExtractingAttachments: hasExtractingPaperChatAttachments,
  } = useChatAttachments();
  const {
    scrollContainerRef: paperChatScrollRef,
    scrollEndRef: chatEndRef,
    scrollToBottomIfFollowing: scrollPaperChatToBottomIfFollowing,
    enableFollowOutput: enablePaperChatFollowOutput,
  } = useChatAutoScroll();
  const retrievalStrategy = webSearch && paperRagEnabled
    ? '混合检索'
    : webSearch
      ? '联网检索'
      : paperRagEnabled
        ? '论文库增强'
        : '仅当前论文';

  const handlePanelResizePointerDown = (event: React.PointerEvent<HTMLDivElement>) => {
    if (isMobile || !showPdf) return;
    event.preventDefault();
    const container = paperBodyRef.current;
    if (!container) return;
    const rect = container.getBoundingClientRect();
    event.currentTarget.setPointerCapture(event.pointerId);

    const handlePointerMove = (moveEvent: PointerEvent) => {
      const rawPercent = ((moveEvent.clientX - rect.left) / rect.width) * 100;
      if (rawPercent >= CHAT_COLLAPSE_THRESHOLD_PERCENT) {
        setPdfPanelWidth(PDF_PANEL_MAX_PERCENT);
        setChatCollapsed(true);
        return;
      }
      setChatCollapsed(false);
      setPdfPanelWidth(Math.min(Math.max(rawPercent, PDF_PANEL_MIN_PERCENT), PDF_PANEL_MAX_PERCENT));
    };

    const handlePointerUp = () => {
      window.removeEventListener('pointermove', handlePointerMove);
      window.removeEventListener('pointerup', handlePointerUp);
      window.removeEventListener('pointercancel', handlePointerUp);
    };

    window.addEventListener('pointermove', handlePointerMove);
    window.addEventListener('pointerup', handlePointerUp);
    window.addEventListener('pointercancel', handlePointerUp);
  };

  const handleContentChatResizePointerDown = (event: React.PointerEvent<HTMLDivElement>) => {
    if (isMobile || showPdf) return;
    event.preventDefault();
    const container = paperBodyRef.current;
    if (!container) return;
    const rect = container.getBoundingClientRect();
    event.currentTarget.setPointerCapture(event.pointerId);

    const handlePointerMove = (moveEvent: PointerEvent) => {
      const rawPercent = ((moveEvent.clientX - rect.left) / rect.width) * 100;
      setContentPanelWidth(Math.min(Math.max(rawPercent, CONTENT_PANEL_MIN_PERCENT), CONTENT_PANEL_MAX_PERCENT));
    };

    const handlePointerUp = () => {
      window.removeEventListener('pointermove', handlePointerMove);
      window.removeEventListener('pointerup', handlePointerUp);
      window.removeEventListener('pointercancel', handlePointerUp);
    };

    window.addEventListener('pointermove', handlePointerMove);
    window.addEventListener('pointerup', handlePointerUp);
    window.addEventListener('pointercancel', handlePointerUp);
  };

  const reopenChatPanel = () => {
    setChatCollapsed(false);
    setPdfPanelWidth(CHAT_REOPEN_WIDTH_PERCENT);
  };

  useEffect(() => {
    if (!paperId) return;
    setLoading(true);
    api.get(`/papers/${paperId}`).then(res => {
      setPaper(res.data);
      setParseStatus(res.data.structured_parse_status || null);
      if (res.data.tags && typeof res.data.tags === 'object' && res.data.tags.domain) setShowPdf(true);
    }).catch(() => message.error('论文加载失败')).finally(() => setLoading(false));
  }, [paperId]);

  useEffect(() => {
    if (!showPdf || isMobile) {
      setChatCollapsed(false);
      setPdfPanelWidth(CHAT_REOPEN_WIDTH_PERCENT);
    }
  }, [isMobile, showPdf]);

  useEffect(() => {
    if (!paperId || !isAuthenticated) return;
    api.get(`/papers/${paperId}/user-state`).then(res => {
      setSaved(res.data.saved);
      setReadStatus(res.data.read_status || 'unread');
      setNotes(res.data.personal_notes || '');
    }).catch(() => {});
    // 加载问答历史
    api.get(`/papers/${paperId}/chat-history`).then(res => {
      if (res.data.messages?.length > 0) setChatMsgs(res.data.messages);
    }).catch(() => {});
    api.get(`/papers/${paperId}/annotations`).then(res => {
      setAnnotations(res.data || []);
    }).catch(() => {});
    api.get(`/toolbox/papers/${paperId}/tools`).then(res => {
      setPaperTools(res.data || []);
    }).catch(() => {});
  }, [paperId, isAuthenticated]);

  const fetchAvailableTools = async () => {
    if (!isAuthenticated) return;
    try {
      const response = await api.get('/toolbox/tools', { params: { limit: 100 } });
      setAvailableTools(response.data.items || []);
    } catch {
      // The paper detail page remains usable without toolbox suggestions.
    }
  };

  useEffect(() => { fetchAvailableTools(); }, [isAuthenticated]);

  useEffect(() => { scrollPaperChatToBottomIfFollowing(); }, [chatMsgs, scrollPaperChatToBottomIfFollowing]);

  const appendStreamingReply = (content: string, references: PaperChatReference[], evidence?: PaperChatEvidenceMeta | null) => {
    setChatMsgs(prev => {
      const msgs = [...prev];
      const last = msgs[msgs.length - 1];
      if (last?.role === 'assistant' && last._streaming) {
        msgs[msgs.length - 1] = {
          ...last,
          content: `${last.content}${content}`,
          references,
          evidence: evidence || last.evidence,
          _reasoningStreaming: false,
        };
      } else {
        msgs.push({ role: 'assistant', content, references, evidence: evidence || undefined, _streaming: true });
      }
      return msgs;
    });
  };
  const appendStreamingReasoning = (content: string) => {
    setChatMsgs(prev => {
      const msgs = [...prev];
      const last = msgs[msgs.length - 1];
      if (last?.role === 'assistant' && last._streaming) {
        msgs[msgs.length - 1] = {
          ...last,
          reasoning: `${last.reasoning || ''}${content}`,
          _reasoningStreaming: true,
          thinkingStartedAt: last.thinkingStartedAt || Date.now(),
        };
      } else {
        msgs.push({
          role: 'assistant',
          content: '',
          reasoning: content,
          _streaming: true,
          _reasoningStreaming: true,
          thinkingStartedAt: Date.now(),
        });
      }
      return msgs;
    });
  };

  const appendStreamingWarning = (content: string) => {
    setChatMsgs(prev => {
      const msgs = [...prev];
      const last = msgs[msgs.length - 1];
      if (last?.role === 'assistant') {
        msgs[msgs.length - 1] = { ...last, warning: content, _streaming: false, _reasoningStreaming: false };
      } else {
        msgs.push({ role: 'assistant', content: '', warning: content, _streaming: false });
      }
      return msgs;
    });
  };

  const consumePaperChatStream = async (response: Response) => {
    const reader = response.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let full = '';
    let reasoning = '';
    let references: PaperChatReference[] = [];
    let evidence: PaperChatEvidenceMeta | null = null;
    let warning: string | undefined;
    let finished = false;

    const handleFrame = (frame: string) => {
      const data = frame
        .split('\n')
        .filter(line => line.startsWith('data: '))
        .map(line => line.slice(6))
        .join('\n');
      if (!data) return false;
      if (data === '[DONE]') return true;

      try {
        const event = JSON.parse(data) as { type?: string; content?: string | { references?: PaperChatReference[]; evidence?: PaperChatEvidenceMeta } };
        if (event.type === 'status' && typeof event.content === 'string') {
          setAskStatus(event.content);
        } else if (event.type === 'reasoning' && typeof event.content === 'string') {
          reasoning += event.content;
          appendStreamingReasoning(event.content);
        } else if (event.type === 'meta' && typeof event.content === 'object') {
          references = event.content.references || [];
          evidence = event.content.evidence || null;
        } else if (event.type === 'warning' && typeof event.content === 'string') {
          warning = event.content;
          appendStreamingWarning(event.content);
        } else if ((event.type === 'content' || event.type === 'error') && typeof event.content === 'string') {
          full += event.content;
          appendStreamingReply(event.content, references, evidence);
        } else if (event.type === 'done') {
          return true;
        }
      } catch {
        full += data;
        appendStreamingReply(data, references, evidence);
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
    setChatMsgs(prev => prev.map(msg => msg._streaming ? { ...msg, _streaming: false, _reasoningStreaming: false } : msg));
    return { content: full, references, reasoning, evidence, warning };
  };

  const handleWebSearchToggle = () => {
    const nextWebSearch = !webSearch;
    setWebSearch(nextWebSearch);
    if (nextWebSearch && searchDepth !== 'deep') {
      setSearchDepth('deep');
      message.info('已开启联网增强，并自动切换为深度检索');
    }
  };

  const handleEvidenceReferenceClick = (ref: PaperChatReference) => {
    if (ref.type === 'paper_evidence' || ref.source === 'current_paper') {
      const page = ref.page || ref.page_start;
      if (page) {
        setTargetPdfPage(page);
        if (isMobile) setMobilePanel('pdf');
        else setShowPdf(true);
        message.info(`已跳转到 PDF 第 ${page} 页`);
      }
      return;
    }
    if (ref.url) window.open(ref.url, '_blank', 'noopener,noreferrer');
    else if (ref.arxiv_id) window.open(`https://arxiv.org/abs/${ref.arxiv_id.replace(/v\d+$/, '')}`, '_blank', 'noopener,noreferrer');
  };

  const referenceTitle = (ref: PaperChatReference) => {
    if (ref.type === 'paper_evidence' || ref.source === 'current_paper') {
      const page = ref.page || ref.page_start;
      const section = ref.section ? `${ref.section} · ` : '';
      const visualKind = ref.metadata?.visual_evidence ? `${ref.metadata.kind || ref.evidence_type} · ` : '';
      return `${ref.id || '证据'} · ${section}${visualKind}${page ? `PDF 第 ${page} 页` : '当前论文片段'}`;
    }
    return `${ref.source === 'web' ? '网页 · ' : ''}${ref.title?.slice(0, 24)}${ref.title?.length > 24 ? '...' : ''}`;
  };

  const referenceTooltip = (ref: PaperChatReference) => {
    const caption = typeof ref.metadata?.caption === 'string' ? ref.metadata.caption : '';
    const summary = typeof ref.metadata?.summary === 'string' ? ref.metadata.summary : '';
    const confidence = typeof ref.metadata?.confidence === 'number' ? `confidence ${(ref.metadata.confidence * 100).toFixed(0)}%` : '';
    return [caption, summary, confidence, ref.snippet, ref.title].filter(Boolean).join('\n\n');
  };

  const isTableLikeEvidenceReference = (ref: PaperChatReference) => {
    const evidenceType = String(ref.evidence_type || '').toLowerCase();
    const kind = String(ref.metadata?.kind || '').toLowerCase();
    const captionType = String(ref.metadata?.caption_type || '').toLowerCase();
    return (
      evidenceType === 'table' ||
      evidenceType === 'visual_table' ||
      evidenceType === 'table_pack' ||
      evidenceType === 'table_catalog' ||
      kind === 'table' ||
      kind === 'table_crop' ||
      captionType === 'table_caption'
    );
  };

  const isVisualLikeEvidenceReference = (ref: PaperChatReference) => (
    Boolean(ref.metadata?.visual_evidence) ||
    String(ref.evidence_type || '').toLowerCase().startsWith('visual') ||
    ['figure', 'image', 'ocr', 'formula'].includes(String(ref.metadata?.kind || '').toLowerCase())
  );

  const paperEvidenceCategoryMeta: Record<PaperEvidenceCategory, { label: string; color: string }> = {
    paper_text: { label: '正文证据', color: 'gold' },
    table: { label: '表格证据', color: 'blue' },
    visual: { label: '视觉/OCR', color: 'purple' },
    web: { label: '网页来源', color: 'cyan' },
    related: { label: '相关论文', color: 'geekblue' },
    other: { label: '其他来源', color: 'default' },
  };

  const evidenceCategoryForReference = (ref: PaperChatReference): PaperEvidenceCategory => {
    if (ref.source === 'web' || ref.url) return 'web';
    if (isTableLikeEvidenceReference(ref)) return 'table';
    if (isVisualLikeEvidenceReference(ref)) return 'visual';
    if (ref.type === 'paper_evidence' || ref.source === 'current_paper') return 'paper_text';
    if (ref.arxiv_id || ref.source === 'local' || ref.source === 'library') return 'related';
    return 'other';
  };

  const groupedEvidenceReferences = (refs?: PaperChatReference[]) => {
    const groups: Record<PaperEvidenceCategory, PaperChatReference[]> = {
      paper_text: [],
      table: [],
      visual: [],
      web: [],
      related: [],
      other: [],
    };
    (refs || []).forEach(ref => {
      groups[evidenceCategoryForReference(ref)].push(ref);
    });
    return groups;
  };

  const visualPreviewReferences = (refs?: PaperChatReference[]) => (refs || []).filter(ref => {
    const hasVisualType = isVisualLikeEvidenceReference(ref);
    const asset = ref.metadata?.thumbnail_path || ref.metadata?.asset_path;
    return hasVisualType && !isTableLikeEvidenceReference(ref) && typeof asset === 'string' && asset.length > 0;
  });

  const referencePanelKey = (msg: PaperChatMessage, idx: number) => {
    const firstRef = msg.references?.[0];
    return [
      idx,
      msg.role,
      firstRef?.id || firstRef?.url || firstRef?.arxiv_id || '',
      String(msg.content || '').slice(0, 48),
    ].join(':');
  };

  const openEvidenceDrawer = (messageItem: PaperChatMessage, index: number, referenceKey: string) => {
    setExpandedReferencePanels(prev => ({ ...prev, [referenceKey]: true }));
    setEvidenceDrawer({ open: true, message: messageItem, index, referenceKey });
  };

  const closeEvidenceDrawer = () => {
    if (evidenceDrawer.referenceKey) {
      setExpandedReferencePanels(prev => ({ ...prev, [evidenceDrawer.referenceKey!]: false }));
    }
    setEvidenceDrawer({ open: false });
  };

  const submitPaperQuestion = async (rawQuestion?: string, displayQuestion?: string, quoteOverride?: PaperPdfQuote | null) => {
    const templateMode = typeof rawQuestion === 'string';
    const activeQuote = quoteOverride !== undefined ? quoteOverride : templateMode ? null : pdfQuote;
    const visibleQuestion = (displayQuestion || rawQuestion || question.trim() || '请解释这段选中内容。').trim();
    const readyAttachmentContext = mergedPaperChatReadyAttachments();
    if ((!visibleQuestion && !activeQuote && readyAttachmentContext.length === 0) || asking) return;
    if (hasExtractingPaperChatAttachments) { message.warning('附件还在解析中...'); return; }
    const attachedFiles = [...paperChatAttachments];
    const attachmentNames = readyAttachmentContext.map(file => file.file.name);
    const attachmentText = paperChatAttachmentTextContext(readyAttachmentContext);
    const imageAttachments = paperChatImageAttachmentPayloads(readyAttachmentContext);
    const attachmentContext = [
      attachmentText ? `用户上传附件提取内容：\n${attachmentText}` : '',
      imageAttachments.length > 0 ? `用户上传图片：${imageAttachments.map(file => file.filename).join('、')}` : '',
    ].filter(Boolean).join('\n\n');
    const baseQuestion = activeQuote
      ? `引用 PDF 第 ${activeQuote.pageNumber} 页选中内容：\n${activeQuote.text}\n\n用户问题：${visibleQuestion}`
      : (rawQuestion || visibleQuestion);
    const q = attachmentContext ? `${baseQuestion}\n\n---\n\n${attachmentContext}` : baseQuestion;
    const userMessage: PaperChatMessage = {
      role: 'user',
      content: q,
      displayContent: visibleQuestion,
      quote: activeQuote || undefined,
      attachmentNames: attachmentNames.length > 0 ? attachmentNames : undefined,
    };
    setQuestion('');
    if (!templateMode) setPdfQuote(null);
    setPaperChatAttachments([]);
    if (templateMode && isMobile) setMobilePanel('chat');
    enablePaperChatFollowOutput();
    setChatMsgs(prev => [...prev, userMessage]);
    setAsking(true);
    setAskStatus(webSearch ? '正在检索当前论文、论文库与网络来源...' : paperRagEnabled ? '正在检索当前论文与相关论文...' : '正在阅读当前论文...');
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`/api/papers/${paperId}/ask-stream`, {
        method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ question: q, history: chatMsgs.slice(-6), rag_enabled: paperRagEnabled, web_search: webSearch, search_depth: searchDepth, show_thinking: showThinking, attachments: imageAttachments }),
      });
      if (!response.ok) throw new Error('Stream failed');
      const reply = await consumePaperChatStream(response);
      rememberPaperChatAttachments(attachedFiles);
      // Save to DB
      const allMsgs = [...chatMsgs, userMessage, { role: 'assistant', content: reply.content, references: reply.references, reasoning: reply.reasoning, evidence: reply.evidence, warning: reply.warning }];
      api.post(`/papers/${paperId}/chat-history`, { messages: allMsgs }).catch(()=>{});
    } catch {
      if (!templateMode) {
        setQuestion(current => current || visibleQuestion);
        setPdfQuote(current => current || activeQuote);
      }
      setPaperChatAttachments(current => current.length > 0 ? current : attachedFiles);
      setChatMsgs(prev => [...prev, { role: 'assistant', content: '❌ 问答失败，请稍后重试。' }]);
    }
    finally { setAsking(false); setAskStatus(null); }
  };

  const handleAsk = async () => {
    await submitPaperQuestion();
  };

  const handleReadingTemplate = async (template: PaperReadingTemplate) => {
    await submitPaperQuestion(template.question, template.title);
  };

  const handleSaveAnnotation = async (quoteOverride?: PaperPdfQuote) => {
    const activeQuote = quoteOverride || pdfQuote;
    if (!paperId || !activeQuote) return;
    if (!isAuthenticated) { message.warning('请先登录'); return; }
    setAnnotationSaving(true);
    try {
      const response = await api.post(`/papers/${paperId}/annotations`, {
        text: activeQuote.text,
        page: activeQuote.pageNumber,
        kind: 'quote',
      });
      setAnnotations(prev => [response.data, ...prev]);
      setSaved(true);
      message.success('已保存为论文摘录');
    } catch (error: any) {
      message.error(error.response?.data?.detail || '保存摘录失败');
    } finally {
      setAnnotationSaving(false);
    }
  };

  const handleAskAnnotation = async (annotation: PaperAnnotation) => {
    await submitPaperQuestion(
      '请解释这段已保存摘录，并说明它在论文论证中的作用。如果上下文不足，请明确说明。',
      `解释第 ${annotation.page} 页摘录`,
      { text: annotation.text, pageNumber: annotation.page },
    );
  };

  const handleDeleteAnnotation = async (annotation: PaperAnnotation) => {
    if (!paperId) return;
    setDeletingAnnotationIds(prev => new Set(prev).add(annotation.id));
    try {
      await api.delete(`/papers/${paperId}/annotations/${annotation.id}`);
      setAnnotations(prev => prev.filter(item => item.id !== annotation.id));
      message.success('摘录已删除');
    } catch (error: any) {
      message.error(error.response?.data?.detail || '删除摘录失败');
    } finally {
      setDeletingAnnotationIds(prev => { const next = new Set(prev); next.delete(annotation.id); return next; });
    }
  };

  const handleSelectionAddToQuestion = () => {
    if (!selectionMenu) return;
    const selected = selectionMenu;
    closeSelectionMenu();
    if (selected.pageNumber) {
      setPdfQuote({ text: selected.text, pageNumber: selected.pageNumber });
      message.success(`已添加第 ${selected.pageNumber} 页引用`);
    } else {
      setQuestion(current => current ? `${current}\n\n${selected.text}` : selected.text);
      message.success('已加入问题草稿');
    }
    if (isMobile) setMobilePanel('chat');
  };

  const handleSelectionExplain = async () => {
    if (!selectionMenu) return;
    const selected = selectionMenu;
    closeSelectionMenu();
    if (selected.pageNumber) {
      await submitPaperQuestion(
        '请解释这段选中内容，并说明它在论文论证中的作用。如果上下文不足，请明确说明。',
        `解释第 ${selected.pageNumber} 页选段`,
        { text: selected.text, pageNumber: selected.pageNumber },
      );
      return;
    }
    await submitPaperQuestion(
      `${groundingInstruction}\n请解释下面这段选中文本，并说明它与当前论文的关系：\n\n${selected.text}`,
      '解释选中文本',
      null,
    );
  };

  const handleSelectionSaveAnnotation = async () => {
    const selected = selectionMenu;
    const pageNumber = selected?.pageNumber;
    if (!selected || pageNumber === undefined) return;
    closeSelectionMenu();
    await handleSaveAnnotation({ text: selected.text, pageNumber });
  };

  const handleSelectionCopy = async () => {
    if (!selectionMenu) return;
    const text = selectionMenu.text;
    closeSelectionMenu();
    try {
      await navigator.clipboard.writeText(text);
      message.success('已复制选中文本');
    } catch {
      message.error('复制失败，请手动复制');
    }
  };

  const handleSelectionAppendToNotes = () => {
    if (!selectionMenu) return;
    if (!isAuthenticated) { message.warning('请先登录'); return; }
    const selected = selectionMenu;
    closeSelectionMenu();
    const source = selected.pageNumber ? `PDF 第 ${selected.pageNumber} 页` : '选中文本';
    const block = `${source}\n${selected.text}`;
    setNotes(current => current ? `${current.trimEnd()}\n\n${block}` : block);
    setSaved(true);
    message.success('已加入笔记草稿');
    if (isMobile) setMobilePanel('content');
  };

  const handleSave = async () => {
    if (!isAuthenticated) { message.warning('请先登录'); return; }
    try {
      if (saved) { await api.delete(`/papers/${paperId}/save`); setSaved(false); }
      else { await api.post(`/papers/${paperId}/save`); setSaved(true); }
    } catch { message.error('操作失败'); }
  };

  const handleReadStatusChange = async (status: 'unread' | 'reading' | 'completed') => {
    if (!isAuthenticated) { message.warning('请先登录'); return; }
    setReadStatusUpdating(true);
    try {
      await api.put(`/papers/${paperId}/read-status`, { status });
      setReadStatus(status);
      setSaved(true);
      message.success(`已标记为${readingStatusMeta[status].label}`);
    } catch {
      message.error('阅读状态更新失败');
    } finally {
      setReadStatusUpdating(false);
    }
  };

  const handleImportanceChange = async (label: PaperImportanceLabel | null) => {
    if (!isAuthenticated) { message.warning('请先登录'); return; }
    if (!paperId) return;
    try {
      const response = await api.put(`/papers/${paperId}/importance`, { label });
      setPaper(current => current ? {
        ...current,
        importance_label: response.data.importance_label,
        importance_note: response.data.importance_note,
      } : current);
      message.success(label ? `已标记为${paperImportanceMeta[label].label}` : '已清除共享标记');
    } catch {
      message.error('共享标记更新失败');
    }
  };

  const handleClearChatHistory = () => {
    Modal.confirm({
      title: '清空这篇论文的问答记录？',
      content: '清空后将无法恢复，但不会影响收藏、笔记和阅读状态。',
      okText: '确认清空',
      cancelText: '取消',
      okButtonProps: { danger: true },
      onOk: async () => {
        try {
          await api.delete(`/papers/${paperId}/chat-history`);
          setChatMsgs([]);
          setExpandedReferencePanels({});
          message.success('已清空论文问答记录');
        } catch {
          message.error('清空失败');
        }
      },
    });
  };

  const handleSaveNotes = async () => {
    if (!isAuthenticated) return; setNotesLoading(true);
    try { await api.put(`/papers/${paperId}/note`, { note: notes }); message.success('已保存'); }
    catch { message.error('保存失败'); } finally { setNotesLoading(false); }
  };

  const handleAutoTag = async () => {
    setTagging(true);
    try { const res = await api.post(`/papers/${paperId}/auto-tag`); if (paper) setPaper({...paper, tags:res.data.tags}); message.success('标签已生成'); }
    catch { message.error('标签提取失败'); } finally { setTagging(false); }
  };

  const handleGenerateInsights = async (refresh = false) => {
    if (!isAuthenticated) { message.warning('请先登录'); return; }
    setInsightLoading(true);
    try {
      const response = await api.get(`/papers/${paperId}/insights`, { params: { refresh } });
      setPaperInsight(response.data);
      message.success(refresh ? '论文洞察已刷新' : '论文洞察已生成');
    } catch (error: any) {
      message.error(error.response?.data?.detail || '论文洞察生成失败');
    } finally {
      setInsightLoading(false);
    }
  };

  const handleLinkTool = async () => {
    if (!paperId || !selectedToolId) {
      message.warning('请选择要关联的工具');
      return;
    }
    setToolLinking(true);
    try {
      await api.post(`/toolbox/tools/${selectedToolId}/papers`, {
        paper_id: paperId,
        relation: toolRelation,
        evidence_note: toolEvidenceNote.trim() || undefined,
      });
      const response = await api.get(`/toolbox/papers/${paperId}/tools`);
      setPaperTools(response.data || []);
      setSelectedToolId(undefined);
      setToolEvidenceNote('');
      message.success('已关联到工具箱');
    } catch {
      message.error('工具关联失败');
    } finally {
      setToolLinking(false);
    }
  };

  const paperCitationReadiness = paper ? computeMetadataQuality(paper, { detail: true }) : null;
  const paperGraphNodes: ResearchGraphNode[] = paper ? [
    { id: `paper:${paper.id}`, label: paper.title, type: 'paper', status: paper.year ? String(paper.year) : paper.source, href: `/papers/${paper.id}` },
    ...((paper.similar_papers || []).slice(0, 4).map(item => ({
      id: `paper:${item.id}`,
      label: item.title,
      type: 'paper',
      status: item.year ? String(item.year) : 'related',
      href: `/papers/${item.id}`,
    }))),
    ...annotations.slice(0, 3).map(item => ({
      id: `note:${item.id}`,
      label: item.text.slice(0, 48),
      type: 'note',
      status: `PDF ${item.page}`,
    })),
  ] : [];
  const paperGraphEdges: ResearchGraphEdge[] = paper ? [
    ...((paper.similar_papers || []).slice(0, 4).map(item => ({
      from: `paper:${paper.id}`,
      to: `paper:${item.id}`,
      label: 'related',
      strength: scoreGraphEdgeStrength({ relation: 'related', count: paper.similar_papers?.length || 0 }),
    }))),
    ...annotations.slice(0, 3).map(item => ({
      from: `paper:${paper.id}`,
      to: `note:${item.id}`,
      label: '摘录',
      strength: scoreGraphEdgeStrength({ relation: '摘录', count: annotations.length }),
    })),
  ] : [];

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;
  if (!paper) return <Empty description="论文未找到" />;
  const activeParseStatus = parseStatus || paper.structured_parse_status || null;
  const parseStatusColor = activeParseStatus?.ready ? 'green' : activeParseStatus?.last_error ? 'red' : 'default';
  const parseStatusLabel = activeParseStatus?.ready ? '结构化已就绪' : activeParseStatus?.last_error ? '解析失败' : '结构化未就绪';
  const processingLabelMeta = (state?: string) => {
    if (state === 'ready') return { color: 'green', suffix: '就绪' };
    if (state === 'running' || state === 'pending') return { color: 'processing', suffix: '处理中' };
    if (state === 'failed') return { color: 'red', suffix: '失败' };
    if (state === 'stale') return { color: 'gold', suffix: '待刷新' };
    return { color: 'default', suffix: '待处理' };
  };
  const processingTimeline: ProcessingTimelineItem[] = (paper.processing_timeline && paper.processing_timeline.length > 0)
    ? paper.processing_timeline
    : (paper.processing_labels || []).map(label => ({ ...label }));
  const structuredCountItems = activeParseStatus ? [
    ['页数', activeParseStatus.page_count],
    ['结构块', activeParseStatus.block_count],
    ['表格', activeParseStatus.table_count],
    ['图注', activeParseStatus.caption_count],
    ['视觉', activeParseStatus.visual_count],
    ['OCR', activeParseStatus.ocr_count],
    ['公式', activeParseStatus.formula_count],
  ] : [];

  return (
    <div className="paper-detail-page">
      {/* 顶部工具栏 */}
      <div className="paper-detail-toolbar" style={{ borderBottom: '1px solid #f0f0f0', background: '#fff', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexShrink: 0 }}>
        <Space className="paper-detail-toolbar-main">
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)}>返回</Button>
          <Text className="paper-detail-title" strong ellipsis>{paper.title}</Text>
        </Space>
        <Space>
          {paper.pdf_url && <Button icon={<LinkOutlined />} href={paper.pdf_url} target="_blank" rel="noreferrer">开放 PDF</Button>}
          {isAuthenticated && (
            <Space.Compact>
              {(['unread', 'reading', 'completed'] as const).map(status => (
                <Tooltip key={status} title={`标记为${readingStatusMeta[status].label}`}>
                  <Button
                    type={readStatus === status ? 'primary' : 'default'}
                    icon={readingStatusMeta[status].icon}
                    loading={readStatusUpdating && readStatus !== status}
                    onClick={() => handleReadStatusChange(status)}
                  >
                    {!isMobile ? readingStatusMeta[status].label : undefined}
                  </Button>
                </Tooltip>
              ))}
            </Space.Compact>
          )}
          {!isMobile && pdfUrl && (
            <Button type={showPdf ? 'primary' : 'default'} icon={showPdf ? <MenuFoldOutlined /> : <MenuUnfoldOutlined />} onClick={() => setShowPdf(!showPdf)}>
              {showPdf ? '隐藏 PDF' : '显示 PDF'}
            </Button>
          )}
          {isAuthenticated && (
            <Space.Compact>
              <Tooltip title="所有用户可见的重点论文标记">
                <Button
                  type={paper?.importance_label === 'important' ? 'primary' : 'default'}
                  icon={<ExclamationCircleOutlined />}
                  onClick={() => handleImportanceChange('important')}
                >
                  {!isMobile ? '重点' : undefined}
                </Button>
              </Tooltip>
              <Tooltip title="所有用户可见的有趣论文标记">
                <Button
                  type={paper?.importance_label === 'interesting' ? 'primary' : 'default'}
                  icon={<RocketOutlined />}
                  onClick={() => handleImportanceChange('interesting')}
                >
                  {!isMobile ? '有趣' : undefined}
                </Button>
              </Tooltip>
              {paper?.importance_label && (
                <Tooltip title="清除共享标记">
                  <Button icon={<CloseOutlined />} onClick={() => handleImportanceChange(null)} />
                </Tooltip>
              )}
            </Space.Compact>
          )}
          {isAuthenticated && <Button icon={saved ? <StarFilled style={{color:'#faad14'}}/> : <StarFilled/>} onClick={handleSave}>{saved?'':'收藏'}</Button>}
        </Space>
        {isMobile && (
          <Space.Compact className="paper-detail-mobile-tabs">
            <Button type={mobilePanel === 'content' ? 'primary' : 'default'} onClick={() => setMobilePanel('content')}>正文</Button>
            {pdfUrl && <Button type={mobilePanel === 'pdf' ? 'primary' : 'default'} onClick={() => setMobilePanel('pdf')}>PDF</Button>}
            <Button type={mobilePanel === 'chat' ? 'primary' : 'default'} onClick={() => setMobilePanel('chat')}>问答</Button>
          </Space.Compact>
        )}
      </div>

      <div className="paper-detail-body" ref={paperBodyRef}>
        {/* PDF 面板 */}
        {pdfUrl && (isMobile ? mobilePanel === 'pdf' : showPdf) && (
          <div
            className="paper-detail-pdf-panel"
            style={{
              width: !isMobile && showPdf ? `${chatCollapsed ? PDF_PANEL_MAX_PERCENT : pdfPanelWidth}%` : undefined,
              flexShrink: 0,
              height: '100%',
            }}
          >
            <PDFViewer url={pdfUrl} onTextSelect={handlePdfTextSelect} targetPage={targetPdfPage} />
          </div>
        )}

        {!isMobile && showPdf && pdfUrl && (
          <div
            className="paper-detail-resize-handle"
            role="separator"
            aria-orientation="vertical"
            aria-label="调整 PDF 和 AI 问答宽度"
            onPointerDown={handlePanelResizePointerDown}
          />
        )}

        {/* 中间内容 — 显示 PDF 时自动隐藏 */}
        {(isMobile ? mobilePanel === 'content' : !showPdf) && (
        <div
          className="paper-detail-content-panel"
          style={{
            width: !isMobile && !showPdf ? `${contentPanelWidth}%` : undefined,
            flex: !isMobile && !showPdf ? '0 0 auto' : 1,
            overflowY: 'auto',
            padding: 16,
            borderRight: '1px solid #f0f0f0',
          }}
        >
          <Title level={4} style={{ marginTop: 0 }}>{paper.title}</Title>
          <Space size="small" wrap style={{ marginBottom: 12 }}>
            <Tag color="blue">{paper.year || 'N/A'}</Tag>
            {paper.arxiv_id && <a href={`https://arxiv.org/abs/${paper.arxiv_id.replace(/v\d+$/,'')}`} target="_blank"><Tag icon={<LinkOutlined />} color="#b31b1b">arXiv:{paper.arxiv_id}</Tag></a>}
            <Tag>{paper.citation_count} 引用</Tag>
            <Tag color="green">{paper.source}</Tag>
            {paper.importance_label && (
              <Tooltip title={paper.importance_note || '团队共享标记'}>
                <Tag icon={paperImportanceMeta[paper.importance_label].icon} color={paperImportanceMeta[paper.importance_label].color}>
                  {paperImportanceMeta[paper.importance_label].label}
                </Tag>
              </Tooltip>
            )}
            {(paper.processing_labels || []).filter(label => label.key !== 'pdf').slice(0, 5).map(label => {
              const meta = processingLabelMeta(label.state);
              return (
                <Tooltip key={label.key} title={label.detail || `${label.label}${meta.suffix}`}>
                  <Tag color={meta.color}>{label.label}{meta.suffix}</Tag>
                </Tooltip>
              );
            })}
          </Space>
          <Space size="small" wrap style={{ marginBottom: 12 }}>
            <TagOutlined style={{ color: '#999' }} />
            {paper.tags ? (() => { const t: any = paper.tags || {};
              if (Array.isArray(t)) return t.slice(0,5).map((x: string,i: number) => <Tag key={i} color="purple">{x}</Tag>);
              return <>{t.domain && <Tag color="blue">{t.domain}</Tag>}{(t.methods||[]).slice(0,3).map((m:string,i:number) => <Tag key={i} color="purple">{m}</Tag>)}</>;
            })() : <Text type="secondary">无</Text>}
            {isAdmin && <Button size="small" type="link" icon={<BulbOutlined />} loading={tagging} onClick={handleAutoTag}>AI 智能提取</Button>}
          </Space>
          <div style={{ marginTop: 12 }}>
            <Text strong>作者：</Text>
            <Text>{Array.isArray(paper.authors)?paper.authors.join(', '):paper.authors}</Text>
          </div>
          {processingTimeline.length > 0 && (
            <Card
              size="small"
              className="paper-processing-timeline-card"
              title={<span><DatabaseOutlined /> 后台处理时间线</span>}
              extra={paper.processing_status && (
                <Tag color={paper.processing_status === 'ready' ? 'green' : paper.processing_status === 'failed' ? 'red' : paper.processing_status === 'processing' ? 'processing' : 'orange'}>
                  {paper.processing_status === 'ready' ? '全部就绪' : paper.processing_status === 'failed' ? '存在失败' : paper.processing_status === 'processing' ? '处理中' : '待补齐'}
                </Tag>
              )}
              style={{ marginTop: 16, borderRadius: 12 }}
            >
              <div className="paper-processing-timeline-grid">
                {processingTimeline.map(item => {
                  const meta = processingLabelMeta(item.state);
                  const timestamp = item.timestamp;
                  const timestampLabel = item.timestamp_label;
                  const error = item.error;
                  const retryHint = item.next_retry_hint;
                  return (
                    <div className={`paper-processing-timeline-item is-${item.state || 'missing'}`} key={item.key}>
                      <Space size={6} wrap>
                        <Tag color={meta.color}>{item.label}{meta.suffix}</Tag>
                        {typeof item.count === 'number' && <Tag>{item.count}</Tag>}
                      </Space>
                      <Text className="paper-processing-timeline-detail" type={error ? 'danger' : 'secondary'}>
                        {error || item.detail || '暂无详情'}
                      </Text>
                      {timestamp && (
                        <Text type="secondary" className="paper-processing-timeline-time">
                          {timestampLabel || '时间'}: {formatParseTime(timestamp)}
                        </Text>
                      )}
                      {retryHint && (
                        <Text type="secondary" className="paper-processing-timeline-hint">
                          {retryHint}
                        </Text>
                      )}
                    </div>
                  );
                })}
              </div>
            </Card>
          )}
          <Card
            size="small"
            className="paper-reading-assistant-card"
            title={<span><RobotOutlined /> AI 精读助手</span>}
            extra={
              <Space size={6} wrap>
                <Tag color="blue">{readingStatusMeta[readStatus].label}</Tag>
                <Tag color={paper.full_text_preview ? 'green' : 'default'}>{paper.full_text_preview ? '全文增强' : '摘要优先'}</Tag>
              </Space>
            }
            style={{ marginTop: 16, borderRadius: 12 }}
          >
            <Text type="secondary" style={{ display: 'block', marginBottom: 12, fontSize: 13 }}>
              选择一个阅读任务，系统会自动组织更稳定的提问，并通过右侧 AI 问答返回结果。
            </Text>
            <Row gutter={[8, 8]}>
              {paperReadingTemplates.map(template => (
                <Col xs={24} sm={12} lg={8} key={template.key}>
                  <button
                    type="button"
                    className="paper-reading-template"
                    disabled={asking}
                    onClick={() => handleReadingTemplate(template)}
                  >
                    <span className="paper-reading-template-icon">{template.icon}</span>
                    <span className="paper-reading-template-copy">
                      <Text strong>{template.title}</Text>
                      <Text type="secondary">{template.description}</Text>
                    </span>
                  </button>
                </Col>
              ))}
            </Row>
          </Card>
          {activeParseStatus?.last_error && (
          <Card
            size="small"
            className="paper-parse-status-card"
            title={<span><FileSearchOutlined /> PDF 自动解析状态</span>}
            extra={
              <Space size={6} wrap>
                <Tag color={parseStatusColor}>{parseStatusLabel}</Tag>
              </Space>
            }
            style={{ marginTop: 16, borderRadius: 12 }}
          >
            {activeParseStatus ? (
              <Space direction="vertical" size={10} style={{ width: '100%' }}>
                <Space size={6} wrap>
                  <Tag color={activeParseStatus.parsed_at ? 'blue' : 'default'}>解析时间: {formatParseTime(activeParseStatus.parsed_at)}</Tag>
                </Space>
                <div className="paper-parse-count-grid">
                  {structuredCountItems.map(([label, value]) => (
                    <div className="paper-parse-count-item" key={label}>
                      <Text type="secondary">{label}</Text>
                      <Text strong>{Number(value || 0)}</Text>
                    </div>
                  ))}
                </div>
                {activeParseStatus.last_error ? (
                  <div className="paper-parse-error">
                    <Space size={6} wrap>
                      <Tag color="red">{activeParseStatus.last_error.parser_backend || 'parser'}</Tag>
                      {activeParseStatus.last_error.failed_at && <Tag color="red">失败时间: {formatParseTime(activeParseStatus.last_error.failed_at)}</Tag>}
                    </Space>
                    <Text type="danger" style={{ display: 'block', marginTop: 6 }}>
                      {activeParseStatus.last_error.message || '最近一次结构化解析失败'}
                    </Text>
                  </div>
                ) : (
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    最近一次结构化解析无错误记录。
                  </Text>
                )}
              </Space>
            ) : (
              <Text type="secondary">尚未检测到 PDF 结构化解析状态。</Text>
            )}
          </Card>
          )}
          {isAuthenticated && (
            <Card
              size="small"
              style={{ marginTop: 16, borderRadius: 12 }}
              title={<span><BulbOutlined /> AI 论文洞察</span>}
              extra={(
                <Space size={6}>
                  {paperInsight && <Tag color={paperInsight.evidence_coverage === 'full_text' ? 'green' : 'orange'}>{paperInsight.evidence_coverage === 'full_text' ? '基于全文' : '基于摘要'}</Tag>}
                  <Button size="small" icon={<BulbOutlined />} loading={insightLoading} onClick={() => handleGenerateInsights(!!paperInsight)}>
                    {paperInsight ? '刷新洞察' : '生成洞察'}
                  </Button>
                </Space>
              )}
            >
              {paperInsight ? (
                <Row gutter={[10, 10]}>
                  {[
                    ['核心贡献', paperInsight.contribution],
                    ['可借鉴方法', paperInsight.reusable_methods],
                    ['可复现实验', paperInsight.reproducible_experiments],
                    ['局限', paperInsight.limitations],
                    ['研究缺口', paperInsight.research_gaps],
                    ['研究方向关联', paperInsight.research_fit],
                  ].map(([title, content]) => (
                    <Col xs={24} md={12} key={title}>
                      <Card size="small" style={{ height: '100%', borderRadius: 10 }}>
                        <Text strong>{title}</Text>
                        <Paragraph style={{ marginTop: 8, marginBottom: 0, whiteSpace: 'pre-wrap', lineHeight: 1.7 }} ellipsis={{ rows: 5, expandable: true }}>
                          {content || '暂无内容'}
                        </Paragraph>
                      </Card>
                    </Col>
                  ))}
                </Row>
              ) : (
                <Text type="secondary">生成后会得到核心贡献、可借鉴方法、复现实验、局限、研究缺口和研究方向关联。</Text>
              )}
            </Card>
          )}
          {isAuthenticated && (
            <Card
              size="small"
              style={{ marginTop: 16, borderRadius: 12 }}
              title={<span><ToolOutlined /> 工具箱关联</span>}
              extra={<Button size="small" type="link" onClick={() => navigate('/toolbox')}>打开工具箱</Button>}
            >
              <Space direction="vertical" size={12} style={{ width: '100%' }}>
                {paperTools.length ? (
                  <Space size={8} wrap>
                    {paperTools.map(tool => (
                      <Tooltip key={tool.id} title={tool.summary || '工具箱条目'}>
                        <Tag color="cyan" icon={<ToolOutlined />}>{tool.name}</Tag>
                      </Tooltip>
                    ))}
                  </Space>
                ) : (
                  <Text type="secondary">这篇论文还没有关联工具。可以把它用到的算法、模型、数据集或评价协议沉淀到工具箱。</Text>
                )}
                <Space.Compact style={{ width: '100%' }}>
                  <Select
                    showSearch
                    allowClear
                    placeholder="选择已有工具"
                    value={selectedToolId}
                    onChange={setSelectedToolId}
                    optionFilterProp="label"
                    options={availableTools.map(tool => ({ value: tool.id, label: `${tool.name} · ${tool.kind}` }))}
                    style={{ minWidth: 220, flex: 1 }}
                  />
                  <Select
                    value={toolRelation}
                    onChange={setToolRelation}
                    options={[
                      { value: 'introduced', label: '提出' },
                      { value: 'used', label: '使用' },
                      { value: 'compared', label: '对比' },
                      { value: 'improved', label: '改进' },
                      { value: 'baseline', label: 'Baseline' },
                      { value: 'dataset', label: '数据集' },
                      { value: 'metric', label: '指标' },
                      { value: 'other', label: '其他' },
                    ]}
                    style={{ width: 116 }}
                  />
                  <Button type="primary" loading={toolLinking} onClick={handleLinkTool}>关联</Button>
                </Space.Compact>
                <Input
                  placeholder="证据说明，例如：论文将 GraphRAG 用于跨文档证据组织"
                  value={toolEvidenceNote}
                  onChange={event => setToolEvidenceNote(event.target.value)}
                  maxLength={500}
                  showCount
                />
              </Space>
            </Card>
          )}
          <Card
            size="small"
            className="paper-citation-network-panel"
            style={{ marginTop: 16, borderRadius: 12 }}
            title={<span><NodeIndexOutlined /> 引用网络准备度</span>}
            extra={paperCitationReadiness && <Tag color={paperCitationReadiness.tier === 'ready' ? 'green' : paperCitationReadiness.tier === 'usable' ? 'gold' : 'orange'}>{paperCitationReadiness.percent}%</Tag>}
          >
            {paperCitationReadiness && (
              <Space direction="vertical" size={10} style={{ width: '100%' }}>
                <Space size={6} wrap>
                  <Tag color="geekblue">cite key: {buildResearchCitationKey(paper)}</Tag>
                  <Tag color={paper.similar_papers?.length ? 'green' : 'default'}>邻近论文 {paper.similar_papers?.length || 0}</Tag>
                  <Tag color={paper.full_text_preview ? 'green' : 'orange'}>{paper.full_text_preview ? '全文可检索' : '等待全文抽取'}</Tag>
                </Space>
                <Space size={6} wrap>
                  {paperCitationReadiness.checks.map(check => (
                    <Tag key={check.key} color={check.ready ? 'green' : 'default'}>{check.label}</Tag>
                  ))}
                </Space>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  参考文献抽取：等待结构化解析；当前基于元数据、全文状态和相邻论文展示网络入口。
                </Text>
              </Space>
            )}
          </Card>
          <div style={{ marginTop: 16 }}>
            <ResearchKnowledgeGraph
              title="论文知识图谱"
              nodes={paperGraphNodes}
              edges={paperGraphEdges}
              compact
              maxNodes={8}
            />
          </div>
          {isAuthenticated && (
            <div style={{ marginTop: 16 }}>
              <Space direction="vertical" size={8} style={{ width: '100%' }}>
                <Space>
                  <Text strong>资源反馈</Text>
                  <WorkspaceIssueReporter
                    resourceType="papers"
                    resourceId={paper.id}
                    resourceTitle={paper.title}
                    resourcePath={`/papers/${paper.id}`}
                  />
                </Space>
                <WorkspaceResourceLinks resourceType="papers" resourceId={paper.id} title="所属项目空间" />
              </Space>
            </div>
          )}
          <Divider style={{ marginTop: 16 }}>摘要</Divider>
          <Paragraph style={{ lineHeight: 1.8 }}>{paper.abstract}</Paragraph>
          {paper.full_text_preview && <><Divider>全文</Divider><Paragraph ellipsis={{rows:10,expandable:true}} style={{ lineHeight:1.8 }}>{paper.full_text_preview}</Paragraph></>}
          {paper.similar_papers?.length>0 && <><Divider>📚 相关论文</Divider><Row gutter={[8,8]}>{paper.similar_papers.map((sp:any)=>(<Col xs={12} key={sp.id}><Card hoverable size="small" onClick={()=>navigate(`/papers/${sp.id}`)}><Text strong style={{fontSize:13}}>{sp.title}</Text><div>{sp.year&&<Tag color="blue">{sp.year}</Tag>}{sp.tags&&(Array.isArray(sp.tags)?sp.tags.slice(0,3):[]).map((t:string,i:number)=><Tag key={i} color="purple" style={{fontSize:11}}>{t}</Tag>)}</div></Card></Col>))}</Row></>}
          {isAuthenticated && (
            <Card size="small" style={{ marginTop: 16, borderRadius: 8 }} title="摘录与引用" extra={<Tag color="purple">{annotations.length}</Tag>}>
              {annotations.length ? (
                <Space direction="vertical" size={10} style={{ width: '100%' }}>
                  {annotations.map(annotation => (
                    <div key={annotation.id} className="paper-annotation-item">
                      <Space size={6} wrap style={{ marginBottom: 6 }}>
                        <Tag color="gold">第 {annotation.page} 页</Tag>
                        <Text type="secondary" style={{ fontSize: 12 }}>{new Date(annotation.created_at).toLocaleString()}</Text>
                      </Space>
                      <Paragraph style={{ marginBottom: 8, lineHeight: 1.7 }} ellipsis={{ rows: 3, expandable: true }}>{annotation.text}</Paragraph>
                      <Space size={6} wrap>
                        <Button size="small" icon={<SendOutlined />} disabled={asking} onClick={() => handleAskAnnotation(annotation)}>问 AI</Button>
                        <Button size="small" danger icon={<DeleteOutlined />} loading={deletingAnnotationIds.has(annotation.id)} onClick={() => handleDeleteAnnotation(annotation)}>删除</Button>
                      </Space>
                    </div>
                  ))}
                </Space>
              ) : (
                <Text type="secondary">在 PDF 中划词后，可以保存为摘录，后续用于问答或整理引用。</Text>
              )}
            </Card>
          )}
          {isAuthenticated && (
            <Card size="small" style={{ marginTop: 16, borderRadius: 8 }} title="📝 我的笔记"
              extra={<Button type="primary" size="small" onClick={handleSaveNotes} loading={notesLoading}>保存</Button>}>
              <TextArea rows={4} value={notes} onChange={e=>setNotes(e.target.value)} placeholder="记录对这篇论文的想法、关键要点..." />
            </Card>
          )}
        </div>
        )}

        {!isMobile && !showPdf && (
          <div
            className="paper-detail-resize-handle paper-detail-content-chat-resize-handle"
            role="separator"
            aria-orientation="vertical"
            aria-label="调整正文和 AI 问答宽度"
            onPointerDown={handleContentChatResizePointerDown}
          />
        )}

        {/* AI 问答面板 */}
        {(!isMobile || mobilePanel === 'chat') && chatCollapsed && showPdf ? (
          <div className="paper-detail-chat-rail">
            <Tooltip title="展开 AI 问答">
              <Button type="primary" shape="circle" icon={<RobotOutlined />} onClick={reopenChatPanel} />
            </Tooltip>
            <Text className="paper-detail-chat-rail-label">AI 问答</Text>
          </div>
        ) : (!isMobile || mobilePanel === 'chat') && <div
          className="paper-detail-chat-panel"
          style={{
            width: !isMobile
              ? showPdf
                ? `calc(${100 - pdfPanelWidth}% - 10px)`
                : `calc(${100 - contentPanelWidth}% - 10px)`
              : undefined,
            display: 'flex',
            flexDirection: 'column',
            height: '100%',
            background: '#fafafa',
            flexShrink: 0,
          }}
        >
          <Card title={<span><RobotOutlined /> AI 问答</span>} extra={chatMsgs.length > 0 ? <Tooltip title="清空问答记录"><Button type="text" danger size="small" icon={<DeleteOutlined />} disabled={asking} onClick={handleClearChatHistory} /></Tooltip> : null} size="small"
            className="paper-detail-chat-card"
            style={{ flex: 1, display: 'flex', flexDirection: 'column', borderRadius: 0, border: 'none' }}
            styles={{ body: { flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', minHeight: 0 } }}>
            <div className="paper-chat-controls">
              <Text className="paper-chat-strategy">{retrievalStrategy}</Text>
              <Button className={`chat-control-pill ${paperRagEnabled ? 'is-active' : ''}`} type="text" size="small" icon={<DatabaseOutlined />} onClick={() => setPaperRagEnabled(!paperRagEnabled)}>论文库</Button>
              <Tooltip title="联网增强可以与当前论文、论文库同时使用">
                <Button className={`chat-control-pill ${webSearch ? 'is-active' : ''}`} type="text" size="small" icon={<GlobalOutlined />} onClick={handleWebSearchToggle}>联网增强</Button>
              </Tooltip>
              <Select className="chat-depth-select" size="small" value={searchDepth} onChange={setSearchDepth} variant="borderless" style={{ width: 66, fontSize: 12 }} options={[{ value: 'quick', label: '快速' }, { value: 'standard', label: '标准' }, { value: 'deep', label: '深度' }]} />
            </div>
            <div ref={paperChatScrollRef} className="paper-detail-chat-scroll">
              {chatMsgs.length === 0 ? (
                <div style={{ padding: '24px 16px', textAlign: 'center', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                  <div style={{
                    width: 64, height: 64, margin: '0 auto 16px', borderRadius: 20,
                    background: 'linear-gradient(135deg, #667eea22, #764ba222)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}>
                    <RobotOutlined style={{ fontSize: 32, color: '#667eea' }} />
                  </div>
                  <Text strong style={{ fontSize: 15, color: '#333', marginBottom: 4 }}>论文问答助手</Text>
                  <Text type="secondary" style={{ fontSize: 13, marginBottom: 20 }}>选择一个精读模板，或直接输入你的问题</Text>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {paperReadingTemplates.slice(0, 4).map(item => (
                      <div
                        key={item.key}
                        onClick={() => !asking && handleReadingTemplate(item)}
                        style={{
                          padding: '10px 14px', borderRadius: 10, cursor: asking ? 'not-allowed' : 'pointer',
                          background: '#fff', border: '1px solid #f0f0f0',
                          textAlign: 'left', fontSize: 13, color: '#555',
                          transition: 'all 0.2s', opacity: asking ? 0.55 : 1,
                        }}
                        onMouseEnter={e => { e.currentTarget.style.borderColor = '#667eea'; e.currentTarget.style.background = '#f8f9ff'; }}
                        onMouseLeave={e => { e.currentTarget.style.borderColor = '#f0f0f0'; e.currentTarget.style.background = '#fff'; }}
                      >
                        <span style={{ marginRight: 8 }}>{item.icon}</span>
                        {item.title}
                        <Text type="secondary" style={{ display: 'block', marginLeft: 24, marginTop: 2, fontSize: 11 }}>{item.description}</Text>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                chatMsgs.map((msg,idx) => (
                  <div key={idx} style={{ marginBottom: 16, display: 'flex', gap: 8, flexDirection: msg.role==='user'?'row-reverse':'row', alignItems:'flex-start' }}>
                    <Avatar size={28} icon={msg.role==='user'?<UserOutlined/>:<RobotOutlined/>} style={{flexShrink:0, background:msg.role==='user'?'linear-gradient(135deg,#667eea,#764ba2)':'linear-gradient(135deg,#12c2e9,#c471ed)'}}/>
                    <div style={{ maxWidth: '82%' }}>
                      {msg.role === 'assistant' && msg.reasoning && (
                        <ThinkingPanel reasoningText={msg.reasoning} isStreaming={!!msg._reasoningStreaming} startTime={msg.thinkingStartedAt} />
                      )}
                      {(msg.role === 'user' || msg.content) && (
                        <div style={{ padding: '10px 14px', borderRadius: msg.role==='user'?'14px 4px 14px 14px':'4px 14px 14px 14px', background: msg.role==='user'? 'linear-gradient(135deg,#667eea,#764ba2)':'#fff', color: msg.role==='user'?'#fff':'#333', boxShadow: msg.role==='user'?'0 2px 8px rgba(102,126,234,.25)':'0 1px 3px rgba(0,0,0,.06)', border: msg.role==='user'?'none':'1px solid #f0f0f0', lineHeight: 1.7, fontSize: 13 }}>
                          {msg.role === 'user' ? <>
                            {msg.quote && <div className="paper-chat-message-quote"><strong>PDF 第 {msg.quote.pageNumber} 页</strong><br />{msg.quote.text}</div>}
                            {msg.attachmentNames && msg.attachmentNames.length > 0 && (
                              <div className="paper-chat-message-attachments">
                                {msg.attachmentNames.map(name => <Tag key={name} color="purple">{name}</Tag>)}
                              </div>
                            )}
                            <div style={{whiteSpace:'pre-wrap'}}>{msg.displayContent || msg.content}</div>
                          </> : <Markdown content={msg.content} />}
                        </div>
                      )}
                      {msg.role === 'assistant' && msg.warning && (
                        <div className="paper-chat-turn-warning">
                          <ExclamationCircleOutlined />
                          <Text type="secondary">{msg.warning}</Text>
                        </div>
                      )}
                      {msg.role === 'assistant' && !msg._streaming && (
                        <div style={{ display:'flex', gap: 4, marginTop: 4, paddingLeft: 4 }}>
                          <Button type="text" size="small" icon={<CopyOutlined />} onClick={()=>{navigator.clipboard.writeText(msg.content);message.success('已复制');}} style={{fontSize:11,color:'#bbb'}}>复制</Button>
                          <Button type="text" size="small" icon={<RedoOutlined />} onClick={()=>{setQuestion('请重新回答');}} style={{fontSize:11,color:'#bbb'}}>重新生成</Button>
                        </div>
                      )}
                      {((msg.references && msg.references.length > 0) || msg.evidence) && (() => {
                        const referenceKey = referencePanelKey(msg, idx);
                        const referencesExpanded = !!expandedReferencePanels[referenceKey];
                        const referenceGroups = groupedEvidenceReferences(msg.references);
                        const activeGroupEntries = (Object.keys(paperEvidenceCategoryMeta) as PaperEvidenceCategory[])
                          .filter(category => referenceGroups[category].length > 0);
                        const visualRefs = visualPreviewReferences(msg.references);
                        return (
                        <div className={`paper-chat-references ${referencesExpanded ? 'is-expanded' : 'is-collapsed'}`}>
                          {(() => {
                            const confidence = computeEvidenceConfidence(msg);
                            const meta = paperEvidenceConfidenceMeta[confidence.status];
                            return (
                              <div className="paper-answer-evidence-panel">
                                <div className="paper-chat-reference-summary">
                                  <div>
                                    <Space size={6} wrap>
                                      <Tag color={meta.color}>{meta.label}</Tag>
                                      <Tag color="blue">覆盖率 {Math.round(confidence.coverage * 100)}%</Tag>
                                      <Tag>证据 {confidence.evidenceCount}</Tag>
                                      {!!msg.evidence?.visual_evidence_count && <Tag color="purple">视觉 {msg.evidence.visual_evidence_count}</Tag>}
                                      {activeGroupEntries.map(category => (
                                        <Tag key={category} color={paperEvidenceCategoryMeta[category].color}>
                                          {paperEvidenceCategoryMeta[category].label} {referenceGroups[category].length}
                                        </Tag>
                                      ))}
                                    </Space>
                                    <Text type="secondary" style={{ display: 'block', marginTop: 4, fontSize: 11 }}>
                                      PaperQA 风格证据检查：优先依据当前论文片段和显式引用判断回答可信度。
                                    </Text>
                                  </div>
                                  {((msg.references && msg.references.length > 0) || msg.evidence) && (
                                    <Button
                                      type="text"
                                      size="small"
                                      className="paper-chat-reference-toggle"
                                      icon={referencesExpanded ? <UpOutlined /> : <DownOutlined />}
                                      onClick={() => referencesExpanded ? closeEvidenceDrawer() : openEvidenceDrawer(msg, idx, referenceKey)}
                                    >
                                      {referencesExpanded ? '收起引用' : `查看引用 ${msg.references?.length || 0}`}
                                    </Button>
                                  )}
                                </div>
                              </div>
                            );
                          })()}
                          {referencesExpanded && (
                            <div className="paper-chat-reference-drawer-hint">
                              {msg.evidence && (
                                <div>
                                  <Tag color={msg.evidence.evidence_insufficient ? 'orange' : 'green'} style={{ borderRadius: 8 }}>
                                    {msg.evidence.evidence_insufficient ? '证据不足' : `引用覆盖率 ${Math.round((msg.evidence.evidence_coverage || 0) * 100)}%`}
                                  </Tag>
                                  <Text type="secondary" style={{ fontSize: 11 }}>
                                    当前回答关联 {msg.evidence.evidence_count || 0} 条证据
                                    {msg.evidence.visual_evidence_count ? `，其中 ${msg.evidence.visual_evidence_count} 条视觉证据` : ''}
                                  </Text>
                                </div>
                              )}
                              <Text type="secondary" style={{ fontSize: 11 }}>
                                {visualRefs.length > 0 ? `含 ${visualRefs.length} 条可预览视觉证据。` : '详细引用已移到证据抽屉。'}
                              </Text>
                            </div>
                          )}
                        </div>
                        );
                      })()}
                    </div>
                  </div>
                ))
              )}
              {asking && <div style={{display:'flex',gap:8,alignItems:'flex-start'}}><Avatar size={28} icon={<RobotOutlined/>} style={{background:'linear-gradient(135deg,#12c2e9,#c471ed)'}}/><div style={{padding:'10px 14px',borderRadius:'4px 14px 14px 14px',background:'#fff',border:'1px solid #f0f0f0'}}><Space size={8}><Space size={5}>{[0,0.2,0.4].map((delay,i)=><div key={i} style={{width:6,height:6,borderRadius:'50%',background:'#c471ed',animation:`bounce 1.4s infinite ease-in-out ${delay}s`}}/>)}</Space><Text type="secondary" style={{fontSize:12}}>{askStatus || '正在生成回答...'}</Text></Space></div></div>}
              <div ref={chatEndRef} />
            </div>
            <div className="paper-detail-chat-composer">
              {pdfQuote && (
                <div className="paper-chat-quote-card">
                  <div className="paper-chat-quote-header">
                    <Text strong>PDF 第 {pdfQuote.pageNumber} 页</Text>
                    <Space size={4}>
                      <Button type="link" size="small" loading={annotationSaving} onClick={() => handleSaveAnnotation()}>保存摘录</Button>
                      <Button type="text" size="small" icon={<CloseOutlined />} onClick={() => setPdfQuote(null)} aria-label="移除引用" />
                    </Space>
                  </div>
                  <div className="paper-chat-quote-text">{pdfQuote.text}</div>
                </div>
              )}
              {paperChatAttachments.length > 0 && (
                <div className="chat-attachments paper-chat-attachments">
                  {paperChatAttachments.map(file => (
                    <div key={file.id} className="chat-attachment-chip">
                      {file.file.type.startsWith('image/')
                        ? <img className="chat-attachment-thumb" src={file.dataUrl || URL.createObjectURL(file.file)} alt="" />
                        : <span className="chat-attachment-file-icon"><FilePdfOutlined /></span>}
                      <span className="chat-attachment-name">{paperChatAttachmentStatusLabel(file)} · {file.file.name}</span>
                      <Button className="chat-attachment-remove" type="text" size="small" icon={<CloseOutlined />} onClick={() => removePaperChatAttachment(file.id)} />
                    </div>
                  ))}
                </div>
              )}
              {rememberedPaperChatAttachments.length > 0 && (
                <div className="chat-attachments paper-chat-attachments chat-remembered-attachments">
                  {rememberedPaperChatAttachments.map(file => (
                    <div key={file.id} className="chat-attachment-chip">
                      {file.file.type.startsWith('image/')
                        ? <img className="chat-attachment-thumb" src={file.optimizedDataUrl || file.dataUrl || URL.createObjectURL(file.file)} alt="" />
                        : <span className="chat-attachment-file-icon"><FilePdfOutlined /></span>}
                      <span className="chat-attachment-name">{paperChatAttachmentStatusLabel(file)} · {file.file.name}</span>
                      <Button className="chat-attachment-remove" type="text" size="small" icon={<CloseOutlined />} onClick={() => removeRememberedPaperChatAttachment(file.id)} />
                    </div>
                  ))}
                </div>
              )}
              <div className="paper-detail-chat-editor">
                <Button className="chat-upload-button chat-tool-button paper-detail-chat-upload" type="text" icon={<UploadOutlined />} disabled={asking} onClick={openPaperChatAttachmentPicker} />
                <TextArea className="paper-detail-chat-input" value={question} onChange={e=>setQuestion(e.target.value)}
                onPressEnter={e=>{if(!e.shiftKey){e.preventDefault();handleAsk();}}}
                placeholder={pdfQuote ? '围绕引用内容提问，Enter 发送，Shift+Enter 换行' : '基于论文提问，Enter 发送，Shift+Enter 换行'}
                autoSize={{ minRows: 1, maxRows: 6 }} disabled={asking}/>
                <Button className="paper-detail-chat-send" type="primary" shape="circle" icon={<SendOutlined/>} loading={asking} disabled={(!question.trim() && !pdfQuote && paperChatAttachments.length === 0 && rememberedPaperChatAttachments.length === 0) || hasExtractingPaperChatAttachments} onClick={handleAsk}/>
              </div>
            </div>
          </Card>
        </div>}
      </div>
      <Drawer
        title={<Space><FileSearchOutlined />回答证据</Space>}
        placement="right"
        width={isMobile ? '92vw' : 520}
        open={evidenceDrawer.open}
        onClose={closeEvidenceDrawer}
        className="paper-evidence-drawer"
      >
        {evidenceDrawer.message ? (() => {
          const drawerMessage = evidenceDrawer.message;
          const groups = groupedEvidenceReferences(drawerMessage.references);
          const confidence = computeEvidenceConfidence(drawerMessage);
          const confidenceMeta = paperEvidenceConfidenceMeta[confidence.status];
          const groupKeys = (Object.keys(paperEvidenceCategoryMeta) as PaperEvidenceCategory[])
            .filter(category => groups[category].length > 0);
          return (
            <div className="paper-evidence-drawer-body">
              <div className="paper-evidence-drawer-summary">
                <Space size={6} wrap>
                  <Tag color={confidenceMeta.color}>{confidenceMeta.label}</Tag>
                  <Tag color="blue">覆盖率 {Math.round(confidence.coverage * 100)}%</Tag>
                  <Tag>证据 {confidence.evidenceCount}</Tag>
                  {!!drawerMessage.evidence?.visual_evidence_count && <Tag color="purple">视觉 {drawerMessage.evidence.visual_evidence_count}</Tag>}
                </Space>
                {drawerMessage.evidence && (
                  <Text type="secondary" className="paper-evidence-drawer-copy">
                    当前回答关联 {drawerMessage.evidence.evidence_count || 0} 条证据
                    {drawerMessage.evidence.evidence_insufficient ? '，证据覆盖不足' : ''}
                    {drawerMessage.evidence.visual_evidence_count ? `，其中 ${drawerMessage.evidence.visual_evidence_count} 条视觉证据` : ''}
                  </Text>
                )}
              </div>
              {groupKeys.length === 0 ? (
                <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="当前回答没有可展开的引用证据" />
              ) : (
                groupKeys.map(category => (
                  <div key={category} className="paper-evidence-drawer-section">
                    <div className="paper-evidence-drawer-section-title">
                      <Space>
                        <Badge color={paperEvidenceCategoryMeta[category].color === 'default' ? '#8c8c8c' : undefined} />
                        <Text strong>{paperEvidenceCategoryMeta[category].label}</Text>
                        <Tag>{groups[category].length}</Tag>
                      </Space>
                    </div>
                    <div className={`paper-evidence-drawer-list ${category === 'visual' ? 'paper-chat-visual-preview-list' : ''}`}>
                      {groups[category].map((ref, ri) => {
                        const asset = String(ref.metadata?.thumbnail_path || ref.metadata?.asset_path || '');
                        const showVisualPreview = category === 'visual' && asset && !isTableLikeEvidenceReference(ref);
                        const page = ref.page || ref.page_start;
                        const confidenceLabel = typeof ref.metadata?.confidence === 'number'
                          ? `${Math.round(ref.metadata.confidence * 100)}%`
                          : '';
                        return (
                          <button
                            type="button"
                            key={`${category}-${ref.url || ref.arxiv_id || ref.id || ref.title}-${ri}`}
                            className={`paper-evidence-drawer-item ${showVisualPreview ? 'paper-chat-visual-preview' : ''}`}
                            onClick={() => handleEvidenceReferenceClick(ref)}
                            title={referenceTooltip(ref)}
                          >
                            {showVisualPreview && <img src={asset} alt={String(ref.metadata?.caption || ref.metadata?.kind || 'visual evidence')} />}
                            <span>
                              <strong>[{ri + 1}] {referenceTitle(ref)}</strong>
                              <small>
                                {[page ? `PDF 第 ${page} 页` : '', ref.section || ref.provider || ref.source || '', confidenceLabel].filter(Boolean).join(' · ')}
                              </small>
                              <em>{String(ref.metadata?.caption || ref.metadata?.summary || ref.snippet || ref.title || '').slice(0, 240)}</em>
                            </span>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                ))
              )}
            </div>
          );
        })() : (
          <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="未选择回答" />
        )}
      </Drawer>
      {selectionMenu && (
        <div
          className={`paper-selection-menu ${selectionMenu.source === 'pdf' ? 'is-pdf-selection' : 'is-content-selection'}`}
          style={{ left: selectionMenu.x, top: selectionMenu.y }}
          role="toolbar"
          aria-label="选中文本操作"
          onMouseDown={(event) => event.preventDefault()}
        >
          <span className="paper-selection-menu-source">
            {selectionMenu.pageNumber ? `PDF ${selectionMenu.pageNumber}` : '正文'}
          </span>
          <Tooltip title="加入提问">
            <Button size="small" type="primary" icon={<SendOutlined />} disabled={asking} onClick={handleSelectionAddToQuestion}>
              提问
            </Button>
          </Tooltip>
          <Tooltip title="直接解释">
            <Button size="small" icon={<BulbOutlined />} disabled={asking} onClick={handleSelectionExplain}>
              解释
            </Button>
          </Tooltip>
          {selectionMenu.pageNumber && (
            <Tooltip title="保存为摘录">
              <Button size="small" loading={annotationSaving} onClick={handleSelectionSaveAnnotation}>
                保存
              </Button>
            </Tooltip>
          )}
          <Tooltip title="复制">
            <Button size="small" icon={<CopyOutlined />} onClick={handleSelectionCopy} />
          </Tooltip>
          <Tooltip title="加入笔记">
            <Button size="small" icon={<BookOutlined />} onClick={handleSelectionAppendToNotes} />
          </Tooltip>
          <Button size="small" type="text" icon={<CloseOutlined />} onClick={closeSelectionMenu} aria-label="关闭划词操作" />
        </div>
      )}
      <style>{'@keyframes bounce{0%,80%,100%{transform:scale(.6);opacity:.4}40%{transform:scale(1);opacity:1}}'}</style>
    </div>
  );
};

export default PaperDetailPage;
