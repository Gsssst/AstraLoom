import React, { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Input, Button, List, Tag, Select, Space, Typography, Spin, Badge,
  Card, message, Modal, Checkbox, Row, Col,
} from 'antd';
import {
  SearchOutlined, CalendarOutlined, UserOutlined,
  RiseOutlined, LoadingOutlined,
  StarFilled, StarOutlined, DeleteOutlined, ExclamationCircleOutlined,
  ImportOutlined, FileTextOutlined, BookOutlined,
  RocketOutlined, EyeOutlined, RedoOutlined, LinkOutlined,
  BellOutlined, PlayCircleOutlined, CheckCircleOutlined, RollbackOutlined,
  FolderOutlined, FolderAddOutlined,
} from '@ant-design/icons';
import api from '../services/api';
import { useAuthStore } from '../stores/useAuthStore';

const { Text, Paragraph, Title } = Typography;

interface PaperItem {
  id: string; title: string; authors: string[]; year: number | null;
  abstract: string | null; abstract_full?: string | null; arxiv_id: string | null; doi: string | null;
  source: string; citation_count: number; created_at: string;
  remote_id?: string | null;
  remote_ingest_token?: string | null;
  pdf_url?: string | null;
  source_url?: string | null;
  read_status?: 'unread' | 'reading' | 'completed' | null;
}

interface PaperCollection {
  id: string;
  name: string;
  paper_count?: number;
}

const heroGradient = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
const readingStatusMeta = {
  unread: { label: '待读', color: 'default' as const },
  reading: { label: '阅读中', color: 'processing' as const },
  completed: { label: '已完成', color: 'success' as const },
};

const PapersPage: React.FC = () => {
  const navigate = useNavigate();
  const [papers, setPapers] = useState<PaperItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [source, setSource] = useState<string>('local');
  const [ingesting, setIngesting] = useState(false);
  const [ingestQuery, setIngestQuery] = useState('');
  const [sort, setSort] = useState<string>('created_desc');
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [reportModalOpen, setReportModalOpen] = useState(false);
  const [reportTitle, setReportTitle] = useState('组会报告');
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
  const isAuthenticated = !!localStorage.getItem('access_token');
  const isAdmin = useAuthStore((state) => state.user?.role === 'admin');
  const isRemoteSource = ['scholarly', 'arxiv', 'semantic_scholar', 'openalex', 'google_scholar'].includes(source);
  const yearOptions = Array.from({ length: new Date().getFullYear() - 1899 }, (_, index) => {
    const year = new Date().getFullYear() - index;
    return { value: year, label: `${year}` };
  });

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

  const handleSearch = useCallback(async (requestedRemotePage = 1) => {
    if (yearFrom && yearTo && yearFrom > yearTo) {
      message.warning('起始年份不能晚于截止年份');
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
        const r = await api.get('/papers/search', { params: { q: searchQuery, source, sort, page: requestedPage, page_size: 30, year_from: yearFrom, year_to: yearTo } });
        setPapers(r.data.items);
        setRemotePage(requestedPage);
      }
    } catch (e: any) { setPapers([]); message.error(e.response?.data?.detail || (e.code === 'ECONNABORTED' ? '远程学术检索超时，请稍后重试' : '搜索失败')); } finally { setLoading(false); }
  }, [isRemoteSource, readingStatus, searchQuery, selectedCollectionId, source, sort, yearFrom, yearTo]);

  useEffect(() => { handleSearch(1); }, [source, sort, readingStatus, selectedCollectionId]);

  useEffect(() => { fetchReadingCounts(); }, [fetchReadingCounts, source]);

  useEffect(() => { fetchCollections(); }, [fetchCollections]);

  useEffect(() => {
    if (source === 'collection' && !selectedCollectionId && collections.length > 0) {
      setSelectedCollectionId(collections[0].id);
    }
  }, [collections, selectedCollectionId, source]);

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
        const r = await api.post('/writing/group-report', { paper_ids: Array.from(selectedIds), title: reportTitle }, { responseType: 'blob', timeout: 120000 });
        const url = URL.createObjectURL(new Blob([r.data])); const a = document.createElement('a');
        a.href = url; a.download = `${reportTitle}_${new Date().toISOString().slice(0, 10)}.docx`; a.click();
        message.success('报告已下载');
      }
    } catch { message.error('生成失败'); } finally { setReportLoading(false); setReportModalOpen(false); }
  };

  const handleIngestOne = useCallback(async (e: React.MouseEvent, paper: PaperItem) => {
    e.stopPropagation();
    if (!paper.remote_id) return;
    const remoteKey = `${paper.source}:${paper.remote_id}`;
    setIngestingIds(prev => new Set(prev).add(remoteKey));
    try {
      await api.post('/papers/ingest-personal', {
        source: paper.source,
        remote_id: paper.remote_id,
        remote_ingest_token: paper.remote_ingest_token,
        auto_download: false,
      });
      setIngestedRemoteIds(prev => new Set(prev).add(remoteKey));
      message.success('已加入你的论文库');
    } catch (e: any) {
      message.error(e.response?.data?.detail || '加入论文库失败');
    } finally {
      setIngestingIds(prev => { const n = new Set(prev); n.delete(remoteKey); return n; });
    }
  }, []);

  const handleIngest = useCallback(async () => {
    if (!ingestQuery.trim()) { message.warning('请输入搜索关键词或 arXiv ID'); return; }
    setIngesting(true);
    try {
      const isId = /^\d{4}\.\d{4,5}(v\d+)?$/.test(ingestQuery.trim());
      const r = await api.post('/papers/ingest', isId ? { arxiv_ids: [ingestQuery.trim()], auto_download: true } : { search_query: ingestQuery.trim(), max_results: 10, auto_download: true });
      message.success(`入库完成: ${r.data.success} 新增, ${r.data.skipped} 已存在${r.data.error > 0 ? `, ${r.data.error} 失败` : ''}`);
      if (r.data.success > 0) handleSearch();
    } catch { message.error('入库失败'); } finally { setIngesting(false); }
  }, [ingestQuery, handleSearch]);

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
    } catch { message.error('操作失败'); }
  }, [savedIds, isAuthenticated]);

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
      message.success('分类已创建');
      await fetchCollections();
      setSource('collection');
      setSelectedCollectionId(response.data.id);
      setTargetCollectionId(response.data.id);
    } catch (e: any) {
      message.error(e.response?.data?.detail || '创建分类失败');
    } finally {
      setCreatingCollection(false);
    }
  }, [fetchCollections, isAuthenticated]);

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
      message.success(`已加入分类：新增 ${response.data.added || 0} 篇，跳过 ${response.data.skipped || 0} 篇`);
      setSelectedIds(new Set());
      await fetchCollections();
      if (source === 'collection' && selectedCollectionId === targetCollectionId) handleSearch();
    } catch (e: any) {
      message.error(e.response?.data?.detail || '加入分类失败');
    } finally {
      setAddingCollection(false);
    }
  }, [fetchCollections, handleSearch, selectedCollectionId, selectedIds, source, targetCollectionId]);

  const handleRemoveFromCollection = useCallback(async (e: React.MouseEvent, paper: PaperItem) => {
    e.stopPropagation();
    if (!selectedCollectionId || !paper.id) return;
    try {
      await api.delete(`/folders/${selectedCollectionId}/papers/${paper.id}`);
      message.success('已从分类移除');
      setPapers(prev => prev.filter(item => item.id !== paper.id));
      await fetchCollections();
    } catch (err: any) {
      message.error(err.response?.data?.detail || '移出分类失败');
    }
  }, [fetchCollections, selectedCollectionId]);

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
      message.success(`已标记为${readingStatusMeta[status].label}`);
    } catch {
      message.error('阅读状态更新失败');
    } finally {
      setUpdatingStatusIds(prev => { const n = new Set(prev); n.delete(paper.id); return n; });
    }
  }, [fetchReadingCounts, isAuthenticated, readingStatus, source]);

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

  const confirmDelete = async (global: boolean) => {
    if (!deleteModal.paper) return; setDeleting(true);
    try { await api.delete(`/papers/${deleteModal.paper.id}${global ? '/global' : ''}`); message.success(global ? '已从总库删除' : '已从收藏移除'); setPapers(prev => prev.filter(p => p.id !== deleteModal.paper!.id)); setSavedIds(prev => { const n = new Set(prev); n.delete(deleteModal.paper!.id!); return n; }); }
    catch (e: any) { message.error(e.response?.data?.detail || '删除失败'); } finally { setDeleting(false); setDeleteModal({ open: false, paper: null }); }
  };

  const sc = (s: string) => ({ arxiv: '#b31b1b', semantic_scholar: '#1890ff', openalex: '#13a8a8', google_scholar: '#5f6368', manual: '#52c41a' }[s] || '#999');
  const sl = (s: string) => ({ arxiv: 'arXiv', semantic_scholar: 'Semantic Scholar', openalex: 'OpenAlex', google_scholar: 'Google Scholar', manual: '手动' }[s] || s);

  const stats = papers.length > 0 ? `共 ${papers.length} 篇论文` : '';

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', height: 'calc(100vh - 110px)', display: 'flex', flexDirection: 'column' }}>
      {/* ── Hero ── */}
      <div style={{ background: heroGradient, borderRadius: 16, padding: '18px 28px', marginBottom: 12, color: '#fff', position: 'relative', overflow: 'hidden', flexShrink: 0 }}>
        <div style={{ position: 'absolute', right: -10, top: -30, fontSize: 140, opacity: 0.08 }}>📚</div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
          <Space size={12}>
            <div style={{ width: 48, height: 48, borderRadius: 14, background: 'rgba(255,255,255,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 24 }}><BookOutlined /></div>
            <div>
              <Title level={3} style={{ color: '#fff', margin: 0 }}>论文知识库</Title>
              <Text style={{ color: 'rgba(255,255,255,0.75)', fontSize: 13 }}>{stats || '搜索、发现、管理你的学术论文'}</Text>
            </div>
          </Space>
          <Space size={8} wrap>
            {isAuthenticated && (
              <Badge count={digestUnreadCount} size="small">
                <Button icon={<BellOutlined />} onClick={() => navigate('/papers/digests')} style={{ borderRadius: 10, background: 'rgba(255,255,255,0.2)', color: '#fff', border: 'none' }}>论文推送</Button>
              </Badge>
            )}
            {isAdmin && <>
              <Button icon={<ImportOutlined />} loading={ingesting} onClick={handleIngest} style={{ borderRadius: 10, background: 'rgba(255,255,255,0.2)', color: '#fff', border: 'none' }}>一键入库</Button>
              <Button icon={<FileTextOutlined />} onClick={() => (document.getElementById('import-file') as HTMLInputElement)?.click()} style={{ borderRadius: 10, background: 'rgba(255,255,255,0.2)', color: '#fff', border: 'none' }}>导入</Button>
              <input type="file" accept=".csv,.bib" style={{ display: 'none' }} id="import-file" onChange={async (e) => {
                const f = e.target.files?.[0]; if (!f) return;
                const ep = f.name.endsWith('.bib') ? '/api/papers/import-bibtex' : '/api/papers/import-zotero';
                const fd = new FormData(); fd.append('file', f);
                try { const r = await api.post(ep, fd, { headers: { 'Content-Type': 'multipart/form-data' } }); message.success(`导入: ${r.data.imported} 新增, ${r.data.skipped} 跳过`); handleSearch(); } catch { message.error('导入失败'); }
              }} />
            </>}
            <Button icon={<FileTextOutlined />} disabled={selectedIds.size === 0} onClick={() => setReportModalOpen(true)} style={{ borderRadius: 10, background: 'rgba(255,255,255,0.2)', color: '#fff', border: 'none' }}>
              组会报告 ({selectedIds.size})
            </Button>
          </Space>
        </div>
      </div>

      {/* ── 搜索栏 ── */}
      <Card style={{ borderRadius: 14, marginBottom: 12, border: '1px solid #f0f0f0', flexShrink: 0 }} styles={{ body: { padding: '10px 20px' } }}>
        <Row gutter={[8, 8]} align="middle">
          <Col xs={24} sm={4}><Select value={source} onChange={setSource} style={{ width: '100%', borderRadius: 10 }}
            options={[
              { value: 'local', label: '📚 全部论文' },
              { value: 'saved', label: '⭐ 收藏' },
              { value: 'collection', label: '🗂️ 自定义分类' },
              { value: 'reading', label: '📖 阅读列表' },
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
                  options={collections.map(item => ({ value: item.id, label: `${item.name}（${item.paper_count || 0}）` }))}
                  style={{ minWidth: 220 }}
                />
                <Button icon={<FolderAddOutlined />} loading={creatingCollection} onClick={handleCreateCollection} style={{ borderRadius: 8 }}>
                  新建分类
                </Button>
              </Space>
            </Col>
          </Row>
        )}
        <Row gutter={[8, 8]} align="middle" style={{ marginTop: 8 }}>
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
        </Row>
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
      <Spin spinning={loading}>
        {papers.length > 0 ? (
          <List dataSource={papers} renderItem={(paper, idx) => (
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
                      {paper.read_status && <Tag color={readingStatusMeta[paper.read_status].color} style={{ borderRadius: 6 }}>{readingStatusMeta[paper.read_status].label}</Tag>}
                      {paper.citation_count > 0 && <Tag icon={<RiseOutlined />} color="orange" style={{ borderRadius: 6 }}>引用 {paper.citation_count}</Tag>}
                      <Button type="link" size="small" icon={<EyeOutlined />} onClick={e => handleOpenAbstract(e, paper)} style={{ height: 24, paddingInline: 4 }}>查看摘要</Button>
                      {paper.pdf_url && <Button type="link" size="small" icon={<FileTextOutlined />} href={paper.pdf_url} target="_blank" rel="noreferrer" onClick={e => e.stopPropagation()} style={{ height: 24, paddingInline: 4 }}>开放 PDF</Button>}
                      {source === 'collection' && selectedCollectionId && <Button type="link" danger size="small" onClick={e => handleRemoveFromCollection(e, paper)} style={{ height: 24, paddingInline: 4 }}>移出分类</Button>}
                      {!paper.id && isAuthenticated && paper.remote_id ? (
                        ingestedRemoteIds.has(`${paper.source}:${paper.remote_id}`)
                          ? <Tag color="green" style={{ borderRadius: 6 }}>已加入论文库</Tag>
                          : <Button size="small" type="primary" ghost icon={<ImportOutlined />} loading={ingestingIds.has(`${paper.source}:${paper.remote_id}`)}
                            onClick={e => handleIngestOne(e, paper)} style={{ borderRadius: 8, height: 24 }}>加入论文库</Button>
                      ) : paper.id ? <Tag color="green" style={{ borderRadius: 6 }}>已入库</Tag> : null}
                    </Space>
                  </div>
                  {paper.abstract && <Paragraph type="secondary" ellipsis={{ rows: 2 }} style={{ marginTop: 8, marginBottom: 0, fontSize: 13 }}>{paper.abstract}</Paragraph>}
                  {renderReadingActions(paper)}
                </Col>
                {isAuthenticated && paper.id && (
                  <Col style={{ flexShrink: 0 }}>
                    <Space size={2}>
                      <Button type="text" size="small" icon={savedIds.has(paper.id) ? <StarFilled style={{ color: '#faad14' }} /> : <StarOutlined />} onClick={e => handleSave(e, paper)} />
                      <Button type="text" size="small" danger icon={<DeleteOutlined />} onClick={e => handleDeleteClick(e, paper)} />
                    </Space>
                  </Col>
                )}
              </Row>
            </Card>
          )} />
        ) : (
          <Card style={{ borderRadius: 16, textAlign: 'center', padding: 60, border: '2px dashed #e8e8e8' }}>
            <div style={{ width: 80, height: 80, borderRadius: 20, background: '#f0f2ff', margin: '0 auto 20px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <BookOutlined style={{ fontSize: 36, color: '#667eea' }} />
            </div>
            <Title level={4}>暂无论文</Title>
            <Text type="secondary" style={{ fontSize: 14, display: 'block', marginBottom: 20 }}>尝试搜索 arXiv 或一键入库来添加论文</Text>
            <Button type="primary" size="large" icon={<RocketOutlined />} onClick={() => { setIngestQuery('large language model'); handleIngest(); }} style={{ borderRadius: 12, height: 44 }}>示例：检索 "large language model"</Button>
          </Card>
        )}
      </Spin>
      </div>

      {/* ── 底部选择栏 ── */}
      {selectedIds.size > 0 && (
        <div style={{ position: 'fixed', bottom: 24, left: '50%', transform: 'translateX(-50%)', zIndex: 100, background: 'rgba(255,255,255,0.95)', backdropFilter: 'blur(10px)', borderRadius: 16, boxShadow: '0 8px 32px rgba(0,0,0,0.12)', padding: '10px 24px', display: 'flex', gap: 12, alignItems: 'center', border: '1px solid #e8e8e8' }}>
          <div style={{ background: heroGradient, color: '#fff', borderRadius: 10, padding: '2px 12px', fontWeight: 600, fontSize: 13 }}>已选 {selectedIds.size} 篇</div>
          <Select
            size="small"
            placeholder="加入分类"
            value={targetCollectionId}
            onChange={setTargetCollectionId}
            options={collections.map(item => ({ value: item.id, label: `${item.name}（${item.paper_count || 0}）` }))}
            style={{ width: 180 }}
            suffixIcon={<FolderOutlined />}
          />
          <Button size="small" icon={<FolderAddOutlined />} loading={addingCollection} onClick={handleAddSelectedToCollection} style={{ borderRadius: 8 }}>加入分类</Button>
          <Button size="small" icon={<FolderAddOutlined />} loading={creatingCollection} onClick={handleCreateCollection} style={{ borderRadius: 8 }}>新建分类</Button>
          {isAdmin && <Button size="small" onClick={() => { const t = prompt('输入标签'); if (t) { api.post('/papers/batch-tag', { paper_ids: Array.from(selectedIds), tags: t.split(',').map(x => x.trim()).filter(Boolean) }).then(() => { message.success('已添加'); setSelectedIds(new Set()); handleSearch(); }).catch(() => message.error('失败')); } }} style={{ borderRadius: 8 }}>🏷️ 标签</Button>}
          <Button size="small" onClick={async () => { const r = await api.post('/writing/export', { format: 'bibtex', paper_ids: Array.from(selectedIds) }); const b = new Blob([r.data.data], { type: 'text/plain' }); const a = document.createElement('a'); a.href = URL.createObjectURL(b); a.download = 'selected.bib'; a.click(); }} style={{ borderRadius: 8 }}>📥 导出</Button>
          <Button size="small" onClick={() => setSelectedIds(new Set())} style={{ borderRadius: 8 }}>✕</Button>
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

      <Modal title="生成组会报告" open={reportModalOpen} onCancel={() => setReportModalOpen(false)}
        footer={[<Button key="cancel" onClick={() => setReportModalOpen(false)}>取消</Button>, <Button key="md" icon={<FileTextOutlined />} loading={reportLoading} onClick={async () => {
          const ids = Array.from(selectedIds).join(',');
          try { const r = await api.get(`/writing/group-report-md?paper_ids=${ids}&title=${encodeURIComponent(reportTitle)}`); await navigator.clipboard.writeText(r.data.result); message.success('已复制，可粘贴到飞书'); setReportModalOpen(false); } catch { message.error('失败'); }
        }}>复制 MD</Button>, <Button key="docx" type="primary" icon={<FileTextOutlined />} loading={reportLoading} onClick={() => handleReport('docx')}>下载 Word</Button>]}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Text>已选择 {selectedIds.size} 篇论文</Text>
          <Input placeholder="报告标题" value={reportTitle} onChange={e => setReportTitle(e.target.value)} style={{ borderRadius: 10 }} />
        </Space>
      </Modal>
    </div>
  );
};

export default PapersPage;
