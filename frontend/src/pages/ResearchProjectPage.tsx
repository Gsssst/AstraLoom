import React, { useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Alert, Button, Card, Checkbox, Collapse, Col, Divider, Drawer, Input, List, message,
  Modal, Popconfirm, Row, Select, Space, Steps, Switch, Tabs, Tag, Timeline, Tooltip, Typography,
} from 'antd';
import {
  ArrowLeftOutlined, BulbOutlined, CodeOutlined, CopyOutlined, DeleteOutlined, DownloadOutlined,
  ExperimentOutlined, FileOutlined, FileSearchOutlined, FileTextOutlined, FolderOutlined, MessageOutlined, NodeIndexOutlined,
  HistoryOutlined, ImportOutlined, PlusOutlined, PushpinOutlined, ReloadOutlined, RiseOutlined, RobotOutlined, RocketOutlined, SendOutlined,
  SaveOutlined, ShareAltOutlined, StarFilled, StopOutlined, ThunderboltOutlined, UserOutlined,
} from '@ant-design/icons';
import api from '../services/api';
import WorkspaceResourceLinks from '../components/WorkspaceResourceLinks';
import WorkspaceIssueReporter from '../components/WorkspaceIssueReporter';
import PageShell from '../components/PageShell';
import ApiErrorAlert from '../components/ApiErrorAlert';
import Markdown from '../components/Markdown';
import {
  WorkflowEmptyState,
  WorkflowLoadingState,
  WorkflowProgressState,
  WorkflowUnavailableState,
} from '../components/WorkflowState';
import { getApiErrorDetails, type ApiErrorDetails } from '../services/apiError';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

interface Project {
  id: string; name: string; description: string | null;
  keywords: string[] | null; status: string; ideas_count: number;
}
interface Evidence {
  paper_id: string; title: string; year?: number; arxiv_id?: string;
  category: 'seed' | 'background' | 'inspiration'; score: number;
  abstract_excerpt: string; relevance: string; source?: string; source_url?: string; doi?: string;
  collection_names?: string[];
  imported_paper_id?: string;
}
interface Gap {
  title: string; limitation: string; opportunity: string;
  research_question: string; evidence_ids: string[]; uncertainty: string;
  evidence_rationale?: string;
  selection_status?: string;
  user_feedback?: GapUserFeedback;
  refinement?: { source?: string; focus_note?: string; previous_title?: string };
}
type GapFeedbackRating = 'strong' | 'promising' | 'weak' | 'reject';
type GapFeedbackLabel = 'valuable' | 'too_broad' | 'evidence_weak' | 'already_done' | 'misaligned' | 'needs_narrowing' | 'high_potential';
interface GapUserFeedback {
  rating?: GapFeedbackRating;
  labels?: GapFeedbackLabel[];
  note?: string;
}
interface GapFeedbackDraft {
  title: string;
  limitation: string;
  opportunity: string;
  research_question: string;
  uncertainty: string;
  evidence_rationale: string;
  evidence_ids: string[];
  rating: GapFeedbackRating;
  labels: GapFeedbackLabel[];
  note: string;
}
interface ProposalReviewPackage {
  summary: string;
  contributions: string[];
  weakest_assumptions: string[];
  reviewer_objections: string[];
  required_experiments: string[];
  revision_plan: string[];
  writing_readiness: 'ready' | 'needs_revision' | 'blocked' | string;
  next_revision_focus: string;
}
interface Review {
  scores: Record<string, number>; rationale: string; uncertainty: string; recommendation: string;
  aggregate_score?: number;
  base_score?: number;
  selection_rationale?: string | null;
  selection_score?: number | null;
  diversity_facets?: string[];
  suppressed_duplicates?: Array<{ title?: string; kept?: string; reason?: string; similarity?: number }>;
  gap_selection?: GapSelection | null;
  novelty_check?: {
    status: 'likely_novel' | 'incremental' | 'too_similar';
    score: number; max_similarity: number; rationale: string;
    nearest_evidence?: { paper_id?: string; title?: string; source?: string } | null;
    collision_risk?: 'high' | 'medium' | 'low' | 'unknown';
    similar_work?: Array<{
      paper_id?: string; title?: string; year?: number; source?: string; source_url?: string;
      score?: number; relation?: string; reason?: string; title_similarity?: number; lexical_similarity?: number;
    }>;
    source_coverage?: {
      query?: string; local_count?: number; external_count?: number; total_count?: number;
      sources?: Record<string, number>; source_errors?: Record<string, string>;
    };
  };
  adversarial_review?: {
    verdict: 'advance' | 'revise' | 'reject'; penalty: number;
    objections: string[]; required_fixes: string[]; summary: string;
  };
  proposal_review?: ProposalReviewPackage | null;
  search_tree?: { round?: number; operator?: string; parent_title?: string | null; lineage?: string[]; source?: string };
}
interface Candidate {
  title: string; path: string; gap: string; hypothesis: string; approach: string;
  evidence_ids: string[]; risks: string[]; falsification_test: string;
  minimum_experiment: ExperimentPlan; review?: Review; score?: number;
}
interface ExperimentPlan { dataset: string; baselines: string[]; metrics: string[]; steps: string[]; }
interface CodeProjectFile { path: string; language: string; purpose: string; content: string; }
interface CodeProjectEntrypoint { name: string; path: string; command: string; purpose: string; }
interface CodeProjectManifest {
  name: string;
  framework: string;
  summary: string;
  setup: string[];
  run_commands: string[];
  entrypoints: CodeProjectEntrypoint[];
  safety_notes: string[];
  files: CodeProjectFile[];
}
interface CodeProjectFolderGroup { folder: string; files: CodeProjectFile[]; }
interface CodeProjectVersionSummary {
  id: string;
  idea_id: string;
  version: number;
  project_name: string;
  framework: string;
  summary?: string | null;
  file_count: number;
  created_at: string;
}
interface CodeProjectVersionDetail extends CodeProjectVersionSummary {
  code_project: CodeProjectManifest;
}
interface CodeProjectFileDiff {
  path: string;
  status: 'added' | 'removed' | 'modified' | 'unchanged';
  language: string;
  purpose: string;
  before_line_count: number;
  after_line_count: number;
  before_content?: string | null;
  after_content?: string | null;
  diff: string;
}
interface CodeProjectVersionCompare {
  idea_id: string;
  from_version: number;
  to_version: number;
  summary: Record<'added' | 'removed' | 'modified' | 'unchanged', number>;
  files: CodeProjectFileDiff[];
}
interface Idea {
  id: string; project_id: string; title: string; description: string | null;
  hypothesis?: string | null; approach?: string | null; novelty?: string | null;
  feasibility_score: number | null; novelty_score: number | null; status: string;
  created_at?: string;
  generated_code: string | null; generated_code_project?: CodeProjectManifest | null; evidence_json?: { items?: Evidence[]; scope?: string; collection_sources?: { id: string; name: string; evidence_count: number }[] } | null;
  review_json?: Review | null; experiment_plan?: ExperimentPlan | null;
  parent_idea_id?: string | null;
  evolution_json?: {
    focus?: string;
    rationale?: string;
    round?: number;
    source?: string;
    review_focus?: string;
    review_objections?: string[];
    required_experiments?: string[];
    experiment_feedback?: ExperimentRecord;
  } | null;
  discussion_log?: CopilotLogEntry[];
}
type CopilotMode = 'mentor' | 'skeptic' | 'experiment_designer' | 'writer';
interface CopilotMetadata {
  context_summary?: { evidence_count?: number; has_validation?: boolean; has_execution_pack?: boolean; has_lineage?: boolean; missing?: string[] };
  risks?: string[];
  next_actions?: string[];
  suggested_questions?: string[];
  evolution_focus?: string | null;
}
interface CopilotLogEntry {
  role: 'user' | 'assistant';
  content: string;
  mode?: CopilotMode;
  metadata?: CopilotMetadata;
}
interface CopilotState extends CopilotMetadata {
  msg: string;
  mode: CopilotMode;
  log: CopilotLogEntry[];
  loading: boolean;
  evolving: boolean;
  evolutionFocus: string;
}
interface ExperimentRecord {
  experiment_id: string; idea_id?: string | null; name: string; dataset: string;
  hyperparams: Record<string, unknown>; results: Record<string, unknown>; notes?: string; timestamp: string;
}
interface ValidationRisk { level: 'high' | 'medium' | 'low' | string; type: string; message: string; }
interface ValidationChecklistGroup { label: string; items: string[]; present: boolean; missing_tip?: string; }
interface IdeaValidation {
  summary: string;
  collision_risk: { level: string; label: string; status: string; score?: number; reason: string; nearest_related_work?: { title?: string; paper_id?: string; source?: string } | null };
  related_work: { paper_id?: string; title: string; year?: number; source?: string; relation?: string; reason?: string }[];
  feasibility_risks: ValidationRisk[];
  experiment_checklist: Record<string, ValidationChecklistGroup>;
  writing_readiness: { status: 'ready' | 'needs_validation' | 'blocked' | string; label: string; reasons: string[] };
  coverage: { evidence_count: number; referenced_paper_count: number; experiment_completeness: number; has_enough_evidence: boolean };
  next_actions: string[];
}
interface ExperimentExecutionPack {
  idea_id: string;
  readiness: { status: string; label: string; score: number };
  summary: string;
  minimum_tasks: { key: string; label: string; status: 'ready' | 'missing' | string; detail: string }[];
  success_metrics: { name: string; target: string }[];
  feedback: { count: number; has_results: boolean; latest?: ExperimentRecord | null };
  risks: { level: string; message: string }[];
  next_actions: string[];
}
interface TimelineEvent {
  id: string;
  type: string;
  title: string;
  summary: string;
  timestamp: string;
  severity: 'success' | 'warning' | 'danger' | 'info' | string;
  tags: string[];
  details: Record<string, any>;
}
interface IdeaTimeline {
  idea_id: string;
  project_id: string;
  title: string;
  summary: { event_count: number; discussion_milestones: number; experiment_count: number; child_version_count: number; latest_event_type?: string };
  events: TimelineEvent[];
}
interface ProposalBoardItem {
  idea_id: string;
  title: string;
  status: string;
  label: string;
  priority: number;
  manual_status: string;
  recommended_action: { type: string; label: string; target: string };
  blockers: string[];
  signals: {
    review_score?: number;
    evidence_count?: number;
    experiment_completeness?: number;
    writing_readiness?: string;
    collision_level?: string;
    execution_status?: string;
    experiment_feedback_count?: number;
    has_experiment_results?: boolean;
    discussion_turns?: number;
    evolution_round?: number;
    proposal_review_readiness?: string;
    review_objection_count?: number;
    has_child_versions?: boolean;
  };
  summary: string;
  created_at: string;
}
interface ProposalBoardGroup {
  status: string;
  label: string;
  count: number;
  items: ProposalBoardItem[];
}
interface ProposalBoard {
  project_id: string;
  summary: { total: number; actionable: number; recommended?: string | null; counts: Record<string, number> };
  groups: ProposalBoardGroup[];
}
interface ProposalVersionSnapshot {
  id: string;
  title: string;
  status: string;
  hypothesis?: string | null;
  approach?: string | null;
  experiment_plan?: ExperimentPlan | Record<string, any>;
  evidence_count?: number;
  review_score?: number;
  proposal_review?: ProposalReviewPackage | null;
  evolution?: Record<string, any>;
}
interface ProposalVersionChange {
  field: string;
  label: string;
  before: any;
  after: any;
}
interface ProposalVersionComparison {
  idea_id: string;
  parent_idea_id?: string;
  has_parent: boolean;
  current: ProposalVersionSnapshot;
  parent?: ProposalVersionSnapshot | null;
  changes: ProposalVersionChange[];
  revision_rationale?: string | null;
  review_source?: {
    source?: string | null;
    review_focus?: string | null;
    review_objections?: string[];
    required_experiments?: string[];
  };
}
interface IdeaRun {
  id: string; project_id: string; status: string; stage: string; progress: number;
  message?: string; error?: string; evidence_map?: Record<string, Evidence[] | string | object>;
  gap_map?: { summary?: string; gaps?: Gap[] }; candidate_pool?: Candidate[];
  config_json?: { gap_selection?: GapSelection; generation_constraints?: GenerationConstraints; [key: string]: unknown };
  review_summary?: Record<string, unknown>; ideas?: Idea[];
}
interface GapSelection {
  selected_gap_titles?: string[];
  blocked_gap_titles?: string[];
  focus_note?: string;
  selection_mode?: string;
}
interface GenerationConstraints {
  research_mode?: 'balanced' | 'theory' | 'experiment' | 'system' | 'application';
  risk_appetite?: 'conservative' | 'balanced' | 'high_risk';
  resource_budget?: 'low_compute' | 'reproducible' | 'large_model';
}

const stageItems = [
  ['briefing', '研究简报'], ['retrieving', '证据收集'], ['mapping_gaps', 'Gap Map'],
  ['gap_review', '选择 Gap'], ['generating', '候选生成'], ['deduplicating', '语义去重'], ['reviewing', '六维评审'],
  ['selecting', 'Proposal'], ['complete', '完成'],
];
const scoreLabels: Record<string, string> = {
  novelty: '新颖性', evidence_grounding: '证据支撑', feasibility: '可行性',
  testability: '可验证性', impact: '潜在价值', clarity: '清晰度',
};
const categoryLabels = { seed: '核心论文', background: '背景论文', inspiration: '灵感论文' };
const categoryColors = { seed: 'purple', background: 'blue', inspiration: 'cyan' };
const pathLabels: Record<string, string> = { grounded: 'Gap 推导', inspiration: '跨论文启发', seed_refinement: '种子优化' };
const sourceLabels: Record<string, string> = { local_library: '本地论文库', arxiv: 'arXiv', semantic_scholar: 'Semantic Scholar' };
const statusLabels: Record<string, string> = { draft: '待筛选', pinned: '已收藏', rejected: '已淘汰', implemented: '已有代码' };
const runStatusLabels: Record<string, string> = { pending: '等待中', running: '生成中', complete: '已完成', failed: '失败', cancelled: '已停止' };
const runStatusColors: Record<string, string> = { pending: 'default', running: 'processing', complete: 'green', failed: 'red', cancelled: 'orange' };
const researchModeOptions = [
  { value: 'balanced', label: '均衡' },
  { value: 'theory', label: '偏理论' },
  { value: 'experiment', label: '偏实验' },
  { value: 'system', label: '偏系统' },
  { value: 'application', label: '偏应用' },
] as const;
const riskAppetiteOptions = [
  { value: 'conservative', label: '保守增量' },
  { value: 'balanced', label: '中等创新' },
  { value: 'high_risk', label: '高风险高收益' },
] as const;
const resourceBudgetOptions = [
  { value: 'low_compute', label: '低算力' },
  { value: 'reproducible', label: '可复现' },
  { value: 'large_model', label: '大模型实验' },
] as const;
const gapRatingOptions = [
  { value: 'strong', label: '强价值' },
  { value: 'promising', label: '可推进' },
  { value: 'weak', label: '偏弱' },
  { value: 'reject', label: '不推进' },
] as const;
const gapRatingColors: Record<GapFeedbackRating, string> = { strong: 'green', promising: 'blue', weak: 'orange', reject: 'red' };
const gapLabelOptions = [
  { value: 'valuable', label: '有价值' },
  { value: 'too_broad', label: '太宽泛' },
  { value: 'evidence_weak', label: '证据不足' },
  { value: 'already_done', label: '可能已做过' },
  { value: 'misaligned', label: '不符合方向' },
  { value: 'needs_narrowing', label: '需要收窄' },
  { value: 'high_potential', label: '高潜力' },
] as const;
const gapLabelMap = Object.fromEntries(gapLabelOptions.map(item => [item.value, item.label])) as Record<GapFeedbackLabel, string>;
const gapToDraft = (gap: Gap): GapFeedbackDraft => ({
  title: gap.title || '',
  limitation: gap.limitation || '',
  opportunity: gap.opportunity || '',
  research_question: gap.research_question || '',
  uncertainty: gap.uncertainty || '',
  evidence_rationale: gap.evidence_rationale || '',
  evidence_ids: gap.evidence_ids || [],
  rating: gap.user_feedback?.rating || 'promising',
  labels: gap.user_feedback?.labels || [],
  note: gap.user_feedback?.note || '',
});
type ProposalSortKey = 'review' | 'novelty' | 'feasibility' | 'evidence' | 'recent';
type ProposalFilterKey = 'all' | 'draft' | 'pinned' | 'rejected' | 'implemented';
const proposalSortOptions: { value: ProposalSortKey; label: string }[] = [
  { value: 'review', label: '综合评分优先' },
  { value: 'novelty', label: '新颖性优先' },
  { value: 'feasibility', label: '可行性优先' },
  { value: 'evidence', label: '证据数量优先' },
  { value: 'recent', label: '最新生成优先' },
];
const proposalFilterOptions: { value: ProposalFilterKey; label: string }[] = [
  { value: 'all', label: '全部' },
  { value: 'draft', label: '待筛选' },
  { value: 'pinned', label: '已收藏' },
  { value: 'rejected', label: '已淘汰' },
  { value: 'implemented', label: '已有代码' },
];
const noveltyLabels: Record<string, string> = { likely_novel: '可能新颖', incremental: '增量改进', too_similar: '过于相似' };
const noveltyColors: Record<string, string> = { likely_novel: 'green', incremental: 'gold', too_similar: 'red' };
const adversarialLabels: Record<string, string> = { advance: '建议推进', revise: '需要修改', reject: '暂不推进' };
const adversarialColors: Record<string, string> = { advance: 'green', revise: 'orange', reject: 'red' };
const readinessColors: Record<string, string> = { ready: 'green', needs_validation: 'orange', needs_revision: 'orange', blocked: 'red' };
const proposalReviewReadinessLabels: Record<string, string> = { ready: '可进入写作', needs_revision: '需要修订', blocked: '暂不推进' };
const executionReadinessColors: Record<string, string> = { ready: 'green', needs_setup: 'orange', needs_iteration: 'purple' };
const riskColors: Record<string, string> = { high: 'red', medium: 'orange', low: 'green' };
const timelineTypeLabels: Record<string, string> = {
  created: '创建',
  evolution: '演化来源',
  proposal_review: '审稿包',
  validation: '验证',
  execution: '实验推进',
  discussion: 'Copilot',
  experiment: '实验反馈',
  child_version: '下一版',
};
const timelineSeverityColors: Record<string, string> = {
  success: 'green',
  warning: 'orange',
  danger: 'red',
  info: 'blue',
};
const proposalBoardStatusColors: Record<string, string> = {
  needs_evidence: 'orange',
  needs_experiment_design: 'gold',
  ready_for_experiment: 'blue',
  needs_evolution: 'purple',
  ready_for_writing: 'green',
  review_revision: 'volcano',
  draft_review: 'default',
  implemented: 'cyan',
  rejected: 'red',
};
const copilotModeOptions: { value: CopilotMode; label: string }[] = [
  { value: 'mentor', label: '导师' },
  { value: 'skeptic', label: '审稿人' },
  { value: 'experiment_designer', label: '实验设计' },
  { value: 'writer', label: '写作顾问' },
];
const copilotQuickPrompts: Record<CopilotMode, string[]> = {
  mentor: ['帮我把这个 Proposal 收敛成一个可证伪假设', '下一版最该改进哪一点？', '这个方向最适合先做哪个低成本验证？'],
  skeptic: ['请像严格审稿人一样攻击 novelty 和实验风险', '这个想法最可能和哪些已有工作撞车？', '列出必须修复的三个审稿质疑'],
  experiment_designer: ['设计第一轮最小实验、强基线和消融', '如何定义成功指标和失败判定？', '把实验步骤拆成可执行清单'],
  writer: ['把这个 idea 整理成论文贡献点', 'related work 应该如何组织？', '哪些 claim 现在还不能写？'],
};

const proposalEvidenceCount = (idea: Idea) => idea.evidence_json?.items?.length || 0;
const proposalReviewScore = (idea: Idea) =>
  idea.review_json?.aggregate_score
  ?? (((idea.novelty_score || 0) + (idea.feasibility_score || 0)) / 2);
const proposalSortValue = (idea: Idea, sortKey: ProposalSortKey) => {
  if (sortKey === 'novelty') return idea.novelty_score || 0;
  if (sortKey === 'feasibility') return idea.feasibility_score || 0;
  if (sortKey === 'evidence') return proposalEvidenceCount(idea);
  if (sortKey === 'recent') return idea.created_at ? new Date(idea.created_at).getTime() : 0;
  return proposalReviewScore(idea);
};
const proposalDecisionCounts = (items: Idea[]) => ({
  all: items.length,
  draft: items.filter(idea => idea.status === 'draft').length,
  pinned: items.filter(idea => idea.status === 'pinned').length,
  rejected: items.filter(idea => idea.status === 'rejected').length,
  implemented: items.filter(idea => idea.status === 'implemented').length,
});
const normalizeCodeProjectFiles = (projectPackage: CodeProjectManifest) =>
  [...(projectPackage.files || [])].sort((first, second) => first.path.localeCompare(second.path));
const codeProjectDefaultFilePath = (projectPackage: CodeProjectManifest) => {
  const files = normalizeCodeProjectFiles(projectPackage);
  return (
    files.find(file => file.path.toLowerCase() === 'readme.md')?.path
    || files.find(file => projectPackage.entrypoints?.some(entrypoint => entrypoint.path === file.path))?.path
    || files[0]?.path
    || ''
  );
};
const codeProjectLineCount = (content = '') => content.length === 0 ? 0 : content.split(/\r\n|\r|\n/).length;
const codeProjectFolderGroups = (projectPackage: CodeProjectManifest): CodeProjectFolderGroup[] => {
  const groups = new Map<string, CodeProjectFile[]>();
  normalizeCodeProjectFiles(projectPackage).forEach(file => {
    const parts = file.path.split('/');
    const folder = parts.length > 1 ? parts.slice(0, -1).join('/') : '根目录';
    groups.set(folder, [...(groups.get(folder) || []), file]);
  });
  return Array.from(groups.entries()).map(([folder, files]) => ({ folder, files }));
};
interface CodeProjectHistoryState {
  loading: boolean;
  versions: CodeProjectVersionSummary[];
  selectedVersion?: number | 'latest';
  selectedDetail?: CodeProjectVersionDetail;
  compareFrom?: number;
  compareTo?: number;
  comparing: boolean;
  comparison?: CodeProjectVersionCompare;
  selectedDiffPath?: string;
}

const ResearchProjectPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [ideas, setIdeas] = useState<Idea[]>([]);
  const [run, setRun] = useState<IdeaRun | null>(null);
  const [generating, setGenerating] = useState(false);
  const generationAbortRef = useRef<AbortController | null>(null);
  const generationCancelRequestedRef = useRef(false);
  const [relatedPapers, setRelatedPapers] = useState<any[]>([]);
  const [papersLoading, setPapersLoading] = useState(false);
  const [papersCached, setPapersCached] = useState(false);
  const [papersRefreshedAt, setPapersRefreshedAt] = useState<string | null>(null);
  const [discussMap, setDiscussMap] = useState<Record<string, CopilotState>>({});
  const [copilotIdea, setCopilotIdea] = useState<Idea | null>(null);
  const [codeMap, setCodeMap] = useState<Record<string, { loading: boolean }>>({});
  const [codeProjectSelectedFile, setCodeProjectSelectedFile] = useState<Record<string, string>>({});
  const [codeProjectHistoryMap, setCodeProjectHistoryMap] = useState<Record<string, CodeProjectHistoryState>>({});
  const [externalSearch, setExternalSearch] = useState(true);
  const [selectedIdeaIds, setSelectedIdeaIds] = useState<string[]>([]);
  const [proposalSort, setProposalSort] = useState<ProposalSortKey>('review');
  const [proposalFilter, setProposalFilter] = useState<ProposalFilterKey>('all');
  const [compareIdeas, setCompareIdeas] = useState<Idea[]>([]);
  const [compareOpen, setCompareOpen] = useState(false);
  const [evolvingIdea, setEvolvingIdea] = useState<Idea | null>(null);
  const [evolutionFocus, setEvolutionFocus] = useState('');
  const [evolving, setEvolving] = useState(false);
  const [reviewingIdeaIds, setReviewingIdeaIds] = useState<Set<string>>(new Set());
  const [reviewRevisionIdea, setReviewRevisionIdea] = useState<Idea | null>(null);
  const [reviewRevisionFocus, setReviewRevisionFocus] = useState('');
  const [reviewRevisionLoading, setReviewRevisionLoading] = useState(false);
  const [versionComparisonOpen, setVersionComparisonOpen] = useState(false);
  const [versionComparisonIdea, setVersionComparisonIdea] = useState<Idea | null>(null);
  const [versionComparisonLoading, setVersionComparisonLoading] = useState(false);
  const [versionComparison, setVersionComparison] = useState<ProposalVersionComparison | null>(null);
  const [importingEvidence, setImportingEvidence] = useState<Set<string>>(new Set());
  const [draftingIdeaIds, setDraftingIdeaIds] = useState<Set<string>>(new Set());
  const [experiments, setExperiments] = useState<ExperimentRecord[]>([]);
  const [experimentOpen, setExperimentOpen] = useState(false);
  const [experimentIdea, setExperimentIdea] = useState<Idea | null>(null);
  const [experimentName, setExperimentName] = useState('');
  const [experimentDataset, setExperimentDataset] = useState('');
  const [experimentResults, setExperimentResults] = useState('');
  const [experimentNotes, setExperimentNotes] = useState('');
  const [lineageOpen, setLineageOpen] = useState(false);
  const [lineage, setLineage] = useState<Idea[]>([]);
  const [timelineOpen, setTimelineOpen] = useState(false);
  const [timelineIdea, setTimelineIdea] = useState<Idea | null>(null);
  const [timelineLoading, setTimelineLoading] = useState(false);
  const [timelineData, setTimelineData] = useState<IdeaTimeline | null>(null);
  const [proposalBoard, setProposalBoard] = useState<ProposalBoard | null>(null);
  const [proposalBoardLoading, setProposalBoardLoading] = useState(false);
  const [validationMap, setValidationMap] = useState<Record<string, { loading: boolean; data?: IdeaValidation }>>({});
  const [executionPackMap, setExecutionPackMap] = useState<Record<string, { loading: boolean; data?: ExperimentExecutionPack }>>({});
  const [activeWorkbenchTab, setActiveWorkbenchTab] = useState('evidence');
  const [gapPreviewing, setGapPreviewing] = useState(false);
  const [gapContinuing, setGapContinuing] = useState(false);
  const [selectedGapTitles, setSelectedGapTitles] = useState<string[]>([]);
  const [blockedGapTitles, setBlockedGapTitles] = useState<string[]>([]);
  const [gapFocusNote, setGapFocusNote] = useState('');
  const [gapDrafts, setGapDrafts] = useState<Record<number, GapFeedbackDraft>>({});
  const [savingGapFeedback, setSavingGapFeedback] = useState<Set<number>>(new Set());
  const [refiningGaps, setRefiningGaps] = useState<Set<number>>(new Set());
  const [gapRefineNotes, setGapRefineNotes] = useState<Record<number, string>>({});
  const [researchMode, setResearchMode] = useState<GenerationConstraints['research_mode']>('balanced');
  const [riskAppetite, setRiskAppetite] = useState<GenerationConstraints['risk_appetite']>('balanced');
  const [resourceBudget, setResourceBudget] = useState<GenerationConstraints['resource_budget']>('reproducible');
  const [pageActionError, setPageActionError] = useState<{ title: string; detail: ApiErrorDetails } | null>(null);

  const showPageError = (title: string, error: unknown, fallback = title) => {
    const detail = getApiErrorDetails(error, { fallback });
    setPageActionError({ title, detail });
    message.warning(detail.message);
  };
  const copyCodeProjectText = async (text: string, successMessage = '已复制') => {
    await navigator.clipboard.writeText(text);
    message.success(successMessage);
  };
  const updateCodeProjectHistory = (ideaId: string, patch: Partial<CodeProjectHistoryState>) => {
    setCodeProjectHistoryMap(previous => ({
      ...previous,
      [ideaId]: {
        ...previous[ideaId],
        loading: previous[ideaId]?.loading ?? false,
        versions: previous[ideaId]?.versions ?? [],
        comparing: previous[ideaId]?.comparing ?? false,
        ...patch,
      },
    }));
  };
  const loadCodeProjectVersions = async (ideaId: string) => {
    updateCodeProjectHistory(ideaId, { loading: true });
    try {
      const response = await api.get(`/research/ideas/${ideaId}/code-project/versions`);
      const versions = response.data as CodeProjectVersionSummary[];
      updateCodeProjectHistory(ideaId, {
        loading: false,
        versions,
        compareFrom: versions[1]?.version ?? versions[0]?.version,
        compareTo: versions[0]?.version,
      });
      setPageActionError(null);
    } catch (error) {
      updateCodeProjectHistory(ideaId, { loading: false });
      showPageError('加载实验项目版本失败', error, '加载实验项目版本失败');
    }
  };
  const selectCodeProjectVersion = async (idea: Idea, version: number | 'latest') => {
    if (version === 'latest') {
      updateCodeProjectHistory(idea.id, { selectedVersion: 'latest', selectedDetail: undefined });
      if (idea.generated_code_project) {
        setCodeProjectSelectedFile(previous => ({ ...previous, [idea.id]: codeProjectDefaultFilePath(idea.generated_code_project!) }));
      }
      return;
    }
    updateCodeProjectHistory(idea.id, { selectedVersion: version, loading: true });
    try {
      const response = await api.get(`/research/ideas/${idea.id}/code-project/versions/${version}`);
      const detail = response.data as CodeProjectVersionDetail;
      updateCodeProjectHistory(idea.id, { selectedVersion: version, selectedDetail: detail, loading: false });
      setCodeProjectSelectedFile(previous => ({ ...previous, [idea.id]: codeProjectDefaultFilePath(detail.code_project) }));
      setPageActionError(null);
    } catch (error) {
      updateCodeProjectHistory(idea.id, { loading: false });
      showPageError('加载实验项目版本详情失败', error, '加载实验项目版本详情失败');
    }
  };
  const compareCodeProjectVersions = async (ideaId: string) => {
    const history = codeProjectHistoryMap[ideaId];
    if (!history?.compareFrom || !history.compareTo || history.compareFrom === history.compareTo) {
      message.warning('请选择两个不同版本进行比较');
      return;
    }
    updateCodeProjectHistory(ideaId, { comparing: true });
    try {
      const response = await api.get(`/research/ideas/${ideaId}/code-project/versions/compare`, {
        params: { from_version: history.compareFrom, to_version: history.compareTo },
      });
      const comparison = response.data as CodeProjectVersionCompare;
      const selectedDiffPath = comparison.files.find(file => file.status === 'modified')?.path
        || comparison.files.find(file => file.status !== 'unchanged')?.path
        || comparison.files[0]?.path;
      updateCodeProjectHistory(ideaId, { comparing: false, comparison, selectedDiffPath });
      setPageActionError(null);
    } catch (error) {
      updateCodeProjectHistory(ideaId, { comparing: false });
      showPageError('比较实验项目版本失败', error, '比较实验项目版本失败');
    }
  };

  const loadProject = async () => {
    if (!projectId) return;
    const response = await api.get(`/research/projects/${projectId}`);
    setProject(response.data);
    setIdeas(response.data.ideas || []);
  };
  const loadRelatedPapers = async (id: string, refresh = false) => {
    setPapersLoading(true);
    try {
      const response = await api.get(`/research/projects/${id}/recommended-papers`, { params: { refresh: refresh || undefined } });
      const payload = Array.isArray(response.data)
        ? { items: response.data, cached: false, refreshed_at: null }
        : response.data;
      setRelatedPapers(((payload.items || []) as any[]).map(p => ({ ...p, similarity: p.score })));
      setPapersCached(!!payload.cached);
      setPapersRefreshedAt(payload.refreshed_at || null);
    } catch {
      setRelatedPapers([]);
      setPapersCached(false);
      setPapersRefreshedAt(null);
    } finally {
      setPapersLoading(false);
    }
  };
  const loadProposalBoard = async (id = projectId) => {
    if (!id) return;
    setProposalBoardLoading(true);
    try {
      const response = await api.get(`/research/projects/${id}/proposal-board`);
      setProposalBoard(response.data);
      setPageActionError(null);
    } catch (error) {
      showPageError('加载 Proposal 推进看板失败', error, '加载 Proposal 推进看板失败');
    } finally {
      setProposalBoardLoading(false);
    }
  };

  useEffect(() => {
    if (!projectId) return;
    setLoading(true);
    setRelatedPapers([]);
    setPapersCached(false);
    setPapersRefreshedAt(null);
    loadRelatedPapers(projectId);
    Promise.all([
      loadProject(),
      loadProposalBoard(projectId),
      api.get(`/research/projects/${projectId}/idea-runs/latest`).then(response => setRun(response.data)).catch(() => {}),
      api.get(`/research/projects/${projectId}/experiments`).then(response => setExperiments(response.data)).catch(() => {}),
    ]).then(() => setPageActionError(null)).catch(error => showPageError('加载研究工作台失败', error, '加载研究工作台失败')).finally(() => setLoading(false));
  }, [projectId]);

  useEffect(() => {
    const gapTitles = run?.gap_map?.gaps?.map(gap => gap.title).filter(Boolean) || [];
    if (gapTitles.length === 0) {
      setSelectedGapTitles([]);
      setBlockedGapTitles([]);
      setGapDrafts({});
      return;
    }
    const savedSelection = run?.config_json?.gap_selection;
    setSelectedGapTitles(savedSelection?.selected_gap_titles?.filter(title => gapTitles.includes(title)) || gapTitles);
    setBlockedGapTitles(savedSelection?.blocked_gap_titles?.filter(title => gapTitles.includes(title)) || []);
    setGapFocusNote(savedSelection?.focus_note || '');
    const savedConstraints = run?.config_json?.generation_constraints || {};
    setResearchMode(savedConstraints.research_mode || 'balanced');
    setRiskAppetite(savedConstraints.risk_appetite || 'balanced');
    setResourceBudget(savedConstraints.resource_budget || 'reproducible');
    setGapDrafts(Object.fromEntries((run?.gap_map?.gaps || []).map((gap, index) => [index, gapToDraft(gap)])));
  }, [run?.id, run?.gap_map]);

  const applyStreamEvent = (event: any) => {
    if (event.type === 'run' && event.run) setRun(event.run);
    if (event.type === 'stage') {
      setRun(previous => previous ? { ...previous, stage: event.stage, status: event.status, progress: event.progress, message: event.message } : previous);
    }
    if (event.type === 'artifact') {
      setRun(previous => previous ? { ...previous, [event.artifact]: event.data } : previous);
    }
    if (event.type === 'error') showPageError('Idea 工作台运行失败', event, event.message || 'Idea 工作台运行失败');
    if (event.type === 'done' && event.run) {
      setRun(event.run);
      setIdeas(event.ideas || event.run.ideas || []);
    }
    if (event.type === 'cancelled' && event.run) setRun(event.run);
  };

  const handleGenerate = async () => {
    if (!projectId || generating) return;
    generationCancelRequestedRef.current = false;
    const controller = new AbortController();
    generationAbortRef.current = controller;
    setGenerating(true);
    try {
      const token = localStorage.getItem('access_token');
      let finalRunStatus: string | null = null;
      let finalRunError: string | null = null;
      const response = await fetch(`/api/research/projects/${projectId}/idea-runs/stream`, {
        method: 'POST',
        signal: controller.signal,
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ num_ideas: 3, external_search: externalSearch }),
      });
      if (!response.ok || !response.body) throw new Error('无法启动 Idea 工作台');
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const packets = buffer.split('\n\n');
        buffer = packets.pop() || '';
        packets.forEach(packet => {
          const line = packet.split('\n').find(item => item.startsWith('data: '));
          if (line) {
            const event = JSON.parse(line.slice(6));
            applyStreamEvent(event);
            if ((event.type === 'done' || event.type === 'cancelled') && event.run) {
              finalRunStatus = event.run.status || null;
              finalRunError = event.run.error || null;
            }
          }
        });
      }
      await loadProject();
      await loadProposalBoard();
      if (!generationCancelRequestedRef.current && finalRunStatus === 'complete') {
        setActiveWorkbenchTab('proposal-board');
        setPageActionError(null);
        message.success('Idea 工作台已生成新的 Proposal');
      } else if (!generationCancelRequestedRef.current && finalRunStatus === 'failed') {
        showPageError('Idea 工作台运行失败', { message: finalRunError || 'Idea 工作台运行失败' }, finalRunError || 'Idea 工作台运行失败');
      }
    } catch (error: any) {
      if (!generationCancelRequestedRef.current && error?.name !== 'AbortError') {
        showPageError('生成失败', error, error?.message || '生成失败');
      }
    } finally {
      setGenerating(false);
      generationAbortRef.current = null;
      generationCancelRequestedRef.current = false;
    }
  };

  const handleGapPreview = async () => {
    if (!projectId || gapPreviewing || generating) return;
    setGapPreviewing(true);
    try {
      const response = await api.post(`/research/projects/${projectId}/idea-runs/gap-preview`, {
        num_ideas: 3,
        external_search: externalSearch,
      });
      setRun(response.data);
      setActiveWorkbenchTab('gaps');
      setPageActionError(null);
      message.success('Gap Map 已生成，可以先选择要推进的研究空白');
    } catch (error) {
      showPageError('Gap Map 预览失败', error, 'Gap Map 预览失败');
    } finally {
      setGapPreviewing(false);
    }
  };

  const handleContinueFromGaps = async () => {
    if (!projectId || !run?.id || gapContinuing) return;
    setGapContinuing(true);
    try {
      const response = await api.post(`/research/projects/${projectId}/idea-runs/${run.id}/continue-from-gaps`, {
        num_ideas: 3,
        gap_selection: {
          selected_gap_titles: selectedGapTitles,
          blocked_gap_titles: blockedGapTitles,
          focus_note: gapFocusNote,
        },
        generation_constraints: {
          research_mode: researchMode,
          risk_appetite: riskAppetite,
          resource_budget: resourceBudget,
        },
      });
      setRun(response.data);
      setIdeas(response.data.ideas || []);
      await loadProject();
      await loadProposalBoard();
      setActiveWorkbenchTab('proposal-board');
      setPageActionError(null);
      message.success('已按选择的 Gap Map 生成 Proposal');
    } catch (error) {
      showPageError('按 Gap Map 继续生成失败', error, '按 Gap Map 继续生成失败');
    } finally {
      setGapContinuing(false);
    }
  };

  const updateGapDraft = (index: number, patch: Partial<GapFeedbackDraft>) => {
    setGapDrafts(previous => ({
      ...previous,
      [index]: { ...(previous[index] || gapToDraft(gaps[index])), ...patch },
    }));
  };

  const handleSaveGapFeedback = async (index: number) => {
    if (!projectId || !run?.id || savingGapFeedback.has(index)) return;
    const draft = gapDrafts[index] || gapToDraft(gaps[index]);
    setSavingGapFeedback(previous => new Set(previous).add(index));
    try {
      const response = await api.patch(`/research/projects/${projectId}/idea-runs/${run.id}/gaps/${index}/feedback`, draft);
      setRun(response.data);
      setPageActionError(null);
      message.success('Gap 反馈已保存');
    } catch (error) {
      showPageError('保存 Gap 反馈失败', error, '保存 Gap 反馈失败');
    } finally {
      setSavingGapFeedback(previous => {
        const next = new Set(previous); next.delete(index); return next;
      });
    }
  };

  const handleRefineGap = async (index: number) => {
    if (!projectId || !run?.id || refiningGaps.has(index)) return;
    setRefiningGaps(previous => new Set(previous).add(index));
    try {
      const response = await api.post(`/research/projects/${projectId}/idea-runs/${run.id}/gaps/${index}/refine`, {
        focus_note: gapRefineNotes[index] || '',
      });
      setRun(response.data);
      setPageActionError(null);
      message.success('Gap 已细化');
    } catch (error) {
      showPageError('细化 Gap 失败', error, '细化 Gap 失败');
    } finally {
      setRefiningGaps(previous => {
        const next = new Set(previous); next.delete(index); return next;
      });
    }
  };

  const handleStopGeneration = async () => {
    if (!projectId || !generating) return;
    generationCancelRequestedRef.current = true;
    generationAbortRef.current?.abort();
    setGenerating(false);
    if (run?.id) {
      try {
        const response = await api.post(`/research/projects/${projectId}/idea-runs/${run.id}/cancel`);
        setRun(response.data);
      } catch {
        setRun(previous => previous ? { ...previous, status: 'cancelled', message: '已停止生成候选 Proposal', error: undefined } : previous);
      }
    }
    message.info('已停止生成候选 Proposal');
  };

  const defaultDiscussState = (ideaId: string): CopilotState => {
    const idea = ideas.find(item => item.id === ideaId);
    return {
      msg: '',
      mode: 'mentor',
      log: idea?.discussion_log || [],
      loading: false,
      evolving: false,
      evolutionFocus: '',
      risks: [],
      next_actions: [],
      suggested_questions: [],
      evolution_focus: '',
      context_summary: undefined,
    };
  };
  const getDiscuss = (ideaId: string): CopilotState => discussMap[ideaId] || defaultDiscussState(ideaId);
  const setDiscuss = (ideaId: string, update: Partial<CopilotState>) => setDiscussMap(previous => ({
    ...previous, [ideaId]: { ...(previous[ideaId] || defaultDiscussState(ideaId)), ...update },
  }));
  const openCopilot = (idea: Idea) => {
    setDiscuss(idea.id, { log: getDiscuss(idea.id).log.length ? getDiscuss(idea.id).log : idea.discussion_log || [] });
    setCopilotIdea(idea);
  };
  const applyQuickPrompt = (text: string) => {
    if (!copilotIdea) return;
    setDiscuss(copilotIdea.id, { msg: text });
  };
  const handleDiscuss = async (ideaId: string) => {
    const current = getDiscuss(ideaId);
    if (!current.msg.trim()) return;
    setDiscuss(ideaId, { loading: true });
    const log: CopilotLogEntry[] = [...current.log, { role: 'user', content: current.msg, mode: current.mode }];
    setDiscuss(ideaId, { msg: '', log });
    try {
      const response = await api.post(`/research/ideas/${ideaId}/discuss`, { message: current.msg, mode: current.mode });
      const assistantEntry: CopilotLogEntry = {
        role: 'assistant',
        content: response.data.reply,
        mode: response.data.mode,
        metadata: {
          context_summary: response.data.context_summary,
          risks: response.data.risks || [],
          next_actions: response.data.next_actions || [],
          suggested_questions: response.data.suggested_questions || [],
          evolution_focus: response.data.evolution_focus || '',
        },
      };
      setDiscuss(ideaId, {
        log: response.data.discussion_log || [...log, assistantEntry],
        context_summary: response.data.context_summary,
        risks: response.data.risks || [],
        next_actions: response.data.next_actions || [],
        suggested_questions: response.data.suggested_questions || [],
        evolution_focus: response.data.evolution_focus || '',
        evolutionFocus: response.data.evolution_focus || getDiscuss(ideaId).evolutionFocus,
      });
      setIdeas(previous => previous.map(idea => idea.id === ideaId ? { ...idea, discussion_log: response.data.discussion_log || [...log, assistantEntry] } : idea));
      setPageActionError(null);
    } catch (error) { showPageError('讨论失败', error, '讨论失败'); }
    finally { setDiscuss(ideaId, { loading: false }); }
  };
  const evolveFromCopilot = async (ideaId: string) => {
    const current = getDiscuss(ideaId);
    setDiscuss(ideaId, { evolving: true });
    try {
      const focus = current.evolutionFocus || current.evolution_focus || '';
      const response = await api.post(`/research/ideas/${ideaId}/discuss/evolve`, { focus });
      setIdeas(previous => [response.data, ...previous]);
      setCopilotIdea(response.data);
      loadProposalBoard();
      setPageActionError(null);
      message.success('已根据 Copilot 讨论生成下一版 Proposal');
    } catch (error) { showPageError('根据 Copilot 讨论演化失败', error, '根据 Copilot 讨论演化失败'); }
    finally { setDiscuss(ideaId, { evolving: false }); }
  };
  const handleGenCode = async (ideaId: string) => {
    setCodeMap(previous => ({ ...previous, [ideaId]: { loading: true } }));
    try {
      const response = await api.post(`/research/ideas/${ideaId}/generate-code?framework=pytorch`);
      const projectPackage = response.data.code_project as CodeProjectManifest | undefined;
      const defaultPath = projectPackage ? codeProjectDefaultFilePath(projectPackage) : '';
      if (defaultPath) {
        setCodeProjectSelectedFile(previous => ({ ...previous, [ideaId]: defaultPath }));
      }
      setIdeas(previous => previous.map(idea => idea.id === ideaId ? { ...idea, generated_code: response.data.code, generated_code_project: projectPackage || null, status: 'implemented' } : idea));
      updateCodeProjectHistory(ideaId, {
        selectedVersion: 'latest',
        selectedDetail: undefined,
        comparison: undefined,
        selectedDiffPath: undefined,
      });
      loadCodeProjectVersions(ideaId);
      setPageActionError(null);
      message.success('实验项目包已生成');
    } catch (error) { showPageError('实验项目包生成失败', error, '实验项目包生成失败'); }
    finally { setCodeMap(previous => ({ ...previous, [ideaId]: { loading: false } })); }
  };
  const downloadCodeProject = async (idea: Idea) => {
    try {
      const response = await api.get(`/research/ideas/${idea.id}/code-project/download`, { responseType: 'blob' });
      const blob = new Blob([response.data], { type: 'application/zip' });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = `${idea.generated_code_project?.name || idea.title || 'research-code-project'}.zip`;
      anchor.click();
      URL.revokeObjectURL(url);
      setPageActionError(null);
    } catch (error) {
      showPageError('下载实验项目包失败', error, '下载实验项目包失败');
    }
  };
  const createWritingDraft = async (idea: Idea) => {
    setDraftingIdeaIds(previous => new Set(previous).add(idea.id));
    try {
      const response = await api.post(`/research/ideas/${idea.id}/writing-draft`);
      const projectId = response.data.project?.id;
      setPageActionError(null);
      message.success(response.data.evidence_status === 'sufficient' ? '写作草稿已创建' : '写作草稿已创建，但证据不足');
      if (projectId) navigate(`/writing?project=${projectId}`);
    } catch (error) {
      showPageError('创建写作草稿失败', error, '创建写作草稿失败');
    } finally {
      setDraftingIdeaIds(previous => {
        const next = new Set(previous);
        next.delete(idea.id);
        return next;
      });
    }
  };
  const handleShare = async () => {
    try {
      const response = await api.post(`/research/projects/${projectId}/share`);
      await navigator.clipboard.writeText(`${window.location.origin}/research/share/${response.data.share_token}`);
      setPageActionError(null);
      message.success('分享链接已复制');
    } catch (error) { showPageError('分享失败', error, '分享失败'); }
  };
  const updateDecision = async (ideaId: string, status: 'draft' | 'pinned' | 'rejected') => {
    try {
      const response = await api.patch(`/research/ideas/${ideaId}/decision`, { status });
      setIdeas(previous => previous.map(idea => idea.id === ideaId ? response.data : idea));
      loadProposalBoard();
      setPageActionError(null);
      message.success(status === 'pinned' ? '已收藏 Proposal' : status === 'rejected' ? '已标记为淘汰' : '已恢复为待筛选');
    } catch (error) { showPageError('更新 Proposal 状态失败', error, '更新 Proposal 状态失败'); }
  };
  const toggleCompare = (ideaId: string, checked: boolean) => {
    setSelectedIdeaIds(previous => checked ? [...previous, ideaId].slice(-4) : previous.filter(id => id !== ideaId));
  };
  const openComparison = async () => {
    if (selectedIdeaIds.length < 2) return message.info('请至少选择两个 Proposal');
    try {
      const response = await api.post('/research/ideas/compare', { idea_ids: selectedIdeaIds });
      setCompareIdeas(response.data);
      setCompareOpen(true);
      setPageActionError(null);
    } catch (error) { showPageError('加载 Proposal 比较失败', error, '加载 Proposal 比较失败'); }
  };
  const refreshProposalReviewPackage = async (idea: Idea) => {
    setReviewingIdeaIds(previous => new Set(previous).add(idea.id));
    try {
      const response = await api.post(`/research/ideas/${idea.id}/review-package`);
      const proposalReview = response.data as ProposalReviewPackage;
      setIdeas(previous => previous.map(item => item.id === idea.id ? {
        ...item,
        review_json: { ...(item.review_json || {}), proposal_review: proposalReview } as Review,
      } : item));
      if (copilotIdea?.id === idea.id) {
        setCopilotIdea(previous => previous ? { ...previous, review_json: { ...(previous.review_json || {}), proposal_review: proposalReview } as Review } : previous);
      }
      if (reviewRevisionIdea?.id === idea.id) {
        setReviewRevisionIdea(previous => previous ? { ...previous, review_json: { ...(previous.review_json || {}), proposal_review: proposalReview } as Review } : previous);
      }
      loadProposalBoard();
      setPageActionError(null);
      message.success('结构化审稿包已更新');
      return proposalReview;
    } catch (error) {
      showPageError('生成结构化审稿包失败', error, '生成结构化审稿包失败');
      return null;
    } finally {
      setReviewingIdeaIds(previous => {
        const next = new Set(previous);
        next.delete(idea.id);
        return next;
      });
    }
  };
  const openReviewRevision = async (idea: Idea) => {
    let proposalReview = idea.review_json?.proposal_review || null;
    if (!proposalReview) {
      proposalReview = await refreshProposalReviewPackage(idea);
      if (!proposalReview) return;
    }
    const currentIdea = ideas.find(item => item.id === idea.id) || idea;
    setReviewRevisionIdea({
      ...currentIdea,
      review_json: { ...(currentIdea.review_json || {}), proposal_review: proposalReview } as Review,
    });
    setReviewRevisionFocus(proposalReview.next_revision_focus || '');
  };
  const reviseFromReview = async () => {
    if (!reviewRevisionIdea) return;
    setReviewRevisionLoading(true);
    try {
      const response = await api.post(`/research/ideas/${reviewRevisionIdea.id}/revise-from-review`, { focus: reviewRevisionFocus });
      const child = response.data as Idea;
      setIdeas(previous => [child, ...previous.filter(item => item.id !== child.id)]);
      setReviewRevisionIdea(null);
      setReviewRevisionFocus('');
      setActiveWorkbenchTab('proposals');
      loadProposalBoard();
      setPageActionError(null);
      message.success('已根据审稿意见生成 Proposal 子版本');
    } catch (error) {
      showPageError('按审稿意见修订失败', error, '按审稿意见修订失败');
    } finally {
      setReviewRevisionLoading(false);
    }
  };
  const openVersionComparison = async (idea: Idea) => {
    setVersionComparisonIdea(idea);
    setVersionComparisonOpen(true);
    setVersionComparisonLoading(true);
    try {
      const response = await api.get(`/research/ideas/${idea.id}/version-comparison`);
      setVersionComparison(response.data as ProposalVersionComparison);
      setPageActionError(null);
    } catch (error) {
      setVersionComparison(null);
      showPageError('加载 Proposal 版本对比失败', error, '加载 Proposal 版本对比失败');
    } finally {
      setVersionComparisonLoading(false);
    }
  };
  const evolveProposal = async () => {
    if (!evolvingIdea) return;
    setEvolving(true);
    try {
      const response = await api.post(`/research/ideas/${evolvingIdea.id}/evolve`, { focus: evolutionFocus });
      setIdeas(previous => [response.data, ...previous]);
      setEvolvingIdea(null);
      setEvolutionFocus('');
      loadProposalBoard();
      setPageActionError(null);
      message.success('已生成一个可追溯的 Proposal 新版本');
    } catch (error) { showPageError('Proposal 演化失败', error, 'Proposal 演化失败'); }
    finally { setEvolving(false); }
  };
  const importEvidence = async (item: Evidence) => {
    if (!projectId || importingEvidence.has(item.paper_id)) return;
    setImportingEvidence(previous => new Set(previous).add(item.paper_id));
    try {
      const response = await api.post(`/research/projects/${projectId}/evidence/import`, { paper_id: item.paper_id });
      setRun(previous => {
        if (!previous?.evidence_map) return previous;
        const evidenceMap = { ...previous.evidence_map };
        (['seed', 'background', 'inspiration'] as const).forEach(category => {
          evidenceMap[category] = ((evidenceMap[category] as Evidence[]) || []).map(evidence =>
            evidence.paper_id === item.paper_id ? { ...evidence, imported_paper_id: response.data.local_paper_id } : evidence);
        });
        return { ...previous, evidence_map: evidenceMap };
      });
      setPageActionError(null);
      message.success(response.data.is_new ? '外部论文已入库并关联当前项目' : '论文已存在，已关联当前项目');
    } catch (error) { showPageError('外部论文入库失败', error, '外部论文入库失败'); }
    finally {
      setImportingEvidence(previous => {
        const next = new Set(previous); next.delete(item.paper_id); return next;
      });
    }
  };
  const openLineage = async (idea: Idea) => {
    try {
      const response = await api.get(`/research/ideas/${idea.id}/lineage`);
      setLineage(response.data);
      setLineageOpen(true);
      setPageActionError(null);
    } catch (error) { showPageError('加载演化谱系失败', error, '加载演化谱系失败'); }
  };
  const openTimeline = async (idea: Idea) => {
    setTimelineIdea(idea);
    setTimelineOpen(true);
    setTimelineLoading(true);
    try {
      const response = await api.get(`/research/ideas/${idea.id}/timeline`);
      setTimelineData(response.data);
      setPageActionError(null);
    } catch (error) {
      showPageError('加载迭代轨迹失败', error, '加载迭代轨迹失败');
      setTimelineData(null);
    } finally {
      setTimelineLoading(false);
    }
  };
  const handleBoardAction = (item: ProposalBoardItem) => {
    const idea = ideas.find(candidate => candidate.id === item.idea_id);
    if (!idea) return message.warning('Proposal 已不在当前列表中');
    const actionType = item.recommended_action.type;
    if (actionType === 'evidence') {
      setActiveWorkbenchTab('evidence');
      return;
    }
    if (actionType === 'execution') {
      setActiveWorkbenchTab('proposals');
      loadExecutionPack(idea.id);
      return;
    }
    if (actionType === 'experiment') {
      openExperiment(idea);
      return;
    }
    if (actionType === 'writing') {
      createWritingDraft(idea);
      return;
    }
    if (actionType === 'evolve' || actionType === 'copilot') {
      openCopilot(idea);
      return;
    }
    if (actionType === 'review_revision') {
      openReviewRevision(idea);
      return;
    }
    if (actionType === 'version_compare') {
      const latestChild = ideas
        .filter(candidate => candidate.parent_idea_id === idea.id)
        .sort((first, second) => (new Date(second.created_at || 0).getTime()) - (new Date(first.created_at || 0).getTime()))[0];
      openVersionComparison(latestChild || idea);
      return;
    }
    if (actionType === 'restore') {
      updateDecision(idea.id, 'draft');
      return;
    }
    openTimeline(idea);
  };
  const openExperiment = (idea: Idea) => {
    setExperimentIdea(idea);
    setExperimentName('');
    setExperimentDataset(idea.experiment_plan?.dataset || '');
    setExperimentResults('');
    setExperimentNotes('');
    setExperimentOpen(true);
  };
  const saveExperiment = async () => {
    if (!projectId || !experimentIdea || !experimentName.trim()) return message.info('请填写实验名称');
    let results: Record<string, unknown> = {};
    try { results = experimentResults.trim() ? JSON.parse(experimentResults) : {}; }
    catch { return message.error('实验结果请填写合法 JSON，例如 {"accuracy": 0.82}'); }
    try {
      const response = await api.post('/research/experiments', {
        project_id: projectId, idea_id: experimentIdea.id, name: experimentName,
        dataset: experimentDataset, results, notes: experimentNotes, hyperparams: {},
      });
      setExperiments(previous => [response.data.experiment, ...previous]);
      setExperimentOpen(false);
      loadProposalBoard();
      setPageActionError(null);
      message.success('实验反馈已记录');
    } catch (error) { showPageError('保存实验反馈失败', error, '保存实验反馈失败'); }
  };
  const evolveFromFeedback = async (experiment: ExperimentRecord) => {
    if (!experiment.idea_id) return;
    try {
      const response = await api.post(`/research/ideas/${experiment.idea_id}/evolve-from-feedback`, { experiment_id: experiment.experiment_id });
      setIdeas(previous => [response.data, ...previous]);
      loadProposalBoard();
      setPageActionError(null);
      message.success('已根据实验反馈生成下一轮 Proposal');
    } catch (error) { showPageError('根据实验反馈演化失败', error, '根据实验反馈演化失败'); }
  };
  const loadIdeaValidation = async (ideaId: string) => {
    setValidationMap(previous => ({ ...previous, [ideaId]: { ...previous[ideaId], loading: true } }));
    try {
      const response = await api.get(`/research/ideas/${ideaId}/validation`);
      setValidationMap(previous => ({ ...previous, [ideaId]: { loading: false, data: response.data } }));
      setPageActionError(null);
      message.success('验证闭环已更新');
    } catch (error) {
      showPageError('加载验证闭环失败', error, '加载验证闭环失败');
      setValidationMap(previous => ({ ...previous, [ideaId]: { ...previous[ideaId], loading: false } }));
    }
  };
  const loadExecutionPack = async (ideaId: string) => {
    setExecutionPackMap(previous => ({ ...previous, [ideaId]: { ...previous[ideaId], loading: true } }));
    try {
      const response = await api.get(`/research/ideas/${ideaId}/execution-pack`);
      setExecutionPackMap(previous => ({ ...previous, [ideaId]: { loading: false, data: response.data } }));
      setPageActionError(null);
      message.success('实验推进包已更新');
    } catch (error) {
      showPageError('加载实验推进包失败', error, '加载实验推进包失败');
      setExecutionPackMap(previous => ({ ...previous, [ideaId]: { ...previous[ideaId], loading: false } }));
    }
  };

  if (loading) {
    return (
      <PageShell
        title="研究工作台"
        subtitle="正在读取研究方向、运行状态和候选 Proposal。"
        icon={<ExperimentOutlined />}
        maxWidth={1280}
        actions={<Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/research')} style={{ borderRadius: 10 }}>返回研究方向</Button>}
      >
        <WorkflowLoadingState
          title="正在打开研究工作台"
          description="会优先加载方向基础信息，相关论文和辅助状态随后在页面内刷新。"
          icon={<ExperimentOutlined />}
        />
      </PageShell>
    );
  }

  if (!project) {
    return (
      <PageShell
        title="研究工作台"
        subtitle="当前研究方向不可用。"
        icon={<ExperimentOutlined />}
        maxWidth={960}
        actions={<Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/research')} style={{ borderRadius: 10 }}>返回研究方向</Button>}
      >
        <WorkflowUnavailableState
          title="没有找到这个研究方向"
          description="它可能已被删除、归档，或当前账号没有访问权限。"
          icon={<FileSearchOutlined />}
          action={<Button type="primary" icon={<ArrowLeftOutlined />} onClick={() => navigate('/research')} style={{ borderRadius: 10 }}>返回研究方向</Button>}
        />
      </PageShell>
    );
  }

  const evidenceMap = run?.evidence_map || {};
  const evidenceItems = (['seed', 'background', 'inspiration'] as const).flatMap(category => (evidenceMap[category] as Evidence[] || []));
  const evidenceById = new Map(evidenceItems.map(item => [item.paper_id, item]));
  const evidenceOptions = evidenceItems.map(item => ({
    value: item.paper_id,
    label: `${item.title}${item.year ? ` (${item.year})` : ''}`,
  }));
  const sourceErrors = evidenceMap.source_errors as Record<string, string> || {};
  const gaps = run?.gap_map?.gaps || [];
  const candidates = run?.candidate_pool || [];
  const proposalCounts = proposalDecisionCounts(ideas);
  const visibleProposals = ideas
    .filter(idea => proposalFilter === 'all' || idea.status === proposalFilter)
    .sort((a, b) => proposalSortValue(b, proposalSort) - proposalSortValue(a, proposalSort));
  const recommendedProposal = visibleProposals.find(idea => idea.status !== 'rejected') || null;
  const stageIndex = Math.max(0, stageItems.findIndex(([key]) => key === run?.stage));
  const currentStageTitle = stageItems.find(([key]) => key === run?.stage)?.[1] || '尚未启动';
  const runStatus = generating ? 'running' : run?.status || 'idle';
  const runStatusLabel = runStatus === 'idle' ? '尚未启动' : runStatusLabels[runStatus] || runStatus;
  const runStatusColor = runStatus === 'idle' ? 'default' : runStatusColors[runStatus] || 'default';
  const runHasTerminalError = run?.status === 'failed' && !!run.error;
  const runWasCancelled = run?.status === 'cancelled';
  const runCompleted = run?.status === 'complete';
  const relatedPapersUpdatedText = papersRefreshedAt
    ? new Date(papersRefreshedAt).toLocaleString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' })
    : null;

  const evidenceTab = (
    <div>
      <Alert showIcon type="info" message="证据地图" description="核心论文来自你主动关联的文献；背景论文用于界定现有方法；灵感论文可以来自本地论文库、arXiv 或 Semantic Scholar，用于新颖性检查和跨领域启发。" style={{ marginBottom: 16 }} />
      {Object.keys(sourceErrors).length > 0 && <Alert showIcon type="warning" message="部分联网来源暂不可用" description={`已自动使用其余证据继续生成：${Object.keys(sourceErrors).join('、')}`} style={{ marginBottom: 16 }} />}
      {evidenceItems.length === 0 ? (
        <WorkflowEmptyState
          title="证据地图还没有生成"
          description="从论文证据开始运行工作台后，这里会显示种子、背景和灵感论文。"
          icon={<FileSearchOutlined />}
          action={<Button type="primary" icon={<RocketOutlined />} onClick={handleGenerate}>从论文证据开始生成</Button>}
        />
      ) : (
        <List dataSource={evidenceItems} renderItem={item => (
          <List.Item style={{ alignItems: 'flex-start' }}>
            <List.Item.Meta
              title={<Space wrap><Tag color={categoryColors[item.category]}>{categoryLabels[item.category]}</Tag><Tag>{sourceLabels[item.source || 'local_library'] || item.source}</Tag>{item.collection_names?.map(name => <Tag color="magenta" key={name}>分类：{name}</Tag>)}<Text strong>{item.title}</Text>{item.year && <Text type="secondary">{item.year}</Text>}</Space>}
              description={<><Paragraph ellipsis={{ rows: 2 }} style={{ margin: '6px 0 4px' }}>{item.abstract_excerpt || '暂无摘要'}</Paragraph><Space wrap><Text type="secondary">{item.relevance}</Text>{item.source_url && <Button type="link" size="small" href={item.source_url} target="_blank">查看来源</Button>}{item.source !== 'local_library' && (item.imported_paper_id ? <Tag color="green">已入库</Tag> : <Button type="link" size="small" icon={<ImportOutlined />} loading={importingEvidence.has(item.paper_id)} onClick={() => importEvidence(item)}>一键入库</Button>)}</Space></>}
            />
          </List.Item>
        )} />
      )}
    </div>
  );

  const gapTab = gaps.length === 0 ? (
    <WorkflowEmptyState
      title="Gap Map 尚未形成"
      description="工作台完成证据收集后，会把现有限制、研究机会和可验证问题沉淀到这里。"
      icon={<NodeIndexOutlined />}
      action={<Button type="primary" icon={<NodeIndexOutlined />} loading={gapPreviewing} onClick={handleGapPreview}>预览 Gap Map</Button>}
    />
  ) : (
    <Space direction="vertical" size={12} style={{ width: '100%' }}>
      <Card size="small" className="gap-selection-panel">
        <Space direction="vertical" size={12} style={{ width: '100%' }}>
          <Space wrap>
            <Tag color={run?.stage === 'gap_review' ? 'purple' : 'blue'}>{run?.stage === 'gap_review' ? '等待选择' : 'Gap Map 已生成'}</Tag>
            <Text type="secondary">先选择要推进的研究空白，再让系统生成候选 Proposal。</Text>
          </Space>
          <Row gutter={[10, 10]}>
            <Col xs={24} md={8}>
              <Text type="secondary">研究模式</Text>
              <Select style={{ width: '100%', marginTop: 6 }} value={researchMode} options={[...researchModeOptions]} onChange={setResearchMode} />
            </Col>
            <Col xs={24} md={8}>
              <Text type="secondary">风险偏好</Text>
              <Select style={{ width: '100%', marginTop: 6 }} value={riskAppetite} options={[...riskAppetiteOptions]} onChange={setRiskAppetite} />
            </Col>
            <Col xs={24} md={8}>
              <Text type="secondary">资源预算</Text>
              <Select style={{ width: '100%', marginTop: 6 }} value={resourceBudget} options={[...resourceBudgetOptions]} onChange={setResourceBudget} />
            </Col>
          </Row>
          <TextArea
            rows={2}
            value={gapFocusNote}
            onChange={event => setGapFocusNote(event.target.value)}
            placeholder="可选：写下你更想推进的角度，例如偏低算力、偏理论证明、偏系统落地或避开某类方法。"
          />
          <Space wrap>
            <Button
              type="primary"
              icon={<RocketOutlined />}
              loading={gapContinuing}
              disabled={!run?.id || selectedGapTitles.length === 0}
              onClick={handleContinueFromGaps}
            >
              按选择继续生成 Proposal
            </Button>
            <Button icon={<ReloadOutlined />} loading={gapPreviewing} onClick={handleGapPreview}>重新提取 Gap Map</Button>
            <Text type="secondary">已选择 {selectedGapTitles.length} 个，屏蔽 {blockedGapTitles.length} 个</Text>
          </Space>
        </Space>
      </Card>
      {gaps.map((gap, index) => {
        const draft = gapDrafts[index] || gapToDraft(gap);
        const feedback = gap.user_feedback;
        const linkedEvidence = (gap.evidence_ids || []).map(id => evidenceById.get(id)).filter(Boolean) as Evidence[];
        return (
          <Card
            key={`${gap.title}-${index}`}
            size="small"
            className="gap-review-card"
            title={<Space wrap><NodeIndexOutlined style={{ color: '#8b5cf6' }} /><Text strong>{gap.title}</Text>{feedback?.rating && <Tag color={gapRatingColors[feedback.rating]}>{gapRatingOptions.find(item => item.value === feedback.rating)?.label}</Tag>}{feedback?.labels?.map(label => <Tag key={label}>{gapLabelMap[label]}</Tag>)}{gap.refinement && <Tag color="cyan">已细化</Tag>}</Space>}
            style={{ borderRadius: 12 }}
          >
            <Space wrap style={{ marginBottom: 10 }}>
              <Checkbox
                checked={selectedGapTitles.includes(gap.title)}
                onChange={event => {
                  setSelectedGapTitles(previous => event.target.checked ? Array.from(new Set([...previous, gap.title])) : previous.filter(title => title !== gap.title));
                  if (event.target.checked) setBlockedGapTitles(previous => previous.filter(title => title !== gap.title));
                }}
              >
                推进
              </Checkbox>
              <Checkbox
                checked={blockedGapTitles.includes(gap.title)}
                onChange={event => {
                  setBlockedGapTitles(previous => event.target.checked ? Array.from(new Set([...previous, gap.title])) : previous.filter(title => title !== gap.title));
                  if (event.target.checked) setSelectedGapTitles(previous => previous.filter(title => title !== gap.title));
                }}
              >
                暂不考虑
              </Checkbox>
            </Space>
            <Paragraph><Text strong>现有限制：</Text>{gap.limitation}</Paragraph>
            <Paragraph><Text strong>研究机会：</Text>{gap.opportunity}</Paragraph>
            <Paragraph style={{ marginBottom: 6 }}><Text strong>可验证问题：</Text>{gap.research_question}</Paragraph>
            <Text type="secondary">不确定性：{gap.uncertainty}</Text>
            <Collapse
              ghost
              size="small"
              className="gap-feedback-collapse"
              items={[
                {
                  key: 'feedback',
                  label: <Space><SaveOutlined />编辑与反馈</Space>,
                  children: (
                    <Space direction="vertical" size={10} style={{ width: '100%' }}>
                      <Input value={draft.title} onChange={event => updateGapDraft(index, { title: event.target.value })} placeholder="Gap 标题" />
                      <Row gutter={[10, 10]}>
                        <Col xs={24} md={12}><Text type="secondary">现有限制</Text><TextArea rows={2} value={draft.limitation} onChange={event => updateGapDraft(index, { limitation: event.target.value })} /></Col>
                        <Col xs={24} md={12}><Text type="secondary">研究机会</Text><TextArea rows={2} value={draft.opportunity} onChange={event => updateGapDraft(index, { opportunity: event.target.value })} /></Col>
                        <Col xs={24} md={12}><Text type="secondary">可验证问题</Text><TextArea rows={2} value={draft.research_question} onChange={event => updateGapDraft(index, { research_question: event.target.value })} /></Col>
                        <Col xs={24} md={12}><Text type="secondary">不确定性</Text><TextArea rows={2} value={draft.uncertainty} onChange={event => updateGapDraft(index, { uncertainty: event.target.value })} /></Col>
                      </Row>
                      <Row gutter={[10, 10]}>
                        <Col xs={24} md={8}>
                          <Text type="secondary">质量判断</Text>
                          <Select style={{ width: '100%', marginTop: 6 }} value={draft.rating} options={[...gapRatingOptions]} onChange={value => updateGapDraft(index, { rating: value as GapFeedbackRating })} />
                        </Col>
                        <Col xs={24} md={16}>
                          <Text type="secondary">反馈标签</Text>
                          <Select mode="multiple" style={{ width: '100%', marginTop: 6 }} value={draft.labels} options={[...gapLabelOptions]} onChange={value => updateGapDraft(index, { labels: value as GapFeedbackLabel[] })} />
                        </Col>
                      </Row>
                      <TextArea rows={2} value={draft.note} onChange={event => updateGapDraft(index, { note: event.target.value })} placeholder="写下为什么这个 Gap 值得推进、需要收窄或应该暂缓。" />
                      <TextArea rows={2} value={draft.evidence_rationale} onChange={event => updateGapDraft(index, { evidence_rationale: event.target.value })} placeholder="证据解释：这些论文为什么支持这个 Gap？" />
                      <Select mode="multiple" style={{ width: '100%' }} value={draft.evidence_ids} options={evidenceOptions} onChange={value => updateGapDraft(index, { evidence_ids: value as string[] })} placeholder="关联证据论文" />
                      <Space wrap>
                        <Button icon={<SaveOutlined />} type="primary" loading={savingGapFeedback.has(index)} onClick={() => handleSaveGapFeedback(index)}>保存 Gap 反馈</Button>
                        <TextArea
                          rows={1}
                          style={{ width: 320, maxWidth: '100%' }}
                          value={gapRefineNotes[index] || ''}
                          onChange={event => setGapRefineNotes(previous => ({ ...previous, [index]: event.target.value }))}
                          placeholder="可选：告诉 AI 如何细化这个 Gap"
                        />
                        <Button icon={<ReloadOutlined />} loading={refiningGaps.has(index)} onClick={() => handleRefineGap(index)}>细化这个 Gap</Button>
                      </Space>
                    </Space>
                  ),
                },
                {
                  key: 'evidence',
                  label: <Space><FileSearchOutlined />关联证据 {linkedEvidence.length}</Space>,
                  children: (
                    <Space direction="vertical" size={8} style={{ width: '100%' }}>
                      {gap.evidence_rationale && <Alert type="info" showIcon message="证据解释" description={gap.evidence_rationale} />}
                      {linkedEvidence.length === 0 ? <Text type="secondary">这个 Gap 还没有关联证据。</Text> : (
                        <List size="small" dataSource={linkedEvidence} renderItem={item => (
                          <List.Item className="gap-evidence-item">
                            <List.Item.Meta
                              title={<Space wrap><Tag color={categoryColors[item.category]}>{categoryLabels[item.category]}</Tag><Text strong>{item.title}</Text>{item.year && <Text type="secondary">{item.year}</Text>}</Space>}
                              description={<Paragraph ellipsis={{ rows: 2 }} style={{ marginBottom: 0 }}>{item.relevance || item.abstract_excerpt || '暂无证据解释'}</Paragraph>}
                            />
                          </List.Item>
                        )} />
                      )}
                    </Space>
                  ),
                },
              ]}
            />
          </Card>
        );
      })}
    </Space>
  );

  const candidateTab = candidates.length === 0 ? (
    <WorkflowEmptyState
      title="候选假设池为空"
      description="Gap Map 完成后，系统会生成多条可证伪假设并在这里展示。"
      icon={<BulbOutlined />}
      action={<Button type="primary" icon={<RocketOutlined />} onClick={handleGenerate}>生成候选假设</Button>}
    />
  ) : (
    <Space direction="vertical" size={12} style={{ width: '100%' }}>
      {candidates.map((candidate, index) => (
        <Card key={`${candidate.title}-${index}`} size="small" style={{ borderRadius: 12 }}
          title={<Space wrap><Tag color="geekblue">{pathLabels[candidate.path] || candidate.path}</Tag><Text strong>{candidate.title}</Text></Space>}
          extra={candidate.score != null && <Tag color="purple">{candidate.score.toFixed(2)}</Tag>}>
          <Paragraph><Text strong>假设：</Text>{candidate.hypothesis}</Paragraph>
          <Paragraph ellipsis={{ rows: 2 }} style={{ marginBottom: 0 }}><Text strong>验证方式：</Text>{candidate.falsification_test}</Paragraph>
        </Card>
      ))}
    </Space>
  );

  const renderCodeProject = (idea: Idea) => {
    const projectPackage = idea.generated_code_project;
    if (!projectPackage && idea.generated_code) {
      return (
        <Card size="small" title="旧版实验代码" style={{ borderRadius: 8, marginTop: 14 }}>
          <Space direction="vertical" size={10} style={{ width: '100%' }}>
            <Alert
              type="info"
              showIcon
              message="这个 Proposal 只有旧版单文件代码"
              description="可以重新生成结构化实验项目包，获得 README、配置、训练、评估和分析脚本。"
            />
            <div className="code-project-preview legacy-code-preview">
              <pre>{idea.generated_code}</pre>
            </div>
            <Space wrap>
              <Button icon={<CopyOutlined />} onClick={() => copyCodeProjectText(idea.generated_code || '', '旧版实验代码已复制')}>复制代码</Button>
              <Button icon={<CodeOutlined />} loading={codeMap[idea.id]?.loading} onClick={() => handleGenCode(idea.id)}>重新生成实验项目包</Button>
            </Space>
          </Space>
        </Card>
      );
    }
    if (!projectPackage) {
      return (
        <Button type="dashed" icon={<CodeOutlined />} loading={codeMap[idea.id]?.loading} onClick={() => handleGenCode(idea.id)} block>
          生成实验项目包 (PyTorch)
        </Button>
      );
    }
    const history = codeProjectHistoryMap[idea.id] || { loading: false, versions: [], comparing: false };
    const visibleProjectPackage = history.selectedDetail?.code_project || projectPackage;
    const visibleVersionLabel = history.selectedDetail ? `v${history.selectedDetail.version}` : '最新';
    const visibleFiles = normalizeCodeProjectFiles(visibleProjectPackage);
    const selectedPath = codeProjectSelectedFile[idea.id] || codeProjectDefaultFilePath(visibleProjectPackage);
    const visibleSelectedFile = visibleFiles.find(file => file.path === selectedPath) || visibleFiles[0];
    const folderGroups = codeProjectFolderGroups(visibleProjectPackage);
    const entrypointPaths = new Set((visibleProjectPackage.entrypoints || []).map(entrypoint => entrypoint.path));
    const selectProjectFile = (path: string) => setCodeProjectSelectedFile(previous => ({ ...previous, [idea.id]: path }));
    const versionOptions = [
      { value: 'latest', label: '最新版本' },
      ...history.versions.map(version => ({ value: version.version, label: `v${version.version} · ${version.project_name}` })),
    ];
    const compareVersionOptions = history.versions.map(version => ({ value: version.version, label: `v${version.version}` }));
    const selectedDiff = history.comparison?.files.find(file => file.path === history.selectedDiffPath);
    return (
      <Card
        size="small"
        title={<Space wrap><CodeOutlined /><Text strong>实验项目包</Text><Tag color="blue">{visibleProjectPackage.framework}</Tag><Tag>{visibleFiles.length} 文件</Tag><Tag color={history.selectedDetail ? 'purple' : 'green'}>{visibleVersionLabel}</Tag></Space>}
        style={{ borderRadius: 8, marginTop: 14 }}
      >
        <Space direction="vertical" size={14} style={{ width: '100%' }}>
          <div className="code-project-summary">
            <div className="code-project-summary-main">
              <Space wrap size={8}>
                <Text strong>{visibleProjectPackage.name}</Text>
                <Tag color="geekblue">{visibleProjectPackage.framework}</Tag>
                <Tag>{visibleFiles.length} files</Tag>
                {history.selectedDetail && <Tag color="purple">历史版本 v{history.selectedDetail.version}</Tag>}
              </Space>
              <Paragraph style={{ marginBottom: 0, marginTop: 6 }}>{visibleProjectPackage.summary}</Paragraph>
            </div>
            <div className="code-project-actions">
              <Button size="small" icon={<ReloadOutlined />} loading={codeMap[idea.id]?.loading} onClick={() => handleGenCode(idea.id)}>重新生成</Button>
              <Button size="small" type="primary" icon={<DownloadOutlined />} onClick={() => downloadCodeProject(idea)}>下载 ZIP</Button>
            </div>
          </div>
          <div className="code-project-version-panel">
            <div className="code-project-version-header">
              <Space wrap>
                <HistoryOutlined />
                <Text strong>项目版本历史</Text>
                {history.versions.length > 0 ? <Tag>{history.versions.length} 个版本</Tag> : <Tag color="default">暂无历史版本</Tag>}
              </Space>
              <Button size="small" loading={history.loading} onClick={() => loadCodeProjectVersions(idea.id)}>刷新版本</Button>
            </div>
            {history.versions.length > 0 ? (
              <Space direction="vertical" size={10} style={{ width: '100%' }}>
                <Space wrap>
                  <Text type="secondary">预览版本</Text>
                  <Select
                    size="small"
                    value={history.selectedVersion || 'latest'}
                    options={versionOptions}
                    onChange={(value) => selectCodeProjectVersion(idea, value as number | 'latest')}
                    style={{ minWidth: 220 }}
                  />
                  {history.selectedDetail?.created_at && <Text type="secondary">生成于 {new Date(history.selectedDetail.created_at).toLocaleString()}</Text>}
                </Space>
                <Space wrap>
                  <Text type="secondary">比较</Text>
                  <Select
                    size="small"
                    value={history.compareFrom}
                    options={compareVersionOptions}
                    onChange={(value) => updateCodeProjectHistory(idea.id, { compareFrom: value })}
                    placeholder="旧版本"
                    style={{ width: 120 }}
                  />
                  <Text type="secondary">到</Text>
                  <Select
                    size="small"
                    value={history.compareTo}
                    options={compareVersionOptions}
                    onChange={(value) => updateCodeProjectHistory(idea.id, { compareTo: value })}
                    placeholder="新版本"
                    style={{ width: 120 }}
                  />
                  <Button size="small" loading={history.comparing} onClick={() => compareCodeProjectVersions(idea.id)}>比较版本</Button>
                </Space>
              </Space>
            ) : (
              <Text type="secondary">当前最新项目仍可浏览；版本历史会从下一次生成实验项目包开始保存。</Text>
            )}
          </div>
          <div className="code-project-meta-grid">
            <section className="code-project-meta-panel">
              <Text strong>安装</Text>
              <Space direction="vertical" size={6} style={{ width: '100%', marginTop: 8 }}>
                {(visibleProjectPackage.setup || []).length > 0 ? visibleProjectPackage.setup.map(command => (
                  <div className="code-project-command" key={command}>
                    <Text code>{command}</Text>
                    <Tooltip title="复制命令"><Button type="text" size="small" icon={<CopyOutlined />} onClick={() => copyCodeProjectText(command, '安装命令已复制')} /></Tooltip>
                  </div>
                )) : <Text type="secondary">暂无安装命令</Text>}
              </Space>
            </section>
            <section className="code-project-meta-panel">
              <Text strong>运行</Text>
              <Space direction="vertical" size={6} style={{ width: '100%', marginTop: 8 }}>
                {(visibleProjectPackage.run_commands || []).length > 0 ? visibleProjectPackage.run_commands.map(command => (
                  <div className="code-project-command" key={command}>
                    <Text code>{command}</Text>
                    <Tooltip title="复制命令"><Button type="text" size="small" icon={<CopyOutlined />} onClick={() => copyCodeProjectText(command, '运行命令已复制')} /></Tooltip>
                  </div>
                )) : <Text type="secondary">暂无运行命令</Text>}
              </Space>
            </section>
            <section className="code-project-meta-panel">
              <Text strong>入口</Text>
              <Space direction="vertical" size={6} style={{ width: '100%', marginTop: 8 }}>
                {(visibleProjectPackage.entrypoints || []).length > 0 ? visibleProjectPackage.entrypoints.map(entrypoint => (
                  <button className="code-project-entrypoint" type="button" key={`${entrypoint.name}-${entrypoint.path}`} onClick={() => selectProjectFile(entrypoint.path)}>
                    <span>{entrypoint.name}</span>
                    <Text type="secondary">{entrypoint.path}</Text>
                  </button>
                )) : <Text type="secondary">暂无入口文件</Text>}
              </Space>
            </section>
            <section className="code-project-meta-panel">
              <Text strong>安全说明</Text>
              <Space direction="vertical" size={6} style={{ width: '100%', marginTop: 8 }}>
                {(visibleProjectPackage.safety_notes || []).length > 0 ? visibleProjectPackage.safety_notes.map(note => <Text type="secondary" key={note}>{note}</Text>) : <Text type="secondary">暂无安全说明</Text>}
              </Space>
            </section>
          </div>
          <div className="code-project-browser">
            <aside className="code-project-file-tree" aria-label="generated code project file tree">
              <div className="code-project-panel-title">
                <FolderOutlined />
                <Text strong>项目文件</Text>
              </div>
              <div className="code-project-tree-groups">
                {folderGroups.map(group => (
                  <div className="code-project-tree-group" key={group.folder}>
                    <div className="code-project-folder-row"><FolderOutlined /><Text type="secondary">{group.folder}</Text></div>
                    {group.files.map(file => (
                      <button
                        className={`code-project-file-row${file.path === visibleSelectedFile?.path ? ' is-selected' : ''}`}
                        type="button"
                        key={file.path}
                        onClick={() => selectProjectFile(file.path)}
                        title={file.path}
                      >
                        <FileOutlined />
                        <span>{file.path.split('/').pop()}</span>
                        {entrypointPaths.has(file.path) && <Tag color="purple">entry</Tag>}
                      </button>
                    ))}
                  </div>
                ))}
              </div>
            </aside>
            <section className="code-project-preview-panel">
              {visibleSelectedFile ? (
                <>
                  <div className="code-project-preview-toolbar">
                    <div className="code-project-preview-heading">
                      <Text strong>{visibleSelectedFile.path}</Text>
                      <Space wrap size={6}>
                        <Tag>{visibleSelectedFile.language || 'text'}</Tag>
                        <Tag>{codeProjectLineCount(visibleSelectedFile.content)} 行</Tag>
                        {entrypointPaths.has(visibleSelectedFile.path) && <Tag color="purple">入口</Tag>}
                      </Space>
                    </div>
                    <Tooltip title="复制文件内容">
                      <Button size="small" icon={<CopyOutlined />} onClick={() => copyCodeProjectText(visibleSelectedFile.content, '文件内容已复制')}>复制</Button>
                    </Tooltip>
                  </div>
                  {visibleSelectedFile.purpose && <Text type="secondary" className="code-project-file-purpose">{visibleSelectedFile.purpose}</Text>}
                  <div className="code-project-preview">
                    <pre>{visibleSelectedFile.content}</pre>
                  </div>
                </>
              ) : (
                <div className="code-project-empty-preview">
                  <FileTextOutlined />
                  <Text type="secondary">没有可预览文件</Text>
                </div>
              )}
            </section>
          </div>
          {history.comparison && (
            <div className="code-project-diff-panel">
              <div className="code-project-version-header">
                <Space wrap>
                  <Text strong>版本差异</Text>
                  <Tag color="green">新增 {history.comparison.summary.added || 0}</Tag>
                  <Tag color="red">删除 {history.comparison.summary.removed || 0}</Tag>
                  <Tag color="orange">修改 {history.comparison.summary.modified || 0}</Tag>
                  <Tag>未变 {history.comparison.summary.unchanged || 0}</Tag>
                </Space>
                <Text type="secondary">v{history.comparison.from_version} → v{history.comparison.to_version}</Text>
              </div>
              <div className="code-project-diff-layout">
                <div className="code-project-diff-files">
                  {history.comparison.files.map(file => (
                    <button
                      type="button"
                      key={file.path}
                      className={`code-project-diff-row is-${file.status}${file.path === history.selectedDiffPath ? ' is-selected' : ''}`}
                      onClick={() => updateCodeProjectHistory(idea.id, { selectedDiffPath: file.path })}
                    >
                      <span>{file.path}</span>
                      <Tag color={file.status === 'added' ? 'green' : file.status === 'removed' ? 'red' : file.status === 'modified' ? 'orange' : 'default'}>
                        {file.status}
                      </Tag>
                    </button>
                  ))}
                </div>
                <div className="code-project-diff-preview">
                  {selectedDiff ? (
                    <>
                      <Space wrap style={{ marginBottom: 8 }}>
                        <Text strong>{selectedDiff.path}</Text>
                        <Tag>{selectedDiff.language}</Tag>
                        <Tag>旧 {selectedDiff.before_line_count} 行</Tag>
                        <Tag>新 {selectedDiff.after_line_count} 行</Tag>
                      </Space>
                      <pre>{selectedDiff.diff || selectedDiff.after_content || selectedDiff.before_content || '文件内容未变化'}</pre>
                    </>
                  ) : <Text type="secondary">选择一个文件查看差异</Text>}
                </div>
              </div>
            </div>
          )}
        </Space>
      </Card>
    );
  };

  const renderProposalReviewPanel = (idea: Idea) => {
    const proposalReview = idea.review_json?.proposal_review || null;
    const reviewReadiness = proposalReview?.writing_readiness || 'missing';
    const hasChildVersion = ideas.some(candidate => candidate.parent_idea_id === idea.id);
    const latestChild = ideas
      .filter(candidate => candidate.parent_idea_id === idea.id)
      .sort((first, second) => (new Date(second.created_at || 0).getTime()) - (new Date(first.created_at || 0).getTime()))[0];
    const compareTarget = idea.parent_idea_id ? idea : latestChild;
    return (
      <Card
        size="small"
        className="proposal-review-package"
        title={(
          <Space wrap>
            <FileSearchOutlined />
            <Text strong>结构化审稿包</Text>
            {proposalReview ? (
              <Tag color={readinessColors[reviewReadiness] || 'default'}>
                {proposalReviewReadinessLabels[reviewReadiness] || reviewReadiness}
              </Tag>
            ) : <Tag color="default">未生成</Tag>}
          </Space>
        )}
        extra={(
          <Space wrap>
            <Button
              size="small"
              icon={<ReloadOutlined />}
              loading={reviewingIdeaIds.has(idea.id)}
              onClick={() => refreshProposalReviewPackage(idea)}
            >
              {proposalReview ? '刷新审稿包' : '生成审稿包'}
            </Button>
            <Button
              size="small"
              type="primary"
              ghost
              disabled={!proposalReview || (idea.status !== 'draft' && idea.status !== 'pinned')}
              onClick={() => openReviewRevision(idea)}
            >
              按审稿意见修订
            </Button>
            {compareTarget && (
              <Button size="small" onClick={() => openVersionComparison(compareTarget)}>
                版本对比
              </Button>
            )}
          </Space>
        )}
        style={{ borderRadius: 12, marginTop: 14, marginBottom: 12, background: '#fcfdff' }}
      >
        {proposalReview ? (
          <Space direction="vertical" size={12} style={{ width: '100%' }}>
            <Alert
              showIcon
              type={reviewReadiness === 'ready' ? 'success' : reviewReadiness === 'blocked' ? 'error' : 'warning'}
              message="审稿结论"
              description={proposalReview.summary || '已生成审稿式修订建议。'}
            />
            <Row gutter={[12, 12]}>
              <Col xs={24} lg={12}>
                <div className="proposal-review-section">
                  <Text strong>潜在贡献</Text>
                  <Space wrap style={{ marginTop: 8 }}>
                    {(proposalReview.contributions || []).length > 0
                      ? proposalReview.contributions.map(item => <Tag color="green" key={item}>{item}</Tag>)
                      : <Text type="secondary">暂无明确贡献点</Text>}
                  </Space>
                </div>
              </Col>
              <Col xs={24} lg={12}>
                <div className="proposal-review-section">
                  <Text strong>最弱假设</Text>
                  <Space wrap style={{ marginTop: 8 }}>
                    {(proposalReview.weakest_assumptions || []).length > 0
                      ? proposalReview.weakest_assumptions.map(item => <Tag color="orange" key={item}>{item}</Tag>)
                      : <Text type="secondary">暂无明显弱假设</Text>}
                  </Space>
                </div>
              </Col>
            </Row>
            <Row gutter={[12, 12]}>
              <Col xs={24} lg={12}>
                <div className="proposal-review-section">
                  <Text strong>审稿异议</Text>
                  <List
                    size="small"
                    dataSource={proposalReview.reviewer_objections || []}
                    locale={{ emptyText: '暂无阻塞性异议' }}
                    renderItem={(item, index) => <List.Item>{index + 1}. {item}</List.Item>}
                  />
                </div>
              </Col>
              <Col xs={24} lg={12}>
                <div className="proposal-review-section">
                  <Text strong>必要实验</Text>
                  <List
                    size="small"
                    dataSource={proposalReview.required_experiments || []}
                    locale={{ emptyText: '暂无新增必要实验' }}
                    renderItem={(item, index) => <List.Item>{index + 1}. {item}</List.Item>}
                  />
                </div>
              </Col>
            </Row>
            <div className="proposal-review-section">
              <Text strong>修订计划</Text>
              <List
                size="small"
                dataSource={proposalReview.revision_plan || []}
                locale={{ emptyText: '暂无修订计划' }}
                renderItem={(item, index) => <List.Item>{index + 1}. {item}</List.Item>}
              />
            </div>
            <Alert type="info" showIcon message="下一版修订焦点" description={proposalReview.next_revision_focus || '补强证据、实验设置和可证伪假设'} />
            {hasChildVersion && <Text type="secondary">已有基于该 Proposal 的子版本，可通过版本对比查看核心改动。</Text>}
          </Space>
        ) : (
          <Text type="secondary">生成后会把贡献、最弱假设、审稿异议、必要实验、修订计划和写作就绪度收束在这里。</Text>
        )}
      </Card>
    );
  };

  const renderProposal = (idea: Idea) => {
    const review = idea.review_json;
    const plan = idea.experiment_plan;
    const validation = validationMap[idea.id];
    const validationData = validation?.data;
    const executionPack = executionPackMap[idea.id];
    const executionData = executionPack?.data;
    const novelty = review?.novelty_check;
    const collisionRisk = novelty?.collision_risk || (novelty?.status === 'too_similar' ? 'high' : novelty?.status === 'incremental' ? 'medium' : novelty?.status === 'likely_novel' ? 'low' : undefined);
    const similarWork = novelty?.similar_work || [];
    const diversityFacets = review?.diversity_facets || [];
    const appliedGapSelection = review?.gap_selection;
    return (
      <div>
        {idea.hypothesis && <Alert type="success" showIcon message="可证伪假设" description={idea.hypothesis} style={{ marginBottom: 14 }} />}
        <Paragraph style={{ whiteSpace: 'pre-wrap' }}>{idea.description || '暂无描述'}</Paragraph>
        {idea.approach && <Paragraph><Text strong>技术草图：</Text>{idea.approach}</Paragraph>}
        {review && <>
          <Divider>六维评审</Divider>
          <Row gutter={[8, 8]}>
            {Object.entries(review.scores || {}).map(([key, value]) => (
              <Col xs={12} md={8} key={key}><Card size="small" style={{ borderRadius: 10 }}><Text type="secondary">{scoreLabels[key] || key}</Text><Title level={4} style={{ margin: '4px 0 0' }}>{value}/10</Title></Card></Col>
            ))}
          </Row>
          <Paragraph style={{ marginTop: 12 }}><Text strong>评审理由：</Text>{review.rationale}</Paragraph>
          <Text type="secondary">主要不确定性：{review.uncertainty}</Text>
          {(review.novelty_check || review.adversarial_review || review.search_tree || review.selection_rationale || appliedGapSelection) && <>
            <Divider>v3 质量信号</Divider>
            <Space direction="vertical" size={10} style={{ width: '100%' }}>
              {appliedGapSelection && (
                <Card size="small" className="gap-selection-signal">
                  <Space direction="vertical" size={6} style={{ width: '100%' }}>
                    <Space wrap>
                      <Tag color="purple">Gap 约束</Tag>
                      {(appliedGapSelection.selected_gap_titles || []).slice(0, 3).map(title => <Tag color="geekblue" key={title}>{title}</Tag>)}
                    </Space>
                    {appliedGapSelection.focus_note && <Text type="secondary">关注点：{appliedGapSelection.focus_note}</Text>}
                  </Space>
                </Card>
              )}
              {review.selection_rationale && (
                <Card size="small" className="proposal-selection-signal">
                  <Space direction="vertical" size={6} style={{ width: '100%' }}>
                    <Space wrap>
                      <Tag color="purple">选择理由</Tag>
                      {review.selection_score != null && <Tag>选择分 {review.selection_score}</Tag>}
                    </Space>
                    <Text>{review.selection_rationale}</Text>
                    {diversityFacets.length > 0 && (
                      <Space wrap size={6}>
                        {diversityFacets.slice(0, 6).map(facet => <Tag color="geekblue" key={facet}>{facet}</Tag>)}
                      </Space>
                    )}
                    {(review.suppressed_duplicates || []).length > 0 && (
                      <Text type="secondary">已压制相近候选：{review.suppressed_duplicates?.slice(0, 2).map(item => item.title).filter(Boolean).join('、')}</Text>
                    )}
                  </Space>
                </Card>
              )}
              {novelty && (
                <Alert
                  type={novelty.status === 'likely_novel' ? 'success' : novelty.status === 'incremental' ? 'warning' : 'error'}
                  showIcon
                  message={
                    <Space wrap>
                      <Text strong>Novelty Check</Text>
                      <Tag color={noveltyColors[novelty.status]}>{noveltyLabels[novelty.status]}</Tag>
                      <Tag>{Math.round(novelty.score * 100)}%</Tag>
                      {collisionRisk && <Tag color={riskColors[collisionRisk] || 'default'}>碰撞风险 {collisionRisk}</Tag>}
                    </Space>
                  }
                  description={
                    <Space direction="vertical" size={6} style={{ width: '100%' }}>
                      <span>{novelty.rationale}{novelty.nearest_evidence?.title ? ` 最近相似证据：${novelty.nearest_evidence.title}` : ''}</span>
                      {similarWork.length > 0 && (
                        <div className="proposal-similar-work-list">
                          {similarWork.slice(0, 3).map((item, index) => (
                            <div className="proposal-similar-work-item" key={`${item.paper_id || item.title || index}`}>
                              <Space size={6} wrap>
                                <Tag color={item.relation === 'nearest_collision_candidate' ? 'red' : 'blue'}>{Math.round((item.score || 0) * 100)}%</Tag>
                                {item.source && <Tag>{item.source}</Tag>}
                                {item.year && <Tag>{item.year}</Tag>}
                                <Text strong>{item.title || '相似工作'}</Text>
                              </Space>
                              {item.reason && <Text type="secondary">{item.reason}</Text>}
                            </div>
                          ))}
                        </div>
                      )}
                      {novelty.source_coverage && (
                        <Text type="secondary">
                          相似工作池：本地 {novelty.source_coverage.local_count ?? 0}，外部 {novelty.source_coverage.external_count ?? 0}
                          {Object.keys(novelty.source_coverage.source_errors || {}).length > 0 ? '，部分外部源不可用' : ''}
                        </Text>
                      )}
                    </Space>
                  }
                />
              )}
              {review.adversarial_review && (
                <Alert
                  type={review.adversarial_review.verdict === 'advance' ? 'success' : review.adversarial_review.verdict === 'revise' ? 'warning' : 'error'}
                  showIcon
                  message={<Space wrap><Text strong>反驳评审</Text><Tag color={adversarialColors[review.adversarial_review.verdict]}>{adversarialLabels[review.adversarial_review.verdict]}</Tag><Tag>扣分 {review.adversarial_review.penalty}</Tag></Space>}
                  description={
                    <div>
                      <Paragraph style={{ marginBottom: 6 }}>{review.adversarial_review.summary}</Paragraph>
                      {review.adversarial_review.objections?.slice(0, 3).map((item, index) => <Tag color="red" key={index} style={{ marginBottom: 4 }}>{item}</Tag>)}
                    </div>
                  }
                />
              )}
              {review.search_tree && (
                <Card size="small" style={{ borderRadius: 10, background: '#fafafa' }}>
                  <Space wrap>
                    <Tag color="geekblue">搜索树 Round {review.search_tree.round ?? 0}</Tag>
                    <Tag>{review.search_tree.operator || 'root'}</Tag>
                    {review.search_tree.source && <Tag color={review.search_tree.source === 'llm' ? 'purple' : 'default'}>{review.search_tree.source}</Tag>}
                    {review.search_tree.parent_title && <Text type="secondary">父节点：{review.search_tree.parent_title}</Text>}
                  </Space>
                </Card>
              )}
            </Space>
          </>}
        </>}
        {renderProposalReviewPanel(idea)}
        <Divider>实验推进包</Divider>
        <Card size="small" style={{ borderRadius: 12, marginBottom: 12, background: '#fbfaff' }}>
          <Space direction="vertical" size={12} style={{ width: '100%' }}>
            <Space wrap>
              <Button
                type="primary"
                ghost
                icon={<ExperimentOutlined />}
                loading={executionPack?.loading}
                onClick={() => loadExecutionPack(idea.id)}
              >
                生成/刷新推进包
              </Button>
              {executionData && (
                <>
                  <Tag color={executionReadinessColors[executionData.readiness.status] || 'default'}>
                    {executionData.readiness.label}
                  </Tag>
                  <Tag color="blue">推进度 {Math.round((executionData.readiness.score || 0) * 100)}%</Tag>
                  <Tag color={executionData.feedback.has_results ? 'purple' : 'default'}>
                    反馈 {executionData.feedback.count}
                  </Tag>
                </>
              )}
            </Space>
            {executionData ? (
              <>
                <Alert
                  showIcon
                  type={executionData.readiness.status === 'ready' ? 'success' : executionData.readiness.status === 'needs_iteration' ? 'info' : 'warning'}
                  message="从 Proposal 到实验的执行路线"
                  description={executionData.summary}
                />
                <Row gutter={[12, 12]}>
                  <Col xs={24} lg={12}>
                    <Card size="small" title="最小实验任务" style={{ borderRadius: 10, height: '100%' }}>
                      <Space direction="vertical" size={6} style={{ width: '100%' }}>
                        {executionData.minimum_tasks.map(task => (
                          <Tag
                            key={task.key}
                            color={task.status === 'ready' ? 'green' : 'orange'}
                            style={{ whiteSpace: 'normal', lineHeight: 1.6, padding: '4px 8px' }}
                          >
                            {task.status === 'ready' ? '已就绪' : '待补齐'} · {task.label}：{task.detail}
                          </Tag>
                        ))}
                      </Space>
                    </Card>
                  </Col>
                  <Col xs={24} lg={12}>
                    <Card size="small" title="成功指标与下一步" style={{ borderRadius: 10, height: '100%' }}>
                      <List
                        size="small"
                        dataSource={executionData.success_metrics}
                        renderItem={item => <List.Item><Text><Text strong>{item.name}：</Text>{item.target}</Text></List.Item>}
                      />
                      <Divider style={{ margin: '8px 0' }} />
                      <Space wrap>
                        {executionData.next_actions.map(action => <Tag color="purple" key={action}>{action}</Tag>)}
                      </Space>
                    </Card>
                  </Col>
                </Row>
                {executionData.risks.length > 0 && (
                  <Card size="small" title="实验风险" style={{ borderRadius: 10 }}>
                    <Space wrap>
                      {executionData.risks.map((risk, index) => (
                        <Tag color={riskColors[risk.level] || 'default'} key={`${risk.message}-${index}`}>{risk.message}</Tag>
                      ))}
                    </Space>
                  </Card>
                )}
                {executionData.feedback.latest && (
                  <Alert
                    showIcon
                    type="info"
                    message={`最近反馈：${executionData.feedback.latest.name}`}
                    description={<Space direction="vertical" size={2}><Text>{executionData.feedback.latest.notes || '暂无备注'}</Text><Text code>{JSON.stringify(executionData.feedback.latest.results || {})}</Text></Space>}
                  />
                )}
              </>
            ) : (
              <Text type="secondary">点击生成后，会把最小实验、成功指标、风险、反馈状态和下一步动作收束到这里。</Text>
            )}
          </Space>
        </Card>
        {plan && <>
          <Divider>最小实验方案</Divider>
          <Paragraph><Text strong>数据集：</Text>{plan.dataset}</Paragraph>
          <Space wrap>{plan.baselines?.map(item => <Tag key={item}>基线：{item}</Tag>)}</Space>
          <Space wrap style={{ marginTop: 8 }}>{plan.metrics?.map(item => <Tag color="blue" key={item}>指标：{item}</Tag>)}</Space>
          <List size="small" dataSource={plan.steps || []} renderItem={(item, index) => <List.Item>{index + 1}. {item}</List.Item>} />
        </>}
        {idea.evidence_json?.items && idea.evidence_json.items.length > 0 && <>
          <Divider>证据引用</Divider>
          {idea.evidence_json.collection_sources && idea.evidence_json.collection_sources.length > 0 && (
            <Space wrap style={{ marginBottom: 8 }}>
              {idea.evidence_json.collection_sources.map(source => (
                <Tag color="magenta" key={source.id}>来自分类：{source.name} · {source.evidence_count} 条证据</Tag>
              ))}
            </Space>
          )}
          <Space wrap>{idea.evidence_json.items.map(item => <Tag color={categoryColors[item.category]} key={item.paper_id}>{item.title.slice(0, 36)}</Tag>)}</Space>
        </>}
        {validationData && (
          <>
            <Divider>验证闭环</Divider>
            <Alert
              showIcon
              type={validationData.writing_readiness.status === 'ready' ? 'success' : validationData.writing_readiness.status === 'blocked' ? 'error' : 'warning'}
              message={<Space wrap><Text strong>{validationData.writing_readiness.label}</Text><Tag color={readinessColors[validationData.writing_readiness.status] || 'default'}>{validationData.writing_readiness.status}</Tag><Tag>实验完整度 {Math.round((validationData.coverage.experiment_completeness || 0) * 100)}%</Tag></Space>}
              description={validationData.summary}
              style={{ marginBottom: 12 }}
            />
            <Row gutter={[12, 12]}>
              <Col xs={24} lg={8}>
                <Card size="small" title="撞车风险" style={{ borderRadius: 12, height: '100%' }}>
                  <Space wrap style={{ marginBottom: 8 }}>
                    <Tag color={riskColors[validationData.collision_risk.level] || 'default'}>{validationData.collision_risk.label}</Tag>
                    {validationData.collision_risk.score != null && <Tag>{Math.round(validationData.collision_risk.score * 100)}%</Tag>}
                  </Space>
                  <Paragraph style={{ marginBottom: 8 }}>{validationData.collision_risk.reason}</Paragraph>
                  {validationData.collision_risk.nearest_related_work?.title && <Text type="secondary">最近相似：{validationData.collision_risk.nearest_related_work.title}</Text>}
                </Card>
              </Col>
              <Col xs={24} lg={8}>
                <Card size="small" title="风险与缺口" style={{ borderRadius: 12, height: '100%' }}>
                  {validationData.feasibility_risks.length === 0 ? <Text type="secondary">暂无明显阻塞项</Text> : (
                    <Space direction="vertical" size={6} style={{ width: '100%' }}>
                      {validationData.feasibility_risks.slice(0, 5).map((risk, index) => (
                        <Tag color={riskColors[risk.level] || 'default'} key={`${risk.type}-${index}`} style={{ whiteSpace: 'normal', lineHeight: 1.5 }}>{risk.message}</Tag>
                      ))}
                    </Space>
                  )}
                </Card>
              </Col>
              <Col xs={24} lg={8}>
                <Card size="small" title="下一步动作" style={{ borderRadius: 12, height: '100%' }}>
                  <List size="small" dataSource={validationData.next_actions} renderItem={(item, index) => <List.Item>{index + 1}. {item}</List.Item>} />
                </Card>
              </Col>
            </Row>
            <Card size="small" title="最小实验检查清单" style={{ borderRadius: 12, marginTop: 12 }}>
              <Space wrap>
                {Object.entries(validationData.experiment_checklist).map(([key, group]) => (
                  <Tooltip key={key} title={group.present ? group.items.join('；') : group.missing_tip}>
                    <Tag color={group.present ? 'green' : 'orange'}>{group.present ? '已覆盖' : '待补充'} · {group.label}</Tag>
                  </Tooltip>
                ))}
              </Space>
            </Card>
            {validationData.related_work.length > 0 && (
              <Card size="small" title="相关/冲突工作" style={{ borderRadius: 12, marginTop: 12 }}>
                <Space wrap>
                  {validationData.related_work.slice(0, 5).map(item => <Tag color={item.relation === 'nearest_collision_candidate' ? 'red' : 'blue'} key={item.paper_id || item.title}>{item.title.slice(0, 48)}</Tag>)}
                </Space>
              </Card>
            )}
          </>
        )}
        {idea.evolution_json && <Alert style={{ marginTop: 14 }} type="info" showIcon message="演化版本" description={idea.evolution_json.rationale || '该 Proposal 是根据父版本评审反馈生成的新版本。'} />}
        <Divider>Proposal 决策</Divider>
        <Space wrap>
          {idea.status !== 'pinned' && <Button icon={<PushpinOutlined />} onClick={() => updateDecision(idea.id, 'pinned')}>收藏</Button>}
          {idea.status !== 'rejected' && <Button danger onClick={() => updateDecision(idea.id, 'rejected')}>淘汰</Button>}
          {(idea.status === 'pinned' || idea.status === 'rejected') && <Button onClick={() => updateDecision(idea.id, 'draft')}>恢复待筛选</Button>}
          <Button type="primary" ghost onClick={() => { setEvolvingIdea(idea); setEvolutionFocus(''); }}>演化新版本</Button>
          <Button icon={<HistoryOutlined />} onClick={() => openLineage(idea)}>查看谱系</Button>
          <Button icon={<HistoryOutlined />} onClick={() => openTimeline(idea)}>迭代轨迹</Button>
          <Button icon={<ExperimentOutlined />} onClick={() => openExperiment(idea)}>记录实验反馈</Button>
          <Button icon={<ExperimentOutlined />} loading={executionPack?.loading} onClick={() => loadExecutionPack(idea.id)}>实验推进包</Button>
          <Button icon={<FileSearchOutlined />} loading={validation?.loading} onClick={() => loadIdeaValidation(idea.id)}>验证闭环</Button>
          <Button icon={<FileTextOutlined />} loading={draftingIdeaIds.has(idea.id)} onClick={() => createWritingDraft(idea)}>生成写作草稿</Button>
          <Button type="primary" icon={<MessageOutlined />} onClick={() => openCopilot(idea)}>打开 Idea Copilot</Button>
        </Space>
        <Card size="small" style={{ borderRadius: 12, marginTop: 14, background: '#fbfcff' }}>
          <Space wrap>
            <RobotOutlined style={{ color: '#1677ff' }} />
            <Text strong>Idea Copilot</Text>
            <Text type="secondary">用证据、验证闭环、实验推进包和谱系继续迭代这个 Proposal。</Text>
            {(idea.discussion_log?.length || getDiscuss(idea.id).log.length) > 0 && <Tag color="blue">{idea.discussion_log?.length || getDiscuss(idea.id).log.length} 条讨论</Tag>}
            <Button type="link" icon={<MessageOutlined />} onClick={() => openCopilot(idea)}>进入迭代面板</Button>
          </Space>
        </Card>
        {renderCodeProject(idea)}
      </div>
    );
  };

  const proposalTab = ideas.length === 0 ? (
    <WorkflowEmptyState
      title="还没有 Top Proposal"
      description="候选假设经过去重和评审后，会保存为可讨论、可验证、可写作的 Proposal。"
      icon={<ExperimentOutlined />}
      action={<Button type="primary" icon={<ThunderboltOutlined />} onClick={handleGenerate}>生成 Proposal</Button>}
    />
  ) : (
    <Space direction="vertical" size={14} style={{ width: '100%' }}>
      <Card size="small" style={{ borderRadius: 12 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
          <Space wrap>
            <Tag color="blue">全部 {proposalCounts.all}</Tag>
            <Tag color="default">待筛选 {proposalCounts.draft}</Tag>
            <Tag color="green">已收藏 {proposalCounts.pinned}</Tag>
            <Tag color="red">已淘汰 {proposalCounts.rejected}</Tag>
            <Tag color="purple">已有代码 {proposalCounts.implemented}</Tag>
          </Space>
          <Space wrap>
            <Select size="small" value={proposalFilter} options={proposalFilterOptions} onChange={setProposalFilter} style={{ width: 122 }} />
            <Select size="small" value={proposalSort} options={proposalSortOptions} onChange={setProposalSort} style={{ width: 150 }} />
          </Space>
        </div>
        {recommendedProposal && (
          <Alert
            type="success"
            showIcon
            style={{ marginTop: 12 }}
            message={<Space wrap><Text strong>推荐优先推进</Text><Tag color="green">{recommendedProposal.title}</Tag><Tag>综合 {proposalReviewScore(recommendedProposal).toFixed(1)}</Tag><Tag>证据 {proposalEvidenceCount(recommendedProposal)}</Tag></Space>}
            description="基于当前排序和过滤条件，从未淘汰 Proposal 中选择最高分项。"
          />
        )}
      </Card>
      {visibleProposals.length === 0 ? (
        <WorkflowEmptyState
          title="当前筛选条件下没有 Proposal"
          description="可以切回全部状态，或调整排序后继续比较候选项。"
          icon={<FileSearchOutlined />}
          action={<Button onClick={() => setProposalFilter('all')} style={{ borderRadius: 10 }}>查看全部 Proposal</Button>}
        />
      ) : (
        <Collapse accordion items={visibleProposals.map((idea, index) => {
          const isRecommended = recommendedProposal?.id === idea.id;
          return {
            key: idea.id,
            label: <Space wrap><BulbOutlined style={{ color: isRecommended ? '#52c41a' : '#faad14' }} /><Text strong>{idea.title}</Text>{isRecommended && <Tag color="green">推荐</Tag>}<Tag color={idea.status === 'pinned' ? 'green' : idea.status === 'rejected' ? 'red' : 'default'}>{statusLabels[idea.status] || idea.status}</Tag><Tag>#{index + 1}</Tag>{idea.parent_idea_id && <Tag color="cyan">第 {idea.evolution_json?.round || 2} 轮</Tag>}{idea.review_json?.aggregate_score != null && <Tag color="purple">综合 {idea.review_json.aggregate_score}</Tag>}<Tag>证据 {proposalEvidenceCount(idea)}</Tag></Space>,
            extra: <Space onClick={event => event.stopPropagation()}>
              <Checkbox checked={selectedIdeaIds.includes(idea.id)} onChange={event => toggleCompare(idea.id, event.target.checked)}>比较</Checkbox>
              {idea.status !== 'pinned' && <Button size="small" type="text" icon={<PushpinOutlined />} onClick={() => updateDecision(idea.id, 'pinned')}>收藏</Button>}
              {idea.status !== 'rejected' && <Button size="small" type="text" danger onClick={() => updateDecision(idea.id, 'rejected')}>淘汰</Button>}
              {idea.feasibility_score != null && <Tooltip title="可行性"><Tag icon={<RiseOutlined />} color="blue">{idea.feasibility_score}/10</Tag></Tooltip>}
              {idea.novelty_score != null && <Tooltip title="新颖性"><Tag icon={<StarFilled />} color="gold">{idea.novelty_score}/10</Tag></Tooltip>}
              <Popconfirm title="删除这个 Proposal？" onConfirm={async () => { await api.delete(`/research/ideas/${idea.id}`); setIdeas(previous => previous.filter(item => item.id !== idea.id)); }}>
                <Button danger type="text" size="small" icon={<DeleteOutlined />} />
              </Popconfirm>
            </Space>,
            children: renderProposal(idea),
          };
        })} />
      )}
    </Space>
  );

  const proposalBoardTab = proposalBoardLoading ? (
    <WorkflowLoadingState
      title="正在计算 Proposal 推进看板"
      description="正在汇总验证、实验、讨论和演化信号。"
      icon={<ExperimentOutlined />}
    />
  ) : !proposalBoard || proposalBoard.summary.total === 0 ? (
    <WorkflowEmptyState
      title="推进看板还没有 Proposal"
      description="生成 Proposal 后，这里会按下一步动作自动分组。"
      icon={<ExperimentOutlined />}
      action={<Button type="primary" icon={<ThunderboltOutlined />} onClick={handleGenerate}>生成 Proposal</Button>}
    />
  ) : (
    <Space direction="vertical" size={14} style={{ width: '100%' }}>
      <Card size="small" style={{ borderRadius: 12 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
          <Space wrap>
            <Tag color="blue">全部 {proposalBoard.summary.total}</Tag>
            <Tag color="green">可推进 {proposalBoard.summary.actionable}</Tag>
            {proposalBoard.summary.recommended && <Tag color="purple">推荐 {ideas.find(idea => idea.id === proposalBoard.summary.recommended)?.title || proposalBoard.summary.recommended}</Tag>}
          </Space>
          <Button size="small" icon={<ReloadOutlined />} loading={proposalBoardLoading} onClick={() => loadProposalBoard()}>刷新看板</Button>
        </div>
      </Card>
      <Row gutter={[12, 12]}>
        {proposalBoard.groups.filter(group => group.count > 0).map(group => (
          <Col xs={24} md={12} xl={8} key={group.status}>
            <Card
              size="small"
              title={<Space wrap><Tag color={proposalBoardStatusColors[group.status] || 'default'}>{group.label}</Tag><Text type="secondary">{group.count}</Text></Space>}
              style={{ borderRadius: 8, minHeight: 220, minWidth: 0 }}
            >
              <Space direction="vertical" size={10} style={{ width: '100%' }}>
                {group.items.map(item => {
                  const idea = ideas.find(candidate => candidate.id === item.idea_id);
                  return (
                    <div
                      key={item.idea_id}
                      style={{
                        border: '1px solid #edf0f7',
                        borderRadius: 8,
                        padding: 12,
                        background: '#fbfcff',
                        maxWidth: '100%',
                        minWidth: 0,
                        overflow: 'hidden',
                      }}
                    >
                      <Space direction="vertical" size={8} style={{ width: '100%', minWidth: 0 }}>
                        <Space wrap style={{ width: '100%', minWidth: 0 }}>
                          <Text strong style={{ maxWidth: '100%', overflowWrap: 'anywhere' }}>{item.title}</Text>
                          <Tag color={item.priority >= 75 ? 'green' : item.priority >= 45 ? 'blue' : 'orange'}>优先级 {item.priority}</Tag>
                          <Tag>{statusLabels[item.manual_status] || item.manual_status}</Tag>
                        </Space>
                        <Paragraph ellipsis={{ rows: 2 }} style={{ marginBottom: 0, maxWidth: '100%', overflowWrap: 'anywhere' }}>{item.summary}</Paragraph>
                        <Space wrap style={{ width: '100%', minWidth: 0 }}>
                          <Tag>证据 {item.signals.evidence_count ?? 0}</Tag>
                          <Tag>实验 {Math.round((item.signals.experiment_completeness || 0) * 100)}%</Tag>
                          <Tag>反馈 {item.signals.experiment_feedback_count ?? 0}</Tag>
                          <Tag>讨论 {item.signals.discussion_turns ?? 0}</Tag>
                          {item.signals.proposal_review_readiness && (
                            <Tag color={readinessColors[item.signals.proposal_review_readiness] || 'default'}>
                              审稿 {proposalReviewReadinessLabels[item.signals.proposal_review_readiness] || item.signals.proposal_review_readiness}
                            </Tag>
                          )}
                          {(item.signals.review_objection_count || 0) > 0 && <Tag color="volcano">异议 {item.signals.review_objection_count}</Tag>}
                          {item.signals.has_child_versions && <Tag color="cyan">已有修订版</Tag>}
                        </Space>
                        {item.blockers.length > 0 && (
                          <Space wrap style={{ width: '100%', minWidth: 0 }}>
                            {item.blockers.slice(0, 3).map(blocker => (
                              <span
                                key={blocker}
                                style={{
                                  maxWidth: '100%',
                                  padding: '4px 8px',
                                  borderRadius: 8,
                                  background: '#fff7e6',
                                  color: '#d46b08',
                                  lineHeight: 1.5,
                                  overflowWrap: 'anywhere',
                                }}
                              >
                                {blocker}
                              </span>
                            ))}
                          </Space>
                        )}
                        <Space wrap style={{ width: '100%', minWidth: 0 }}>
                          <Button type="primary" size="small" onClick={() => handleBoardAction(item)}>{item.recommended_action.label}</Button>
                          {idea && <Button size="small" onClick={() => openTimeline(idea)}>轨迹</Button>}
                          {idea && <Button size="small" onClick={() => openCopilot(idea)}>Copilot</Button>}
                        </Space>
                      </Space>
                    </div>
                  );
                })}
              </Space>
            </Card>
          </Col>
        ))}
      </Row>
    </Space>
  );

  const experimentTab = experiments.length === 0 ? (
    <WorkflowEmptyState
      title="还没有实验反馈"
      description="在 Proposal 中记录实验结果后，这里会形成反馈闭环，并支持基于结果继续演化。"
      icon={<ExperimentOutlined />}
    />
  ) : (
    <List dataSource={experiments} renderItem={experiment => (
      <List.Item actions={experiment.idea_id ? [<Button key="evolve" type="link" onClick={() => evolveFromFeedback(experiment)}>根据反馈演化</Button>] : []}>
        <List.Item.Meta
          title={<Space wrap><ExperimentOutlined style={{ color: '#8b5cf6' }} /><Text strong>{experiment.name}</Text>{experiment.dataset && <Tag>{experiment.dataset}</Tag>}</Space>}
          description={<Space direction="vertical" size={2}><Text type="secondary">{experiment.notes || '暂无备注'}</Text><Text code>{JSON.stringify(experiment.results || {})}</Text></Space>}
        />
      </List.Item>
    )} />
  );
  const renderCopilotPanel = () => {
    if (!copilotIdea) return null;
    const discussion = getDiscuss(copilotIdea.id);
    const summary = discussion.context_summary;
    const metadata = discussion.log.slice().reverse().find(entry => entry.role === 'assistant' && entry.metadata)?.metadata || {};
    const risks = discussion.risks?.length ? discussion.risks : metadata.risks || [];
    const nextActions = discussion.next_actions?.length ? discussion.next_actions : metadata.next_actions || [];
    const suggestedQuestions = discussion.suggested_questions?.length ? discussion.suggested_questions : metadata.suggested_questions || [];
    const evolutionFocus = discussion.evolutionFocus || discussion.evolution_focus || metadata.evolution_focus || '';
    return (
      <Drawer
        title={<Space wrap><RobotOutlined style={{ color: '#1677ff' }} /><Text strong>Idea Copilot</Text><Tag color="blue">{copilotModeOptions.find(item => item.value === discussion.mode)?.label}</Tag></Space>}
        width={720}
        open={!!copilotIdea}
        onClose={() => setCopilotIdea(null)}
        extra={<Space>
          <Button type="primary" ghost icon={<HistoryOutlined />} onClick={() => openTimeline(copilotIdea)}>迭代轨迹</Button>
          <Button type="primary" ghost icon={<HistoryOutlined />} onClick={() => openLineage(copilotIdea)}>查看谱系</Button>
        </Space>}
      >
        <Space direction="vertical" size={14} style={{ width: '100%' }}>
          <Card size="small" style={{ borderRadius: 12, background: '#fbfcff' }}>
            <Space direction="vertical" size={8} style={{ width: '100%' }}>
              <Text strong>{copilotIdea.title}</Text>
              <Space wrap>
                <Tag color="purple">证据 {summary?.evidence_count ?? proposalEvidenceCount(copilotIdea)}</Tag>
                <Tag color={summary?.has_validation === false ? 'orange' : 'green'}>验证闭环</Tag>
                <Tag color={summary?.has_execution_pack === false ? 'orange' : 'green'}>实验推进包</Tag>
                <Tag color={summary?.has_lineage || copilotIdea.parent_idea_id ? 'cyan' : 'default'}>谱系</Tag>
                {summary?.missing?.map(item => <Tag color="orange" key={item}>缺少 {item}</Tag>)}
              </Space>
              <Select
                value={discussion.mode}
                options={copilotModeOptions}
                onChange={mode => setDiscuss(copilotIdea.id, { mode })}
                style={{ width: 180 }}
              />
              <Space wrap>
                {copilotQuickPrompts[discussion.mode].map(prompt => (
                  <Button key={prompt} size="small" onClick={() => applyQuickPrompt(prompt)}>{prompt}</Button>
                ))}
              </Space>
            </Space>
          </Card>

          <div style={{ minHeight: 300, maxHeight: '48vh', overflowY: 'auto', padding: 12, border: '1px solid #edf0f7', borderRadius: 12, background: '#f7f9fc' }}>
            {discussion.log.length === 0 && (
              <WorkflowEmptyState
                title="还没有 Copilot 讨论"
                description="选择一个模式，围绕 novelty、实验、写作或下一版演化继续推进这个 Proposal。"
                icon={<MessageOutlined />}
              />
            )}
            {discussion.log.map((entry, index) => (
              <div key={`${entry.role}-${index}`} style={{ display: 'flex', gap: 10, marginBottom: 12, flexDirection: entry.role === 'user' ? 'row-reverse' : 'row' }}>
                <div style={{ width: 28, height: 28, borderRadius: 14, display: 'grid', placeItems: 'center', background: entry.role === 'user' ? '#1677ff' : '#fff', border: '1px solid #e5e7eb', color: entry.role === 'user' ? '#fff' : '#1677ff', flex: '0 0 auto' }}>
                  {entry.role === 'user' ? <UserOutlined /> : <RobotOutlined />}
                </div>
                <div style={{ maxWidth: '86%', padding: '10px 12px', borderRadius: 12, background: entry.role === 'user' ? '#1677ff' : '#fff', color: entry.role === 'user' ? '#fff' : '#1f2937', boxShadow: entry.role === 'assistant' ? '0 1px 4px rgba(15, 23, 42, 0.06)' : 'none' }}>
                  {entry.role === 'assistant' ? <Markdown content={entry.content} /> : <div style={{ whiteSpace: 'pre-wrap' }}>{entry.content}</div>}
                </div>
              </div>
            ))}
          </div>

          {(risks.length > 0 || nextActions.length > 0 || suggestedQuestions.length > 0 || evolutionFocus) && (
            <Row gutter={[12, 12]}>
              <Col xs={24} md={12}>
                <Card size="small" title="风险与缺口" style={{ borderRadius: 12, height: '100%' }}>
                  <Space wrap>{risks.length ? risks.map(item => <Tag color="orange" key={item}>{item}</Tag>) : <Text type="secondary">暂无结构化风险</Text>}</Space>
                </Card>
              </Col>
              <Col xs={24} md={12}>
                <Card size="small" title="下一步" style={{ borderRadius: 12, height: '100%' }}>
                  <List size="small" dataSource={nextActions} locale={{ emptyText: '暂无下一步动作' }} renderItem={(item, index) => <List.Item>{index + 1}. {item}</List.Item>} />
                </Card>
              </Col>
              <Col xs={24}>
                <Card size="small" title="建议追问" style={{ borderRadius: 12 }}>
                  <Space wrap>{suggestedQuestions.map(item => <Button key={item} size="small" onClick={() => applyQuickPrompt(item)}>{item}</Button>)}</Space>
                </Card>
              </Col>
            </Row>
          )}

          <Card size="small" title="讨论转演化" style={{ borderRadius: 12 }}>
            <Space direction="vertical" size={10} style={{ width: '100%' }}>
              <TextArea
                value={evolutionFocus}
                onChange={event => setDiscuss(copilotIdea.id, { evolutionFocus: event.target.value })}
                autoSize={{ minRows: 2, maxRows: 5 }}
                placeholder="把这次讨论收束成下一版 Proposal 的演化焦点"
              />
              <Button
                type="primary"
                icon={<ThunderboltOutlined />}
                loading={discussion.evolving}
                disabled={copilotIdea.status !== 'draft' && copilotIdea.status !== 'pinned'}
                onClick={() => evolveFromCopilot(copilotIdea.id)}
              >
                创建下一版 Proposal
              </Button>
            </Space>
          </Card>

          <Space.Compact style={{ width: '100%' }}>
            <TextArea
              autoSize={{ minRows: 2, maxRows: 6 }}
              value={discussion.msg}
              onChange={event => setDiscuss(copilotIdea.id, { msg: event.target.value })}
              onPressEnter={event => { if (!event.shiftKey) { event.preventDefault(); handleDiscuss(copilotIdea.id); } }}
              placeholder="继续讨论这个 Proposal..."
            />
            <Button type="primary" icon={<SendOutlined />} loading={discussion.loading} onClick={() => handleDiscuss(copilotIdea.id)} />
          </Space.Compact>
        </Space>
      </Drawer>
    );
  };
  const renderTimelineDrawer = () => (
    <Drawer
      title={<Space wrap><HistoryOutlined style={{ color: '#1677ff' }} /><Text strong>Proposal 迭代轨迹</Text>{timelineData && <Tag color="blue">{timelineData.summary.event_count} 个事件</Tag>}</Space>}
      width={720}
      open={timelineOpen}
      onClose={() => setTimelineOpen(false)}
      extra={timelineIdea && <Button type="primary" ghost icon={<ReloadOutlined />} loading={timelineLoading} onClick={() => openTimeline(timelineIdea)}>刷新</Button>}
    >
      {timelineLoading ? (
        <WorkflowLoadingState
          title="正在加载迭代轨迹"
          description="正在汇总创建、讨论、验证、实验反馈和演化版本。"
          icon={<HistoryOutlined />}
        />
      ) : timelineData ? (
        <Space direction="vertical" size={14} style={{ width: '100%' }}>
          <Card size="small" style={{ borderRadius: 12, background: '#fbfcff' }}>
            <Space direction="vertical" size={8} style={{ width: '100%' }}>
              <Text strong>{timelineData.title}</Text>
              <Space wrap>
                <Tag color="blue">事件 {timelineData.summary.event_count}</Tag>
                <Tag color="purple">讨论 {timelineData.summary.discussion_milestones}</Tag>
                <Tag color="green">实验 {timelineData.summary.experiment_count}</Tag>
                <Tag color="cyan">子版本 {timelineData.summary.child_version_count}</Tag>
                {timelineData.summary.latest_event_type && <Tag>{timelineTypeLabels[timelineData.summary.latest_event_type] || timelineData.summary.latest_event_type}</Tag>}
              </Space>
            </Space>
          </Card>
          <Timeline
            mode="left"
            items={timelineData.events.map(event => ({
              color: timelineSeverityColors[event.severity] || 'blue',
              label: new Date(event.timestamp).toLocaleString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' }),
              children: (
                <Card size="small" style={{ borderRadius: 12 }}>
                  <Space direction="vertical" size={8} style={{ width: '100%' }}>
                    <Space wrap>
                      <Tag color={timelineSeverityColors[event.severity] || 'blue'}>{timelineTypeLabels[event.type] || event.type}</Tag>
                      <Text strong>{event.title}</Text>
                    </Space>
                    <Paragraph style={{ marginBottom: 0, whiteSpace: 'pre-wrap' }}>{event.summary}</Paragraph>
                    {event.tags.length > 0 && <Space wrap>{event.tags.map(tag => <Tag key={tag}>{tag}</Tag>)}</Space>}
                    {event.details?.next_actions?.length > 0 && (
                      <Space wrap>{event.details.next_actions.slice(0, 5).map((item: string) => <Tag color="purple" key={item}>{item}</Tag>)}</Space>
                    )}
                    {event.details?.risks?.length > 0 && (
                      <Space wrap>{event.details.risks.slice(0, 5).map((item: any, index: number) => <Tag color="orange" key={`${event.id}-risk-${index}`}>{typeof item === 'string' ? item : item.message || item.type || '风险'}</Tag>)}</Space>
                    )}
                    {event.details?.evolution_focus && <Alert type="info" showIcon message="演化焦点" description={event.details.evolution_focus} />}
                    {event.details?.rationale && <Alert type="info" showIcon message="演化说明" description={event.details.rationale} />}
                    {event.details?.results && Object.keys(event.details.results).length > 0 && <Text code>{JSON.stringify(event.details.results)}</Text>}
                  </Space>
                </Card>
              ),
            }))}
          />
        </Space>
      ) : (
        <WorkflowEmptyState
          title="暂无迭代轨迹"
          description="轨迹会从 Proposal 创建、Copilot 讨论、验证闭环、实验反馈和演化版本中自动汇总。"
          icon={<HistoryOutlined />}
        />
      )}
    </Drawer>
  );
  const renderVersionComparisonDrawer = () => {
    const renderSnapshot = (snapshot?: ProposalVersionSnapshot | null, label = '版本') => {
      if (!snapshot) return <Text type="secondary">暂无版本数据</Text>;
      return (
        <Card size="small" title={<Space wrap><Tag>{label}</Tag><Text strong>{snapshot.title}</Text></Space>} style={{ borderRadius: 12, height: '100%' }}>
          <Space direction="vertical" size={8} style={{ width: '100%' }}>
            <Space wrap>
              <Tag>{statusLabels[snapshot.status] || snapshot.status}</Tag>
              <Tag color="purple">评审 {Number(snapshot.review_score || 0).toFixed(1)}</Tag>
              <Tag color="blue">证据 {snapshot.evidence_count ?? 0}</Tag>
              {snapshot.proposal_review?.writing_readiness && (
                <Tag color={readinessColors[snapshot.proposal_review.writing_readiness] || 'default'}>
                  {proposalReviewReadinessLabels[snapshot.proposal_review.writing_readiness] || snapshot.proposal_review.writing_readiness}
                </Tag>
              )}
            </Space>
            <Paragraph style={{ marginBottom: 0 }}><Text strong>假设：</Text>{snapshot.hypothesis || '暂无'}</Paragraph>
            <Paragraph style={{ marginBottom: 0 }}><Text strong>技术路线：</Text>{snapshot.approach || '暂无'}</Paragraph>
            <Paragraph style={{ marginBottom: 0 }}><Text strong>最小实验：</Text>{(snapshot.experiment_plan as ExperimentPlan)?.dataset || '暂无数据集'}</Paragraph>
          </Space>
        </Card>
      );
    };
    return (
      <Drawer
        title={<Space wrap><HistoryOutlined style={{ color: '#1677ff' }} /><Text strong>Proposal 版本对比</Text>{versionComparisonIdea && <Tag color="blue">{versionComparisonIdea.title}</Tag>}</Space>}
        width={920}
        open={versionComparisonOpen}
        onClose={() => setVersionComparisonOpen(false)}
        extra={versionComparisonIdea && <Button type="primary" ghost icon={<ReloadOutlined />} loading={versionComparisonLoading} onClick={() => openVersionComparison(versionComparisonIdea)}>刷新</Button>}
      >
        {versionComparisonLoading ? (
          <WorkflowLoadingState
            title="正在加载版本对比"
            description="正在对比父版本和当前修订版本的核心字段。"
            icon={<HistoryOutlined />}
          />
        ) : versionComparison ? (
          <Space direction="vertical" size={14} style={{ width: '100%' }}>
            {!versionComparison.has_parent && (
              <Alert type="info" showIcon message="当前 Proposal 没有父版本" description="版本对比会在审稿修订、Copilot 演化或实验反馈演化生成子版本后显示父子差异。" />
            )}
            {versionComparison.review_source?.source === 'proposal_review' && (
              <Alert
                type="success"
                showIcon
                message="审稿修订来源"
                description={versionComparison.review_source.review_focus || '该版本由结构化审稿包驱动生成。'}
              />
            )}
            <Row gutter={[12, 12]}>
              <Col xs={24} lg={12}>{renderSnapshot(versionComparison.parent, '父版本')}</Col>
              <Col xs={24} lg={12}>{renderSnapshot(versionComparison.current, versionComparison.has_parent ? '当前版本' : '当前 Proposal')}</Col>
            </Row>
            {versionComparison.revision_rationale && <Alert type="info" showIcon message="修订说明" description={versionComparison.revision_rationale} />}
            {versionComparison.review_source?.review_objections?.length ? (
              <Card size="small" title="继承的审稿异议" style={{ borderRadius: 12 }}>
                <Space wrap>
                  {versionComparison.review_source.review_objections.map(item => <Tag color="volcano" key={item}>{item}</Tag>)}
                </Space>
              </Card>
            ) : null}
            {versionComparison.changes.length > 0 ? (
              <Card size="small" title="字段级变化" style={{ borderRadius: 12 }}>
                <Space direction="vertical" size={10} style={{ width: '100%' }}>
                  {versionComparison.changes.map(change => (
                    <div className="proposal-version-change" key={change.field}>
                      <Text strong>{change.label}</Text>
                      <Row gutter={[8, 8]} style={{ marginTop: 6 }}>
                        <Col xs={24} md={12}>
                          <div className="proposal-version-side">
                            <Text type="secondary">修改前</Text>
                            <Paragraph style={{ marginBottom: 0, whiteSpace: 'pre-wrap' }}>
                              {typeof change.before === 'object' ? JSON.stringify(change.before, null, 2) : change.before || '暂无'}
                            </Paragraph>
                          </div>
                        </Col>
                        <Col xs={24} md={12}>
                          <div className="proposal-version-side is-after">
                            <Text type="secondary">修改后</Text>
                            <Paragraph style={{ marginBottom: 0, whiteSpace: 'pre-wrap' }}>
                              {typeof change.after === 'object' ? JSON.stringify(change.after, null, 2) : change.after || '暂无'}
                            </Paragraph>
                          </div>
                        </Col>
                      </Row>
                    </div>
                  ))}
                </Space>
              </Card>
            ) : (
              <WorkflowEmptyState
                title="暂无明显字段变化"
                description="当前版本和父版本的标题、假设、技术路线、实验计划与证据数量基本一致。"
                icon={<HistoryOutlined />}
              />
            )}
          </Space>
        ) : (
          <WorkflowEmptyState
            title="暂无版本对比"
            description="请从 Proposal 详情或推进看板打开一个修订版本。"
            icon={<HistoryOutlined />}
          />
        )}
      </Drawer>
    );
  };

  return (
    <PageShell
      title={project?.name || '研究工作台'}
      subtitle={project?.description || '把一个研究方向逐步收敛为可验证的 Proposal。'}
      icon={<ExperimentOutlined />}
      maxWidth={1280}
      actions={(
        <>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/research')} style={{ borderRadius: 10 }}>返回研究方向</Button>
          <Button icon={<ShareAltOutlined />} onClick={handleShare} style={{ borderRadius: 10 }}>分享</Button>
          <Button disabled={selectedIdeaIds.length < 2} onClick={openComparison} style={{ borderRadius: 10 }}>比较 Proposal ({selectedIdeaIds.length})</Button>
          <Space style={{ padding: '4px 10px', borderRadius: 8, border: '1px solid #f0f0f0', background: '#fff' }}>
            <Text>联网补充文献</Text>
            <Switch checked={externalSearch} onChange={setExternalSearch} />
          </Space>
          <Button icon={<NodeIndexOutlined />} loading={gapPreviewing} onClick={handleGapPreview} style={{ borderRadius: 10 }}>预览 Gap Map</Button>
          {generating ? (
            <Button danger icon={<StopOutlined />} onClick={handleStopGeneration} style={{ borderRadius: 10 }}>停止生成</Button>
          ) : (
            <Button type="primary" icon={<ThunderboltOutlined />} onClick={handleGenerate} style={{ borderRadius: 10 }}>生成 Proposal</Button>
          )}
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

      <Card style={{ borderRadius: 14, marginBottom: 18 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap', marginBottom: 10 }}>
          <div>
            <Space wrap style={{ marginBottom: 4 }}>
              <Text strong>Research Idea Workbench</Text>
              <Tag color={runStatusColor}>{runStatusLabel}</Tag>
              {run && <Tag>当前阶段：{currentStageTitle}</Tag>}
            </Space>
            <br />
            <Text type="secondary">{run?.message || '从证据开始，而不是让模型直接猜一个 Idea'}</Text>
          </div>
        </div>
        {(generating || run) && (
          <WorkflowProgressState
            title={generating ? '正在生成 Proposal' : '最近一次工作台进度'}
            description={run?.message || '从证据开始推进到 Gap Map、候选池和 Top Proposal。'}
            percent={run?.progress}
            phase={currentStageTitle}
            statusText={runStatusLabel}
            icon={generating ? <ThunderboltOutlined /> : <ExperimentOutlined />}
            compact
            style={{ marginBottom: 12 }}
          />
        )}
        <Steps current={stageIndex} size="small" responsive items={stageItems.map(([, title]) => ({ title }))} />
        <Space wrap style={{ marginTop: 12 }}>
          {generating && <Button danger icon={<StopOutlined />} onClick={handleStopGeneration}>停止当前生成</Button>}
          {!generating && (runHasTerminalError || runWasCancelled) && <Button type="primary" icon={<ReloadOutlined />} onClick={handleGenerate}>{runWasCancelled ? '重新开始生成' : '重试生成'}</Button>}
          {runCompleted && ideas.length > 0 && <Button type="primary" ghost icon={<ExperimentOutlined />} onClick={() => setActiveWorkbenchTab('proposal-board')}>查看推进看板</Button>}
        </Space>
        {runHasTerminalError && <Alert type="error" showIcon message="最近一次运行失败" description={<Space direction="vertical" size={4}><Text>{run.error}</Text><Text type="secondary">最后阶段：{currentStageTitle}</Text></Space>} style={{ marginTop: 12 }} />}
        {runWasCancelled && <Alert type="warning" showIcon message="生成已停止" description={`已保留 ${currentStageTitle} 阶段之前的进度和中间产物，可随时重新开始。`} style={{ marginTop: 12 }} />}
        {runCompleted && ideas.length > 0 && <Alert type="success" showIcon message="Top Proposal 已就绪" description={`已保存 ${ideas.length} 个 Proposal，可以进入 Top Proposal 继续筛选、比较、验证或生成写作草稿。`} style={{ marginTop: 12 }} />}
      </Card>

      <Row gutter={[18, 18]}>
        <Col xs={24} lg={6}>
          <Card title="研究简报" style={{ borderRadius: 14, marginBottom: 14 }}>
            <Space wrap>{project.keywords?.map(keyword => <Tag color="purple" key={keyword}>{keyword}</Tag>)}</Space>
            <Divider />
            <Text type="secondary">工作台运行</Text><Title level={4} style={{ margin: '4px 0' }}>{run ? run.status : '尚未启动'}</Title>
            <Text type="secondary">已保存 Proposal：{ideas.length}</Text>
          </Card>
          <div style={{ marginBottom: 14 }}>
            <Space direction="vertical" size={8} style={{ width: '100%' }}>
              <Space>
                <Text strong>资源反馈</Text>
                <WorkspaceIssueReporter
                  resourceType="research_projects"
                  resourceId={project.id}
                  resourceTitle={project.name}
                  resourcePath={`/research/${project.id}`}
                />
              </Space>
              <WorkspaceResourceLinks resourceType="research_projects" resourceId={project.id} title="所属项目空间" />
            </Space>
          </div>
          <Card
            title={<Space><span>相关论文</span>{papersCached && <Tag color="green">缓存</Tag>}</Space>}
            loading={papersLoading}
            style={{ borderRadius: 14 }}
            extra={
              <Tooltip title={relatedPapersUpdatedText ? `上次刷新：${relatedPapersUpdatedText}` : '重新计算相关论文推荐'}>
                <Button
                  type="text"
                  size="small"
                  icon={<ReloadOutlined />}
                  loading={papersLoading}
                  onClick={() => projectId && loadRelatedPapers(projectId, true)}
                >
                  刷新
                </Button>
              </Tooltip>
            }
          >
            {relatedPapersUpdatedText && (
              <Text type="secondary" style={{ display: 'block', fontSize: 12, marginBottom: 8 }}>
                {papersCached ? '已使用缓存' : '刚刚刷新'} · {relatedPapersUpdatedText}
              </Text>
            )}
            <List size="small" dataSource={relatedPapers} locale={{ emptyText: '暂无匹配论文' }} renderItem={paper => (
              <List.Item style={{ cursor: 'pointer' }} onClick={() => navigate(`/papers/${paper.id}`)}>
                <List.Item.Meta title={<Text ellipsis>{paper.title}</Text>} description={<Space>{paper.year && <Tag>{paper.year}</Tag>}<Tag color="blue">{Math.round((paper.similarity || 0) * 100)}%</Tag></Space>} />
              </List.Item>
            )} />
          </Card>
        </Col>
        <Col xs={24} lg={18}>
          <Card style={{ borderRadius: 14 }} styles={{ body: { paddingTop: 8 } }}>
            <Tabs activeKey={activeWorkbenchTab} onChange={setActiveWorkbenchTab} items={[
              { key: 'evidence', label: <Space><FileSearchOutlined />证据地图 <Tag>{evidenceItems.length}</Tag></Space>, children: evidenceTab },
              { key: 'gaps', label: <Space><NodeIndexOutlined />Gap Map <Tag>{gaps.length}</Tag></Space>, children: gapTab },
              { key: 'candidates', label: <Space><BulbOutlined />候选池 <Tag>{candidates.length}</Tag></Space>, children: candidateTab },
              { key: 'proposal-board', label: <Space><ExperimentOutlined />推进看板 <Tag color="blue">{proposalBoard?.summary.total || ideas.length}</Tag></Space>, children: proposalBoardTab },
              { key: 'proposals', label: <Space><ExperimentOutlined />Top Proposal <Tag color="purple">{ideas.length}</Tag></Space>, children: proposalTab },
              { key: 'experiments', label: <Space><ExperimentOutlined />实验反馈 <Tag>{experiments.length}</Tag></Space>, children: experimentTab },
            ]} />
          </Card>
        </Col>
      </Row>
      {!run && <div style={{ textAlign: 'center', padding: 28 }}><Button type="primary" size="large" icon={<RocketOutlined />} onClick={handleGenerate}>从论文证据开始生成</Button></div>}
      <Modal open={compareOpen} title="Proposal 并排比较" width={1180} footer={null} onCancel={() => setCompareOpen(false)}>
        <Row gutter={[12, 12]}>
          {compareIdeas.map(idea => (
            <Col xs={24} md={compareIdeas.length > 2 ? 12 : 24 / compareIdeas.length} key={idea.id}>
              <Card size="small" style={{ height: '100%', borderRadius: 12 }} title={<Text strong>{idea.title}</Text>}>
                <Space wrap style={{ marginBottom: 10 }}><Tag>{statusLabels[idea.status] || idea.status}</Tag>{idea.review_json?.aggregate_score != null && <Tag color="purple">综合 {idea.review_json.aggregate_score}</Tag>}</Space>
                <Paragraph><Text strong>假设：</Text>{idea.hypothesis || '暂无'}</Paragraph>
                <Paragraph><Text strong>证据数量：</Text>{idea.evidence_json?.items?.length || 0}</Paragraph>
                <Paragraph><Text strong>最小实验：</Text>{idea.experiment_plan?.dataset || '暂无'}</Paragraph>
                <Space wrap>{Object.entries(idea.review_json?.scores || {}).map(([key, value]) => <Tag color="blue" key={key}>{scoreLabels[key] || key} {value}</Tag>)}</Space>
                {idea.evolution_json?.rationale && <Paragraph style={{ marginTop: 10 }}><Text strong>演化说明：</Text>{idea.evolution_json.rationale}</Paragraph>}
              </Card>
            </Col>
          ))}
        </Row>
      </Modal>
      <Modal open={!!evolvingIdea} title="演化 Proposal 新版本" confirmLoading={evolving} onOk={evolveProposal} onCancel={() => { setEvolvingIdea(null); setEvolutionFocus(''); }} okText="开始演化">
        <Paragraph type="secondary">原 Proposal 会完整保留，新版本会记录父子关系和演化理由。可以填写你希望优先改进的方向。</Paragraph>
        <TextArea value={evolutionFocus} onChange={event => setEvolutionFocus(event.target.value)} autoSize={{ minRows: 3, maxRows: 6 }} placeholder="例如：优先降低实验成本，或者增强跨数据集泛化验证" />
      </Modal>
      <Modal
        open={!!reviewRevisionIdea}
        title="按审稿意见修订 Proposal"
        confirmLoading={reviewRevisionLoading}
        onOk={reviseFromReview}
        onCancel={() => { setReviewRevisionIdea(null); setReviewRevisionFocus(''); }}
        okText="生成修订版"
      >
        <Space direction="vertical" size={12} style={{ width: '100%' }}>
          <Paragraph type="secondary">原 Proposal 会保留，新版本会记录审稿来源、主要异议和必要实验。</Paragraph>
          {reviewRevisionIdea?.review_json?.proposal_review && (
            <Alert
              showIcon
              type={reviewRevisionIdea.review_json.proposal_review.writing_readiness === 'blocked' ? 'error' : 'warning'}
              message={reviewRevisionIdea.review_json.proposal_review.summary || '结构化审稿包'}
              description={reviewRevisionIdea.review_json.proposal_review.revision_plan?.slice(0, 3).join('；') || reviewRevisionIdea.review_json.proposal_review.next_revision_focus}
            />
          )}
          <TextArea
            value={reviewRevisionFocus}
            onChange={event => setReviewRevisionFocus(event.target.value)}
            autoSize={{ minRows: 4, maxRows: 8 }}
            placeholder="补充这一版最应该优先处理的审稿意见，例如：先把 novelty 和跨数据集实验讲清楚"
          />
        </Space>
      </Modal>
      <Modal open={experimentOpen} title="记录实验反馈" onOk={saveExperiment} onCancel={() => setExperimentOpen(false)} okText="保存反馈">
        <Space direction="vertical" style={{ width: '100%' }}>
          <Input prefix={<PlusOutlined />} value={experimentName} onChange={event => setExperimentName(event.target.value)} placeholder="实验名称，例如：跨数据集 baseline" />
          <Input value={experimentDataset} onChange={event => setExperimentDataset(event.target.value)} placeholder="数据集" />
          <TextArea value={experimentResults} onChange={event => setExperimentResults(event.target.value)} autoSize={{ minRows: 3, maxRows: 6 }} placeholder={'结构化结果 JSON，例如：{"accuracy": 0.82, "latency_ms": 31}'} />
          <TextArea value={experimentNotes} onChange={event => setExperimentNotes(event.target.value)} autoSize={{ minRows: 2, maxRows: 5 }} placeholder="失败案例、观察和下一轮改进方向" />
        </Space>
      </Modal>
      <Modal open={lineageOpen} title="Proposal 演化谱系" footer={null} onCancel={() => setLineageOpen(false)}>
        <Steps direction="vertical" items={lineage.map(idea => ({
          title: <Space wrap><Text strong>{idea.title}</Text><Tag color="cyan">第 {idea.evolution_json?.round || 1} 轮</Tag></Space>,
          description: idea.evolution_json?.rationale || '初始 Proposal',
        }))} />
      </Modal>
      {renderCopilotPanel()}
      {renderTimelineDrawer()}
      {renderVersionComparisonDrawer()}
    </PageShell>
  );
};

export default ResearchProjectPage;
