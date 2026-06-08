import React, { useState, useCallback, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import {
  Alert, Card, Button, Input, Tag, Typography, Space, message,
  Select, Tooltip, List, Divider, Row, Col, Empty, Segmented, Upload,
  Collapse,
} from 'antd';
import {
  EditOutlined, SearchOutlined, FileTextOutlined,
  CopyOutlined, BulbOutlined,
  BookOutlined, FormOutlined, ReadOutlined, SwapOutlined,
  AuditOutlined, FolderOutlined, RocketOutlined, DownloadOutlined,
  FileZipOutlined, UploadOutlined, CodeOutlined, RobotOutlined, PlusOutlined,
  MenuFoldOutlined, MenuUnfoldOutlined,
} from '@ant-design/icons';
import api from '../services/api';
import Markdown from '../components/Markdown';
import WorkspaceResourceLinks from '../components/WorkspaceResourceLinks';
import WorkspaceIssueReporter from '../components/WorkspaceIssueReporter';
import WorkflowStepGuide from '../components/WorkflowStepGuide';
import PageShell from '../components/PageShell';
import ApiErrorAlert from '../components/ApiErrorAlert';
import { WorkflowEmptyState } from '../components/WorkflowState';
import { DiffViewer, WritingProjectPanel, SectionEditor } from '../components/writing';
import AuthenticatedPdfPreview from '../components/writing/AuthenticatedPdfPreview';
import { getApiErrorDetails, type ApiErrorDetails } from '../services/apiError';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

// ───────────────── 样式常量 ─────────────────
const cardStyle = { borderRadius: 12, border: '1px solid #f0f0f0', transition: 'all 0.3s' };
const inputStyle = { borderRadius: 10, fontSize: 14 };
const primaryBtn = { borderRadius: 10, height: 40, fontWeight: 500 };
const resultCard = { marginTop: 20, borderRadius: 12, border: '1px solid #e8e8e8', overflow: 'hidden' };

// ───────────────── 输入/输出卡片 ─────────────────
const ToolCard: React.FC<{
  icon: React.ReactNode; color: string; title: string; desc: string;
  children: React.ReactNode;
}> = ({ icon, color, title, desc, children }) => (
  <Card
    style={{ ...cardStyle, borderTop: `3px solid ${color}` }}
    styles={{ body: { padding: 24 } }}
  >
    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 16, marginBottom: 20 }}>
      <div style={{
        width: 48, height: 48, borderRadius: 14, background: `${color}15`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 22, color, flexShrink: 0,
      }}>
        {icon}
      </div>
      <div>
        <Title level={5} style={{ margin: 0 }}>{title}</Title>
        <Text type="secondary" style={{ fontSize: 13 }}>{desc}</Text>
      </div>
    </div>
    {children}
  </Card>
);

const ResultCard: React.FC<{ children: React.ReactNode; onCopy?: () => void; extra?: React.ReactNode }> = ({ children, onCopy, extra }) => (
  <Card style={resultCard} styles={{ body: { padding: 20 } }}
    extra={extra || (onCopy ? <Button size="small" icon={<CopyOutlined />} onClick={onCopy} style={{ borderRadius: 8 }}>复制</Button> : undefined)}
  >
    {children}
  </Card>
);

const LoadingDots = () => (
  <Space size={5} style={{ padding: '20px 0' }}>
    {[0, 0.15, 0.3].map((d, i) => (
      <div key={i} style={{
        width: 8, height: 8, borderRadius: '50%',
        background: '#667eea',
        animation: `bounce 1.4s infinite ease-in-out ${d}s`,
      }} />
    ))}
  </Space>
);

const workbenchStageSteps = [
  { key: 'setup', label: '结构', target: 'sections' },
  { key: 'drafting', label: '初稿', target: 'sections' },
  { key: 'evidence', label: '证据', target: 'evidence' },
  { key: 'review', label: '校验', target: 'citations' },
  { key: 'export', label: '导出', target: 'export' },
];

const workbenchTargetLabels: Record<string, string> = {
  brief: '写作准备包',
  sections: '章节',
  evidence: '证据',
  'evidence-table': '证据表',
  citations: '引用校验',
  'submission-template': '投稿模板',
  export: '导出',
};

const workbenchPriorityLabels: Record<string, string> = {
  high: '高优先级',
  medium: '建议处理',
  low: '可稍后',
};

type WritingBriefEvidenceRef = {
  id?: string;
  marker?: string;
  title?: string;
  role_label?: string;
  snippet?: string;
  paper_id?: string;
};

type WritingBriefClaim = {
  claim?: string;
  status?: string;
  evidence_refs?: WritingBriefEvidenceRef[];
  writing_use?: string;
  priority?: number;
};

type WritingBriefOutlineItem = {
  section?: string;
  purpose?: string;
  seed_content?: string;
  evidence_ids?: string[];
};

type WritingBriefContribution = {
  step?: number;
  claim?: string;
  evidence_status?: string;
  writing_goal?: string;
};

type ProposalWritingBrief = {
  title_candidates?: string[];
  abstract_draft?: string;
  contribution_chain?: WritingBriefContribution[];
  section_outline?: WritingBriefOutlineItem[];
  claim_evidence_map?: WritingBriefClaim[];
  unsafe_claims?: string[];
  evidence_gaps?: string[];
  experiment_writing_plan?: string[];
  limitations?: string[];
  evidence_status?: string;
  evidence_count?: number;
  local_paper_count?: number;
  source_project_name?: string;
};

const getProjectWritingBrief = (project: any): ProposalWritingBrief | null => {
  const brief = project?.metadata_json?.writing_brief;
  return brief && typeof brief === 'object' ? brief : null;
};

const getBriefClaimStatusCounts = (brief?: ProposalWritingBrief | null) => {
  const claims = brief?.claim_evidence_map || [];
  return {
    total: claims.length,
    supported: claims.filter(item => item.status === 'supported').length,
    partial: claims.filter(item => item.status === 'partially_supported').length,
    unsupported: claims.filter(item => item.status === 'unsupported').length,
  };
};

const hasWritingBriefRisk = (brief?: ProposalWritingBrief | null) => {
  const counts = getBriefClaimStatusCounts(brief);
  return Boolean((brief?.unsafe_claims || []).length || (brief?.evidence_gaps || []).length || counts.unsupported);
};

const claimStatusLabel = (status?: string) => {
  if (status === 'supported') return '已支撑';
  if (status === 'partially_supported') return '部分支撑';
  if (status === 'unsupported') return '缺证据';
  return '待确认';
};

const claimStatusColor = (status?: string) => {
  if (status === 'supported') return 'green';
  if (status === 'partially_supported') return 'gold';
  if (status === 'unsupported') return 'red';
  return 'default';
};

const stageStepState = (activeKey?: string) => {
  const activeIndex = Math.max(0, workbenchStageSteps.findIndex(step => step.key === activeKey));
  return workbenchStageSteps.map((step, index) => ({
    ...step,
    state: index < activeIndex ? 'done' : index === activeIndex ? 'current' : 'pending',
  }));
};

const buildWorkbenchBlockers = (summary: any, brief?: ProposalWritingBrief | null) => {
  const blockers: { key: string; label: string; severity: 'high' | 'medium' | 'low'; target: string }[] = [];
  const progress = summary?.progress || {};
  const evidence = summary?.evidence || {};
  const citations = summary?.citations || {};
  const submission = summary?.submission || {};
  const evidenceTotal = evidence.total || 0;
  const localEvidence = evidence.local || 0;
  const briefCounts = getBriefClaimStatusCounts(brief);

  if (progress.empty_sections > 0) {
    blockers.push({ key: 'empty-sections', label: `空章节 ${progress.empty_sections}`, severity: 'high', target: 'sections' });
  }
  if (briefCounts.unsupported > 0) {
    blockers.push({ key: 'unsupported-brief-claims', label: `未支撑 Claim ${briefCounts.unsupported}`, severity: 'high', target: 'brief' });
  }
  if ((brief?.unsafe_claims || []).length > 0) {
    blockers.push({ key: 'unsafe-brief-claims', label: `风险 Claim ${brief?.unsafe_claims?.length || 0}`, severity: 'high', target: 'brief' });
  }
  if ((brief?.evidence_gaps || []).length > 0) {
    blockers.push({ key: 'brief-evidence-gaps', label: `证据缺口 ${brief?.evidence_gaps?.length || 0}`, severity: 'medium', target: 'evidence' });
  }
  if (progress.short_sections > 0) {
    blockers.push({ key: 'short-sections', label: `偏短章节 ${progress.short_sections}`, severity: 'medium', target: 'sections' });
  }
  if (evidenceTotal === 0) {
    blockers.push({ key: 'missing-evidence', label: '缺少证据卡', severity: 'high', target: 'evidence' });
  } else if (localEvidence < Math.max(1, Math.ceil(evidenceTotal * 0.5))) {
    blockers.push({ key: 'weak-local-evidence', label: `本地证据 ${localEvidence}/${evidenceTotal}`, severity: 'high', target: 'evidence' });
  }
  if (citations.unmatched > 0) {
    blockers.push({ key: 'unmatched-citations', label: `未匹配引用 ${citations.unmatched}`, severity: 'high', target: 'citations' });
  }
  if (!submission.template_status || submission.template_status === 'missing') {
    blockers.push({ key: 'missing-template', label: '未绑定官方模板', severity: 'medium', target: 'submission-template' });
  }
  return blockers;
};

const WritingPage: React.FC = () => {
  const location = useLocation();
  const [assistantMode, setAssistantMode] = useState<'paper' | 'grant'>('paper');
  const [paperWorkflow, setPaperWorkflow] = useState<'manuscript' | 'survey' | 'tools'>('manuscript');

  // ── 状态 ──
  const [citeText, setCiteText] = useState('');
  const [citations, setCitations] = useState<any[]>([]);
  const [citeLoading, setCiteLoading] = useState(false);
  const [rwTopic, setRwTopic] = useState('');
  const [rwResult, setRwResult] = useState('');
  const [rwTable, setRwTable] = useState('');
  const [rwLoading, setRwLoading] = useState(false);
  const [rwTableLoading, setRwTableLoading] = useState(false);
  const [polishText, setPolishText] = useState('');
  const [polishStyle, setPolishStyle] = useState('academic');
  const [polishResult, setPolishResult] = useState('');
  const [polishLoading, setPolishLoading] = useState(false);
  const [absTitle, setAbsTitle] = useState('');
  const [absKeyPoints, setAbsKeyPoints] = useState('');
  const [absResult, setAbsResult] = useState('');
  const [absLoading, setAbsLoading] = useState(false);
  const [lrTopic, setLrTopic] = useState('');
  const [lrResult, setLrResult] = useState<any>(null);
  const [lrLoading, setLrLoading] = useState(false);
  const [compareIds, setCompareIds] = useState('');
  const [compareResult, setCompareResult] = useState('');
  const [compareLoading, setCompareLoading] = useState(false);
  const [grantTopic, setGrantTopic] = useState('');
  const [grantBg, setGrantBg] = useState('');
  const [grantSection, setGrantSection] = useState('立项依据');
  const [grantResult, setGrantResult] = useState('');
  const [grantLoading, setGrantLoading] = useState(false);
  const [grantReview, setGrantReview] = useState('');
  const [grantReviewing, setGrantReviewing] = useState(false);
  const [grantPolishText, setGrantPolishText] = useState('');
  const [grantPolishResult, setGrantPolishResult] = useState('');
  const [grantPolishing, setGrantPolishing] = useState(false);
  const [grantInnovResult, setGrantInnovResult] = useState('');
  const [grantInnovLoading, setGrantInnovLoading] = useState(false);
  const [diffResult, setDiffResult] = useState<any>(null);
  const [diffLoading, setDiffLoading] = useState(false);
  const [selectedProject, setSelectedProject] = useState<any>(null);
  const [supportRailCollapsed, setSupportRailCollapsed] = useState(false);
  const [projectSections, setProjectSections] = useState<any[]>([]);
  const [evidenceCards, setEvidenceCards] = useState<any[]>([]);
  const [evidenceCoverage, setEvidenceCoverage] = useState<any>(null);
  const [evidenceLoading, setEvidenceLoading] = useState(false);
  const [evidenceTableLoading, setEvidenceTableLoading] = useState(false);
  const [evidenceTable, setEvidenceTable] = useState<any>(null);
  const [activeSectionId, setActiveSectionId] = useState<string | null>(null);
  const [citationChecks, setCitationChecks] = useState<Record<string, any>>({});
  const [citationChecking, setCitationChecking] = useState<Record<string, boolean>>({});
  const [qualityChecks, setQualityChecks] = useState<Record<string, any>>({});
  const [qualityChecking, setQualityChecking] = useState<Record<string, boolean>>({});
  const [latexPreviewChecks, setLatexPreviewChecks] = useState<Record<string, any>>({});
  const [latexPreviewing, setLatexPreviewing] = useState<Record<string, boolean>>({});
  const [manuscriptPreview, setManuscriptPreview] = useState<any>(null);
  const [manuscriptPreviewing, setManuscriptPreviewing] = useState(false);
  const [sectionAiState, setSectionAiState] = useState<Record<string, { loading?: boolean; action?: string; status?: string; output?: string }>>({});
  const [creatingSection, setCreatingSection] = useState(false);
  const [draftTopic, setDraftTopic] = useState('');
  const [draftLoading, setDraftLoading] = useState(false);
  const [projectRefreshSignal, setProjectRefreshSignal] = useState(0);
  const [exportReadiness, setExportReadiness] = useState<any>(null);
  const [exportPackage, setExportPackage] = useState<any>(null);
  const [exportLoading, setExportLoading] = useState(false);
  const [workbenchSummary, setWorkbenchSummary] = useState<any>(null);
  const [workbenchLoading, setWorkbenchLoading] = useState(false);
  const [submissionVenue, setSubmissionVenue] = useState('');
  const [submissionYear, setSubmissionYear] = useState('');
  const [submissionTemplateFile, setSubmissionTemplateFile] = useState<any>(null);
  const [submissionInspection, setSubmissionInspection] = useState<any>(null);
  const [submissionUploading, setSubmissionUploading] = useState(false);
  const [pageActionError, setPageActionError] = useState<{ title: string; detail: ApiErrorDetails } | null>(null);

  const showPageError = useCallback((title: string, error: unknown, fallback = title) => {
    const detail = getApiErrorDetails(error, { fallback });
    setPageActionError({ title, detail });
    message.warning(detail.message);
  }, []);

  const handleCopy = (text: string) => { navigator.clipboard.writeText(text); message.success('已复制'); };
  const matchColor = (status?: string) => status === 'strong' ? 'green' : status === 'partial' ? 'gold' : 'red';
  const decisionColor = (confidence?: string) => confidence === 'high' ? 'green' : confidence === 'medium' ? 'gold' : 'red';
  const exportStatusColor = (status?: string) => status === 'ready' ? 'green' : status === 'needs_attention' ? 'gold' : 'red';
  const riskColor = (risk?: string) => risk === 'high' ? 'red' : risk === 'medium' ? 'gold' : risk === 'low' ? 'blue' : 'green';
  const priorityColor = (priority?: string) => priority === 'high' ? 'red' : priority === 'medium' ? 'gold' : 'blue';
  const selectedWritingBrief = getProjectWritingBrief(selectedProject);
  const selectedBriefClaimCounts = getBriefClaimStatusCounts(selectedWritingBrief);
  const scrollToWorkbenchTarget = (target?: string) => {
    if (target === 'brief') {
      document.getElementById('writing-brief-panel')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      return;
    }
    if (target === 'submission-template' || target === 'export') {
      document.getElementById('writing-export-panel')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      return;
    }
    if (target === 'evidence' || target === 'evidence-table') {
      document.getElementById('writing-evidence-panel')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      return;
    }
    if (target === 'citations') {
      document.getElementById('writing-sections-panel')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      return;
    }
    document.getElementById('writing-sections-panel')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };
  const downloadTextFile = (filename: string, content: string) => {
    const blob = new Blob([content || ''], { type: 'text/plain;charset=utf-8' });
    downloadBlobFile(filename, blob);
  };
  const downloadBlobFile = (filename: string, blob: Blob) => {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const projectId = params.get('project');
    if (!projectId) return;
    setAssistantMode('paper');
    setPaperWorkflow('manuscript');
    api.get(`/writing/projects/${projectId}`)
      .then(response => {
        setSelectedProject(response.data);
        setProjectSections(response.data.sections || []);
        setActiveSectionId((response.data.sections || [])[0]?.id || null);
        setPageActionError(null);
      })
      .catch(error => showPageError('无法打开写作项目', error, '无法打开写作项目'));
  }, [location.search, showPageError]);

  useEffect(() => {
    if (!selectedProject?.id) {
      setEvidenceCards([]);
      setEvidenceCoverage(null);
      setEvidenceTable(null);
      setCitationChecks({});
      setQualityChecks({});
      setLatexPreviewChecks({});
      setManuscriptPreview(null);
      setSectionAiState({});
      setExportReadiness(null);
      setExportPackage(null);
      setWorkbenchSummary(null);
      return;
    }
    setCitationChecks({});
    setQualityChecks({});
    setLatexPreviewChecks({});
    setManuscriptPreview(null);
    setSectionAiState({});
    setEvidenceLoading(true);
    api.get(`/writing/projects/${selectedProject.id}/evidence-cards`)
      .then(response => {
        setEvidenceCards(response.data.cards || []);
        setEvidenceCoverage(response.data.coverage || null);
        setEvidenceTable(null);
      })
      .catch(() => {
        setEvidenceCards([]);
        setEvidenceCoverage(null);
      })
      .finally(() => setEvidenceLoading(false));
  }, [selectedProject?.id]);

  useEffect(() => {
    if (!selectedProject?.id) return;
    setWorkbenchLoading(true);
    api.get(`/writing/projects/${selectedProject.id}/workbench-summary`)
      .then(response => setWorkbenchSummary(response.data))
      .catch(() => setWorkbenchSummary(null))
      .finally(() => setWorkbenchLoading(false));
  }, [selectedProject?.id, projectRefreshSignal]);

  useEffect(() => {
    if (!selectedProject?.id) return;
    setExportPackage(null);
    api.get(`/writing/projects/${selectedProject.id}/export/readiness`)
      .then(response => setExportReadiness(response.data))
      .catch(() => setExportReadiness(null));
  }, [selectedProject?.id, projectRefreshSignal]);

  useEffect(() => {
    const profile = selectedProject?.metadata_json?.submission_profile || null;
    setSubmissionVenue(profile?.venue || '');
    setSubmissionYear(profile?.year || '');
    setSubmissionInspection(profile?.template_source ? profile : null);
  }, [selectedProject?.id]);

  // ── 处理器 ── (保持简洁)
  const handleRecommend = useCallback(async () => {
    if (!citeText.trim()) return;
    setCiteLoading(true);
    try { const r = await api.post('/writing/recommend-citations', { text: citeText, top_k: 5 }); setCitations(r.data); setPageActionError(null); if (!r.data.length) message.info('知识库中暂无相关论文'); }
    catch (error) { showPageError('引用推荐失败', error, '引用推荐失败'); } finally { setCiteLoading(false); }
  }, [citeText, showPageError]);
  const handleRelatedWork = useCallback(async () => {
    if (!rwTopic.trim()) return;
    setRwLoading(true);
    try { const r = await api.post('/writing/related-work', { topic: rwTopic, max_papers: 5, language: 'chinese' }); setRwResult(r.data.result); setPageActionError(null); }
    catch (error) { showPageError('Related Work 生成失败', error, 'Related Work 生成失败'); } finally { setRwLoading(false); }
  }, [rwTopic, showPageError]);
  const handleRelatedWorkTable = useCallback(async () => {
    if (!rwTopic.trim()) return;
    setRwTableLoading(true);
    try { const r = await api.post('/writing/related-work/table', { topic: rwTopic, max_papers: 8, language: 'chinese' }); setRwTable(r.data.markdown || ''); setPageActionError(null); }
    catch (error) { showPageError('对比表生成失败', error, '对比表生成失败'); } finally { setRwTableLoading(false); }
  }, [rwTopic, showPageError]);
  const handlePolish = useCallback(async () => {
    if (!polishText.trim()) return;
    setPolishLoading(true);
    try { const r = await api.post('/writing/polish', { text: polishText, style: polishStyle }); setPolishResult(r.data.result); setPageActionError(null); }
    catch (error) { showPageError('润色失败', error, '润色失败'); } finally { setPolishLoading(false); }
  }, [polishText, polishStyle, showPageError]);
  const handleAbstract = useCallback(async () => {
    if (!absTitle.trim()) return;
    setAbsLoading(true);
    try { const r = await api.post('/writing/generate-abstract', { title: absTitle, key_points: absKeyPoints, language: 'chinese' }); setAbsResult(r.data.result); setPageActionError(null); }
    catch (error) { showPageError('摘要生成失败', error, '摘要生成失败'); } finally { setAbsLoading(false); }
  }, [absTitle, absKeyPoints, showPageError]);
  const handleLitReview = useCallback(async () => {
    if (!lrTopic.trim()) return;
    setLrLoading(true);
    try { const r = await api.post('/writing/literature-review', { topic: lrTopic, max_papers: 10 }); setLrResult(r.data); setPageActionError(null); }
    catch (error) { showPageError('文献综述生成失败', error, '文献综述生成失败'); } finally { setLrLoading(false); }
  }, [lrTopic, showPageError]);
  const handleCompare = useCallback(async () => {
    const ids = compareIds.split(/[\s,]+/).filter(Boolean);
    if (ids.length < 2) { message.warning('请输入至少 2 个论文 ID'); return; }
    setCompareLoading(true);
    try { const r = await api.post('/writing/compare-papers', { paper_ids: ids }); setCompareResult(r.data.result); setPageActionError(null); }
    catch (error) { showPageError('论文对比失败', error, '论文对比失败'); } finally { setCompareLoading(false); }
  }, [compareIds, showPageError]);
  const handleDiffPolish = async () => {
    if (!polishText.trim()) return;
    setDiffLoading(true);
    try { const r = await api.post('/writing/polish/diff', { text: polishText, style: polishStyle }); setDiffResult(r.data); setPageActionError(null); }
    catch (error) { showPageError('Diff 润色失败', error, 'Diff 润色失败'); } finally { setDiffLoading(false); }
  };
  const handleApplyDiff = (result: string) => { setPolishResult(result); setDiffResult(null); message.success('Diff 修改已应用'); };
  const handleSelectProject = async (p: any) => {
    setSelectedProject(p);
    setProjectSections(p.sections || []);
    setCitationChecks({});
    setQualityChecks({});
    setLatexPreviewChecks({});
    setManuscriptPreview(null);
    setSectionAiState({});
    setActiveSectionId((p.sections || [])[0]?.id || null);
    setEvidenceTable(null);
    const profile = p.metadata_json?.submission_profile || {};
    setSubmissionVenue(profile.venue || '');
    setSubmissionYear(profile.year || '');
    setSubmissionInspection(profile.template_source ? profile : null);
    setSubmissionTemplateFile(null);
  };
  const handleCreateReviewDraft = async () => {
    const topic = draftTopic.trim();
    if (!topic) { message.warning('请先输入研究方向'); return; }
    setDraftLoading(true);
    try {
      const r = await api.post('/writing/projects/from-topic', { topic, max_papers: 8, language: 'chinese' });
      const project = r.data.project;
      setSelectedProject(project);
      setProjectSections(project.sections || []);
      setProjectRefreshSignal(v => v + 1);
      setPageActionError(null);
      message.success(r.data.evidence_status === 'sufficient' ? '综述草稿已创建' : '已创建草稿，但证据不足，建议先补充论文');
    } catch (error) {
      showPageError('创建综述草稿失败', error, '创建综述草稿失败');
    } finally {
      setDraftLoading(false);
    }
  };
  const handleUpdateSection = async (sid: string, d: any) => {
    try { await api.put(`/writing/projects/${selectedProject.id}/sections/${sid}`, d); setProjectSections(prev => prev.map(s => s.id === sid ? { ...s, ...d } : s)); }
    catch { /* ignore */ }
  };
  const handleCreateSection = async () => {
    if (!selectedProject?.id) return;
    setCreatingSection(true);
    try {
      const title = projectSections.length ? `New Section ${projectSections.length + 1}` : 'Introduction';
      const response = await api.post(`/writing/projects/${selectedProject.id}/sections`, { title, content: '', status: 'draft' });
      const section = response.data;
      setProjectSections(prev => [...prev, section]);
      setActiveSectionId(section.id);
      setProjectRefreshSignal(v => v + 1);
      setPageActionError(null);
      message.success(`已创建章节「${section.title}」`);
    } catch (error) {
      showPageError('创建章节失败', error, '创建章节失败');
    } finally {
      setCreatingSection(false);
    }
  };
  const persistSectionContent = async (section: any, content: string, successText?: string) => {
    if (!selectedProject?.id) return;
    try {
      await api.put(`/writing/projects/${selectedProject.id}/sections/${section.id}`, { content });
      setProjectSections(prev => prev.map(s => s.id === section.id ? { ...s, content, word_count: content.length } : s));
      setPageActionError(null);
      if (successText) message.success(successText);
    } catch (error) {
      showPageError('章节更新失败', error, '章节更新失败');
    }
  };
  const handleInsertEvidenceMarker = async (marker: string) => {
    const target = projectSections.find(s => s.id === activeSectionId) || projectSections[0];
    if (!target) {
      message.warning('当前项目还没有可写入章节');
      return;
    }
    const nextContent = `${(target.content || '').trimEnd()}${target.content ? ' ' : ''}${marker}`;
    await persistSectionContent(
      target,
      nextContent,
      activeSectionId ? `已插入到「${target.title}」` : `未检测到当前编辑章节，已插入到「${target.title}」`,
    );
  };
  const handleResolveBriefClaim = (claim: string) => {
    setCiteText(claim);
    setPaperWorkflow('tools');
    message.info('已把该 Claim 放入引用推荐输入，可在辅助工具区继续检索支撑证据');
  };
  const handleGenerateEvidenceTable = async () => {
    if (!selectedProject?.id) return;
    setEvidenceTableLoading(true);
    try {
      const response = await api.post(`/writing/projects/${selectedProject.id}/evidence-related-work-table`);
      setEvidenceTable(response.data);
      setPageActionError(null);
      if (response.data.warnings?.length) message.warning('证据表已生成，但存在证据覆盖提醒');
      else message.success('证据对比表已生成');
    } catch (error) {
      showPageError('生成证据对比表失败', error, '生成证据对比表失败');
    } finally {
      setEvidenceTableLoading(false);
    }
  };
  const handleWriteEvidenceTableToSection = async () => {
    if (!evidenceTable?.markdown) {
      await handleGenerateEvidenceTable();
      return;
    }
    const target = projectSections.find(s => /related work comparison table/i.test(s.title))
      || projectSections.find(s => /related work/i.test(s.title));
    if (!target) {
      handleCopy(evidenceTable.markdown);
      message.info('没有找到 Related Work 章节，已复制证据表');
      return;
    }
    await persistSectionContent(target, evidenceTable.markdown, `已写入「${target.title}」`);
  };
  const handleCheckSectionCitations = async (section: any) => {
    if (!selectedProject?.id) return;
    if (!(section.content || '').trim()) {
      message.warning('章节内容为空，暂时没有可校验的引用');
      return;
    }
    setCitationChecking(prev => ({ ...prev, [section.id]: true }));
    try {
      const response = await api.post(`/writing/projects/${selectedProject.id}/citations/check-section`, {
        section_id: section.id,
        text: section.content || '',
      });
      setCitationChecks(prev => ({ ...prev, [section.id]: response.data }));
      const warning = response.data.summary?.evidence_warning;
      setPageActionError(null);
      message.success(warning ? '引用校验完成：存在需要确认的证据' : '引用校验完成：当前引用较稳');
    } catch (error) {
      showPageError('引用校验失败', error, '引用校验失败');
    } finally {
      setCitationChecking(prev => ({ ...prev, [section.id]: false }));
    }
  };
  const handleCheckSectionQuality = async (section: any) => {
    if (!selectedProject?.id) return;
    if (!(section.content || '').trim()) {
      message.warning('章节内容为空，请先写出核心论断再评估质量');
      return;
    }
    setQualityChecking(prev => ({ ...prev, [section.id]: true }));
    try {
      const response = await api.post(`/writing/projects/${selectedProject.id}/sections/quality-check`, {
        section_id: section.id,
        title: section.title || '',
        text: section.content || '',
      });
      setQualityChecks(prev => ({ ...prev, [section.id]: response.data }));
      setPageActionError(null);
      message.success(response.data.status === 'ready' ? '质量评估完成：可进入润色' : '质量评估完成：仍有可补强点');
    } catch (error) {
      showPageError('质量评估失败', error, '质量评估失败');
    } finally {
      setQualityChecking(prev => ({ ...prev, [section.id]: false }));
    }
  };
  const handlePreviewSectionLatex = async (section: any) => {
    if (!selectedProject?.id) return;
    setLatexPreviewing(prev => ({ ...prev, [section.id]: true }));
    try {
      const response = await api.post(`/writing/projects/${selectedProject.id}/latex/preview-section`, {
        section_id: section.id,
        title: section.title || 'Section',
        source: section.content || '',
      });
      setLatexPreviewChecks(prev => ({ ...prev, [section.id]: response.data }));
      setPageActionError(null);
      const previewScope = response.data.pdf_scope === 'manuscript' ? '整篇' : '当前章节';
      message.success(response.data.success ? `${previewScope} LaTeX 检查通过` : `${previewScope} LaTeX 检查完成，请查看诊断`);
    } catch (error) {
      showPageError('LaTeX 章节预览失败', error, 'LaTeX 章节预览失败');
    } finally {
      setLatexPreviewing(prev => ({ ...prev, [section.id]: false }));
    }
  };
  const handlePreviewManuscriptLatex = async () => {
    if (!selectedProject?.id) return;
    setManuscriptPreviewing(true);
    try {
      const response = await api.post(`/writing/projects/${selectedProject.id}/latex/preview-manuscript`);
      setManuscriptPreview(response.data);
      setPageActionError(null);
      message.success(response.data.success ? '整篇 LaTeX 检查通过' : '整篇 LaTeX 检查完成，请查看诊断');
    } catch (error) {
      showPageError('整篇 LaTeX 预览失败', error, '整篇 LaTeX 预览失败');
    } finally {
      setManuscriptPreviewing(false);
    }
  };
  const handleSectionAiAction = async (section: any, action: string) => {
    if (!selectedProject?.id) return;
    const sectionId = section.id;
    const evidenceSummary = evidenceCards.slice(0, 8).map((card: any) => ({
      marker: card.citation_marker,
      role: card.role_label,
      title: card.title,
      snippet: card.snippet,
    }));
    setSectionAiState(prev => ({
      ...prev,
      [sectionId]: { loading: true, action, status: '正在准备当前章节上下文...', output: '' },
    }));
    try {
      const token = localStorage.getItem('access_token');
      const resp = await fetch('/api/writing/pipeline/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({
          task_type: 'full_chapter',
          phases: ['writer'],
          input_data: {
            topic: selectedProject.title,
            project_title: selectedProject.title,
            section_action: action,
            section_id: section.id,
            section_title: section.title || 'Section',
            section_source: section.content || '',
            project_context: selectedProject.metadata_json?.writing_context || {},
            writing_brief: selectedWritingBrief || {},
            evidence_summary: evidenceSummary,
            citation_diagnostics: citationChecks[section.id] || qualityChecks[section.id] || {},
            latex_diagnostics: latexPreviewChecks[section.id] || manuscriptPreview || {},
          },
        }),
      });
      if (!resp.ok || !resp.body) throw new Error(`AI 请求失败：${resp.status}`);
      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, '\n');
        const frames = buffer.split('\n\n');
        buffer = frames.pop() || '';
        for (const frame of frames) {
          for (const line of frame.split('\n').filter(item => item.startsWith('data: '))) {
            const payload = line.slice(6);
            if (payload === '[DONE]') continue;
            const event = JSON.parse(payload);
            if (event.type === 'status') {
              setSectionAiState(prev => ({
                ...prev,
                [sectionId]: {
                  ...(prev[sectionId] || {}),
                  loading: true,
                  action,
                  status: typeof event.content === 'string' ? event.content : 'AI 正在处理当前章节...',
                },
              }));
            } else if (event.type === 'content') {
              setSectionAiState(prev => ({
                ...prev,
                [sectionId]: {
                  ...(prev[sectionId] || {}),
                  loading: true,
                  action,
                  status: 'AI 正在生成当前章节建议...',
                  output: `${prev[sectionId]?.output || ''}${event.content || ''}`,
                },
              }));
            } else if (event.type === 'error') {
              throw new Error(typeof event.content === 'string' ? event.content : event.content?.message || 'AI 章节助手失败');
            } else if (event.type === 'done') {
              setSectionAiState(prev => ({
                ...prev,
                [sectionId]: { ...(prev[sectionId] || {}), loading: false, action, status: 'AI 建议已生成' },
              }));
            }
          }
        }
      }
      setSectionAiState(prev => ({
        ...prev,
        [sectionId]: { ...(prev[sectionId] || {}), loading: false, action, status: 'AI 建议已生成' },
      }));
      setPageActionError(null);
    } catch (error) {
      setSectionAiState(prev => ({
        ...prev,
        [sectionId]: { ...(prev[sectionId] || {}), loading: false, action, status: 'AI 章节助手失败' },
      }));
      showPageError('AI 章节助手失败', error, 'AI 章节助手失败');
    }
  };
  const handleLoadExportPackage = async () => {
    if (!selectedProject?.id) return null;
    setExportLoading(true);
    try {
      const response = await api.get(`/writing/projects/${selectedProject.id}/export/package`);
      setExportPackage(response.data);
      setExportReadiness(response.data.readiness || null);
      setPageActionError(null);
      return response.data;
    } catch (error) {
      showPageError('导出包生成失败', error, '导出包生成失败');
      return null;
    } finally {
      setExportLoading(false);
    }
  };
  const getExportPackage = async () => exportPackage || await handleLoadExportPackage();
  const handleCopyExportFormat = async (format: string) => {
    const pkg = await getExportPackage();
    const item = pkg?.formats?.[format];
    if (!item?.content) {
      message.warning('当前格式暂无可复制内容');
      return;
    }
    handleCopy(item.content);
  };
  const handleDownloadExportFormat = async (format: string) => {
    const pkg = await getExportPackage();
    const item = pkg?.formats?.[format];
    if (!item?.content) {
      message.warning('当前格式暂无可下载内容');
      return;
    }
    downloadTextFile(item.filename || `${format}.txt`, item.content);
  };
  const handleDownloadDocx = async () => {
    if (!selectedProject?.id) return;
    try {
      const pkg = exportPackage || await handleLoadExportPackage();
      const filename = pkg?.formats?.docx?.filename || `${selectedProject.title || 'writing_project'}.docx`;
      const response = await api.get(`/writing/projects/${selectedProject.id}/export?format=docx`, { responseType: 'blob' });
      downloadBlobFile(filename, response.data);
      setPageActionError(null);
    } catch (error) {
      showPageError('Word 下载失败', error, 'Word 下载失败');
    }
  };
  const handleBindSubmissionTemplate = async () => {
    if (!selectedProject?.id) return;
    if (!submissionTemplateFile) {
      message.warning('请先选择会议官方模板文件或模板 zip 包');
      return;
    }
    setSubmissionUploading(true);
    try {
      const formData = new FormData();
      formData.append('venue', submissionVenue);
      formData.append('year', submissionYear);
      formData.append('file', submissionTemplateFile);
      const response = await api.post(`/writing/projects/${selectedProject.id}/submission-template`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setSelectedProject(response.data.project);
      setProjectSections(response.data.project.sections || []);
      setSubmissionInspection(response.data.inspection);
      setSubmissionTemplateFile(null);
      setExportPackage(null);
      const readiness = await api.get(`/writing/projects/${selectedProject.id}/export/readiness`);
      setExportReadiness(readiness.data);
      setPageActionError(null);
      message.success('投稿模板已检查并绑定到项目');
    } catch (error: any) {
      showPageError('模板绑定失败', error, '模板绑定失败');
    } finally {
      setSubmissionUploading(false);
    }
  };
  // ── 申请书处理器 ──
  const handleGrantWrite = async () => {
    if (!grantTopic.trim()) { message.warning('请填写项目主题'); return; }
    setGrantLoading(true);
    try {
      const r = await api.post('/writing/grant/write-section', {
        section: grantSection,
        topic: grantTopic,
        background: grantBg,
        previous_content: grantResult,
      });
      setGrantResult(r.data.result);
      setPageActionError(null);
    } catch (error) {
      showPageError('申请书生成失败', error, '申请书生成失败');
    } finally {
      setGrantLoading(false);
    }
  };
  const handleGrantReview = async () => {
    if (!grantResult.trim()) { message.warning('请先生成或粘贴内容'); return; }
    setGrantReviewing(true);
    try {
      const r = await api.post('/writing/grant/review-section', {
        section: grantSection,
        content: grantResult,
        topic: grantTopic,
      });
      setGrantReview(r.data.result);
      setPageActionError(null);
    } catch (error) {
      showPageError('申请书审阅失败', error, '申请书审阅失败');
    } finally {
      setGrantReviewing(false);
    }
  };
  const handleGrantPolish = async () => {
    if (!grantPolishText.trim()) return;
    setGrantPolishing(true);
    try {
      const r = await api.post('/writing/grant/polish', { text: grantPolishText });
      setGrantPolishResult(r.data.result);
      setPageActionError(null);
    } catch (error) {
      showPageError('申请书润色失败', error, '申请书润色失败');
    } finally {
      setGrantPolishing(false);
    }
  };
  const handleGrantInnov = async () => {
    if (!grantTopic.trim()) { message.warning('请先填写项目主题'); return; }
    setGrantInnovLoading(true);
    try {
      const r = await api.post('/writing/grant/extract-innovation', {
        topic: grantTopic,
        background: grantBg,
        methods: grantResult,
      });
      setGrantInnovResult(r.data.result);
      setPageActionError(null);
    } catch (error) {
      showPageError('创新点提炼失败', error, '创新点提炼失败');
    } finally {
      setGrantInnovLoading(false);
    }
  };

  // ══════════════════════════════════════════════════
  //  Tab 内容
  // ══════════════════════════════════════════════════

  const citationTab = (
    <ToolCard icon={<SearchOutlined />} color="#667eea" title="引用推荐" desc="输入写作段落，AI 从知识库中推荐最相关的论文引用">
      <TextArea rows={4} style={{ ...inputStyle, marginBottom: 12 }} placeholder="粘贴你的论文段落，AI 将推荐最相关的引用论文..." value={citeText} onChange={e => setCiteText(e.target.value)} />
      <Button type="primary" icon={<RocketOutlined />} loading={citeLoading} onClick={handleRecommend} style={{ ...primaryBtn, width: '100%' }}>智能推荐引用</Button>
      {citeLoading && <div style={{ textAlign: 'center', marginTop: 16 }}><LoadingDots /></div>}
      {!citeLoading && citations.length > 0 && (
        <div style={{ marginTop: 16 }}>
          <Alert
            type="info"
            showIcon
            message="引用决策概览"
            description={
              <Space size={6} wrap>
                {['supporting_evidence', 'baseline_method', 'counterexample', 'background'].map(role => {
                  const count = citations.filter(item => item.role === role).length;
                  const label = citations.find(item => item.role === role)?.role_label || ({ supporting_evidence: '支持证据', baseline_method: '基线方法', counterexample: '反例/局限', background: '背景资料' } as any)[role];
                  return <Tag key={role} color={count ? 'purple' : 'default'} style={{ borderRadius: 999 }}>{label} {count}</Tag>;
                })}
                <Tag color="green" style={{ borderRadius: 999 }}>强匹配 {citations.filter(item => item.match_status === 'strong').length}</Tag>
                <Tag color="gold" style={{ borderRadius: 999 }}>需确认 {citations.filter(item => item.match_status === 'partial').length}</Tag>
                <Tag color="red" style={{ borderRadius: 999 }}>谨慎使用 {citations.filter(item => item.match_status === 'weak').length}</Tag>
              </Space>
            }
            style={{ borderRadius: 10, marginBottom: 12 }}
          />
          <List dataSource={citations}
            renderItem={(item, idx) => (
              <Card hoverable size="small" style={{ marginBottom: 10, borderRadius: 10, border: '1px solid #f0f0f0', borderTop: `3px solid ${decisionColor(item.decision_confidence) === 'green' ? '#52c41a' : decisionColor(item.decision_confidence) === 'gold' ? '#faad14' : '#ff4d4f'}` }}
                extra={<Tooltip title="复制 BibTeX"><Button size="small" type="text" icon={<CopyOutlined />} onClick={() => handleCopy(item.bibtex)} /></Tooltip>}>
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
                  <div style={{ width: 28, height: 28, borderRadius: 8, background: '#667eea15', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#667eea', fontWeight: 700, fontSize: 13, flexShrink: 0 }}>{idx + 1}</div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <Text strong style={{ fontSize: 13 }} ellipsis>{item.title}</Text>
                    <div style={{ marginTop: 4 }}>
                      <Space size={4} wrap>
                        <Tag color="blue" style={{ borderRadius: 6 }}>{item.year}</Tag>
                        <Tag style={{ borderRadius: 6 }}>{item.authors?.split(',')[0]}</Tag>
                        <Tag color="geekblue" style={{ borderRadius: 6 }}>★{(item.similarity * 100).toFixed(0)}%</Tag>
                        {item.role_label && <Tag color="purple" style={{ borderRadius: 6 }}>{item.role_label}</Tag>}
                        {item.match_label && <Tag color={matchColor(item.match_status)} style={{ borderRadius: 6 }}>{item.match_label}</Tag>}
                        {item.decision_label && <Tag color={decisionColor(item.decision_confidence)} style={{ borderRadius: 6 }}>{item.decision_label}</Tag>}
                      </Space>
                    </div>
                    {item.decision_action && (
                      <Alert
                        type={item.decision_confidence === 'low' ? 'warning' : 'success'}
                        showIcon
                        message={item.decision_action}
                        description={item.decision_warning}
                        style={{ borderRadius: 8, marginTop: 8, padding: '6px 10px', fontSize: 12 }}
                      />
                    )}
                    <Paragraph type="secondary" ellipsis={{ rows: 2 }} style={{ fontSize: 12, marginTop: 8, marginBottom: 0 }}>{item.abstract_snippet}</Paragraph>
                    {(item.role_reason || item.match_explanation) && (
                      <Text type="secondary" style={{ fontSize: 11, display: 'block', marginTop: 6 }}>
                        {item.role_reason} {item.match_explanation}
                      </Text>
                    )}
                  </div>
                </div>
              </Card>
            )}
          />
        </div>
      )}
    </ToolCard>
  );

  const relatedWorkTab = (
    <ToolCard icon={<BookOutlined />} color="#f5576c" title="Related Work" desc="输入研究方向，AI 基于知识库检索论文并撰写规范的 Related Work 章节">
      <Input size="large" style={{ ...inputStyle, marginBottom: 12 }} placeholder="研究方向，如：Video Grounding、多模态大语言模型的偏好对齐" value={rwTopic} onChange={e => setRwTopic(e.target.value)} prefix={<BulbOutlined style={{ color: '#f5576c' }} />} />
      <Row gutter={12}>
        <Col flex="auto"><Button type="primary" icon={<RocketOutlined />} loading={rwLoading} onClick={handleRelatedWork} style={{ ...primaryBtn, width: '100%' }}>生成 Related Work</Button></Col>
        <Col><Button icon={<SwapOutlined />} loading={rwTableLoading} onClick={handleRelatedWorkTable} style={{ ...primaryBtn, borderColor: '#f5576c', color: '#f5576c' }}>生成对比表</Button></Col>
      </Row>
      {(rwLoading || rwTableLoading) && <div style={{ textAlign: 'center', marginTop: 16 }}><LoadingDots /></div>}
      {rwTable && <ResultCard onCopy={() => handleCopy(rwTable)} extra={<Tag color="magenta">Related Work 对比表</Tag>}><Markdown content={rwTable} /></ResultCard>}
      {rwResult && <ResultCard onCopy={() => handleCopy(rwResult)}><Markdown content={rwResult} /></ResultCard>}
    </ToolCard>
  );

  const polishTab = (
    <ToolCard icon={<FormOutlined />} color="#11998e" title="文本润色" desc="学术化、简洁化、流畅性优化，或翻译为学术英语">
      <Select value={polishStyle} onChange={setPolishStyle} style={{ width: 160, marginBottom: 12, borderRadius: 10 }}
        options={[{ value: 'academic', label: '📝 学术化' }, { value: 'concise', label: '📐 简洁化' }, { value: 'fluent', label: '🌊 流畅性' }, { value: 'english', label: '🌍 翻译成英语' }]} />
      <TextArea rows={5} style={{ ...inputStyle, marginBottom: 12 }} placeholder="输入需要润色的学术文本..." value={polishText} onChange={e => setPolishText(e.target.value)} />
      <Row gutter={12}>
        <Col flex="auto"><Button type="primary" icon={<RocketOutlined />} loading={polishLoading} onClick={handlePolish} style={{ ...primaryBtn, width: '100%' }}>一键润色</Button></Col>
        <Col><Button icon={<SwapOutlined />} loading={diffLoading} onClick={handleDiffPolish} style={{ ...primaryBtn, borderColor: '#11998e', color: '#11998e' }}>Diff 模式</Button></Col>
      </Row>
      {polishLoading && <div style={{ textAlign: 'center', marginTop: 16 }}><LoadingDots /></div>}
      {diffResult && <div style={{ marginTop: 16 }}><DiffViewer original={diffResult.original} polished={diffResult.polished} diff={diffResult.diff} onApply={handleApplyDiff} onCancel={() => setDiffResult(null)} /></div>}
      {polishResult && !diffResult && <ResultCard onCopy={() => handleCopy(polishResult)}><Markdown content={polishResult} /></ResultCard>}
    </ToolCard>
  );

  const abstractTab = (
    <ToolCard icon={<FileTextOutlined />} color="#f093fb" title="摘要生成" desc="基于标题和关键要点，生成符合顶会标准的学术摘要">
      <Input size="large" style={{ ...inputStyle, marginBottom: 12 }} placeholder="论文标题" prefix={<FileTextOutlined style={{ color: '#f093fb' }} />} value={absTitle} onChange={e => setAbsTitle(e.target.value)} />
      <TextArea rows={4} style={{ ...inputStyle, marginBottom: 12 }} placeholder="论文关键要点：研究问题、方法概述、主要结果..." value={absKeyPoints} onChange={e => setAbsKeyPoints(e.target.value)} />
      <Button type="primary" icon={<RocketOutlined />} loading={absLoading} onClick={handleAbstract} style={{ ...primaryBtn, width: '100%' }}>生成摘要</Button>
      {absLoading && <div style={{ textAlign: 'center', marginTop: 16 }}><LoadingDots /></div>}
      {absResult && <ResultCard onCopy={() => handleCopy(absResult)}><Markdown content={absResult} /></ResultCard>}
    </ToolCard>
  );

  const litReviewTab = (
    <ToolCard icon={<ReadOutlined />} color="#4facfe" title="文献综述" desc="AI 自动检索、分析、分类，生成包含对比表格和研究空白的完整综述">
      <Input size="large" style={{ ...inputStyle, marginBottom: 12 }} placeholder="研究方向，如：Large Language Model Alignment Techniques" prefix={<ReadOutlined style={{ color: '#4facfe' }} />} value={lrTopic} onChange={e => setLrTopic(e.target.value)} />
      <Button type="primary" icon={<RocketOutlined />} loading={lrLoading} onClick={handleLitReview} style={{ ...primaryBtn, width: '100%' }}>生成文献综述</Button>
      {lrLoading && <div style={{ textAlign: 'center', marginTop: 16 }}><LoadingDots /></div>}
      {lrResult && (
        <ResultCard onCopy={() => handleCopy(lrResult.content)}
          extra={<Space>{lrResult.papers?.map((p: any) => <Tag key={p.index} color="blue" style={{ borderRadius: 6 }}>[{p.index}] {p.title.slice(0, 24)}...</Tag>)}</Space>}>
          <Text type="secondary" style={{ fontSize: 12, marginBottom: 12, display: 'block' }}>基于 {lrResult.total_papers} 篇论文生成</Text>
          <Divider style={{ margin: '12px 0' }} />
          <Markdown content={lrResult.content} />
        </ResultCard>
      )}
    </ToolCard>
  );

  const compareTab = (
    <ToolCard icon={<SwapOutlined />} color="#fa709a" title="论文对比" desc="输入论文 ID（从详情页 URL 复制），AI 自动对比方法、数据集和实验结果">
      <TextArea rows={3} style={{ ...inputStyle, marginBottom: 12 }} placeholder="粘贴论文 ID，逗号或换行分隔&#10;例如：d995a02d-b87a-43c4-aa04-5731e23c8225, 62c7cdd1-81ba-465a-b6a7" value={compareIds} onChange={e => setCompareIds(e.target.value)} />
      <Button type="primary" icon={<RocketOutlined />} loading={compareLoading} onClick={handleCompare} style={{ ...primaryBtn, width: '100%' }}>对比分析</Button>
      {compareLoading && <div style={{ textAlign: 'center', marginTop: 16 }}><LoadingDots /></div>}
      {compareResult && <ResultCard onCopy={() => handleCopy(compareResult)}><Markdown content={compareResult} /></ResultCard>}
    </ToolCard>
  );

  const grantTab = (
    <ToolCard icon={<AuditOutlined />} color="#a18cd1" title="NSFC 申请书助手" desc="参考 NSFC 模板分段撰写，支持 AI 撰写、模拟评审、创新点提炼和文本润色">
      <Row gutter={[12, 12]}>
        <Col xs={24} sm={8}><Select value={grantSection} onChange={setGrantSection} style={{ width: '100%', borderRadius: 10 }} options={['立项依据', '研究内容', '研究方案', '特色创新', '预期成果', '研究基础'].map(v => ({ value: v, label: v }))} /></Col>
        <Col xs={24} sm={16}><Input placeholder="项目主题" value={grantTopic} onChange={e => setGrantTopic(e.target.value)} style={{ borderRadius: 10 }} /></Col>
      </Row>
      <TextArea rows={3} style={{ ...inputStyle, marginTop: 12 }} placeholder="项目背景/摘要（有助于提高生成质量）" value={grantBg} onChange={e => setGrantBg(e.target.value)} />
      <Space style={{ marginTop: 12 }}>
        <Button type="primary" icon={<RocketOutlined />} loading={grantLoading} onClick={handleGrantWrite} style={primaryBtn}>生成 {grantSection}</Button>
        <Button icon={<AuditOutlined />} loading={grantReviewing} onClick={handleGrantReview} style={primaryBtn}>模拟评审</Button>
        <Button icon={<BulbOutlined />} loading={grantInnovLoading} onClick={handleGrantInnov} style={primaryBtn}>提炼创新点</Button>
      </Space>
      {grantLoading && <div style={{ textAlign: 'center', marginTop: 16 }}><LoadingDots /></div>}
      {grantResult && <ResultCard onCopy={() => handleCopy(grantResult)} extra={<Tag color="purple">{grantSection}</Tag>}><Markdown content={grantResult} /></ResultCard>}
      {grantReview && <Card style={{ marginTop: 12, borderRadius: 12, border: '2px solid #faad14', background: '#fffbe6' }} title="📋 评审意见"><Markdown content={grantReview} /></Card>}
      {grantInnovResult && <ResultCard onCopy={() => handleCopy(grantInnovResult)} extra={<Tag color="orange">创新点</Tag>}><Markdown content={grantInnovResult} /></ResultCard>}
      <Divider style={{ margin: '16px 0' }}>文本润色</Divider>
      <TextArea rows={3} style={inputStyle} placeholder="粘贴需润色的申请书文本..." value={grantPolishText} onChange={e => setGrantPolishText(e.target.value)} />
      <Button icon={<FormOutlined />} loading={grantPolishing} onClick={handleGrantPolish} style={{ ...primaryBtn, marginTop: 8, borderColor: '#a18cd1', color: '#a18cd1' }}>润色申请书文本</Button>
      {grantPolishResult && <ResultCard onCopy={() => handleCopy(grantPolishResult)}><Markdown content={grantPolishResult} /></ResultCard>}
    </ToolCard>
  );

  const renderWritingBriefWorkbenchPanel = (brief: ProposalWritingBrief | null) => {
    if (!brief) return null;
    const counts = getBriefClaimStatusCounts(brief);
    const riskActive = hasWritingBriefRisk(brief);
    const titleCandidates = brief.title_candidates || [];
    const claimMap = brief.claim_evidence_map || [];
    const unsafeClaims = brief.unsafe_claims || [];
    const evidenceGaps = brief.evidence_gaps || [];
    const outline = brief.section_outline || [];
    const contributions = brief.contribution_chain || [];
    const limitations = brief.limitations || [];
    const experimentPlan = brief.experiment_writing_plan || [];

    return (
      <Card
        id="writing-brief-panel"
        style={{ ...cardStyle, marginBottom: 16, borderTop: `3px solid ${riskActive ? '#faad14' : '#52c41a'}` }}
        styles={{ body: { padding: 18 } }}
        title={<Space><BulbOutlined /> Proposal 写作准备包</Space>}
        extra={
          <Space size={6} wrap>
            <Tag color={brief.evidence_status === 'sufficient' ? 'green' : 'orange'}>
              {brief.evidence_status === 'sufficient' ? '证据可用' : '证据不足'}
            </Tag>
            <Tag color="blue">Claim {counts.total}</Tag>
            <Tag color={counts.unsupported ? 'red' : 'green'}>未支撑 {counts.unsupported}</Tag>
            <Tag color={unsafeClaims.length ? 'red' : 'green'}>风险 {unsafeClaims.length}</Tag>
          </Space>
        }
      >
        <Space direction="vertical" size={14} style={{ width: '100%' }}>
          <Alert
            type={riskActive ? 'warning' : 'success'}
            showIcon
            message={riskActive ? '写作前需要处理 Proposal 风险' : 'Proposal brief 可作为写作起点'}
            description={brief.abstract_draft || '当前写作准备包没有摘要草稿。'}
            style={{ borderRadius: 10 }}
          />

          <Row gutter={[10, 10]}>
            <Col xs={12} md={6}>
              <div style={{ borderRadius: 10, border: '1px solid #f0f0f0', padding: 10 }}>
                <Text type="secondary">Claim 支撑</Text>
                <Title level={4} style={{ margin: '4px 0' }}>{counts.supported}/{counts.total}</Title>
                <Text type="secondary">部分 {counts.partial} · 缺证据 {counts.unsupported}</Text>
              </div>
            </Col>
            <Col xs={12} md={6}>
              <div style={{ borderRadius: 10, border: '1px solid #f0f0f0', padding: 10 }}>
                <Text type="secondary">证据缺口</Text>
                <Title level={4} style={{ margin: '4px 0' }}>{evidenceGaps.length}</Title>
                <Text type="secondary">定稿前补强</Text>
              </div>
            </Col>
            <Col xs={12} md={6}>
              <div style={{ borderRadius: 10, border: '1px solid #f0f0f0', padding: 10 }}>
                <Text type="secondary">章节骨架</Text>
                <Title level={4} style={{ margin: '4px 0' }}>{outline.length}</Title>
                <Text type="secondary">建议映射到草稿</Text>
              </div>
            </Col>
            <Col xs={12} md={6}>
              <div style={{ borderRadius: 10, border: '1px solid #f0f0f0', padding: 10 }}>
                <Text type="secondary">证据来源</Text>
                <Title level={4} style={{ margin: '4px 0' }}>{brief.local_paper_count || 0}/{brief.evidence_count || 0}</Title>
                <Text type="secondary">本地 / 总数</Text>
              </div>
            </Col>
          </Row>

          {titleCandidates.length > 0 && (
            <div>
              <Text strong>标题候选</Text>
              <Space size={8} wrap style={{ marginTop: 8, width: '100%' }}>
                {titleCandidates.map(title => (
                  <Tag
                    key={title}
                    color="geekblue"
                    style={{ borderRadius: 999, maxWidth: '100%', whiteSpace: 'normal', overflowWrap: 'anywhere', cursor: 'pointer' }}
                    onClick={() => handleCopy(title)}
                  >
                    {title}
                  </Tag>
                ))}
              </Space>
            </div>
          )}

          <Collapse
            bordered={false}
            items={[
              {
                key: 'outline',
                label: `章节骨架 (${outline.length})`,
                children: outline.length ? (
                  <List
                    size="small"
                    dataSource={outline}
                    renderItem={(item) => (
                      <List.Item>
                        <div style={{ width: '100%', minWidth: 0 }}>
                          <Space wrap>
                            <Tag color="blue">{item.section || '未命名章节'}</Tag>
                            {(item.evidence_ids || []).map(id => <Tag key={id}>{id}</Tag>)}
                          </Space>
                          <Text style={{ display: 'block', marginTop: 6 }}>{item.purpose}</Text>
                          {item.seed_content && <Paragraph type="secondary" style={{ margin: '4px 0 0', overflowWrap: 'anywhere' }}>{item.seed_content}</Paragraph>}
                        </div>
                      </List.Item>
                    )}
                  />
                ) : <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无章节骨架" />,
              },
              {
                key: 'contribution',
                label: `贡献链 (${contributions.length})`,
                children: contributions.length ? (
                  <List
                    size="small"
                    dataSource={contributions}
                    renderItem={(item) => (
                      <List.Item
                        actions={[
                          <Button key="copy" size="small" onClick={() => handleCopy(item.claim || '')} style={{ borderRadius: 8 }}>复制</Button>,
                        ]}
                      >
                        <div style={{ width: '100%', minWidth: 0 }}>
                          <Space wrap>
                            <Tag color="purple">Step {item.step || '-'}</Tag>
                            <Tag color={claimStatusColor(item.evidence_status)}>{claimStatusLabel(item.evidence_status)}</Tag>
                          </Space>
                          <Text style={{ display: 'block', marginTop: 6, overflowWrap: 'anywhere' }}>{item.claim}</Text>
                          <Text type="secondary" style={{ display: 'block', marginTop: 4 }}>{item.writing_goal}</Text>
                        </div>
                      </List.Item>
                    )}
                  />
                ) : <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无贡献链" />,
              },
              {
                key: 'claims',
                label: `Claim-Evidence Map (${claimMap.length})`,
                children: claimMap.length ? (
                  <List
                    size="small"
                    dataSource={claimMap}
                    renderItem={(item) => (
                      <List.Item
                        actions={[
                          <Button key="copy" size="small" onClick={() => handleCopy(item.claim || '')} style={{ borderRadius: 8 }}>复制 Claim</Button>,
                          <Button key="resolve" size="small" type={item.status === 'unsupported' ? 'primary' : 'default'} onClick={() => handleResolveBriefClaim(item.claim || '')} style={{ borderRadius: 8 }}>
                            去核对证据
                          </Button>,
                        ]}
                      >
                        <div style={{ width: '100%', minWidth: 0 }}>
                          <Space wrap>
                            <Tag color={claimStatusColor(item.status)}>{claimStatusLabel(item.status)}</Tag>
                            {(item.evidence_refs || []).map(ref => (
                              <Tag
                                key={ref.id || ref.marker || ref.title}
                                color="purple"
                                style={{ cursor: ref.marker ? 'pointer' : 'default' }}
                                onClick={() => ref.marker && handleCopy(ref.marker)}
                              >
                                {ref.marker || ref.id || 'Evidence'}
                              </Tag>
                            ))}
                          </Space>
                          <Text style={{ display: 'block', marginTop: 6, overflowWrap: 'anywhere' }}>{item.claim}</Text>
                          <Text type="secondary" style={{ display: 'block', marginTop: 4 }}>{item.writing_use}</Text>
                        </div>
                      </List.Item>
                    )}
                  />
                ) : <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无 Claim-Evidence 映射" />,
              },
              {
                key: 'risks',
                label: `风险与缺口 (${unsafeClaims.length + evidenceGaps.length + limitations.length})`,
                children: (
                  <Row gutter={[12, 12]}>
                    <Col xs={24} md={8}>
                      <Alert
                        type={unsafeClaims.length ? 'warning' : 'success'}
                        showIcon
                        message="暂不应直接写成结论"
                        description={unsafeClaims.length ? (
                          <Space direction="vertical" size={4}>
                            {unsafeClaims.slice(0, 6).map(item => <Text key={item} style={{ overflowWrap: 'anywhere' }}>{item}</Text>)}
                          </Space>
                        ) : '暂无明确风险 claim。'}
                        style={{ borderRadius: 10 }}
                      />
                    </Col>
                    <Col xs={24} md={8}>
                      <Alert
                        type={evidenceGaps.length ? 'warning' : 'success'}
                        showIcon
                        message="证据缺口"
                        description={evidenceGaps.length ? (
                          <Space direction="vertical" size={4}>
                            {evidenceGaps.slice(0, 6).map(item => <Text key={item} style={{ overflowWrap: 'anywhere' }}>{item}</Text>)}
                          </Space>
                        ) : '暂无明确证据缺口。'}
                        style={{ borderRadius: 10 }}
                      />
                    </Col>
                    <Col xs={24} md={8}>
                      <Alert
                        type={limitations.length ? 'info' : 'success'}
                        showIcon
                        message="限制与反驳点"
                        description={limitations.length ? (
                          <Space direction="vertical" size={4}>
                            {limitations.slice(0, 6).map(item => <Text key={item} style={{ overflowWrap: 'anywhere' }}>{item}</Text>)}
                          </Space>
                        ) : '暂无需要单列的限制。'}
                        style={{ borderRadius: 10 }}
                      />
                    </Col>
                  </Row>
                ),
              },
              {
                key: 'experiment',
                label: `实验写作计划 (${experimentPlan.length})`,
                children: experimentPlan.length ? (
                  <List
                    size="small"
                    dataSource={experimentPlan}
                    renderItem={(item, index) => (
                      <List.Item>
                        <Space align="start">
                          <Tag color="cyan">{index + 1}</Tag>
                          <Text style={{ overflowWrap: 'anywhere' }}>{item}</Text>
                        </Space>
                      </List.Item>
                    )}
                  />
                ) : <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无实验写作计划" />,
              },
            ]}
          />

          <Space wrap>
            {brief.abstract_draft && <Button icon={<CopyOutlined />} onClick={() => handleCopy(brief.abstract_draft || '')} style={{ borderRadius: 8 }}>复制摘要草稿</Button>}
            <Button icon={<BookOutlined />} onClick={() => scrollToWorkbenchTarget('evidence')} style={{ borderRadius: 8 }}>查看证据卡</Button>
            <Button icon={<SearchOutlined />} onClick={() => scrollToWorkbenchTarget('citations')} style={{ borderRadius: 8 }}>校验章节引用</Button>
          </Space>
        </Space>
      </Card>
    );
  };

  const workbenchOverviewPanel = selectedProject ? (
    <Card
      loading={workbenchLoading}
      style={{ ...cardStyle, marginBottom: 16 }}
      styles={{ body: { padding: 18 } }}
    >
      {workbenchSummary ? (() => {
        const blockers = buildWorkbenchBlockers(workbenchSummary, selectedWritingBrief);
        const stageSteps = stageStepState(workbenchSummary.stage?.key);
        const briefAction = hasWritingBriefRisk(selectedWritingBrief) ? {
          key: 'writing-brief-risk',
          label: '处理 Proposal 写作风险',
          reason: `写作准备包中有 ${selectedBriefClaimCounts.unsupported} 个未支撑 Claim、${selectedWritingBrief?.unsafe_claims?.length || 0} 个风险 Claim。`,
          priority: 'high',
          target: 'brief',
        } : null;
        const nextActions = briefAction
          ? [briefAction, ...(workbenchSummary.next_actions || []).filter((action: any) => action.key !== briefAction.key)]
          : (workbenchSummary.next_actions || []);
        const primaryAction = nextActions[0];
        return (
          <Space direction="vertical" size={16} style={{ width: '100%' }}>
            <Row gutter={[12, 12]} align="middle">
              <Col flex="auto">
                <Space size={8} wrap>
                  <Text strong style={{ fontSize: 16 }}>写作推进栏</Text>
                  <Tag color={riskColor(workbenchSummary.risk_level)}>风险：{workbenchSummary.risk_level}</Tag>
                  <Tag color={exportStatusColor(workbenchSummary.status)}>{workbenchSummary.status_label}</Tag>
                </Space>
                <Text type="secondary" style={{ display: 'block', marginTop: 6, fontSize: 13 }}>
                  {workbenchSummary.stage?.label || '写作推进'}：{workbenchSummary.stage?.description || '继续完善当前写作项目。'}
                </Text>
              </Col>
              {primaryAction && (
                <Col>
                  <Button
                    type="primary"
                    icon={<RocketOutlined />}
                    onClick={() => scrollToWorkbenchTarget(primaryAction.target)}
                    style={{ borderRadius: 10 }}
                  >
                    {primaryAction.label}
                  </Button>
                </Col>
              )}
            </Row>

            <div>
              <Text type="secondary" style={{ display: 'block', fontSize: 12, marginBottom: 8 }}>阶段路径</Text>
              <Space size={6} wrap>
                {stageSteps.map(step => (
                  <Button
                    key={step.key}
                    size="small"
                    type={step.state === 'current' ? 'primary' : 'default'}
                    onClick={() => scrollToWorkbenchTarget(step.target)}
                    style={{
                      borderRadius: 999,
                      opacity: step.state === 'pending' ? 0.72 : 1,
                    }}
                  >
                    {step.state === 'done' ? '✓ ' : ''}{step.label}
                  </Button>
                ))}
              </Space>
            </div>

            <Row gutter={[12, 12]}>
              <Col xs={24} md={14}>
                <div style={{ padding: 12, borderRadius: 12, background: '#fafafa', border: '1px solid #f0f0f0' }}>
                  <Row justify="space-between" align="middle" gutter={[8, 8]} style={{ marginBottom: 8 }}>
                    <Col><Text strong>建议下一步</Text></Col>
                    <Col><Text type="secondary" style={{ fontSize: 12 }}>按当前项目状态排序</Text></Col>
                  </Row>
                  <Space direction="vertical" size={8} style={{ width: '100%' }}>
                    {nextActions.map((action: any) => (
                      <div key={action.key} style={{ display: 'flex', gap: 10, alignItems: 'flex-start', padding: '8px 10px', borderRadius: 10, background: '#fff', border: '1px solid #f0f0f0' }}>
                        <Tag color={priorityColor(action.priority)} style={{ marginTop: 1 }}>{workbenchPriorityLabels[action.priority] || action.priority}</Tag>
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <Text strong style={{ display: 'block' }}>{action.label}</Text>
                          <Text type="secondary" style={{ fontSize: 12 }}>{action.reason}</Text>
                        </div>
                        <Button size="small" onClick={() => scrollToWorkbenchTarget(action.target)} style={{ borderRadius: 8 }}>
                          {workbenchTargetLabels[action.target] || '去处理'}
                        </Button>
                      </div>
                    ))}
                  </Space>
                </div>
              </Col>
              <Col xs={24} md={10}>
                <div style={{ padding: 12, borderRadius: 12, background: '#fff7e6', border: '1px solid #ffe7ba', minHeight: '100%' }}>
                  <Row justify="space-between" align="middle" gutter={[8, 8]} style={{ marginBottom: 8 }}>
                    <Col><Text strong>阻塞项</Text></Col>
                    <Col><Tag color={blockers.length ? 'gold' : 'green'}>{blockers.length ? `${blockers.length} 项待处理` : '暂无明显阻塞'}</Tag></Col>
                  </Row>
                  {blockers.length ? (
                    <Space size={6} wrap>
                      {blockers.map(blocker => (
                        <Tag
                          key={blocker.key}
                          color={priorityColor(blocker.severity)}
                          style={{ borderRadius: 999, cursor: 'pointer', marginBottom: 4 }}
                          onClick={() => scrollToWorkbenchTarget(blocker.target)}
                        >
                          {blocker.label}
                        </Tag>
                      ))}
                    </Space>
                  ) : (
                    <Text type="secondary" style={{ fontSize: 13 }}>章节、证据、引用和模板没有检测到高优先级阻塞。</Text>
                  )}
                </div>
              </Col>
            </Row>

            <Row gutter={[10, 10]}>
              <Col xs={12} md={6}>
                <div style={{ borderRadius: 10, border: '1px solid #f0f0f0', padding: 10 }}>
                  <Text type="secondary">章节进度</Text>
                  <Title level={4} style={{ margin: '4px 0' }}>{workbenchSummary.progress?.completed_sections || 0}/{workbenchSummary.progress?.total_sections || 0}</Title>
                  <Text type="secondary">{workbenchSummary.progress?.total_words || 0} 字</Text>
                </div>
              </Col>
              <Col xs={12} md={6}>
                <div style={{ borderRadius: 10, border: '1px solid #f0f0f0', padding: 10 }}>
                  <Text type="secondary">证据覆盖</Text>
                  <Title level={4} style={{ margin: '4px 0' }}>{workbenchSummary.evidence?.local || 0}/{workbenchSummary.evidence?.total || 0}</Title>
                  <Text type="secondary">BibTeX {workbenchSummary.evidence?.bibtex_ready || 0}</Text>
                </div>
              </Col>
              <Col xs={12} md={6}>
                <div style={{ borderRadius: 10, border: '1px solid #f0f0f0', padding: 10 }}>
                  <Text type="secondary">引用风险</Text>
                  <Title level={4} style={{ margin: '4px 0' }}>{workbenchSummary.citations?.unmatched || 0}</Title>
                  <Text type="secondary">未匹配 / {workbenchSummary.citations?.mentions || 0}</Text>
                </div>
              </Col>
              <Col xs={12} md={6}>
                <div style={{ borderRadius: 10, border: '1px solid #f0f0f0', padding: 10 }}>
                  <Text type="secondary">投稿模板</Text>
                  <Title level={5} style={{ margin: '6px 0' }}>{workbenchSummary.submission?.status_label || '未绑定官方模板'}</Title>
                  <Text type="secondary">{[workbenchSummary.submission?.venue, workbenchSummary.submission?.year].filter(Boolean).join(' ') || '待配置'}</Text>
                </div>
              </Col>
            </Row>

            {workbenchSummary.quick_links?.length > 0 && (
              <Space size={8} wrap>
                <Text type="secondary" style={{ fontSize: 12 }}>快速跳转</Text>
                {selectedWritingBrief && (
                  <Button size="small" onClick={() => scrollToWorkbenchTarget('brief')} style={{ borderRadius: 999 }}>
                    写作准备包
                  </Button>
                )}
                {workbenchSummary.quick_links.map((link: any) => (
                  <Button key={link.key} size="small" onClick={() => scrollToWorkbenchTarget(link.target)} style={{ borderRadius: 999 }}>
                    {link.label}
                  </Button>
                ))}
              </Space>
            )}

            {workbenchSummary.warnings?.length > 0 && (
              <Alert
                type="warning"
                showIcon
                message="工作台提醒"
                description={workbenchSummary.warnings.join(' ')}
                style={{ borderRadius: 10 }}
              />
            )}
          </Space>
        );
      })() : (
        <Alert
          type="info"
          showIcon
          message="暂时无法生成工作台总览"
          description="你仍然可以继续编辑章节、查看证据卡和导出预检。"
          style={{ borderRadius: 10 }}
        />
      )}
    </Card>
  ) : null;

  const evidencePanel = selectedProject ? (
    <Card
      id="writing-evidence-panel"
      title="证据卡片"
      loading={evidenceLoading}
      style={cardStyle}
      styles={{ body: { padding: 14, maxHeight: 520, overflowY: 'auto' } }}
      extra={evidenceCoverage && <Tag color={evidenceCoverage.external ? 'gold' : 'green'}>{evidenceCoverage.local}/{evidenceCoverage.total} 已入库</Tag>}
    >
      <Space direction="vertical" style={{ width: '100%', marginBottom: 12 }}>
        <Button
          block
          size="small"
          icon={<SwapOutlined />}
          loading={evidenceTableLoading}
          onClick={handleGenerateEvidenceTable}
          style={{ borderRadius: 8 }}
        >
          生成证据对比表
        </Button>
        <Button
          block
          size="small"
          type="primary"
          disabled={!evidenceTable?.markdown}
          onClick={handleWriteEvidenceTableToSection}
          style={{ borderRadius: 8 }}
        >
          写入对比表章节
        </Button>
        {evidenceTable?.warnings?.length > 0 && (
          <Alert
            type="warning"
            showIcon
            message="证据覆盖提醒"
            description={evidenceTable.warnings.join(' ')}
            style={{ borderRadius: 8, fontSize: 12 }}
          />
        )}
      </Space>
      {evidenceCards.length ? (
        <List
          dataSource={evidenceCards}
          renderItem={(card: any) => (
            <List.Item style={{ padding: '10px 0' }}>
              <div style={{ width: '100%' }}>
                <Space size={6} wrap>
                  <Tag color="purple">{card.citation_marker}</Tag>
                  <Tag color={card.local_status === 'local' ? 'green' : 'gold'}>{card.local_status_label}</Tag>
                  <Tag>{card.role_label}</Tag>
                </Space>
                <Text strong style={{ display: 'block', marginTop: 6, fontSize: 13 }}>
                  {card.title}
                </Text>
                <Text type="secondary" style={{ display: 'block', fontSize: 12, marginTop: 4 }}>
                  {[card.year, card.authors].filter(Boolean).join(' · ')}
                </Text>
                <Paragraph type="secondary" ellipsis={{ rows: 3 }} style={{ fontSize: 12, marginTop: 6, marginBottom: 8 }}>
                  {card.snippet || '暂无摘要片段，建议补全文后再精细校验。'}
                </Paragraph>
                <Space>
                  <Button size="small" onClick={() => handleCopy(card.citation_marker)} style={{ borderRadius: 8 }}>
                    复制引用
                  </Button>
                  <Button size="small" type="primary" onClick={() => handleInsertEvidenceMarker(card.citation_marker)} style={{ borderRadius: 8 }}>
                    插入当前章节
                  </Button>
                  {card.paper_id && (
                    <Button size="small" onClick={() => handleCopy(`Paper ID: ${card.paper_id}`)} style={{ borderRadius: 8 }}>
                      复制 Paper ID
                    </Button>
                  )}
                </Space>
              </div>
            </List.Item>
          )}
        />
      ) : (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="这个项目还没有关联证据。可先从研究方向创建草稿或补充推荐论文。"
        />
      )}
    </Card>
  ) : null;

  const publicationExportPanel = selectedProject ? (
    <Card
      id="writing-export-panel"
      title={<Space><FileZipOutlined /> 投稿导出包</Space>}
      style={{ ...cardStyle, marginBottom: 16 }}
      extra={exportReadiness && <Tag color={exportStatusColor(exportReadiness.status)}>{exportReadiness.status_label}</Tag>}
    >
      <Card
        size="small"
        title="投稿目标与官方模板"
        style={{ borderRadius: 12, marginBottom: 12, background: '#fafafa' }}
      >
        <Alert
          type="info"
          showIcon
          message="会议格式每年可能变化，建议上传官网模板包"
          description="系统会检查 .tex/.cls/.sty/.zip 中的 documentclass、样式文件和主 tex 信息，并把结果绑定到当前写作项目。当前版本用于投稿预检和写作指导，不会声称自动保证格式合规。"
          style={{ borderRadius: 8, marginBottom: 12 }}
        />
        <Row gutter={[10, 10]} align="middle">
          <Col xs={24} md={7}>
            <Input placeholder="会议/期刊，如 CVPR" value={submissionVenue} onChange={e => setSubmissionVenue(e.target.value)} style={inputStyle} />
          </Col>
          <Col xs={24} md={5}>
            <Input placeholder="年份，如 2026" value={submissionYear} onChange={e => setSubmissionYear(e.target.value)} style={inputStyle} />
          </Col>
          <Col xs={24} md={7}>
            <Upload
              beforeUpload={(file) => {
                setSubmissionTemplateFile(file);
                return false;
              }}
              onRemove={() => setSubmissionTemplateFile(null)}
              maxCount={1}
              accept=".tex,.cls,.sty,.zip"
            >
              <Button icon={<UploadOutlined />} style={{ borderRadius: 8 }}>选择官方模板</Button>
            </Upload>
          </Col>
          <Col xs={24} md={5}>
            <Button type="primary" block loading={submissionUploading} onClick={handleBindSubmissionTemplate} style={{ borderRadius: 8 }}>
              检查并绑定
            </Button>
          </Col>
        </Row>
        {(submissionInspection || exportReadiness?.submission_profile) && (
          <div style={{ marginTop: 12 }}>
            <Space wrap>
              <Tag color={(submissionInspection?.template_status || submissionInspection?.status) === 'ready' ? 'green' : 'gold'}>
                {submissionInspection?.status_label || exportReadiness?.submission_profile?.status_label || '模板状态'}
              </Tag>
              {(submissionInspection?.template_source || submissionInspection?.source_filename) && (
                <Tag>{submissionInspection.template_source || submissionInspection.source_filename}</Tag>
              )}
              {(submissionInspection?.document_class || exportReadiness?.submission_profile?.document_class) && (
                <Tag color="blue">documentclass: {submissionInspection.document_class || exportReadiness?.submission_profile?.document_class}</Tag>
              )}
              {(submissionInspection?.venue || exportReadiness?.submission_profile?.venue) && (
                <Tag color="purple">{submissionInspection.venue || exportReadiness?.submission_profile?.venue} {submissionInspection.year || exportReadiness?.submission_profile?.year}</Tag>
              )}
            </Space>
            {(submissionInspection?.warnings?.length || exportReadiness?.submission_profile?.warnings?.length) ? (
              <Alert
                type="warning"
                showIcon
                message="模板检查提醒"
                description={(submissionInspection?.warnings || exportReadiness?.submission_profile?.warnings || []).join(' ')}
                style={{ borderRadius: 8, marginTop: 8 }}
              />
            ) : null}
          </div>
        )}
      </Card>
      {exportReadiness?.warnings?.length ? (
        <Alert
          type={exportReadiness.status === 'incomplete' ? 'error' : 'warning'}
          showIcon
          message="导出前建议检查"
          description={exportReadiness.warnings.join(' ')}
          style={{ borderRadius: 10, marginBottom: 12 }}
        />
      ) : (
        <Alert
          type="success"
          showIcon
          message="当前草稿具备基础导出条件"
          description="仍建议在投稿前人工检查格式、引用和实验细节。"
          style={{ borderRadius: 10, marginBottom: 12 }}
        />
      )}
      <Row gutter={[12, 12]} style={{ marginBottom: 12 }}>
        <Col xs={12} md={6}><Tag color="blue">章节 {exportReadiness?.section_summary?.total ?? '-'}</Tag></Col>
        <Col xs={12} md={6}><Tag color="purple">字数 {exportReadiness?.section_summary?.total_words ?? '-'}</Tag></Col>
        <Col xs={12} md={6}><Tag color="green">证据 {exportReadiness?.evidence_coverage?.local ?? 0}/{exportReadiness?.evidence_coverage?.total ?? 0}</Tag></Col>
        <Col xs={12} md={6}><Tag color="geekblue">参考文献 {exportReadiness?.reference_summary?.papers ?? 0}</Tag></Col>
      </Row>
      <Space wrap>
        <Button icon={<FileZipOutlined />} loading={exportLoading} onClick={handleLoadExportPackage} style={{ borderRadius: 8 }}>
          生成导出包
        </Button>
        <Button icon={<CopyOutlined />} onClick={() => handleCopyExportFormat('markdown')} style={{ borderRadius: 8 }}>
          复制 Markdown
        </Button>
        <Button icon={<DownloadOutlined />} onClick={() => handleDownloadExportFormat('markdown')} style={{ borderRadius: 8 }}>
          下载 MD
        </Button>
        <Button icon={<CopyOutlined />} onClick={() => handleCopyExportFormat('bibtex')} style={{ borderRadius: 8 }}>
          复制 BibTeX
        </Button>
        <Button icon={<DownloadOutlined />} onClick={() => handleDownloadExportFormat('bibtex')} style={{ borderRadius: 8 }}>
          下载 BibTeX
        </Button>
        <Button icon={<DownloadOutlined />} onClick={() => handleDownloadExportFormat('latex')} style={{ borderRadius: 8 }}>
          下载 LaTeX
        </Button>
        <Button icon={<CopyOutlined />} onClick={() => handleCopyExportFormat('references')} style={{ borderRadius: 8 }}>
          复制参考文献
        </Button>
        <Button type="primary" icon={<DownloadOutlined />} onClick={handleDownloadDocx} style={{ borderRadius: 8 }}>
          下载 Word
        </Button>
      </Space>
    </Card>
  ) : null;

  const activeSection = selectedProject
    ? (projectSections.find(section => section.id === activeSectionId) || projectSections[0] || null)
    : null;
  const activeSectionAi = activeSection ? sectionAiState[activeSection.id] || {} : {};
  const latexDiagnosticScopeLabel = (diagnostic: any, fallback: string) => (
    diagnostic?.pdf_scope === 'manuscript' || diagnostic?.scope === 'manuscript' ? '整篇' : fallback
  );
  const latexDiagnosticPanel = (diagnostic: any, scopeLabel: string) => {
    const effectiveScopeLabel = latexDiagnosticScopeLabel(diagnostic, scopeLabel);
    return diagnostic ? (
    <Alert
      type={diagnostic.success ? ((diagnostic.warnings || []).length ? 'warning' : 'success') : 'error'}
      showIcon
      message={
        diagnostic.compiler_available === false
          ? `${effectiveScopeLabel}源码级检查${diagnostic.success ? '通过' : '发现问题'}`
          : diagnostic.success ? `${effectiveScopeLabel} LaTeX 检查通过` : `${effectiveScopeLabel} LaTeX 检查未通过`
      }
      description={(
        <Space direction="vertical" size={8} style={{ width: '100%' }}>
          <Space size={6} wrap>
            {diagnostic.compiler_available === false && <Tag color="gold">未安装 pdflatex</Tag>}
            <Tag color={(diagnostic.errors || []).length ? 'red' : 'green'}>错误 {(diagnostic.errors || []).length}</Tag>
            <Tag color={(diagnostic.warnings || []).length ? 'gold' : 'green'}>警告 {(diagnostic.warnings || []).length}</Tag>
            <Tag>{effectiveScopeLabel}</Tag>
          </Space>
          {(diagnostic.errors || []).slice(0, 5).map((item: string) => (
            <Text key={item} type="danger" style={{ overflowWrap: 'anywhere' }}>{item}</Text>
          ))}
          {(diagnostic.warnings || []).slice(0, 5).map((item: string) => (
            <Text key={item} type="secondary" style={{ overflowWrap: 'anywhere' }}>{item}</Text>
          ))}
          {diagnostic.pdf_preview_url && (
            <AuthenticatedPdfPreview previewUrl={diagnostic.pdf_preview_url} title={`${effectiveScopeLabel} PDF 预览`} height={520} />
          )}
        </Space>
      )}
      style={{ borderRadius: 10 }}
    />
    ) : null;
  };

  const manuscriptWorkbench = (
    <div
      className="manuscript-workbench-grid"
      data-support-rail-state={supportRailCollapsed ? 'collapsed' : 'expanded'}
      style={{
        display: 'grid',
        gridTemplateColumns: supportRailCollapsed ? '64px minmax(0, 1fr)' : '320px minmax(0, 1fr)',
        gap: 16,
        alignItems: 'start',
      }}
    >
      {supportRailCollapsed ? (
        <div
          className="manuscript-support-rail manuscript-support-rail-collapsed"
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 12,
            position: 'sticky',
            top: 12,
            padding: 10,
            border: '1px solid #f0f0f0',
            borderRadius: 12,
            background: '#fff',
            boxShadow: '0 6px 18px rgba(15, 23, 42, 0.06)',
          }}
        >
          <Tooltip title="展开项目与证据栏" placement="right">
            <Button
              type="primary"
              shape="circle"
              icon={<MenuUnfoldOutlined />}
              onClick={() => setSupportRailCollapsed(false)}
              aria-label="展开项目与证据栏"
            />
          </Tooltip>
          <Tooltip title="我的项目" placement="right">
            <Button shape="circle" icon={<FolderOutlined />} aria-label="我的项目" />
          </Tooltip>
          <Tooltip title={`证据卡片 ${evidenceCoverage?.local ?? 0}/${evidenceCoverage?.total ?? 0}`} placement="right">
            <Button shape="circle" icon={<BookOutlined />} aria-label="证据卡片" />
          </Tooltip>
        </div>
      ) : (
        <div className="manuscript-support-rail" style={{ display: 'flex', flexDirection: 'column', gap: 14, position: 'sticky', top: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
            <Text type="secondary" style={{ fontSize: 12 }}>项目与证据</Text>
            <Tooltip title="收起项目与证据栏">
              <Button
                size="small"
                icon={<MenuFoldOutlined />}
                onClick={() => setSupportRailCollapsed(true)}
                aria-label="收起项目与证据栏"
                style={{ borderRadius: 8 }}
              />
            </Tooltip>
          </div>
          <WritingProjectPanel onSelectProject={handleSelectProject} selectedProjectId={selectedProject?.id} refreshSignal={projectRefreshSignal} />
          {evidencePanel}
        </div>
      )}
      <div className="manuscript-editor-main" style={{ minWidth: 0, minHeight: 400 }}>
        {selectedProject ? (
          <>
              {workbenchOverviewPanel}
              {renderWritingBriefWorkbenchPanel(selectedWritingBrief)}
              <Card style={{ ...cardStyle, marginBottom: 16 }} styles={{ body: { padding: '14px 18px' } }}>
                <Row gutter={[12, 12]} align="middle">
                  <Col flex="auto">
                    <Space wrap>
                      <Text strong style={{ fontSize: 16 }}>{selectedProject.title}</Text>
                      <Tag color="geekblue" icon={<CodeOutlined />}>章节 LaTeX 工作台</Tag>
                  {selectedProject.metadata_json?.writing_context?.research_project_name && (
                    <Tag color="purple" style={{ borderRadius: 6 }}>
                      研究方向：{selectedProject.metadata_json.writing_context.research_project_name}
                    </Tag>
                  )}
                  {selectedProject.metadata_json?.writing_context?.collection_names?.length > 0 && (
                    <Tag color="geekblue" style={{ borderRadius: 6 }}>
                      论文分类 {selectedProject.metadata_json.writing_context.collection_names.length}
                    </Tag>
                  )}
                  {selectedProject.metadata_json?.writing_context?.target_venue && (
                    <Tag color="gold" style={{ borderRadius: 6 }}>
                      目标：{selectedProject.metadata_json.writing_context.target_venue} {selectedProject.metadata_json.writing_context.target_year || ''}
                    </Tag>
                  )}
                    </Space>
                    <Text type="secondary" style={{ display: 'block', marginTop: 6, fontSize: 12 }}>
                      正文写作按章节推进；综述生成和一次性工具已移到独立 workflow。模板配置只保留在投稿导出包中。
                    </Text>
                  </Col>
                  <Col>
                    <Space wrap>
                      <Button icon={<CodeOutlined />} loading={manuscriptPreviewing} onClick={handlePreviewManuscriptLatex} style={{ borderRadius: 8 }}>
                        整篇 LaTeX 检查
                      </Button>
                      <Button size="small" onClick={async () => { const r = await api.get(`/writing/projects/${selectedProject.id}/export?format=markdown`); handleCopy(r.data.data); }} style={{ borderRadius: 8 }}>导出 MD</Button>
                      <Button size="small" onClick={async () => { const r = await api.get(`/writing/projects/${selectedProject.id}/export?format=bibtex`); handleCopy(r.data.data || ''); }} style={{ borderRadius: 8 }}>导出 BibTeX</Button>
                      <Button size="small" onClick={handleDownloadDocx} style={{ borderRadius: 8 }}>导出 Word</Button>
                  <WorkspaceIssueReporter
                    resourceType="writing_projects"
                    resourceId={selectedProject.id}
                    resourceTitle={selectedProject.title}
                    resourcePath={`/writing?project=${selectedProject.id}`}
                  />
                    </Space>
                  </Col>
                </Row>
              </Card>
              <div style={{ marginBottom: 16 }}>
                <WorkspaceResourceLinks resourceType="writing_projects" resourceId={selectedProject.id} title="所属项目空间" />
              </div>
              {manuscriptPreview && <div style={{ marginBottom: 16 }}>{latexDiagnosticPanel(manuscriptPreview, '整篇')}</div>}
              <div id="writing-sections-panel" style={{ display: 'grid', gridTemplateColumns: '240px minmax(0, 1fr)', gap: 16, alignItems: 'start', marginBottom: 16 }}>
                <Card
                  title={<Space><FileTextOutlined /> 章节导航</Space>}
                  style={{ ...cardStyle, position: 'sticky', top: 12 }}
                  styles={{ body: { padding: 10, maxHeight: 640, overflowY: 'auto' } }}
                  extra={<Tag>{projectSections.length}</Tag>}
                >
                  <Button
                    block
                    type="primary"
                    ghost
                    icon={<PlusOutlined />}
                    loading={creatingSection}
                    onClick={handleCreateSection}
                    style={{ borderRadius: 10, marginBottom: 10 }}
                  >
                    新增章节
                  </Button>
                  {projectSections.length ? (
                    <Space direction="vertical" size={8} style={{ width: '100%' }}>
                      {projectSections.map((section, index) => {
                        const selected = activeSection?.id === section.id;
                        const hasLatexIssue = latexPreviewChecks[section.id] && !latexPreviewChecks[section.id].success;
                        return (
                          <Button
                            key={section.id}
                            block
                            type={selected ? 'primary' : 'default'}
                            onClick={() => setActiveSectionId(section.id)}
                            style={{
                              height: 'auto',
                              minHeight: 46,
                              borderRadius: 10,
                              textAlign: 'left',
                              whiteSpace: 'normal',
                              padding: '8px 10px',
                            }}
                          >
                            <div style={{ width: '100%', minWidth: 0 }}>
                              <Space size={6} wrap>
                                <Tag color={selected ? 'blue' : 'default'}>{index + 1}</Tag>
                                {hasLatexIssue && <Tag color="red">LaTeX</Tag>}
                              </Space>
                              <Text strong style={{ display: 'block', color: selected ? '#fff' : undefined, overflowWrap: 'anywhere' }}>{section.title || 'Untitled'}</Text>
                              <Text type={selected ? undefined : 'secondary'} style={{ fontSize: 12, color: selected ? 'rgba(255,255,255,0.82)' : undefined }}>
                                {section.word_count || 0} 字 · {section.status || 'draft'}
                              </Text>
                            </div>
                          </Button>
                        );
                      })}
                    </Space>
                  ) : (
                    <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无章节">
                      <Button
                        type="primary"
                        icon={<PlusOutlined />}
                        loading={creatingSection}
                        onClick={handleCreateSection}
                        style={{ borderRadius: 10 }}
                      >
                        创建第一个章节
                      </Button>
                    </Empty>
                  )}
                </Card>
                <Card
                  title={<Space><CodeOutlined /> 当前章节 LaTeX 源码</Space>}
                  style={cardStyle}
                  extra={activeSection && <Tag color="blue">{activeSection.title || 'Untitled'}</Tag>}
                >
                  {activeSection ? (
                    <SectionEditor
                      key={activeSection.id}
                      section={activeSection}
                      onUpdate={handleUpdateSection}
                      onFocus={section => setActiveSectionId(section.id)}
                      onCheckCitations={handleCheckSectionCitations}
                      onCheckQuality={handleCheckSectionQuality}
                      onPreviewLatex={handlePreviewSectionLatex}
                      onSectionAiAction={handleSectionAiAction}
                      checking={citationChecking[activeSection.id]}
                      qualityChecking={qualityChecking[activeSection.id]}
                      previewing={latexPreviewing[activeSection.id]}
                      citationCheck={citationChecks[activeSection.id]}
                      qualityCheck={qualityChecks[activeSection.id]}
                      latexPreview={latexPreviewChecks[activeSection.id]}
                      aiRunning={activeSectionAi.loading}
                      aiRunningAction={activeSectionAi.action}
                      aiStatus={activeSectionAi.status}
                      aiOutput={activeSectionAi.output}
                    />
                  ) : (
                    <WorkflowEmptyState
                      title="当前项目还没有章节"
                      description="先创建第一个章节，然后就可以按章节写作 LaTeX 源码。"
                      icon={<FileTextOutlined />}
                      action={<Button type="primary" icon={<PlusOutlined />} loading={creatingSection} onClick={handleCreateSection} style={{ borderRadius: 10 }}>创建第一个章节</Button>}
                    />
                  )}
                </Card>
              </div>
              {publicationExportPanel}
          </>
        ) : (
          <WorkflowEmptyState
            title="选择或创建一个论文项目开始"
            description="正文写作会按章节组织，每个章节都可以编辑 LaTeX 源码、运行预览检查并唤出当前章节 AI 助手。"
            icon={<FolderOutlined />}
          />
        )}
      </div>
    </div>
  );

  const surveyWorkflowPanel = (
    <div style={{ display: 'grid', gridTemplateColumns: '280px minmax(0, 1fr)', gap: 20, alignItems: 'start' }}>
      <WritingProjectPanel onSelectProject={handleSelectProject} selectedProjectId={selectedProject?.id} refreshSignal={projectRefreshSignal} />
      <Space direction="vertical" size={16} style={{ width: '100%' }}>
        <Card style={cardStyle} styles={{ body: { padding: 16 } }}>
          <Text strong>从研究方向创建综述草稿</Text>
          <Text type="secondary" style={{ display: 'block', fontSize: 12, margin: '4px 0 12px' }}>综述、Related Work 对比表、研究空白和参考文献作为独立 workflow 处理，不再混在正文编辑器顶部。</Text>
          <Row gutter={12}>
            <Col flex="auto"><Input placeholder="例如：video grounding in multimodal large language models" value={draftTopic} onChange={e => setDraftTopic(e.target.value)} style={inputStyle} /></Col>
            <Col><Button type="primary" icon={<RocketOutlined />} loading={draftLoading} onClick={handleCreateReviewDraft} style={primaryBtn}>创建综述草稿</Button></Col>
          </Row>
        </Card>
        <Row gutter={[16, 16]}>
          <Col xs={24} xl={12}>{relatedWorkTab}</Col>
          <Col xs={24} xl={12}>{litReviewTab}</Col>
          <Col xs={24}>{compareTab}</Col>
        </Row>
      </Space>
    </div>
  );

  const auxiliaryToolsPanel = (
    <Row gutter={[16, 16]}>
      <Col xs={24} xl={12}>{citationTab}</Col>
      <Col xs={24} xl={12}>{abstractTab}</Col>
      <Col xs={24}>{polishTab}</Col>
    </Row>
  );

  const paperWorkflowContent = paperWorkflow === 'manuscript'
    ? manuscriptWorkbench
    : paperWorkflow === 'survey'
      ? surveyWorkflowPanel
      : auxiliaryToolsPanel;

  return (
    <PageShell
      title={assistantMode === 'paper' ? '写作工作台' : '基金申请助手'}
      subtitle="以项目为中心管理论文、本子、证据、引用校验和导出预检。"
      icon={<EditOutlined />}
      maxWidth={assistantMode === 'paper' && paperWorkflow === 'manuscript' ? 1600 : 1100}
      actions={(
        <Segmented
          value={assistantMode}
          onChange={(value) => {
            const mode = value as 'paper' | 'grant';
            setAssistantMode(mode);
            if (mode === 'paper') setPaperWorkflow('manuscript');
          }}
          options={[
            { label: '写论文助手', value: 'paper', icon: <FileTextOutlined /> },
            { label: '写本子助手', value: 'grant', icon: <AuditOutlined /> },
          ]}
        />
      )}
    >
      {pageActionError ? (
        <ApiErrorAlert
          title={pageActionError.title}
          detail={pageActionError.detail}
          onClose={() => setPageActionError(null)}
          style={{ marginBottom: 18 }}
        />
      ) : null}

      <WorkflowStepGuide
        title="写作工作台下一步"
        subtitle="把研究方向、证据、引用和投稿模板收束到同一个写作流程。"
        style={{ marginBottom: 18 }}
        steps={[
          {
            key: 'research-source',
            title: '从研究方向开始',
            description: '先确认 idea 和实验计划，再把成熟方向转成写作项目。',
            actionLabel: '去研究方向',
            status: 'recommended',
            icon: <RocketOutlined />,
            path: '/research',
          },
          {
            key: 'evidence',
            title: '补齐证据与引用',
            description: '用证据卡片、引用推荐和句子校验降低写作幻觉风险。',
            actionLabel: '查看项目工作台',
            status: 'ready',
            icon: <BookOutlined />,
            onClick: () => {
              setAssistantMode('paper');
              setPaperWorkflow('manuscript');
              scrollToWorkbenchTarget('evidence');
            },
          },
          {
            key: 'export',
            title: '导出前检查模板',
            description: '会议格式每年会变，正式导出前应绑定或核对官方模板。',
            actionLabel: '查看导出预检',
            status: 'optional',
            icon: <DownloadOutlined />,
            onClick: () => {
              setAssistantMode('paper');
              setPaperWorkflow('manuscript');
              scrollToWorkbenchTarget('export');
            },
          },
        ]}
      />

      {assistantMode === 'paper' ? (
        <>
          <Alert
            type="info"
            showIcon
            style={{ borderRadius: 12, marginBottom: 18 }}
            message="写论文助手现在按章节写作"
            description="正文工作台默认按章节编辑 LaTeX 源码；综述、Related Work 和一次性辅助工具被拆到独立 workflow。官方模板不作为写正文的入口，只在导出预检里使用。"
          />
          <Segmented
            value={paperWorkflow}
            onChange={(value) => setPaperWorkflow(value as 'manuscript' | 'survey' | 'tools')}
            options={[
              { label: '论文章节工作台', value: 'manuscript', icon: <CodeOutlined /> },
              { label: '综述与 Related Work', value: 'survey', icon: <ReadOutlined /> },
              { label: '辅助工具', value: 'tools', icon: <RobotOutlined /> },
            ]}
            style={{ marginBottom: 18 }}
          />
          {paperWorkflowContent}
        </>
      ) : (
        <>
          <Alert
            type="warning"
            showIcon
            style={{ borderRadius: 12, marginBottom: 18 }}
            message="写本子助手独立处理申请书流程"
            description="本模式聚焦申请书分段撰写、模拟评审、创新点提炼和文本润色，避免和论文投稿流程混在一起。"
          />
          {grantTab}
        </>
      )}

      {/* ── 全局 CSS 动画 ── */}
      <style>{`
        @keyframes bounce {
          0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
          40% { transform: scale(1); opacity: 1; }
        }
        @media (max-width: 1100px) {
          .manuscript-workbench-grid {
            grid-template-columns: 1fr !important;
          }
          .manuscript-support-rail {
            position: static !important;
          }
          .manuscript-support-rail-collapsed {
            width: 100% !important;
            flex-direction: row !important;
            justify-content: flex-start !important;
          }
          #writing-sections-panel {
            grid-template-columns: 1fr !important;
          }
        }
      `}</style>
    </PageShell>
  );
};

export default WritingPage;
