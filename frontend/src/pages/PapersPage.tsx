import React, { useState, useCallback, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Input, Button, List, Tag, Select, Space, Typography, Spin, Badge,
  Card, message, Modal, Checkbox, Row, Col, Alert, Progress, Tooltip,
  Statistic, Empty, Segmented,
} from 'antd';
import {
  SearchOutlined, CalendarOutlined, UserOutlined,
  RiseOutlined, LoadingOutlined,
  StarFilled, StarOutlined, DeleteOutlined, ExclamationCircleOutlined,
  ImportOutlined, FileTextOutlined, BookOutlined,
  RocketOutlined, EyeOutlined, RedoOutlined, LinkOutlined,
  BellOutlined, PlayCircleOutlined, CheckCircleOutlined, RollbackOutlined,
  FolderOutlined, FolderAddOutlined, DatabaseOutlined,
  CaretDownOutlined, CaretRightOutlined,
  TagsOutlined, DownloadOutlined, CloseOutlined,
} from '@ant-design/icons';
import api from '../services/api';
import { getApiErrorDetails, type ApiErrorDetails } from '../services/apiError';
import { useAuthStore } from '../stores/useAuthStore';
import WorkflowStepGuide from '../components/WorkflowStepGuide';
import PageShell from '../components/PageShell';
import ApiErrorAlert from '../components/ApiErrorAlert';
import { WorkflowEmptyState, WorkflowLoadingState } from '../components/WorkflowState';
import {
  buildResearchCitationKey,
  computeDuplicateRiskMap,
  computeMetadataQuality,
  duplicateRiskForPaper,
} from '../services/researchAlgorithms';

const { Text, Paragraph, Title } = Typography;

interface PaperItem {
  id: string; title: string; authors: string[]; year: number | null;
  abstract: string | null; abstract_full?: string | null; arxiv_id: string | null; doi: string | null;
  source: string; citation_count: number; created_at: string;
  remote_id?: string | null;
  remote_ingest_token?: string | null;
  pdf_url?: string | null;
  source_url?: string | null;
  read_status?: ReadingStatus | null;
  imported_by_user_id?: string | null;
  imported_by_username?: string | null;
  importance_label?: PaperImportanceLabel | null;
  importance_note?: string | null;
  has_pdf?: boolean;
  has_full_text?: boolean;
  has_embedding?: boolean;
  has_tags?: boolean;
  processing_status?: string | null;
  processing_labels?: ProcessingLabel[];
  processing_automation?: { last_checked_at?: string; last_completed_at?: string; last_error?: { message?: string } } | null;
  recommendation_kind?: string;
  recommendation_reason?: string;
}

interface ProcessingLabel {
  key: string;
  label: string;
  state: 'ready' | 'missing' | 'pending' | 'running' | 'failed' | 'stale' | string;
  ready: boolean;
  detail?: string;
  count?: number;
  action?: string;
}

interface ProcessingStatusItem {
  id: string;
  title: string;
  year?: number | null;
  source: string;
  imported_by_username?: string | null;
  has_pdf: boolean;
  has_full_text: boolean;
  has_embedding: boolean;
  has_tags: boolean;
  status: string;
  missing: string[];
  failed?: string[];
  processing_labels?: ProcessingLabel[];
  automation?: { last_checked_at?: string; last_completed_at?: string; last_error?: { message?: string } } | null;
  repair_actions: { key: string; label: string; endpoint: string }[];
  structured_parse_status?: {
    ready: boolean;
    parser?: string | null;
    block_count?: number;
    table_count?: number;
    caption_count?: number;
    visual_count?: number;
    ocr_count?: number;
    formula_count?: number;
    table_quality?: {
      quality?: 'none' | 'low' | 'medium' | 'high' | string;
      low_quality_table_count?: number;
      table_count?: number;
      warnings?: string[];
      empty_cell_ratio?: number;
      generic_header_ratio?: number;
      average_rows?: number;
      flags?: string[];
      merged_numeric_cell_count?: number;
      inconsistent_row_count?: number;
    } | null;
    last_error?: { message?: string; parser_backend?: string; failed_at?: string } | null;
  } | null;
  visual_evidence_status?: {
    ready: boolean;
    status?: string;
    parser?: string | null;
    item_count?: number;
    visual_count?: number;
    table_count?: number;
    asset_count?: number;
    summary_count?: number;
    ocr_count?: number;
    missing_summary_count?: number;
    missing_ocr_count?: number;
    low_confidence_table_count?: number;
    failed?: boolean;
    last_error?: { message?: string; failed_at?: string } | null;
  } | null;
}

interface PaperCollection {
  id: string;
  name: string;
  paper_count?: number;
  diagnostics?: CollectionDiagnostics;
}

interface CollectionDiagnostics {
  paper_count: number;
  full_text_coverage: number;
  embedding_coverage: number;
  read_status_counts?: Record<string, number>;
  ready_for_idea: boolean;
  warnings?: string[];
}

interface CollectionCoverageTopic {
  label: string;
  query: string;
  matched_count: number;
  matched_titles?: string[];
  status: 'covered' | 'thin' | 'missing';
}

interface CollectionCoverage {
  folder_id: string;
  name: string;
  paper_count: number;
  topic_terms: string[];
  topics: CollectionCoverageTopic[];
  summary: string;
  recommended_queries: Record<'classic' | 'recent' | 'gap' | 'related', string>;
}

type ReadingStatus = 'unread' | 'reading' | 'completed';
type PaperImportanceLabel = 'important' | 'interesting';
type SelectedExportFormat = 'bibtex' | 'markdown' | 'json';
type RecommendationKind = 'classic' | 'recent' | 'gap' | 'related';
type DiagnosticTab = 'hybrid' | 'bm25' | 'dense' | 'visual';
type PaperResultStateFilter = 'all' | 'local' | 'importable' | 'imported' | 'open_pdf' | 'missing_remote_id';
type MaintenanceJobState = 'queued' | 'running' | 'success' | 'failed' | 'cancelled' | 'unknown';

interface MaintenanceJobStatus {
  id?: string;
  kind: string;
  state: MaintenanceJobState;
  status: string;
  total: number;
  processed: number;
  success: number;
  failed: number;
  skipped: number;
  progress_percent: number;
  current_paper?: { id?: string; title?: string; year?: number | null } | null;
  errors?: { paper_id?: string; title?: string; reason?: string }[];
  message?: string;
  result?: { processed: number; success: number; failed: number; skipped: number; errors?: any[] } | null;
}

interface ProcessingAutomationHealth {
  enabled: boolean;
  cadence_minutes: number;
  batch_limit: number;
  pending: number;
  ready: number;
  failed: number;
  labels: { key: string; label: string; ready: number; pending: number; failed: number; ready_ratio?: number }[];
}

const remoteSearchSources = ['scholarly', 'arxiv', 'semantic_scholar', 'openalex', 'google_scholar'];
const paperSearchSources = ['local', 'mine', 'saved', 'collection', 'reading', 'maintenance', ...remoteSearchSources];
const readingStatusMeta: Record<ReadingStatus, { label: string; color: 'default' | 'processing' | 'success' }> = {
  unread: { label: '待读', color: 'default' },
  reading: { label: '阅读中', color: 'processing' },
  completed: { label: '已完成', color: 'success' },
};
const paperImportanceMeta: Record<PaperImportanceLabel, { label: string; color: string; icon: React.ReactNode }> = {
  important: { label: '重点论文', color: 'volcano', icon: <ExclamationCircleOutlined /> },
  interesting: { label: '有趣论文', color: 'geekblue', icon: <RocketOutlined /> },
};
const providerGuidance: Record<string, { label: string; providers: string[]; description: string; retry: string }> = {
  scholarly: {
    label: '综合学术检索',
    providers: ['arXiv', 'Semantic Scholar', 'OpenAlex', 'Google Scholar'],
    description: '会尽量融合多个学术源，适合先找全局候选；不同来源可用性取决于网络、API Key 和开放访问状态。',
    retry: '结果少时可以放宽年份、换一批，或切换到单一 provider 排查来源问题。',
  },
  arxiv: {
    label: 'arXiv',
    providers: ['arXiv'],
    description: '偏预印本和最新工作，通常最容易获得开放 PDF，但不覆盖所有会议/期刊论文。',
    retry: '如果没有结果，尝试英文关键词、缩短查询，或去综合学术检索补 OpenAlex/Semantic Scholar。',
  },
  semantic_scholar: {
    label: 'Semantic Scholar',
    providers: ['Semantic Scholar'],
    description: '适合查高引论文、引用信息和跨来源论文，但开放 PDF 需要看返回元数据。',
    retry: '如果命中少，尝试更宽泛任务词，或切换 OpenAlex 查 DOI/期刊论文。',
  },
  openalex: {
    label: 'OpenAlex',
    providers: ['OpenAlex'],
    description: '覆盖期刊、会议和 DOI 元数据较广，部分论文可能没有 PDF。',
    retry: '如果只有摘要没有 PDF，可先入库，再用来源链接或 DOI 继续追踪全文。',
  },
  google_scholar: {
    label: 'Google Scholar',
    providers: ['Google Scholar'],
    description: '需要后端配置可用 provider，适合兜底查较分散的学术网页结果。',
    retry: '如果不可用，优先使用综合学术、OpenAlex 或 Semantic Scholar。',
  },
};
const paperResultStateOptions: { value: PaperResultStateFilter; label: string }[] = [
  { value: 'all', label: '全部状态' },
  { value: 'local', label: '已在库' },
  { value: 'importable', label: '可入库' },
  { value: 'imported', label: '本次已加入' },
  { value: 'open_pdf', label: '开放 PDF' },
  { value: 'missing_remote_id', label: '缺远程 ID' },
];

const paperRemoteKey = (paper: PaperItem) => paper.remote_id ? `${paper.source}:${paper.remote_id}` : '';
const paperResultState = (paper: PaperItem, ingestedRemoteIds: Set<string>) => {
  const remoteKey = paperRemoteKey(paper);
  if (paper.id) return { key: 'local' as const, label: '已在库', color: 'green' };
  if (remoteKey && ingestedRemoteIds.has(remoteKey)) return { key: 'imported' as const, label: '本次已加入', color: 'success' };
  if (paper.remote_id) return { key: 'importable' as const, label: '可入库', color: 'geekblue' };
  return { key: 'missing_remote_id' as const, label: '缺远程 ID', color: 'default' };
};
const paperResultStateCounts = (items: PaperItem[], ingestedRemoteIds: Set<string>) => {
  const counts = { all: items.length, local: 0, importable: 0, imported: 0, open_pdf: 0, missing_remote_id: 0 };
  items.forEach(item => {
    counts[paperResultState(item, ingestedRemoteIds).key] += 1;
    if (item.pdf_url) counts.open_pdf += 1;
  });
  return counts;
};

const escapeBibtexValue = (value: unknown) => String(value || '')
  .replace(/[{}]/g, '')
  .replace(/\s+/g, ' ')
  .trim();

const buildBibtexKey = (paper: PaperItem, index: number) => {
  const firstAuthor = Array.isArray(paper.authors) && paper.authors[0]
    ? paper.authors[0].split(/\s+/).slice(-1)[0]
    : 'paper';
  const year = paper.year || 'nd';
  return `${firstAuthor}${year}_${index + 1}`.replace(/[^a-zA-Z0-9_:-]/g, '');
};

const buildSelectedBibtex = (items: PaperItem[]) => items.map((paper, index) => {
  const entryType = paper.arxiv_id ? 'misc' : 'article';
  const fields = [
    `  title = {${escapeBibtexValue(paper.title)}}`,
    paper.authors?.length ? `  author = {${escapeBibtexValue(paper.authors.join(' and '))}}` : '',
    paper.year ? `  year = {${paper.year}}` : '',
    paper.arxiv_id ? `  eprint = {${escapeBibtexValue(paper.arxiv_id)}}` : '',
    paper.arxiv_id ? '  archivePrefix = {arXiv}' : '',
    paper.doi ? `  doi = {${escapeBibtexValue(paper.doi)}}` : '',
    paper.source_url ? `  url = {${escapeBibtexValue(paper.source_url)}}` : '',
  ].filter(Boolean).join(',\n');
  return `@${entryType}{${buildBibtexKey(paper, index)},\n${fields}\n}`;
}).join('\n\n');

const buildSelectedMarkdown = (items: PaperItem[]) => [
  '# Selected Papers',
  '',
  `Exported at: ${new Date().toISOString()}`,
  '',
  ...items.flatMap((paper, index) => [
    `## ${index + 1}. ${paper.title}`,
    '',
    `- Authors: ${paper.authors?.length ? paper.authors.join(', ') : 'N/A'}`,
    `- Year: ${paper.year || 'N/A'}`,
    `- Source: ${paper.source || 'N/A'}`,
    `- arXiv: ${paper.arxiv_id || 'N/A'}`,
    `- DOI: ${paper.doi || 'N/A'}`,
    `- Read status: ${paper.read_status ? readingStatusMeta[paper.read_status].label : 'N/A'}`,
    '',
    paper.abstract_full || paper.abstract || 'No abstract available.',
    '',
  ]),
].join('\n');

const buildSelectedJson = (items: PaperItem[]) => JSON.stringify({
  exported_at: new Date().toISOString(),
  count: items.length,
  papers: items.map(paper => ({
    id: paper.id,
    title: paper.title,
    authors: paper.authors,
    year: paper.year,
    abstract: paper.abstract_full || paper.abstract,
    arxiv_id: paper.arxiv_id,
    doi: paper.doi,
    source: paper.source,
    citation_count: paper.citation_count,
    read_status: paper.read_status,
    source_url: paper.source_url,
    pdf_url: paper.pdf_url,
  })),
}, null, 2);

const selectedExportConfig: Record<SelectedExportFormat, { label: string; extension: string; mime: string; build: (items: PaperItem[]) => string }> = {
  bibtex: { label: 'BibTeX', extension: 'bib', mime: 'text/x-bibtex;charset=utf-8', build: buildSelectedBibtex },
  markdown: { label: 'Markdown', extension: 'md', mime: 'text/markdown;charset=utf-8', build: buildSelectedMarkdown },
  json: { label: 'JSON', extension: 'json', mime: 'application/json;charset=utf-8', build: buildSelectedJson },
};

const downloadTextFile = (content: string, filename: string, type = 'text/plain;charset=utf-8') => {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 0);
};

const PapersPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const initialSearchParams = new URLSearchParams(location.search);
  const initialSearchQuery = initialSearchParams.get('q')?.trim() || '';
  const initialSourceParam = initialSearchParams.get('source')?.trim() || '';
  const initialSource = initialSearchQuery
    ? (paperSearchSources.includes(initialSourceParam) ? initialSourceParam : 'scholarly')
    : 'local';
  const [papers, setPapers] = useState<PaperItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState(initialSearchQuery);
  const [source, setSource] = useState<string>(initialSource);
  const [resultStateFilter, setResultStateFilter] = useState<PaperResultStateFilter>('all');
  const [urlSearchRevision, setUrlSearchRevision] = useState(0);
  const lastAppliedUrlSearchRef = useRef(location.search);
  const [ingesting, setIngesting] = useState(false);
  const [ingestQuery, setIngestQuery] = useState('');
  const [sort, setSort] = useState<string>('created_desc');
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [reportModalOpen, setReportModalOpen] = useState(false);
  const [reportTitle, setReportTitle] = useState('组会报告');
  const [reportPrompt, setReportPrompt] = useState('');
  const [reportPreset, setReportPreset] = useState('default');
  const [reportLoading, setReportLoading] = useState(false);
  const [savedIds, setSavedIds] = useState<Set<string>>(new Set());
  const [deleteModal, setDeleteModal] = useState<{ open: boolean; paper: PaperItem | null }>({ open: false, paper: null });
  const [deleting, setDeleting] = useState(false);
  const [ingestingIds, setIngestingIds] = useState<Set<string>>(new Set());
  const [ingestedRemoteIds, setIngestedRemoteIds] = useState<Set<string>>(new Set());
  const [yearFrom, setYearFrom] = useState<number | undefined>();
  const [yearTo, setYearTo] = useState<number | undefined>();
  const [remotePage, setRemotePage] = useState(1);
  const [detailPaper, setDetailPaper] = useState<PaperItem | null>(null);
  const [digestUnreadCount, setDigestUnreadCount] = useState(0);
  const [readingStatus, setReadingStatus] = useState<'unread' | 'reading' | 'completed'>('unread');
  const [readingCounts, setReadingCounts] = useState<Record<'unread' | 'reading' | 'completed', number>>({ unread: 0, reading: 0, completed: 0 });
  const [updatingStatusIds, setUpdatingStatusIds] = useState<Set<string>>(new Set());
  const [collections, setCollections] = useState<PaperCollection[]>([]);
  const [selectedCollectionId, setSelectedCollectionId] = useState<string | undefined>();
  const [targetCollectionId, setTargetCollectionId] = useState<string | undefined>();
  const [creatingCollection, setCreatingCollection] = useState(false);
  const [addingCollection, setAddingCollection] = useState(false);
  const [deleteCollectionModal, setDeleteCollectionModal] = useState<{ open: boolean; collection: PaperCollection | null }>({ open: false, collection: null });
  const [deletingCollection, setDeletingCollection] = useState(false);
  const [collectionDiagnostics, setCollectionDiagnostics] = useState<CollectionDiagnostics | null>(null);
  const [collectionCoverage, setCollectionCoverage] = useState<CollectionCoverage | null>(null);
  const [recommendationKind, setRecommendationKind] = useState<RecommendationKind>('gap');
  const [recommendationLoading, setRecommendationLoading] = useState(false);
  const [recommendationPapers, setRecommendationPapers] = useState<PaperItem[]>([]);
  const [recommendationMeta, setRecommendationMeta] = useState<{ query: string; reason: string } | null>(null);
  const [kbHealth, setKbHealth] = useState<any>(null);
  const [processingAutomation, setProcessingAutomation] = useState<ProcessingAutomationHealth | null>(null);
  const [migrationHealth, setMigrationHealth] = useState<any>(null);
  const [kbRecommendations, setKbRecommendations] = useState<any[]>([]);
  const [kbLoading, setKbLoading] = useState(false);
  const [kbAction, setKbAction] = useState<string | null>(null);
  const [activeMaintenanceJob, setActiveMaintenanceJob] = useState<MaintenanceJobStatus | null>(null);
  const [processingStatuses, setProcessingStatuses] = useState<ProcessingStatusItem[]>([]);
  const [processingLoading, setProcessingLoading] = useState(false);
  const [processingStatusFilter, setProcessingStatusFilter] = useState<'all' | 'ready' | 'needs_processing'>('needs_processing');
  const [kbQuery, setKbQuery] = useState('');
  const [kbDiagnostics, setKbDiagnostics] = useState<any>(null);
  const [kbDiagTab, setKbDiagTab] = useState<DiagnosticTab>('hybrid');
  const [kbDiagLoading, setKbDiagLoading] = useState(false);
  const [showCoverage, setShowCoverage] = useState(false);
  const [pageActionError, setPageActionError] = useState<{ title: string; detail: ApiErrorDetails } | null>(null);
  const [filterImporter, setFilterImporter] = useState<string | undefined>();
  const [filterLocalSource, setFilterLocalSource] = useState<string | undefined>();
  const [filterFullText, setFilterFullText] = useState<'all' | 'true' | 'false'>('all');
  const [filterEmbedding, setFilterEmbedding] = useState<'all' | 'true' | 'false'>('all');
  const [filterReadStatus, setFilterReadStatus] = useState<'all' | ReadingStatus>('all');
  const [filterImportance, setFilterImportance] = useState<'all' | PaperImportanceLabel>('all');
  const isAuthenticated = !!localStorage.getItem('access_token');
  const isAdmin = useAuthStore((state) => state.user?.role === 'admin');
  const isRemoteSource = remoteSearchSources.includes(source);
  const remoteGuidance = isRemoteSource ? providerGuidance[source] : null;
  const showKnowledgeFilters = !isRemoteSource && !['collection', 'saved', 'reading', 'maintenance'].includes(source);
  const yearOptions = Array.from({ length: new Date().getFullYear() - 1899 }, (_, index) => {
    const year = new Date().getFullYear() - index;
    return { value: year, label: `${year}` };
  });

  const updateSource = useCallback((nextSource: string) => {
    setSource(nextSource);
    setResultStateFilter('all');
  }, []);

  const showPageError = useCallback((title: string, error: unknown, fallback = title) => {
    const detail = getApiErrorDetails(error, { fallback });
    setPageActionError({ title, detail });
    message.warning(detail.message);
  }, []);

  const fetchReadingCounts = useCallback(async () => {
    if (!isAuthenticated) return;
    try {
      const response = await api.get('/papers/collection/reading-status-counts');
      setReadingCounts({
        unread: response.data.unread || 0,
        reading: response.data.reading || 0,
        completed: response.data.completed || 0,
      });
    } catch {
      // Counts are helpful but not critical to searching papers.
    }
  }, [isAuthenticated]);

  const fetchCollections = useCallback(async () => {
    if (!isAuthenticated) return;
    try {
      const response = await api.get('/folders/');
      setCollections(response.data || []);
      const first = response.data?.[0]?.id;
      setTargetCollectionId(prev => prev || first);
    } catch {
      // Collection metadata is optional for the normal paper search flow.
    }
  }, [isAuthenticated]);

  useEffect(() => {
    if (location.search === lastAppliedUrlSearchRef.current) return;
    lastAppliedUrlSearchRef.current = location.search;
    const params = new URLSearchParams(location.search);
    const queryFromUrl = params.get('q')?.trim();
    if (!queryFromUrl) {
      setSearchQuery('');
      setSource('local');
      setResultStateFilter('all');
      setRemotePage(1);
      setUrlSearchRevision(value => value + 1);
      return;
    }

    const sourceFromUrl = params.get('source')?.trim();
    const nextSource = sourceFromUrl && paperSearchSources.includes(sourceFromUrl)
      ? sourceFromUrl
      : 'scholarly';
    setSearchQuery(queryFromUrl);
    setSource(nextSource);
    setResultStateFilter('all');
    setRemotePage(1);
    setUrlSearchRevision(value => value + 1);
  }, [location.search]);

  const handleSearch = useCallback(async (requestedRemotePage = 1) => {
    if (yearFrom && yearTo && yearFrom > yearTo) {
      message.warning('起始年份不能晚于截止年份');
      return;
    }
    if (source === 'maintenance') {
      setPapers([]);
      return;
    }
    const requestedPage = isRemoteSource ? requestedRemotePage : 1;
    setLoading(true);
    try {
      if (source === 'collection') {
        if (!selectedCollectionId) {
          setPapers([]);
          return;
        }
        const r = await api.get(`/folders/${selectedCollectionId}/papers`);
        setPapers(r.data.map((p: any) => ({ ...p, id: p.id })));
      } else if (source === 'saved' || source === 'reading') {
        const ep = source === 'saved' ? '/papers/collection/saved' : '/papers/collection/reading-list';
        const r = await api.get(ep, { params: source === 'reading' ? { status: readingStatus } : undefined });
        setPapers(r.data.map((p: any) => ({ ...p, id: p.id })));
      } else {
        const searchSource = source === 'mine' ? 'local' : source;
        const owner = source === 'mine' ? 'mine' : undefined;
        const r = await api.get('/papers/search', {
          params: {
            q: searchQuery,
            source: searchSource,
            owner,
            sort,
            page: requestedPage,
            page_size: 30,
            year_from: yearFrom,
            year_to: yearTo,
            importer: filterImporter,
            local_source: filterLocalSource,
            has_full_text: filterFullText === 'all' ? undefined : filterFullText,
            has_embedding: filterEmbedding === 'all' ? undefined : filterEmbedding,
            read_status: filterReadStatus === 'all' ? undefined : filterReadStatus,
            importance_label: filterImportance === 'all' ? undefined : filterImportance,
          },
        });
        setPapers(r.data.items);
        setRemotePage(requestedPage);
      }
      setPageActionError(null);
    } catch (e: any) { setPapers([]); showPageError('搜索失败', e, '搜索失败'); } finally { setLoading(false); }
  }, [filterEmbedding, filterFullText, filterImportance, filterImporter, filterLocalSource, filterReadStatus, isRemoteSource, readingStatus, searchQuery, selectedCollectionId, showPageError, source, sort, yearFrom, yearTo]);

  useEffect(() => { handleSearch(1); }, [source, sort, readingStatus, selectedCollectionId, urlSearchRevision, filterImporter, filterLocalSource, filterFullText, filterEmbedding, filterReadStatus, filterImportance]);

  useEffect(() => { fetchReadingCounts(); }, [fetchReadingCounts, source]);

  useEffect(() => { fetchCollections(); }, [fetchCollections]);

  useEffect(() => {
    if (source === 'collection' && !selectedCollectionId && collections.length > 0) {
      setSelectedCollectionId(collections[0].id);
    }
  }, [collections, selectedCollectionId, source]);

  useEffect(() => {
    if (!selectedCollectionId) {
      setCollectionDiagnostics(null);
      setCollectionCoverage(null);
      setRecommendationPapers([]);
      setRecommendationMeta(null);
      return;
    }
    setRecommendationPapers([]);
    setRecommendationMeta(null);
    api.get(`/folders/${selectedCollectionId}/diagnostics`)
      .then(response => setCollectionDiagnostics(response.data))
      .catch(() => {
        setCollectionDiagnostics(collections.find(item => item.id === selectedCollectionId)?.diagnostics || null);
      });
    api.get(`/folders/${selectedCollectionId}/coverage`)
      .then(response => setCollectionCoverage(response.data))
      .catch(() => setCollectionCoverage(null));
  }, [collections, selectedCollectionId]);

  useEffect(() => {
    if (!isAuthenticated) return;
    const fetchDigestUnread = () => {
      api.get('/notifications/digests/unread-count')
        .then(response => setDigestUnreadCount(response.data.unread_count || 0))
        .catch(() => {});
    };
    fetchDigestUnread();
    window.addEventListener('notifications:refresh', fetchDigestUnread);
    return () => window.removeEventListener('notifications:refresh', fetchDigestUnread);
  }, [isAuthenticated]);

  const handleReport = async (format: 'json' | 'docx') => {
    if (selectedIds.size === 0) { message.warning('请先选择论文'); return; }
    setReportLoading(true);
    try {
      if (format === 'docx') {
        const r = await api.post('/writing/group-report', {
          paper_ids: Array.from(selectedIds),
          title: reportTitle,
          custom_prompt: reportPrompt.trim() || undefined,
          report_preset: reportPreset,
        }, { responseType: 'blob', timeout: 120000 });
        const url = URL.createObjectURL(new Blob([r.data])); const a = document.createElement('a');
        a.href = url; a.download = `${reportTitle}_${new Date().toISOString().slice(0, 10)}.docx`; a.click();
        setPageActionError(null);
        message.success('报告已下载');
      }
    } catch (error) { showPageError('组会报告生成失败', error, '组会报告生成失败'); } finally { setReportLoading(false); setReportModalOpen(false); }
  };

  const handleIngestOne = useCallback(async (e: React.MouseEvent, paper: PaperItem, collectionOverrideId?: string) => {
    e.stopPropagation();
    if (!paper.remote_id) return;
    const remoteKey = `${paper.source}:${paper.remote_id}`;
    const collectionId = collectionOverrideId || targetCollectionId;
    setIngestingIds(prev => new Set(prev).add(remoteKey));
    try {
      const response = await api.post('/papers/ingest-personal', {
        source: paper.source,
        remote_id: paper.remote_id,
        remote_ingest_token: paper.remote_ingest_token,
        auto_download: false,
      });
      const localPaperId = response.data.paper_ids?.[0];
      if (collectionId && localPaperId) {
        await api.post(`/folders/${collectionId}/papers`, { paper_ids: [localPaperId] });
        await fetchCollections();
        if (collectionId === selectedCollectionId) {
          const [diagnostics, coverage] = await Promise.all([
            api.get(`/folders/${collectionId}/diagnostics`),
            api.get(`/folders/${collectionId}/coverage`),
          ]);
          setCollectionDiagnostics(diagnostics.data);
          setCollectionCoverage(coverage.data);
          if (source === 'collection') handleSearch();
        }
      }
      setIngestedRemoteIds(prev => new Set(prev).add(remoteKey));
      setPageActionError(null);
      message.success(collectionId ? '已入库并加入目标分类' : '已加入你的论文库');
    } catch (e: any) {
      showPageError('加入论文库失败', e, '加入论文库失败');
    } finally {
      setIngestingIds(prev => { const n = new Set(prev); n.delete(remoteKey); return n; });
    }
  }, [fetchCollections, handleSearch, selectedCollectionId, showPageError, source, targetCollectionId]);

  const handleIngest = useCallback(async () => {
    if (!ingestQuery.trim()) { message.warning('请输入搜索关键词或 arXiv ID'); return; }
    setIngesting(true);
    try {
      const isId = /^\d{4}\.\d{4,5}(v\d+)?$/.test(ingestQuery.trim());
      const r = await api.post('/papers/ingest', isId ? { arxiv_ids: [ingestQuery.trim()], auto_download: true } : { search_query: ingestQuery.trim(), max_results: 10, auto_download: true });
      setPageActionError(null);
      message.success(`入库完成: ${r.data.success} 新增, ${r.data.skipped} 已存在${r.data.error > 0 ? `, ${r.data.error} 失败` : ''}`);
      if (r.data.success > 0) handleSearch();
    } catch (error) { showPageError('入库失败', error, '入库失败'); } finally { setIngesting(false); }
  }, [ingestQuery, handleSearch, showPageError]);

  const handleViewDetail = useCallback(async (paper: PaperItem) => {
    if (!paper.id) { message.info('来自远程搜索，请先入库后查看详情'); return; }
    navigate(`/papers/${paper.id}`);
  }, [navigate]);

  const handleOpenAbstract = useCallback((e: React.MouseEvent, paper: PaperItem) => {
    e.stopPropagation();
    setDetailPaper(paper);
  }, []);

  const handleSave = useCallback(async (e: React.MouseEvent, paper: PaperItem) => {
    e.stopPropagation(); if (!paper.id || !isAuthenticated) { message.warning('请先登录'); return; }
    const isSaved = savedIds.has(paper.id);
    try {
      if (isSaved) { await api.delete(`/papers/${paper.id}/save`); setSavedIds(prev => { const n = new Set(prev); n.delete(paper.id); return n; }); }
      else { await api.post(`/papers/${paper.id}/save`); setSavedIds(prev => new Set(prev).add(paper.id)); }
      setPageActionError(null);
    } catch (error) { showPageError(isSaved ? '取消收藏失败' : '收藏失败', error, isSaved ? '取消收藏失败' : '收藏失败'); }
  }, [savedIds, isAuthenticated, showPageError]);

  const handleImportanceChange = useCallback(async (
    e: React.MouseEvent,
    paper: PaperItem,
    label: PaperImportanceLabel | null,
  ) => {
    e.stopPropagation();
    if (!paper.id || !isAuthenticated) {
      message.warning('请先登录');
      return;
    }
    try {
      const response = await api.put(`/papers/${paper.id}/importance`, { label });
      setPapers(prev => prev.map(item => item.id === paper.id ? {
        ...item,
        importance_label: response.data.importance_label,
        importance_note: response.data.importance_note,
      } : item));
      setPageActionError(null);
      message.success(label ? `已标记为${paperImportanceMeta[label].label}` : '已清除共享标记');
    } catch (error) {
      showPageError('共享标记更新失败', error, '共享标记更新失败');
    }
  }, [isAuthenticated, showPageError]);

  const handleCreateCollection = useCallback(async () => {
    if (!isAuthenticated) {
      message.warning('请先登录');
      return;
    }
    const name = window.prompt('请输入分类名称，例如：Video Grounding 核心论文');
    if (!name?.trim()) return;
    setCreatingCollection(true);
    try {
      const response = await api.post('/folders/', { name: name.trim() });
      setPageActionError(null);
      message.success('分类已创建');
      await fetchCollections();
      updateSource('collection');
      setSelectedCollectionId(response.data.id);
      setTargetCollectionId(response.data.id);
    } catch (e: any) {
      showPageError('创建分类失败', e, '创建分类失败');
    } finally {
      setCreatingCollection(false);
    }
  }, [fetchCollections, isAuthenticated, showPageError, updateSource]);

  const handleAddSelectedToCollection = useCallback(async () => {
    if (!targetCollectionId) {
      message.warning('请先选择或创建一个分类');
      return;
    }
    if (selectedIds.size === 0) {
      message.warning('请先选择论文');
      return;
    }
    setAddingCollection(true);
    try {
      const response = await api.post(`/folders/${targetCollectionId}/papers`, { paper_ids: Array.from(selectedIds) });
      setPageActionError(null);
      message.success(`已加入分类：新增 ${response.data.added || 0} 篇，跳过 ${response.data.skipped || 0} 篇`);
      setSelectedIds(new Set());
      await fetchCollections();
      if (source === 'collection' && selectedCollectionId === targetCollectionId) handleSearch();
    } catch (e: any) {
      showPageError('加入分类失败', e, '加入分类失败');
    } finally {
      setAddingCollection(false);
    }
  }, [fetchCollections, handleSearch, selectedCollectionId, selectedIds, showPageError, source, targetCollectionId]);

  const handleExportSelected = useCallback((format: SelectedExportFormat) => {
    if (selectedIds.size === 0) {
      message.warning('请先选择论文');
      return;
    }
    const loadedSelectedPapers = papers.filter(paper => paper.id && selectedIds.has(paper.id));
    if (loadedSelectedPapers.length === 0) {
      message.warning('当前列表中没有可导出的已选论文，请调整视图或清空选择后重试');
      return;
    }
    const config = selectedExportConfig[format];
    const today = new Date().toISOString().slice(0, 10);
    downloadTextFile(
      config.build(loadedSelectedPapers),
      `selected-papers-${today}.${config.extension}`,
      config.mime,
    );
    setPageActionError(null);
    const missingCount = selectedIds.size - loadedSelectedPapers.length;
    message.success(`${config.label} 已导出 ${loadedSelectedPapers.length} 篇${missingCount > 0 ? `，${missingCount} 篇不在当前列表` : ''}`);
  }, [papers, selectedIds]);

  const handleBulkReadStatus = useCallback(async (status: ReadingStatus) => {
    if (!isAuthenticated) {
      message.warning('请先登录');
      return;
    }
    if (selectedIds.size === 0) {
      message.warning('请先选择论文');
      return;
    }
    const loadedSelectedPapers = papers.filter(paper => paper.id && selectedIds.has(paper.id));
    if (loadedSelectedPapers.length === 0) {
      message.warning('当前列表中没有可更新的已选论文，请调整视图或清空选择后重试');
      return;
    }
    const targetIds = loadedSelectedPapers.map(paper => paper.id);
    setUpdatingStatusIds(prev => new Set([...prev, ...targetIds]));
    try {
      const results = await Promise.allSettled(
        loadedSelectedPapers.map(paper => api.put(`/papers/${paper.id}/read-status`, { status })),
      );
      const successfulIds = new Set<string>();
      results.forEach((result, index) => {
        if (result.status === 'fulfilled') successfulIds.add(loadedSelectedPapers[index].id);
      });
      const successCount = successfulIds.size;
      const failedCount = loadedSelectedPapers.length - successCount;
      if (successCount > 0) {
        setSavedIds(prev => new Set([...prev, ...successfulIds]));
        setPapers(prev => prev
          .map(item => successfulIds.has(item.id) ? { ...item, read_status: status } : item)
          .filter(item => source !== 'reading' || !successfulIds.has(item.id) || status === readingStatus));
        await fetchReadingCounts();
        setPageActionError(null);
      }
      const missingCount = selectedIds.size - loadedSelectedPapers.length;
      if (failedCount > 0 || missingCount > 0) {
        message.warning(`阅读状态更新完成：成功 ${successCount} 篇，失败 ${failedCount} 篇${missingCount > 0 ? `，${missingCount} 篇不在当前列表` : ''}`);
      } else {
        message.success(`已将 ${successCount} 篇标记为${readingStatusMeta[status].label}`);
      }
    } catch (error) {
      showPageError('批量阅读状态更新失败', error, '批量阅读状态更新失败');
    } finally {
      setUpdatingStatusIds(prev => {
        const next = new Set(prev);
        targetIds.forEach(id => next.delete(id));
        return next;
      });
    }
  }, [fetchReadingCounts, isAuthenticated, papers, readingStatus, selectedIds, showPageError, source]);

  const handleBatchTagSelected = useCallback(async () => {
    if (selectedIds.size === 0) {
      message.warning('请先选择论文');
      return;
    }
    const tagInput = window.prompt('输入标签，多个标签用英文逗号分隔');
    const tags = tagInput?.split(',').map(tag => tag.trim()).filter(Boolean) || [];
    if (tags.length === 0) return;
    try {
      await api.post('/papers/batch-tag', { paper_ids: Array.from(selectedIds), tags });
      setPageActionError(null);
      message.success(`已添加 ${tags.length} 个标签`);
      setSelectedIds(new Set());
      handleSearch();
    } catch (error) {
      showPageError('批量标签失败', error, '批量标签失败');
    }
  }, [handleSearch, selectedIds, showPageError]);

  const handleDeleteCollectionClick = useCallback(() => {
    const collection = collections.find(item => item.id === selectedCollectionId) || null;
    if (!collection) {
      message.warning('请先选择一个分类');
      return;
    }
    setDeleteCollectionModal({ open: true, collection });
  }, [collections, selectedCollectionId]);

  const confirmDeleteCollection = useCallback(async () => {
    const collection = deleteCollectionModal.collection;
    if (!collection) return;
    setDeletingCollection(true);
    try {
      await api.delete(`/folders/${collection.id}`);
      const remainingCollections = collections.filter(item => item.id !== collection.id);
      const nextCollectionId = remainingCollections[0]?.id;
      setCollections(remainingCollections);
      setSelectedCollectionId(nextCollectionId);
      setTargetCollectionId(prev => prev === collection.id ? nextCollectionId : prev);
      setPapers([]);
      setCollectionDiagnostics(null);
      setCollectionCoverage(null);
      setRecommendationPapers([]);
      setRecommendationMeta(null);
      setDeleteCollectionModal({ open: false, collection: null });
      setPageActionError(null);
      message.success('分类已删除，论文仍保留在论文库中');
    } catch (e: any) {
      showPageError('删除分类失败', e, '删除分类失败');
    } finally {
      setDeletingCollection(false);
    }
  }, [collections, deleteCollectionModal.collection, showPageError]);

  const handleFetchRecommendations = useCallback(async (kind: RecommendationKind, query?: string) => {
    if (!selectedCollectionId) {
      message.warning('请先选择一个分类');
      return;
    }
    setRecommendationKind(kind);
    setRecommendationLoading(true);
    try {
      const response = await api.get(`/folders/${selectedCollectionId}/recommendations`, {
        params: { kind, query, limit: 6 },
      });
      setRecommendationPapers(response.data.items || []);
      setRecommendationMeta({ query: response.data.query, reason: response.data.reason });
      setPageActionError(null);
      if ((response.data.items || []).length === 0) {
        message.info('没有找到新的补充论文，可以换一个推荐类型或调整分类关键词');
      }
    } catch (e: any) {
      showPageError('推荐论文检索失败', e, '推荐论文检索失败');
    } finally {
      setRecommendationLoading(false);
    }
  }, [selectedCollectionId, showPageError]);

  const fetchMaintenanceCenter = useCallback(async () => {
    if (!isAdmin) return;
    setKbLoading(true);
    try {
      const [healthRes, automationRes, recommendationsRes, processingRes, migrationRes] = await Promise.all([
        api.get('/papers/maintenance/health'),
        api.get('/papers/processing-automation'),
        api.get('/papers/maintenance/recommendations'),
        api.get('/papers/processing-status', { params: { status: processingStatusFilter, limit: 30 } }),
        api.get('/health/db').catch(error => ({ data: error.response?.data || { status: 'error', detail: '迁移状态读取失败' } })),
      ]);
      setKbHealth(healthRes.data);
      setProcessingAutomation(automationRes.data);
      setKbRecommendations(recommendationsRes.data || []);
      setProcessingStatuses(processingRes.data?.items || []);
      setMigrationHealth(migrationRes.data);
      setPageActionError(null);
    } catch (e: any) {
      showPageError('知识库维护状态读取失败', e, '知识库维护状态读取失败');
    } finally {
      setKbLoading(false);
    }
  }, [isAdmin, processingStatusFilter, showPageError]);

  useEffect(() => {
    if (source === 'maintenance') fetchMaintenanceCenter();
  }, [fetchMaintenanceCenter, source]);

  const runKbAction = useCallback(async (action: string, endpoint: string) => {
    setKbAction(action);
    try {
      const response = await api.post(endpoint, undefined, { timeout: 300000 });
      setPageActionError(null);
      if (response.data?.job_id && response.data?.job) {
        setActiveMaintenanceJob(response.data.job);
        message.success('维护任务已进入后台，可在处理诊断查看进度');
      } else {
        message.success(`维护完成：成功 ${response.data.success || 0}，失败 ${response.data.failed || 0}，跳过 ${response.data.skipped || 0}`);
        await fetchMaintenanceCenter();
      }
    } catch (e: any) {
      showPageError('维护操作失败', e, '维护操作失败');
    } finally {
      setKbAction(null);
    }
  }, [fetchMaintenanceCenter, showPageError]);

  const runProcessingAction = useCallback(async (item: ProcessingStatusItem, action: { key: string; label: string; endpoint: string }) => {
    setProcessingLoading(true);
    try {
      const response = await api.post(action.endpoint, undefined, action.key === 'visual_evidence' ? { timeout: 30000 } : undefined);
      setPageActionError(null);
      if (action.key === 'visual_evidence' && response.data?.job_id && response.data?.job) {
        setActiveMaintenanceJob(response.data.job);
        message.success(`${action.label} 已进入后台：${item.title.slice(0, 28)}`);
      } else {
        message.success(`${action.label} 已执行：${item.title.slice(0, 28)}`);
        await fetchMaintenanceCenter();
      }
    } catch (e: any) {
      showPageError(`${action.label}失败`, e, `${action.label}失败`);
    } finally {
      setProcessingLoading(false);
    }
  }, [fetchMaintenanceCenter, showPageError]);

  const formatMaintenanceJobCompletion = useCallback((job: MaintenanceJobStatus) => {
    const total = (job.success || 0) + (job.failed || 0) + (job.skipped || 0);
    if (job.message && total === 0) return job.message;
    if (job.message && job.kind === 'visual_evidence_single_paper') return job.message;
    return `维护任务完成：成功 ${job.success || 0}，失败 ${job.failed || 0}，跳过 ${job.skipped || 0}`;
  }, []);
  const isVisualEvidenceJob = useCallback((job?: MaintenanceJobStatus | null) => Boolean(job && String(job.kind || '').includes('visual_evidence')), []);

  useEffect(() => {
    const jobId = activeMaintenanceJob?.id;
    if (!jobId || !['queued', 'running', 'unknown'].includes(activeMaintenanceJob.state)) return;
    let cancelled = false;
    const poll = async () => {
      try {
        const response = await api.get(`/papers/maintenance/jobs/${jobId}`);
        if (cancelled) return;
        const nextJob = response.data as MaintenanceJobStatus;
        setActiveMaintenanceJob(nextJob);
        if (['success', 'failed', 'cancelled'].includes(nextJob.state)) {
          await fetchMaintenanceCenter();
          if (nextJob.state === 'success') {
            message.success(formatMaintenanceJobCompletion(nextJob));
          } else {
            message.warning(nextJob.message || '维护任务未正常完成');
          }
        }
      } catch (e: any) {
        if (!cancelled) showPageError('维护任务状态读取失败', e, '维护任务状态读取失败');
      }
    };
    const timer = window.setInterval(poll, 3000);
    poll();
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [activeMaintenanceJob?.id, activeMaintenanceJob?.state, fetchMaintenanceCenter, formatMaintenanceJobCompletion, showPageError]);

  const runKbDiagnostics = useCallback(async () => {
    if (!kbQuery.trim()) {
      message.warning('请输入要诊断的检索词');
      return;
    }
    setKbDiagLoading(true);
    try {
      const response = await api.get('/papers/maintenance/search-diagnostics', { params: { q: kbQuery.trim(), top_k: 5 } });
      setKbDiagnostics(response.data);
      setKbDiagTab('hybrid');
      setPageActionError(null);
    } catch (e: any) {
      showPageError('检索诊断失败', e, '检索诊断失败');
    } finally {
      setKbDiagLoading(false);
    }
  }, [kbQuery, showPageError]);

  const handleRemoveFromCollection = useCallback(async (e: React.MouseEvent, paper: PaperItem) => {
    e.stopPropagation();
    if (!selectedCollectionId || !paper.id) return;
    try {
      await api.delete(`/folders/${selectedCollectionId}/papers/${paper.id}`);
      setPageActionError(null);
      message.success('已从分类移除');
      setPapers(prev => prev.filter(item => item.id !== paper.id));
      await fetchCollections();
    } catch (err: any) {
      showPageError('移出分类失败', err, '移出分类失败');
    }
  }, [fetchCollections, selectedCollectionId, showPageError]);

  const handleDeleteClick = useCallback((e: React.MouseEvent, paper: PaperItem) => { e.stopPropagation(); if (!paper.id || !isAuthenticated) { message.warning('请先登录'); return; } setDeleteModal({ open: true, paper }); }, [isAuthenticated]);
  const handleReadStatusChange = useCallback(async (e: React.MouseEvent, paper: PaperItem, status: 'unread' | 'reading' | 'completed') => {
    e.stopPropagation();
    if (!paper.id || !isAuthenticated) { message.warning('请先登录'); return; }
    setUpdatingStatusIds(prev => new Set(prev).add(paper.id));
    try {
      await api.put(`/papers/${paper.id}/read-status`, { status });
      setSavedIds(prev => new Set(prev).add(paper.id));
      setPapers(prev => prev
        .map(item => item.id === paper.id ? { ...item, read_status: status } : item)
        .filter(item => source !== 'reading' || item.id !== paper.id || status === readingStatus));
      await fetchReadingCounts();
      setPageActionError(null);
      message.success(`已标记为${readingStatusMeta[status].label}`);
    } catch (error) {
      showPageError('阅读状态更新失败', error, '阅读状态更新失败');
    } finally {
      setUpdatingStatusIds(prev => { const n = new Set(prev); n.delete(paper.id); return n; });
    }
  }, [fetchReadingCounts, isAuthenticated, readingStatus, showPageError, source]);

  const renderReadingActions = (paper: PaperItem) => {
    if (!isAuthenticated || !paper.id || source !== 'reading') return null;
    const updating = updatingStatusIds.has(paper.id);
    return (
      <Space size={4} wrap style={{ marginTop: 6 }}>
        {readingStatus !== 'reading' && (
          <Button size="small" icon={<PlayCircleOutlined />} loading={updating} onClick={e => handleReadStatusChange(e, paper, 'reading')} style={{ borderRadius: 8 }}>
            开始阅读
          </Button>
        )}
        {readingStatus !== 'completed' && (
          <Button size="small" icon={<CheckCircleOutlined />} loading={updating} onClick={e => handleReadStatusChange(e, paper, 'completed')} style={{ borderRadius: 8 }}>
            标记完成
          </Button>
        )}
        {readingStatus !== 'unread' && (
          <Button size="small" icon={<RollbackOutlined />} loading={updating} onClick={e => handleReadStatusChange(e, paper, 'unread')} style={{ borderRadius: 8 }}>
            重置待读
          </Button>
        )}
      </Space>
    );
  };

  const renderImportanceActions = (paper: PaperItem) => {
    if (!isAuthenticated || !paper.id) return null;
    if (paper.importance_label) {
      return (
        <Tooltip title={paper.importance_note || '所有用户可见的共享标记'}>
          <Button
            type="text"
            size="small"
            icon={<CloseOutlined />}
            onClick={e => handleImportanceChange(e, paper, null)}
          >
            清除
          </Button>
        </Tooltip>
      );
    }
    return (
      <Space size={2}>
        <Tooltip title="标记为所有人可见的重点论文">
          <Button type="text" size="small" icon={<ExclamationCircleOutlined />} onClick={e => handleImportanceChange(e, paper, 'important')} />
        </Tooltip>
        <Tooltip title="标记为所有人可见的有趣论文">
          <Button type="text" size="small" icon={<RocketOutlined />} onClick={e => handleImportanceChange(e, paper, 'interesting')} />
        </Tooltip>
      </Space>
    );
  };

  const confirmDelete = async (global: boolean) => {
    if (!deleteModal.paper) return; setDeleting(true);
    try { await api.delete(`/papers/${deleteModal.paper.id}${global ? '/global' : ''}`); setPageActionError(null); message.success(global ? '已从总库删除' : '已从收藏移除'); setPapers(prev => prev.filter(p => p.id !== deleteModal.paper!.id)); setSavedIds(prev => { const n = new Set(prev); n.delete(deleteModal.paper!.id!); return n; }); }
    catch (e: any) { showPageError('删除失败', e, '删除失败'); } finally { setDeleting(false); setDeleteModal({ open: false, paper: null }); }
  };

  const sc = (s: string) => ({ arxiv: '#b31b1b', semantic_scholar: '#1890ff', openalex: '#13a8a8', google_scholar: '#5f6368', manual: '#52c41a' }[s] || '#999');
  const sl = (s: string) => ({ arxiv: 'arXiv', semantic_scholar: 'Semantic Scholar', openalex: 'OpenAlex', google_scholar: 'Google Scholar', manual: '手动' }[s] || s);
  const topicStatusMeta = (status: CollectionCoverageTopic['status']) => ({
    covered: { color: 'green', label: '已覆盖' },
    thin: { color: 'orange', label: '偏薄' },
    missing: { color: 'red', label: '缺口' },
  }[status]);
  const recommendationColor = (severity: string) => ({ high: 'red', medium: 'orange', low: 'green' }[severity] || 'blue');
  const renderMaintenanceHits = (items: any[] = []) => (
    <List
      size="small"
      locale={{ emptyText: '暂无结果' }}
      dataSource={items}
      renderItem={item => (
        <List.Item>
          <List.Item.Meta
            title={<Space wrap><Text strong>{item.title}</Text>{item.score !== undefined && <Tag color="blue">score {Number(item.score).toFixed ? Number(item.score).toFixed(2) : item.score}</Tag>}</Space>}
            description={<Space size={6} wrap>
              <Tag color={item.has_full_text ? 'green' : 'default'}>{item.has_full_text ? '有全文' : '缺全文'}</Tag>
              <Tag color={item.has_embedding ? 'green' : 'default'}>{item.has_embedding ? '有向量' : '缺向量'}</Tag>
              {item.has_visual_evidence !== undefined && <Tag color={item.has_visual_evidence ? 'purple' : 'default'}>{item.has_visual_evidence ? '有视觉证据' : '缺视觉证据'}</Tag>}
              {item.match_sources?.map((sourceName: string) => <Tag key={sourceName}>{sourceName}</Tag>)}
            </Space>}
          />
        </List.Item>
      )}
    />
  );

  const resultStateCounts = paperResultStateCounts(papers, ingestedRemoteIds);
  const filteredPapers = papers.filter(paper => {
    if (resultStateFilter === 'all') return true;
    if (resultStateFilter === 'open_pdf') return !!paper.pdf_url;
    return paperResultState(paper, ingestedRemoteIds).key === resultStateFilter;
  });
  const selectedPapers = papers.filter(paper => paper.id && selectedIds.has(paper.id));
  const selectedCount = selectedIds.size;
  const stats = papers.length > 0 ? `共 ${papers.length} 篇论文` : '';
  const collectionOptions = collections.map(item => {
    const diagnostics = item.diagnostics;
    const suffix = diagnostics
      ? ` · 全文 ${Math.round((diagnostics.full_text_coverage || 0) * 100)}% / 向量 ${Math.round((diagnostics.embedding_coverage || 0) * 100)}%`
      : '';
    return { value: item.id, label: `${item.name}（${item.paper_count || 0}）${suffix}` };
  });
  const weakCollections = collections.filter(item => item.diagnostics && !item.diagnostics.ready_for_idea);
  const importerOptions = Array.from(new Set(['gst', ...papers.map(item => item.imported_by_username).filter(Boolean) as string[]]))
    .map(value => ({ value, label: value }));
  const localSourceOptions = ['arxiv', 'openalex', 'semantic_scholar', 'google_scholar', 'manual', 'bibtex_import', 'zotero_import']
    .map(value => ({ value, label: sl(value) }));
  const duplicateRiskMap = computeDuplicateRiskMap(papers);
  const tableQualityMeta = (quality?: string | null) => {
    if (quality === 'high') return { color: 'green', label: '表格高' };
    if (quality === 'medium') return { color: 'gold', label: '表格中' };
    if (quality === 'low') return { color: 'orange', label: '表格低' };
    return { color: 'default', label: '表格无' };
  };
  const processingLabelMeta = (state?: string) => {
    if (state === 'ready') return { color: 'green', suffix: '就绪' };
    if (state === 'running' || state === 'pending') return { color: 'processing', suffix: '处理中' };
    if (state === 'failed') return { color: 'red', suffix: '失败' };
    if (state === 'stale') return { color: 'gold', suffix: '待刷新' };
    return { color: 'default', suffix: '待处理' };
  };
  const renderProcessingLabels = (labels: ProcessingLabel[] = []) => (
    <>
      {labels.filter(label => label.key !== 'pdf').slice(0, 5).map(label => {
        const meta = processingLabelMeta(label.state);
        const text = `${label.label}${meta.suffix}`;
        return (
          <Tooltip key={label.key} title={label.detail || text}>
            <Tag color={meta.color} style={{ borderRadius: 6 }}>
              {text}
            </Tag>
          </Tooltip>
        );
      })}
    </>
  );
  const reportPresetOptions = [
    { value: 'default', label: '默认逐篇' },
    { value: 'compare', label: '横向对比' },
    { value: 'method_lineage', label: '方法脉络' },
    { value: 'reproduction', label: '实验复现' },
    { value: 'review', label: '审稿视角' },
  ];

  const maintenanceView = !isAdmin ? (
    <Card style={{ borderRadius: 16, border: '1px solid #f0f0f0' }}>
      <Alert
        type="info"
        showIcon
        message="知识库维护需要管理员权限"
        description="全文覆盖、向量补齐和 BM25 重建会影响全局检索质量，因此修复动作只对管理员开放。你仍然可以在分类视图查看自己分类的健康提示。"
      />
    </Card>
  ) : (
    <Spin spinning={kbLoading}>
      <Space direction="vertical" size={14} style={{ width: '100%' }}>
        <Card
          style={{ borderRadius: 16, border: '1px solid #efe7ff' }}
          title={<Space><DatabaseOutlined style={{ color: '#764ba2' }} /><Text strong>自动处理诊断</Text></Space>}
          extra={<Button size="small" icon={<RedoOutlined />} loading={kbLoading} onClick={fetchMaintenanceCenter}>刷新</Button>}
        >
          {migrationHealth && (
            <Alert
              type={migrationHealth.status === 'ok' ? 'success' : 'warning'}
              showIcon
              style={{ borderRadius: 10, marginBottom: 14 }}
              message={migrationHealth.status === 'ok' ? '数据库迁移版本正常' : '数据库迁移需要处理'}
              description={
                <Space direction="vertical" size={4}>
                  <Text type="secondary">当前版本：{migrationHealth.current_revision || '未记录'}；代码版本：{migrationHealth.head_revision || '未知'}</Text>
                  {migrationHealth.status !== 'ok' && <Text code>docker compose exec -T backend alembic upgrade head</Text>}
                </Space>
              }
            />
          )}
          <Alert
            type="info"
            showIcon
            style={{ borderRadius: 10, marginBottom: 14 }}
            message="论文入库后会在后台自动补齐全文、结构化解析、视觉证据/OCR、向量和关键词索引"
            description="这里保留为管理员诊断和兜底入口；日常使用只需要看论文卡片上的处理标签。"
          />
          {activeMaintenanceJob && (
            <Alert
              type={activeMaintenanceJob.state === 'failed' ? 'error' : activeMaintenanceJob.state === 'success' ? 'success' : 'info'}
              showIcon
              style={{ borderRadius: 10, marginBottom: 14 }}
              message={
                activeMaintenanceJob.state === 'success'
                  ? '维护任务已完成'
                  : activeMaintenanceJob.state === 'failed'
                    ? '维护任务失败'
                    : '维护任务正在后台执行'
              }
              description={(
                <Space direction="vertical" size={6} style={{ width: '100%' }}>
                  <Progress
                    percent={activeMaintenanceJob.progress_percent || 0}
                    status={activeMaintenanceJob.state === 'failed' ? 'exception' : activeMaintenanceJob.state === 'success' ? 'success' : 'active'}
                  />
                  <Text type="secondary">
                    已处理 {activeMaintenanceJob.processed || 0}/{activeMaintenanceJob.total || 0}，成功 {activeMaintenanceJob.success || 0}，失败 {activeMaintenanceJob.failed || 0}，跳过 {activeMaintenanceJob.skipped || 0}
                  </Text>
                  {activeMaintenanceJob.current_paper?.title && <Text type="secondary">当前论文：{activeMaintenanceJob.current_paper.title}</Text>}
                  {activeMaintenanceJob.message && <Text type="secondary">{activeMaintenanceJob.message}</Text>}
                  {!!activeMaintenanceJob.errors?.length && (
                    <Text type="secondary">最近错误：{activeMaintenanceJob.errors[0].title || activeMaintenanceJob.errors[0].paper_id || '任务'} - {activeMaintenanceJob.errors[0].reason || '未知错误'}</Text>
                  )}
                </Space>
              )}
              action={activeMaintenanceJob.state !== 'running' && activeMaintenanceJob.state !== 'queued' ? (
                <Button size="small" onClick={() => setActiveMaintenanceJob(null)}>关闭</Button>
              ) : undefined}
            />
          )}
          {kbHealth ? (
            <>
              {processingAutomation && (
                <Alert
                  type={processingAutomation.failed ? 'warning' : processingAutomation.pending ? 'info' : 'success'}
                  showIcon
                  style={{ borderRadius: 10, marginBottom: 12 }}
                  message={`后台自动处理：${processingAutomation.ready} 篇就绪，${processingAutomation.pending} 篇待处理`}
                  description={(
                    <Space size={6} wrap>
                      <Tag color="blue">每 {processingAutomation.cadence_minutes} 分钟巡检</Tag>
                      <Tag color="blue">每批最多 {processingAutomation.batch_limit} 篇</Tag>
                      {processingAutomation.labels.map(label => (
                        <Tag key={label.key} color={label.failed ? 'red' : label.pending ? 'orange' : 'green'}>
                          {label.label} {label.ready}/{label.ready + label.pending + label.failed}
                        </Tag>
                      ))}
                    </Space>
                  )}
                />
              )}
              <Row gutter={[12, 12]}>
                <Col xs={12} md={6}><Card size="small" style={{ borderRadius: 12 }}><Statistic title="论文总数" value={kbHealth.total_papers || 0} /></Card></Col>
                <Col xs={12} md={6}><Card size="small" style={{ borderRadius: 12 }}><Statistic title="全文覆盖" value={Math.round((kbHealth.full_text_coverage || 0) * 100)} suffix="%" /><Progress percent={Math.round((kbHealth.full_text_coverage || 0) * 100)} size="small" showInfo={false} /></Card></Col>
                <Col xs={12} md={6}><Card size="small" style={{ borderRadius: 12 }}><Statistic title="向量覆盖" value={Math.round((kbHealth.embedding_coverage || 0) * 100)} suffix="%" /><Progress percent={Math.round((kbHealth.embedding_coverage || 0) * 100)} size="small" showInfo={false} /></Card></Col>
                <Col xs={12} md={6}><Card size="small" style={{ borderRadius: 12 }}><Statistic title="视觉证据" value={Math.round((kbHealth.visual_evidence_coverage || 0) * 100)} suffix="%" /><Progress percent={Math.round((kbHealth.visual_evidence_coverage || 0) * 100)} size="small" showInfo={false} strokeColor="#722ed1" /></Card></Col>
              </Row>
              <Space wrap style={{ marginTop: 12 }}>
                <Tag color={kbHealth.bm25_index?.ready ? 'green' : 'orange'}>BM25：{kbHealth.bm25_index?.ready ? `已索引 ${kbHealth.bm25_index.indexed_papers} 篇` : '未构建'}</Tag>
                <Tag>缺全文 {kbHealth.missing_full_text || 0}</Tag>
                <Tag>缺向量 {kbHealth.missing_embeddings || 0}</Tag>
                <Tag color={(kbHealth.missing_visual_evidence || 0) ? 'purple' : 'green'}>待提取视觉证据 {kbHealth.missing_visual_evidence || 0}</Tag>
                {!!kbHealth.visual_evidence_failed && <Tag color="red">视觉失败 {kbHealth.visual_evidence_failed}</Tag>}
                {!!kbHealth.visual_missing_summary && <Tag color="orange">缺视觉摘要 {kbHealth.visual_missing_summary}</Tag>}
                {!!kbHealth.visual_missing_ocr && <Tag color="orange">缺表格 OCR {kbHealth.visual_missing_ocr}</Tag>}
                {!!kbHealth.low_confidence_visual_tables && <Tag color="gold">低置信视觉表格 {kbHealth.low_confidence_visual_tables}</Tag>}
                <Tag>arXiv 论文 {kbHealth.arxiv_papers || 0}</Tag>
              </Space>
              <Space wrap style={{ marginTop: 14 }}>
                <Button icon={<RedoOutlined />} loading={kbAction === 'bm25'} onClick={() => runKbAction('bm25', '/papers/maintenance/rebuild-bm25')}>兜底重建 BM25</Button>
                <Button loading={kbAction === 'embeddings'} onClick={() => runKbAction('embeddings', '/papers/maintenance/backfill-embeddings?limit=20')}>兜底补向量</Button>
                <Button loading={kbAction === 'fulltext'} onClick={() => runKbAction('fulltext', '/papers/maintenance/backfill-full-text?limit=5')}>兜底补全文</Button>
                <Button loading={kbAction === 'visual'} onClick={() => runKbAction('visual', '/papers/maintenance/backfill-visual-evidence?limit=5')}>兜底提取视觉证据</Button>
              </Space>
            </>
          ) : <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无维护状态" />}
        </Card>

        {kbRecommendations.length > 0 && (
          <Card title="自动处理异常建议" style={{ borderRadius: 16 }}>
            <Row gutter={[12, 12]}>
              {kbRecommendations.map((rec: any) => (
                <Col xs={24} md={8} key={rec.id}>
                  <Card size="small" style={{ borderRadius: 12, height: '100%' }}>
                    <Space direction="vertical" size={8} style={{ width: '100%' }}>
                      <Space wrap><Tag color={recommendationColor(rec.severity)}>{rec.severity}</Tag><Text strong>{rec.title}</Text></Space>
                      <Text type="secondary" style={{ fontSize: 12 }}>{rec.reason}</Text>
                      {!!rec.sample_papers?.length && <Space wrap>{rec.sample_papers.slice(0, 2).map((paper: any) => <Tag key={paper.id}>{paper.title?.slice(0, 24)}</Tag>)}</Space>}
                      <Button
                        size="small"
                        type="primary"
                        loading={kbAction === rec.id}
                        onClick={() => runKbAction(rec.id, rec.action_endpoint)}
                      >
                        {rec.action_label}
                      </Button>
                    </Space>
                  </Card>
                </Col>
              ))}
            </Row>
          </Card>
        )}

        <Card
          title={<Space><DatabaseOutlined /><Text strong>论文处理标签</Text><Tag color="orange">{processingStatuses.length}</Tag></Space>}
          extra={(
            <Segmented
              size="small"
              value={processingStatusFilter}
              onChange={value => setProcessingStatusFilter(String(value) as 'all' | 'ready' | 'needs_processing')}
              options={[
                { label: '待处理', value: 'needs_processing' },
                { label: '已就绪', value: 'ready' },
                { label: '全部', value: 'all' },
              ]}
            />
          )}
          style={{ borderRadius: 16 }}
        >
          {isVisualEvidenceJob(activeMaintenanceJob) && ['queued', 'running', 'unknown'].includes(activeMaintenanceJob?.state || '') && (
            <Alert
              type="info"
              showIcon
              style={{ borderRadius: 10, marginBottom: 12 }}
              message="视觉证据正在后台提取"
              description={(
                <Space direction="vertical" size={6} style={{ width: '100%' }}>
                  <Progress percent={activeMaintenanceJob?.progress_percent || 0} size="small" status="active" />
                  {activeMaintenanceJob?.current_paper?.title && <Text type="secondary">当前论文：{activeMaintenanceJob.current_paper.title}</Text>}
                  {activeMaintenanceJob?.message && <Text type="secondary">{activeMaintenanceJob.message}</Text>}
                  <Text type="secondary">已处理 {activeMaintenanceJob?.processed || 0}/{activeMaintenanceJob?.total || 0}</Text>
                </Space>
              )}
            />
          )}
          {processingStatuses.length === 0 ? (
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无符合条件的论文处理状态" />
          ) : (
            <List
              size="small"
              dataSource={processingStatuses}
              renderItem={item => (
                <List.Item
                  actions={isAdmin && item.status === 'failed' ? item.repair_actions.filter(action => ['full_text', 'structured_parse', 'visual_evidence', 'embedding'].includes(action.key)).slice(0, 2).map(action => (
                    <Button key={action.key} size="small" loading={processingLoading} onClick={() => runProcessingAction(item, action)}>
                      兜底{action.label}
                    </Button>
                  )) : []}
                >
                  <List.Item.Meta
                    title={<Space wrap><Text strong>{item.title}</Text>{item.year && <Tag>{item.year}</Tag>}<Tag color={item.status === 'ready' ? 'green' : item.status === 'failed' ? 'red' : item.status === 'processing' ? 'processing' : 'orange'}>{item.status === 'ready' ? '已就绪' : item.status === 'failed' ? '异常' : item.status === 'processing' ? '处理中' : '待处理'}</Tag></Space>}
                    description={<Space size={4} wrap>
                      {renderProcessingLabels(item.processing_labels)}
                      <Tooltip title={item.structured_parse_status?.last_error?.message || item.structured_parse_status?.parser || 'PDF 结构化解析状态'}>
                        <Tag color={item.structured_parse_status?.last_error ? 'red' : item.structured_parse_status?.ready ? 'green' : 'default'}>
                          结构化 {item.structured_parse_status?.last_error ? '失败' : item.structured_parse_status?.ready ? `已 ${item.structured_parse_status?.block_count || 0}` : '缺'}
                        </Tag>
                      </Tooltip>
                      {item.structured_parse_status?.ready && item.structured_parse_status?.table_count ? (() => {
                        const meta = tableQualityMeta(item.structured_parse_status?.table_quality?.quality);
                        const warnings = item.structured_parse_status?.table_quality?.warnings || [];
                        const flags = item.structured_parse_status?.table_quality?.flags || [];
                        return (
                          <>
                            <Tooltip title={[...warnings, ...flags].length ? [...warnings, ...flags].join('；') : `低质量表格 ${item.structured_parse_status?.table_quality?.low_quality_table_count || 0}/${item.structured_parse_status?.table_count || 0}`}>
                              <Tag color={meta.color}>{meta.label}</Tag>
                            </Tooltip>
                          </>
                        );
                      })() : null}
                      <Tooltip title={item.visual_evidence_status?.last_error?.message || `视觉 ${item.visual_evidence_status?.visual_count || 0}，表格 ${item.visual_evidence_status?.table_count || 0}，资产 ${item.visual_evidence_status?.asset_count || 0}`}>
                        <Tag color={item.visual_evidence_status?.failed ? 'red' : item.visual_evidence_status?.ready ? 'purple' : 'default'}>
                          视觉证据 {item.visual_evidence_status?.failed ? '失败' : item.visual_evidence_status?.ready ? `已 ${item.visual_evidence_status?.item_count || 0}` : '缺'}
                        </Tag>
                      </Tooltip>
                      {!!item.visual_evidence_status?.missing_summary_count && <Tag color="orange">缺摘要 {item.visual_evidence_status.missing_summary_count}</Tag>}
                      {!!item.visual_evidence_status?.missing_ocr_count && <Tag color="orange">缺 OCR {item.visual_evidence_status.missing_ocr_count}</Tag>}
                      {!!item.visual_evidence_status?.low_confidence_table_count && <Tag color="gold">低置信表格 {item.visual_evidence_status.low_confidence_table_count}</Tag>}
                      {item.imported_by_username && <Tag color="purple">导入：{item.imported_by_username}</Tag>}
                    </Space>}
                  />
                </List.Item>
              )}
            />
          )}
        </Card>

        <Card title="分类健康度" style={{ borderRadius: 16 }}>
          {collections.length === 0 ? <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无自定义分类" /> : (
            <Row gutter={[12, 12]}>
              {collections.map(collection => {
                const diagnostics = collection.diagnostics;
                return (
                  <Col xs={24} md={12} key={collection.id}>
                    <Card size="small" style={{ borderRadius: 12, borderColor: diagnostics?.ready_for_idea ? '#b7eb8f' : '#ffe58f' }}>
                      <Space direction="vertical" size={8} style={{ width: '100%' }}>
                        <Space wrap><Text strong>{collection.name}</Text><Tag color={diagnostics?.ready_for_idea ? 'green' : 'orange'}>{diagnostics?.ready_for_idea ? '可用于 Idea' : '需要维护'}</Tag><Tag>论文 {collection.paper_count || diagnostics?.paper_count || 0}</Tag></Space>
                        {diagnostics ? (
                          <>
                            <Space wrap>
                              <Text type="secondary">全文 {Math.round((diagnostics.full_text_coverage || 0) * 100)}%</Text>
                              <Progress style={{ width: 120 }} size="small" percent={Math.round((diagnostics.full_text_coverage || 0) * 100)} showInfo={false} />
                              <Text type="secondary">向量 {Math.round((diagnostics.embedding_coverage || 0) * 100)}%</Text>
                              <Progress style={{ width: 120 }} size="small" percent={Math.round((diagnostics.embedding_coverage || 0) * 100)} showInfo={false} />
                            </Space>
                            {!!diagnostics.warnings?.length && <Text type="secondary" style={{ fontSize: 12 }}>{diagnostics.warnings.join('；')}</Text>}
                          </>
                        ) : <Text type="secondary">暂无诊断信息</Text>}
                      </Space>
                    </Card>
                  </Col>
                );
              })}
            </Row>
          )}
          {weakCollections.length > 0 && <Alert type="warning" showIcon style={{ marginTop: 12, borderRadius: 10 }} message={`${weakCollections.length} 个分类不适合直接用于 Idea 生成`} description={weakCollections.map(item => item.name).join('、')} />}
        </Card>

        <Card title="检索诊断" style={{ borderRadius: 16 }}>
          <Space.Compact style={{ width: '100%' }}>
            <Input value={kbQuery} onChange={e => setKbQuery(e.target.value)} onPressEnter={runKbDiagnostics} placeholder="例如：video grounding 或 introduction token pruning" />
            <Button type="primary" icon={<SearchOutlined />} loading={kbDiagLoading} onClick={runKbDiagnostics}>诊断</Button>
          </Space.Compact>
          {kbDiagnostics && (
            <div style={{ marginTop: 14 }}>
              <Alert
                type={kbDiagnostics.hybrid?.length ? 'success' : 'warning'}
                showIcon
                style={{ borderRadius: 10, marginBottom: 12 }}
                message={kbDiagnostics.summary}
                description={kbDiagnostics.query_terms?.length ? `标准化查询词：${kbDiagnostics.query_terms.join('、')}` : '没有提取到稳定查询词'}
              />
              <Segmented
                value={kbDiagTab}
                onChange={value => setKbDiagTab(String(value) as DiagnosticTab)}
                options={[
                  { label: `Hybrid (${kbDiagnostics.hybrid?.length || 0})`, value: 'hybrid' },
                  { label: `BM25 (${kbDiagnostics.bm25?.length || 0})`, value: 'bm25' },
                  { label: `Dense (${kbDiagnostics.dense?.length || 0})`, value: 'dense' },
                  { label: `Visual (${kbDiagnostics.visual?.length || 0})`, value: 'visual' },
                ]}
              />
              <div style={{ marginTop: 12 }}>{renderMaintenanceHits(kbDiagnostics[kbDiagTab] || [])}</div>
              {!!kbDiagnostics.branch_explanations?.[kbDiagTab]?.length && (
                <Alert
                  type="info"
                  showIcon
                  style={{ marginTop: 12, borderRadius: 10 }}
                  message={`${kbDiagTab.toUpperCase()} 分支解释`}
                  description={<ul style={{ margin: '4px 0 0 18px', padding: 0 }}>{kbDiagnostics.branch_explanations[kbDiagTab].map((note: string, index: number) => <li key={index}>{note}</li>)}</ul>}
                />
              )}
              {!!kbDiagnostics.recommended_actions?.length && (
                <Alert type="warning" showIcon style={{ marginTop: 12, borderRadius: 10 }} message="这次诊断建议" description={kbDiagnostics.recommended_actions.map((rec: any) => rec.title).join('、')} />
              )}
            </div>
          )}
        </Card>
      </Space>
    </Spin>
  );

  return (
    <PageShell
      title="论文库"
      subtitle={stats || '搜索、发现、管理你的学术论文。'}
      icon={<BookOutlined />}
      maxWidth={1100}
      actions={(
        <>
            {isAuthenticated && (
              <Badge count={digestUnreadCount} size="small">
                <Button icon={<BellOutlined />} onClick={() => navigate('/papers/digests')} style={{ borderRadius: 10 }}>论文推送</Button>
              </Badge>
            )}
            {isAdmin && <>
              <Button icon={<ImportOutlined />} loading={ingesting} onClick={handleIngest} style={{ borderRadius: 10 }}>一键入库</Button>
              <Button icon={<FileTextOutlined />} onClick={() => (document.getElementById('import-file') as HTMLInputElement)?.click()} style={{ borderRadius: 10 }}>导入</Button>
              <input type="file" accept=".csv,.bib" style={{ display: 'none' }} id="import-file" onChange={async (e) => {
                const f = e.target.files?.[0]; if (!f) return;
                const ep = f.name.endsWith('.bib') ? '/api/papers/import-bibtex' : '/api/papers/import-zotero';
                const fd = new FormData(); fd.append('file', f);
                try { const r = await api.post(ep, fd, { headers: { 'Content-Type': 'multipart/form-data' } }); setPageActionError(null); message.success(`导入: ${r.data.imported} 新增, ${r.data.skipped} 跳过`); handleSearch(); } catch (error) { showPageError('导入失败', error, '导入失败'); }
              }} />
            </>}
            <Button icon={<FileTextOutlined />} disabled={selectedIds.size === 0} onClick={() => setReportModalOpen(true)} style={{ borderRadius: 10 }}>
              组会报告 ({selectedIds.size})
            </Button>
            {isAdmin && <Button icon={<DatabaseOutlined />} onClick={() => updateSource('maintenance')} style={{ borderRadius: 10 }}>
              处理诊断
            </Button>}
        </>
      )}
    >
      {pageActionError ? (
        <ApiErrorAlert
          title={pageActionError.title}
          detail={pageActionError.detail}
          onClose={() => setPageActionError(null)}
        />
      ) : null}

      <div style={{ height: 'calc(100vh - 170px)', display: 'flex', flexDirection: 'column' }}>

      <WorkflowStepGuide
        title="论文库下一步"
        subtitle="先把论文资料变得可用，再整理成分类并交给研究方向。"
        style={{ marginBottom: 12, flexShrink: 0 }}
        collapsible
        defaultCollapsed
        steps={[
          {
            key: 'maintenance',
            title: '后台自动补齐处理',
            description: '新论文入库后会自动补全文、结构化解析、视觉证据、向量和索引；这里只查看异常诊断。',
            actionLabel: '查看处理诊断',
            status: 'optional',
            icon: <DatabaseOutlined />,
            onClick: () => updateSource('maintenance'),
          },
          {
            key: 'collections',
            title: '整理到论文分类',
            description: '把候选论文归入自定义分类，后续可以一键作为 idea 种子。',
            actionLabel: '管理分类',
            status: 'ready',
            icon: <FolderOutlined />,
            onClick: () => updateSource('collection'),
          },
          {
            key: 'research',
            title: '进入研究方向',
            description: '用分类论文生成研究 idea、实验计划和写作素材。',
            actionLabel: '去研究方向',
            status: 'optional',
            icon: <RocketOutlined />,
            path: '/research',
          },
        ]}
      />

      {/* ── 搜索栏 ── */}
      <Card style={{ borderRadius: 14, marginBottom: 10, border: '1px solid #f0f0f0', flexShrink: 0 }} styles={{ body: { padding: '8px 16px' } }}>
        <Row gutter={[8, 8]} align="middle">
          <Col xs={24} sm={4}><Select value={source} onChange={updateSource} style={{ width: '100%', borderRadius: 10 }}
            options={[
              { value: 'local', label: '📚 全部论文' },
              { value: 'mine', label: '👤 我的' },
              { value: 'saved', label: '⭐ 收藏' },
              { value: 'collection', label: '🗂️ 自定义分类' },
              { value: 'reading', label: '📖 阅读列表' },
              { value: 'maintenance', label: '🛠️ 处理诊断' },
              { value: 'scholarly', label: '🔎 综合学术' },
              { value: 'arxiv', label: '📝 arXiv' },
              { value: 'semantic_scholar', label: '🎓 Semantic Scholar' },
              { value: 'openalex', label: '🌐 OpenAlex' },
              { value: 'google_scholar', label: '🔬 Google Scholar（需配置）' },
            ]} /></Col>
          <Col xs={24} sm={3}><Select value={sort} onChange={setSort} style={{ width: '100%', borderRadius: 10 }}
            options={[{ value: 'created_desc', label: '🕐 最近入库' }, { value: 'year_desc', label: '📅 最新发表' }]} /></Col>
          <Col xs={24} sm={11}>
            <Input.Search placeholder="搜索论文标题、摘要..." value={searchQuery} onChange={e => setSearchQuery(e.target.value)} onSearch={() => handleSearch(1)} allowClear
              enterButton={<><SearchOutlined /> 搜索</>} style={{ borderRadius: 10 }} />
          </Col>
          <Col xs={24} sm={6}>
            {isAdmin && (
              <Input placeholder="arXiv ID 入库" value={ingestQuery} onChange={e => setIngestQuery(e.target.value)} onPressEnter={handleIngest}
                prefix={ingesting ? <LoadingOutlined /> : <ImportOutlined />} style={{ borderRadius: 10 }} />
            )}
          </Col>
        </Row>
        {source === 'collection' && (
          <Row gutter={[8, 8]} align="middle" style={{ marginTop: 8 }}>
            <Col flex="auto">
              <Space size={8} wrap>
                <Text type="secondary" style={{ fontSize: 13 }}>论文分类</Text>
                <Select
                  placeholder="选择分类"
                  value={selectedCollectionId}
                  onChange={setSelectedCollectionId}
                  options={collectionOptions}
                  style={{ minWidth: 220 }}
                />
                <Button icon={<FolderAddOutlined />} loading={creatingCollection} onClick={handleCreateCollection} style={{ borderRadius: 8 }}>
                  新建分类
                </Button>
                <Button
                  danger
                  icon={<DeleteOutlined />}
                  disabled={!selectedCollectionId}
                  loading={deletingCollection}
                  onClick={handleDeleteCollectionClick}
                  style={{ borderRadius: 8 }}
                >
                  删除分类
                </Button>
              </Space>
            </Col>
          </Row>
        )}
        {isAuthenticated && collections.length > 0 && source !== 'collection' && source !== 'maintenance' && (
          <Row gutter={[8, 8]} align="middle" style={{ marginTop: 8 }}>
            <Col span={24}>
              <Space size={8} wrap>
                <Text type="secondary" style={{ fontSize: 13 }}>入库目标分类</Text>
                <Select
                  allowClear
                  placeholder="远程论文可直接入库到分类"
                  value={targetCollectionId}
                  onChange={setTargetCollectionId}
                  options={collectionOptions}
                  style={{ minWidth: 260 }}
                />
              </Space>
            </Col>
          </Row>
        )}
        {remoteGuidance && (
          <Alert
            type="info"
            showIcon
            style={{ borderRadius: 10, marginTop: 10 }}
            message={<Space wrap><Text strong>{remoteGuidance.label}</Text>{remoteGuidance.providers.map(provider => <Tag color="blue" key={provider}>{provider}</Tag>)}</Space>}
            description={`${remoteGuidance.description} ${remoteGuidance.retry}`}
          />
        )}
        {source === 'collection' && collectionDiagnostics && (
          <Alert
            type={collectionDiagnostics.ready_for_idea ? 'success' : 'warning'}
            showIcon
            style={{ borderRadius: 10, marginTop: 10 }}
            message={collectionDiagnostics.ready_for_idea ? '该分类适合作为 Idea 生成语料' : '该分类还需要维护后再用于 Idea 生成'}
            description={(
              <Space direction="vertical" size={6} style={{ width: '100%' }}>
                <Space size={12} wrap>
                  <Text>论文 {collectionDiagnostics.paper_count}</Text>
                  <Text>已读 {collectionDiagnostics.read_status_counts?.completed || 0}</Text>
                  <Text>全文覆盖 {Math.round((collectionDiagnostics.full_text_coverage || 0) * 100)}%</Text>
                  <Text>向量覆盖 {Math.round((collectionDiagnostics.embedding_coverage || 0) * 100)}%</Text>
                </Space>
                <Space size={12} wrap>
                  <Progress size="small" style={{ width: 160 }} percent={Math.round((collectionDiagnostics.full_text_coverage || 0) * 100)} />
                  <Progress size="small" style={{ width: 160 }} percent={Math.round((collectionDiagnostics.embedding_coverage || 0) * 100)} />
                </Space>
                {(collectionDiagnostics.warnings || []).length > 0 && <Text type="secondary">{(collectionDiagnostics.warnings || []).join('；')}</Text>}
              </Space>
            )}
          />
        )}
        {source === 'collection' && collectionCoverage && (
          <Card
            size="small"
            style={{ marginTop: 10, borderRadius: 12, border: '1px solid #efe7ff', background: '#fbfaff' }}
            styles={{ body: { padding: showCoverage ? 12 : 8 } }}
          >
            {/* 折叠头 */}
            <Row
              align="middle"
              justify="space-between"
              style={{ cursor: 'pointer' }}
              onClick={() => setShowCoverage(!showCoverage)}
            >
              <Col>
                <Space size={8} wrap>
                  <Text strong style={{ fontSize: 13 }}>主题覆盖分析</Text>
                  <Text type="secondary" style={{ fontSize: 12 }}>{collectionCoverage.summary}</Text>
                </Space>
              </Col>
              <Col>
                <Tag color={showCoverage ? 'default' : 'purple'} style={{ borderRadius: 999, cursor: 'pointer' }}>
                  {showCoverage ? '收起' : '展开详情'}
                  {showCoverage ? <CaretDownOutlined /> : <CaretRightOutlined />}
                </Tag>
              </Col>
            </Row>
            {showCoverage && (
              <Space direction="vertical" size={10} style={{ width: '100%', marginTop: 10 }}>
                <Space size={6} wrap>
                  {collectionCoverage.topic_terms?.slice(0, 8).map(term => (
                    <Tag key={term} color="purple" style={{ borderRadius: 10 }}>{term}</Tag>
                  ))}
                </Space>
                <Space size={6} wrap>
                  {collectionCoverage.topics?.slice(0, 8).map(topic => {
                    const meta = topicStatusMeta(topic.status);
                    return (
                      <Tag key={`${topic.label}-${topic.query}`} color={meta.color} style={{ borderRadius: 10 }}>
                        {topic.label} · {meta.label} ({topic.matched_count})
                      </Tag>
                    );
                  })}
                </Space>
                <Space size={8} wrap>
                  <Text type="secondary" style={{ fontSize: 13 }}>补论文推荐</Text>
                  <Button
                    size="small"
                    type={recommendationKind === 'classic' ? 'primary' : 'default'}
                    loading={recommendationLoading && recommendationKind === 'classic'}
                    onClick={() => handleFetchRecommendations('classic', collectionCoverage.recommended_queries?.classic)}
                    style={{ borderRadius: 8 }}
                  >
                    补经典
                  </Button>
                  <Button
                    size="small"
                    type={recommendationKind === 'recent' ? 'primary' : 'default'}
                    loading={recommendationLoading && recommendationKind === 'recent'}
                    onClick={() => handleFetchRecommendations('recent', collectionCoverage.recommended_queries?.recent)}
                    style={{ borderRadius: 8 }}
                  >
                    补近期
                  </Button>
                  <Button
                    size="small"
                    type={recommendationKind === 'gap' ? 'primary' : 'default'}
                    loading={recommendationLoading && recommendationKind === 'gap'}
                    onClick={() => handleFetchRecommendations('gap', collectionCoverage.recommended_queries?.gap)}
                    style={{ borderRadius: 8 }}
                  >
                    补缺口
                  </Button>
                  {recommendationMeta && <Text type="secondary" style={{ fontSize: 12 }}>检索式：{recommendationMeta.query}</Text>}
                </Space>
                {recommendationMeta && <Text type="secondary" style={{ fontSize: 12 }}>{recommendationMeta.reason}</Text>}
                {recommendationPapers.length > 0 && (
                  <Row gutter={[8, 8]}>
                    {recommendationPapers.map(paper => {
                      const remoteKey = `${paper.source}:${paper.remote_id}`;
                      return (
                        <Col xs={24} md={12} key={remoteKey || paper.title}>
                          <Card size="small" hoverable onClick={() => setDetailPaper(paper)} style={{ borderRadius: 12 }}>
                            <Space direction="vertical" size={6} style={{ width: '100%' }}>
                              <Text strong ellipsis>{paper.title}</Text>
                              <Space size={4} wrap>
                                {paper.year && <Tag icon={<CalendarOutlined />} color="blue">{paper.year}</Tag>}
                                <Tag color={sc(paper.source)}>{sl(paper.source)}</Tag>
                                {paper.arxiv_id && <Tag color="#b31b1b">arXiv:{paper.arxiv_id}</Tag>}
                                {paper.citation_count > 0 && <Tag icon={<RiseOutlined />} color="orange">引用 {paper.citation_count}</Tag>}
                              </Space>
                              {paper.abstract && <Paragraph type="secondary" ellipsis={{ rows: 2 }} style={{ margin: 0, fontSize: 12 }}>{paper.abstract}</Paragraph>}
                              <Space size={6} wrap>
                                <Button type="link" size="small" icon={<EyeOutlined />} onClick={e => handleOpenAbstract(e, paper)} style={{ paddingInline: 0 }}>详情</Button>
                                {paper.pdf_url && <Button type="link" size="small" icon={<FileTextOutlined />} href={paper.pdf_url} target="_blank" rel="noreferrer" onClick={e => e.stopPropagation()} style={{ paddingInline: 0 }}>PDF</Button>}
                                {ingestedRemoteIds.has(remoteKey)
                                  ? <Tag color="green">已加入当前分类</Tag>
                                  : (
                                    <Button
                                      size="small"
                                      type="primary"
                                      ghost
                                      icon={<ImportOutlined />}
                                      loading={ingestingIds.has(remoteKey)}
                                      onClick={e => handleIngestOne(e, paper, selectedCollectionId)}
                                      style={{ borderRadius: 8 }}
                                    >
                                      入库并加入当前分类
                                    </Button>
                                  )}
                              </Space>
                            </Space>
                          </Card>
                        </Col>
                      );
                    })}
                  </Row>
                )}
              </Space>
            )}
          </Card>
        )}
        {source !== 'maintenance' && <Row gutter={[8, 8]} align="middle" style={{ marginTop: 8 }}>
          <Col flex="auto">
            <Space size={8} wrap>
              <Text type="secondary" style={{ fontSize: 13 }}>发表年份</Text>
              <Select allowClear placeholder="起始年份" value={yearFrom} onChange={setYearFrom} options={yearOptions} style={{ width: 112 }} />
              <Text type="secondary">至</Text>
              <Select allowClear placeholder="截止年份" value={yearTo} onChange={setYearTo} options={yearOptions} style={{ width: 112 }} />
              {(yearFrom || yearTo) && <Button type="link" size="small" onClick={() => { setYearFrom(undefined); setYearTo(undefined); }}>清除年份</Button>}
            </Space>
          </Col>
          {isRemoteSource && searchQuery.trim() && (
            <Col>
              <Space size={8}>
                <Text type="secondary" style={{ fontSize: 12 }}>第 {remotePage} 批</Text>
                <Button icon={<RedoOutlined />} loading={loading} onClick={() => handleSearch(remotePage + 1)} style={{ borderRadius: 8 }}>换一批</Button>
              </Space>
            </Col>
          )}
        </Row>}
        {showKnowledgeFilters && (
          <Row gutter={[8, 8]} align="middle" style={{ marginTop: 8 }}>
            <Col span={24}>
              <Space size={8} wrap>
                <Text type="secondary" style={{ fontSize: 13 }}>知识库筛选</Text>
                <Select allowClear placeholder="导入账号" value={filterImporter} onChange={setFilterImporter} options={importerOptions} style={{ width: 128 }} />
                <Select allowClear placeholder="来源" value={filterLocalSource} onChange={setFilterLocalSource} options={localSourceOptions} style={{ width: 140 }} />
                <Select value={filterFullText} onChange={setFilterFullText} options={[
                  { value: 'all', label: '全文不限' },
                  { value: 'true', label: '有全文' },
                  { value: 'false', label: '缺全文' },
                ]} style={{ width: 112 }} />
                <Select value={filterEmbedding} onChange={setFilterEmbedding} options={[
                  { value: 'all', label: '向量不限' },
                  { value: 'true', label: '有向量' },
                  { value: 'false', label: '缺向量' },
                ]} style={{ width: 112 }} />
                <Select value={filterReadStatus} onChange={setFilterReadStatus} options={[
                  { value: 'all', label: '阅读不限' },
                  { value: 'unread', label: '待读' },
                  { value: 'reading', label: '阅读中' },
                  { value: 'completed', label: '已完成' },
                ]} style={{ width: 120 }} />
                <Select value={filterImportance} onChange={setFilterImportance} options={[
                  { value: 'all', label: '标记不限' },
                  { value: 'important', label: paperImportanceMeta.important.label },
                  { value: 'interesting', label: paperImportanceMeta.interesting.label },
                ]} style={{ width: 128 }} />
              </Space>
            </Col>
          </Row>
        )}
        {source !== 'maintenance' && papers.length > 0 && (
          <Row gutter={[8, 8]} align="middle" style={{ marginTop: 8 }}>
            <Col flex="auto">
              <Space size={6} wrap>
                <Text type="secondary" style={{ fontSize: 13 }}>结果状态</Text>
                <Tag color="blue">全部 {resultStateCounts.all}</Tag>
                <Tag color="green">已在库 {resultStateCounts.local}</Tag>
                <Tag color="geekblue">可入库 {resultStateCounts.importable}</Tag>
                <Tag color="success">本次已加入 {resultStateCounts.imported}</Tag>
                <Tag color="cyan">开放 PDF {resultStateCounts.open_pdf}</Tag>
                <Tag>缺远程 ID {resultStateCounts.missing_remote_id}</Tag>
              </Space>
            </Col>
            <Col>
              <Select
                size="small"
                value={resultStateFilter}
                onChange={setResultStateFilter}
                options={paperResultStateOptions}
                style={{ width: 132 }}
              />
            </Col>
          </Row>
        )}
        {source === 'reading' && (
          <Row style={{ marginTop: 10 }}>
            <Col span={24}>
              <Space size={8} wrap>
                <Text type="secondary" style={{ fontSize: 13 }}>阅读队列</Text>
                <Space.Compact>
                  {(['unread', 'reading', 'completed'] as const).map(status => (
                    <Button
                      key={status}
                      type={readingStatus === status ? 'primary' : 'default'}
                      onClick={() => setReadingStatus(status)}
                    >
                      {readingStatusMeta[status].label} {readingCounts[status] || 0}
                    </Button>
                  ))}
                </Space.Compact>
              </Space>
            </Col>
          </Row>
        )}
      </Card>

      {/* ── 论文列表 (可滚动) ── */}
      <div style={{ flex: 1, overflowY: 'auto', minHeight: 0, paddingRight: 4 }}>
      {source === 'maintenance' ? maintenanceView : (
        loading ? (
          <WorkflowLoadingState
            title={isRemoteSource ? '正在检索外部学术源' : '正在加载论文列表'}
            description={isRemoteSource ? '系统会合并可用学术源，并标记可入库、已入库和开放 PDF 状态。' : '正在读取收藏、阅读状态、分类和论文元数据。'}
            icon={<BookOutlined />}
            style={{ marginBottom: 12 }}
          />
        ) : filteredPapers.length > 0 ? (
          <List dataSource={filteredPapers} renderItem={(paper, idx) => {
            const remoteKey = paperRemoteKey(paper);
            const resultState = paperResultState(paper, ingestedRemoteIds);
            const citationKey = buildResearchCitationKey(paper, idx);
            const metadataQuality = computeMetadataQuality(paper);
            const duplicateRisk = duplicateRiskForPaper(paper, duplicateRiskMap);
            return (
            <Card hoverable size="small" style={{ marginBottom: 10, borderRadius: 12, border: '1px solid #f0f0f0', overflow: 'hidden' }}
              onClick={() => handleViewDetail(paper)}
              extra={paper.id ? <Checkbox checked={selectedIds.has(paper.id)} onChange={e => { e.stopPropagation(); setSelectedIds(prev => { const n = new Set(prev); e.target.checked ? n.add(paper.id) : n.delete(paper.id); return n; }); }} onClick={e => e.stopPropagation()} /> : null}>
              {/* 左侧色条 */}
              <div style={{ height: 3, background: `linear-gradient(90deg, ${sc(paper.source)}, transparent)`, margin: '-1px -1px 0 -1px', borderTopLeftRadius: 12, borderTopRightRadius: 12 }} />
              <Row gutter={16} align="top">
                {/* 编号 + 来源 */}
                <Col style={{ flexShrink: 0 }}>
                  <div style={{ width: 32, height: 32, borderRadius: 10, background: '#667eea10', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#667eea', fontWeight: 700, fontSize: 13 }}>{idx + 1}</div>
                </Col>
                <Col flex={1}>
                  <Text strong style={{ fontSize: 15, lineHeight: 1.5 }}>{paper.title}</Text>
                  <div style={{ marginTop: 6 }}>
                    <Space size={4} wrap>
                      {paper.year && <Tag icon={<CalendarOutlined />} color="blue" style={{ borderRadius: 6 }}>{paper.year}</Tag>}
                      {paper.authors?.slice(0, 2).map((a, i) => <Tag key={i} icon={<UserOutlined />} style={{ borderRadius: 6 }}>{a}</Tag>)}
                      {paper.arxiv_id && <Tag color="#b31b1b" style={{ borderRadius: 6 }}>arXiv:{paper.arxiv_id}</Tag>}
                      <Tag color={sc(paper.source)} style={{ borderRadius: 6 }}>{sl(paper.source)}</Tag>
                      {paper.imported_by_username && <Tag icon={<UserOutlined />} color="purple" style={{ borderRadius: 6 }}>导入：{paper.imported_by_username}</Tag>}
                      {paper.importance_label && (
                        <Tooltip title={paper.importance_note || '团队共享标记'}>
                          <Tag icon={paperImportanceMeta[paper.importance_label].icon} color={paperImportanceMeta[paper.importance_label].color} style={{ borderRadius: 6 }}>
                            {paperImportanceMeta[paper.importance_label].label}
                          </Tag>
                        </Tooltip>
                      )}
                      {paper.id && <Tag color="cyan" style={{ borderRadius: 6 }}>key:{citationKey}</Tag>}
                      {paper.id && <Tag color={metadataQuality.tier === 'ready' ? 'green' : metadataQuality.tier === 'usable' ? 'gold' : 'orange'} style={{ borderRadius: 6 }}>元数据 {metadataQuality.percent}%</Tag>}
                      {duplicateRisk.risk !== 'none' && <Tag color={duplicateRisk.risk === 'strong' ? 'red' : 'orange'} style={{ borderRadius: 6 }}>疑似重复</Tag>}
                      <Tag color={resultState.color} style={{ borderRadius: 6 }}>{resultState.label}</Tag>
                      {paper.id && renderProcessingLabels(paper.processing_labels)}
                      {paper.read_status && <Tag color={readingStatusMeta[paper.read_status].color} style={{ borderRadius: 6 }}>{readingStatusMeta[paper.read_status].label}</Tag>}
                      {paper.citation_count > 0 && <Tag icon={<RiseOutlined />} color="orange" style={{ borderRadius: 6 }}>引用 {paper.citation_count}</Tag>}
                      {!paper.id && <Tag color={paper.pdf_url ? 'green' : 'default'} style={{ borderRadius: 6 }}>{paper.pdf_url ? '开放 PDF' : '未返回 PDF'}</Tag>}
                      {!paper.id && paper.source_url && <Tag color="cyan" style={{ borderRadius: 6 }}>有来源页</Tag>}
                      <Button type="link" size="small" icon={<EyeOutlined />} onClick={e => handleOpenAbstract(e, paper)} style={{ height: 24, paddingInline: 4 }}>查看摘要</Button>
                      {paper.pdf_url && <Button type="link" size="small" icon={<FileTextOutlined />} href={paper.pdf_url} target="_blank" rel="noreferrer" onClick={e => e.stopPropagation()} style={{ height: 24, paddingInline: 4 }}>开放 PDF</Button>}
                      {paper.source_url && <Button type="link" size="small" icon={<LinkOutlined />} href={paper.source_url} target="_blank" rel="noreferrer" onClick={e => e.stopPropagation()} style={{ height: 24, paddingInline: 4 }}>来源页</Button>}
                      {source === 'collection' && selectedCollectionId && <Button type="link" danger size="small" onClick={e => handleRemoveFromCollection(e, paper)} style={{ height: 24, paddingInline: 4 }}>移出分类</Button>}
                      {!paper.id && isAuthenticated && paper.remote_id ? (
                        resultState.key === 'imported'
                          ? <Tag color="green" style={{ borderRadius: 6 }}>已加入论文库</Tag>
                          : <Button size="small" type="primary" ghost icon={<ImportOutlined />} loading={ingestingIds.has(remoteKey)}
                            onClick={e => handleIngestOne(e, paper)} style={{ borderRadius: 8, height: 24 }}>{targetCollectionId ? '入库并加入分类' : '加入论文库'}</Button>
                      ) : null}
                    </Space>
                  </div>
                  {!paper.id && targetCollectionId && (
                    <Text type="secondary" style={{ display: 'block', marginTop: 6, fontSize: 12 }}>
                      入库目标：论文库 + {collections.find(item => item.id === targetCollectionId)?.name || '所选分类'}
                    </Text>
                  )}
                  {paper.abstract && <Paragraph type="secondary" ellipsis={{ rows: 2 }} style={{ marginTop: 8, marginBottom: 0, fontSize: 13 }}>{paper.abstract}</Paragraph>}
                  {paper.id && (
                    <div className="paper-citation-quality-row">
                      <Text type="secondary" style={{ fontSize: 12 }}>JabRef 质量：</Text>
                      <Space size={4} wrap>
                        {metadataQuality.checks.map(check => (
                          <Tag key={check.key} color={check.ready ? 'green' : 'default'} style={{ borderRadius: 6 }}>{check.label}</Tag>
                        ))}
                      </Space>
                    </div>
                  )}
                  {renderReadingActions(paper)}
                </Col>
                {isAuthenticated && paper.id && (
                  <Col style={{ flexShrink: 0 }}>
                    <Space size={2}>
                      {renderImportanceActions(paper)}
                      <Button type="text" size="small" icon={savedIds.has(paper.id) ? <StarFilled style={{ color: '#faad14' }} /> : <StarOutlined />} onClick={e => handleSave(e, paper)} />
                      <Button type="text" size="small" danger icon={<DeleteOutlined />} onClick={e => handleDeleteClick(e, paper)} />
                    </Space>
                  </Col>
                )}
              </Row>
            </Card>
          );
          }} />
        ) : (
          <WorkflowEmptyState
            title={papers.length > 0 ? '当前状态筛选下没有结果' : isRemoteSource ? '这次外部检索没有返回论文' : '暂无论文'}
            description={papers.length > 0
              ? `当前结果中没有符合「${paperResultStateOptions.find(option => option.value === resultStateFilter)?.label}」状态的论文。`
              : isRemoteSource
                ? '可能是关键词过窄、年份限制过紧、当前 provider 不可用，或该来源没有开放元数据。'
                : '尝试搜索 arXiv 或一键入库来添加论文。'}
            icon={<BookOutlined />}
            action={(
              <>
            {papers.length > 0 ? (
              <Space direction="vertical" size={10} style={{ width: '100%', alignItems: 'center' }}>
                <Button onClick={() => setResultStateFilter('all')} style={{ borderRadius: 10 }}>查看全部状态</Button>
              </Space>
            ) : isRemoteSource ? (
              <Space direction="vertical" size={10} style={{ width: '100%', alignItems: 'center' }}>
                <Space wrap style={{ justifyContent: 'center' }}>
                  <Button onClick={() => { setYearFrom(undefined); setYearTo(undefined); }} style={{ borderRadius: 10 }}>放宽年份</Button>
                  <Button icon={<RedoOutlined />} loading={loading} onClick={() => handleSearch(remotePage + 1)} style={{ borderRadius: 10 }}>换一批</Button>
                  <Button onClick={() => updateSource(source === 'scholarly' ? 'openalex' : 'scholarly')} style={{ borderRadius: 10 }}>
                    {source === 'scholarly' ? '切到 OpenAlex' : '切到综合学术'}
                  </Button>
                  {isAdmin && <Button icon={<DatabaseOutlined />} onClick={() => updateSource('maintenance')} style={{ borderRadius: 10 }}>处理诊断</Button>}
                </Space>
                {remoteGuidance && <Text type="secondary" style={{ fontSize: 12 }}>{remoteGuidance.retry}</Text>}
              </Space>
            ) : (
                <Button type="primary" size="large" icon={<RocketOutlined />} onClick={() => { setIngestQuery('large language model'); handleIngest(); }} style={{ borderRadius: 12, height: 44 }}>示例：检索 "large language model"</Button>
            )}
              </>
            )}
          />
        )
      )}
      </div>

      {/* ── 批量操作栏 ── */}
      {selectedCount > 0 && (
        <div className="paper-bulk-action-bar" role="toolbar" aria-label="已选论文批量操作">
          <div className="paper-bulk-action-count">
            <Text strong>已选 {selectedCount} 篇</Text>
            {selectedPapers.length !== selectedCount && (
              <Text type="secondary">{selectedPapers.length} 篇在当前列表</Text>
            )}
          </div>

          <div className="paper-bulk-action-groups">
            <div className="paper-bulk-action-section paper-bulk-action-section-wide">
              <Text className="paper-bulk-action-label" type="secondary">分类</Text>
              <div className="paper-bulk-action-controls">
                <Select
                  size="small"
                  placeholder="选择分类"
                  value={targetCollectionId}
                  onChange={setTargetCollectionId}
                  options={collectionOptions}
                  className="paper-bulk-action-select"
                  suffixIcon={<FolderOutlined />}
                />
                <Button size="small" icon={<FolderAddOutlined />} loading={addingCollection} onClick={handleAddSelectedToCollection}>
                  加入分类
                </Button>
                <Button size="small" icon={<FolderAddOutlined />} loading={creatingCollection} onClick={handleCreateCollection}>
                  新建分类
                </Button>
              </div>
            </div>

            <div className="paper-bulk-action-section">
              <Text className="paper-bulk-action-label" type="secondary">阅读</Text>
              <div className="paper-bulk-action-controls">
                <Button size="small" icon={<RollbackOutlined />} loading={updatingStatusIds.size > 0} onClick={() => handleBulkReadStatus('unread')}>
                  待读
                </Button>
                <Button size="small" icon={<PlayCircleOutlined />} loading={updatingStatusIds.size > 0} onClick={() => handleBulkReadStatus('reading')}>
                  阅读中
                </Button>
                <Button size="small" icon={<CheckCircleOutlined />} loading={updatingStatusIds.size > 0} onClick={() => handleBulkReadStatus('completed')}>
                  已完成
                </Button>
              </div>
            </div>

            <div className="paper-bulk-action-section">
              <Text className="paper-bulk-action-label" type="secondary">导出</Text>
              <div className="paper-bulk-action-controls">
                <Button size="small" icon={<DownloadOutlined />} onClick={() => handleExportSelected('bibtex')}>BibTeX</Button>
                <Button size="small" onClick={() => handleExportSelected('markdown')}>Markdown</Button>
                <Button size="small" onClick={() => handleExportSelected('json')}>JSON</Button>
              </div>
            </div>

            <div className="paper-bulk-action-section">
              <Text className="paper-bulk-action-label" type="secondary">任务</Text>
              <div className="paper-bulk-action-controls">
                <Button size="small" icon={<FileTextOutlined />} onClick={() => setReportModalOpen(true)}>
                  组会报告
                </Button>
                {isAdmin && (
                  <Button size="small" icon={<TagsOutlined />} onClick={handleBatchTagSelected}>
                    标签
                  </Button>
                )}
              </div>
            </div>
          </div>

          <Button
            size="small"
            type="text"
            icon={<CloseOutlined />}
            aria-label="清空选择"
            onClick={() => setSelectedIds(new Set())}
            className="paper-bulk-action-clear"
          />
        </div>
      )}

      {/* 弹窗不变（删除/报告） */}
      <Modal title="论文摘要" open={!!detailPaper} onCancel={() => setDetailPaper(null)} footer={<Button type="primary" onClick={() => setDetailPaper(null)}>关闭</Button>} width={760}>
        {detailPaper && (
          <Space direction="vertical" size={12} style={{ width: '100%' }}>
            <Title level={4} style={{ margin: 0, lineHeight: 1.45 }}>{detailPaper.title}</Title>
            <Space size={6} wrap>
              {detailPaper.year && <Tag icon={<CalendarOutlined />} color="blue">{detailPaper.year}</Tag>}
              <Tag color={sc(detailPaper.source)}>{sl(detailPaper.source)}</Tag>
              {detailPaper.imported_by_username && <Tag icon={<UserOutlined />} color="purple">导入：{detailPaper.imported_by_username}</Tag>}
              {detailPaper.arxiv_id && <Tag color="#b31b1b">arXiv:{detailPaper.arxiv_id}</Tag>}
              {detailPaper.doi && <Tag>DOI:{detailPaper.doi}</Tag>}
            </Space>
            {detailPaper.authors?.length > 0 && <Text type="secondary">作者：{detailPaper.authors.join('、')}</Text>}
            <Paragraph style={{ whiteSpace: 'pre-wrap', lineHeight: 1.8, marginBottom: 0 }}>{detailPaper.abstract_full || detailPaper.abstract || '暂无可展示的摘要'}</Paragraph>
            <Space wrap>
              {detailPaper.pdf_url && <Button icon={<FileTextOutlined />} href={detailPaper.pdf_url} target="_blank" rel="noreferrer">打开开放 PDF</Button>}
              {detailPaper.source_url && <Button icon={<LinkOutlined />} href={detailPaper.source_url} target="_blank" rel="noreferrer">查看来源</Button>}
              {detailPaper.id && <Button icon={<LinkOutlined />} onClick={() => { setDetailPaper(null); navigate(`/papers/${detailPaper.id}`); }}>进入论文详情</Button>}
            </Space>
          </Space>
        )}
      </Modal>

      <Modal title={<span><ExclamationCircleOutlined style={{ color: '#faad14' }} /> 删除论文</span>} open={deleteModal.open} onCancel={() => setDeleteModal({ open: false, paper: null })}
        footer={[<Button key="cancel" onClick={() => setDeleteModal({ open: false, paper: null })}>取消</Button>, <Button key="coll" onClick={() => confirmDelete(false)} loading={deleting}>仅从收藏移除</Button>, ...(isAdmin ? [<Button key="global" type="primary" danger onClick={() => confirmDelete(true)} loading={deleting}>从总库删除</Button>] : [])]}>
        <p>确定删除 <Text strong>"{deleteModal.paper?.title?.slice(0, 60)}..."</Text>？</p>
        <p><Text type="secondary">「仅从收藏移除」：其他用户仍可看到</Text><br /><Text type="danger">「从总库删除」：所有人无法再访问</Text></p>
      </Modal>

      <Modal
        title={<span><ExclamationCircleOutlined style={{ color: '#faad14' }} /> 删除分类</span>}
        open={deleteCollectionModal.open}
        onCancel={() => setDeleteCollectionModal({ open: false, collection: null })}
        footer={[
          <Button key="cancel" onClick={() => setDeleteCollectionModal({ open: false, collection: null })}>取消</Button>,
          <Button key="delete" type="primary" danger loading={deletingCollection} onClick={confirmDeleteCollection}>删除分类</Button>,
        ]}
      >
        <p>确定删除分类 <Text strong>"{deleteCollectionModal.collection?.name}"</Text>？</p>
        <p>
          <Text type="secondary">
            删除后该分类会从列表中移除，分类里的论文仍保留在论文库、收藏和阅读状态中。
          </Text>
        </p>
      </Modal>

      <Modal title="生成组会报告" open={reportModalOpen} onCancel={() => setReportModalOpen(false)}
        footer={[<Button key="cancel" onClick={() => setReportModalOpen(false)}>取消</Button>, <Button key="md" icon={<FileTextOutlined />} loading={reportLoading} onClick={async () => {
          const ids = Array.from(selectedIds).join(',');
          try {
            const r = await api.get('/writing/group-report-md', { params: { paper_ids: ids, title: reportTitle, custom_prompt: reportPrompt.trim() || undefined, report_preset: reportPreset }, timeout: 120000 });
            await navigator.clipboard.writeText(r.data.result);
            setPageActionError(null);
            message.success('已复制，可粘贴到飞书');
            setReportModalOpen(false);
          } catch (error) { showPageError('复制 Markdown 报告失败', error, '复制 Markdown 报告失败'); }
        }}>复制 MD</Button>, <Button key="docx" type="primary" icon={<FileTextOutlined />} loading={reportLoading} onClick={() => handleReport('docx')}>下载 Word</Button>]}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Text>已选择 {selectedIds.size} 篇论文</Text>
          <Input placeholder="报告标题" value={reportTitle} onChange={e => setReportTitle(e.target.value)} style={{ borderRadius: 10 }} />
          <Segmented
            value={reportPreset}
            onChange={value => setReportPreset(String(value))}
            options={reportPresetOptions}
          />
          <Input.TextArea
            placeholder="可选：输入自定义汇报要求。留空时使用默认逐篇论文报告；填写后会按你的要求生成整体组会报告，例如横向比较、按方法脉络汇报、只讲实验设计或从批判性角度分析。"
            value={reportPrompt}
            onChange={e => setReportPrompt(e.target.value)}
            autoSize={{ minRows: 4, maxRows: 8 }}
            maxLength={4000}
            showCount
            style={{ borderRadius: 10 }}
          />
        </Space>
      </Modal>
      </div>
    </PageShell>
  );
};

export default PapersPage;
