import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card, Button, Input, Tag, Typography, Space, Spin,
  message, Row, Col, Modal, Divider, Popconfirm,
} from 'antd';
import {
  PlusOutlined, ExperimentOutlined, BulbOutlined,
  SearchOutlined, BookOutlined, CheckCircleFilled, DeleteOutlined,
  RocketOutlined,
} from '@ant-design/icons';
import api from '../services/api';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

const heroGradient = 'linear-gradient(135deg, #f5576c 0%, #ff9671 100%)';

interface Project {
  id: string; name: string; description: string | null;
  keywords: string[] | null; status: string; ideas_count: number;
}

const ResearchPage: React.FC = () => {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(false);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDesc, setNewProjectDesc] = useState('');
  const [newProjectKeywords, setNewProjectKeywords] = useState('');
  const [paperSearch, setPaperSearch] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [selectedPaperIds, setSelectedPaperIds] = useState<string[]>([]);
  const [searching, setSearching] = useState(false);

  const handlePaperSearch = async () => {
    if (!paperSearch.trim()) return;
    setSearching(true);
    try { const r = await api.get('/papers/search', { params: { q: paperSearch, source: 'local', page_size: 10 } }); setSearchResults(r.data.items.filter((p: any) => p.id)); }
    catch { } finally { setSearching(false); }
  };
  const togglePaper = (id: string) => { setSelectedPaperIds(prev => prev.includes(id) ? prev.filter(p => p !== id) : [...prev, id]); };
  const loadProjects = useCallback(async () => { setLoading(true); try { const r = await api.get('/research/projects'); setProjects(r.data); } catch { message.error('加载失败'); } finally { setLoading(false); } }, []);
  useEffect(() => { loadProjects(); }, [loadProjects]);
  const handleDelete = async (id: string, name: string) => { try { await api.delete(`/research/projects/${id}`); message.success(`已删除「${name}」`); loadProjects(); } catch { message.error('删除失败'); } };
  const handleCreate = async () => {
    if (!newProjectName.trim()) return;
    try {
      await api.post('/research/projects', { name: newProjectName, description: newProjectDesc, keywords: newProjectKeywords.split(',').map(k => k.trim()).filter(Boolean), paper_ids: selectedPaperIds });
      message.success('项目已创建！'); setCreateModalOpen(false);
      setNewProjectName(''); setNewProjectDesc(''); setNewProjectKeywords(''); setSelectedPaperIds([]); setSearchResults([]); setPaperSearch('');
      loadProjects();
    } catch { message.error('创建失败'); }
  };

  const statusColors: Record<string, string> = { active: '#52c41a', completed: '#1677ff', archived: '#999' };
  const statusLabels: Record<string, string> = { active: '进行中', completed: '已完成', archived: '已归档' };

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto' }}>
      {/* ── Hero ── */}
      <div style={{ background: heroGradient, borderRadius: 16, padding: '28px 36px', marginBottom: 24, color: '#fff', position: 'relative', overflow: 'hidden' }}>
        <div style={{ position: 'absolute', right: -10, top: -20, fontSize: 130, opacity: 0.1 }}>🔬</div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Space size={12}>
            <div style={{ width: 48, height: 48, borderRadius: 14, background: 'rgba(255,255,255,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 24 }}><ExperimentOutlined /></div>
            <div>
              <Title level={3} style={{ color: '#fff', margin: 0 }}>研究方向</Title>
              <Text style={{ color: 'rgba(255,255,255,0.75)', fontSize: 14 }}>创建研究方向，让 AI 分析论文、生成 Idea、构建实验代码</Text>
            </div>
          </Space>
          <Button type="primary" size="large" icon={<PlusOutlined />} onClick={() => setCreateModalOpen(true)} style={{ borderRadius: 12, height: 44, background: '#fff', color: '#f5576c', border: 'none', fontWeight: 600 }}>新建方向</Button>
        </div>
      </div>

      {/* ── 项目列表 ── */}
      <Spin spinning={loading}>
        {projects.length === 0 ? (
          <Card style={{ borderRadius: 16, textAlign: 'center', padding: 80, border: '2px dashed #e8e8e8' }}>
            <div style={{ width: 80, height: 80, borderRadius: 20, background: '#fff0f2', margin: '0 auto 20px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <ExperimentOutlined style={{ fontSize: 36, color: '#f5576c' }} />
            </div>
            <Title level={4} style={{ color: '#333' }}>还没有研究方向</Title>
            <Text type="secondary" style={{ fontSize: 14, display: 'block', marginBottom: 24 }}>
              创建研究方向后，AI 将分析知识库论文，为你生成创新性的研究 Idea
            </Text>
            <Button type="primary" size="large" icon={<RocketOutlined />} onClick={() => setCreateModalOpen(true)} style={{ borderRadius: 12, height: 44 }}>创建第一个方向</Button>
          </Card>
        ) : (
          <Row gutter={[16, 16]}>
            {projects.map(p => (
              <Col xs={24} sm={12} lg={8} key={p.id}>
                <Card hoverable style={{ borderRadius: 14, height: '100%', border: '1px solid #f0f0f0', transition: 'all 0.3s', overflow: 'hidden' }}
                  onClick={() => navigate(`/research/${p.id}`)}
                  extra={
                    <Popconfirm title={`删除「${p.name}」？`} description="将同时删除该方向下的所有 Idea"
                      onConfirm={e => { e?.stopPropagation(); handleDelete(p.id, p.name); }}
                      onCancel={e => e?.stopPropagation()}>
                      <Button type="text" size="small" danger icon={<DeleteOutlined />} onClick={e => e.stopPropagation()} />
                    </Popconfirm>
                  }>
                  {/* 顶部色条 */}
                  <div style={{ height: 4, background: `linear-gradient(90deg, ${statusColors[p.status] || '#667eea'}, transparent)`, margin: '-1px -1px 0 -1px', borderTopLeftRadius: 14, borderTopRightRadius: 14 }} />
                  <div style={{ marginTop: 8 }}>
                    <Text strong style={{ fontSize: 15 }}>{p.name}</Text>
                    <Paragraph type="secondary" ellipsis={{ rows: 2 }} style={{ minHeight: 42, marginBottom: 12, marginTop: 4, fontSize: 13 }}>
                      {p.description || '暂无描述'}
                    </Paragraph>
                  </div>
                  {p.keywords && p.keywords.length > 0 && (
                    <Space size={4} wrap style={{ marginBottom: 12 }}>
                      {p.keywords.slice(0, 4).map((k, i) => <Tag key={i} color="blue" style={{ borderRadius: 6 }}>{k}</Tag>)}
                    </Space>
                  )}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid #f5f5f5', paddingTop: 10 }}>
                    <Space size={8}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                        <BulbOutlined style={{ color: '#faad14' }} />
                        <Text strong style={{ color: '#faad14' }}>{p.ideas_count}</Text>
                        <Text type="secondary" style={{ fontSize: 12 }}>Idea</Text>
                      </div>
                    </Space>
                    <Tag color={p.status === 'active' ? 'green' : 'default'} style={{ borderRadius: 6 }}>{statusLabels[p.status] || p.status}</Tag>
                  </div>
                </Card>
              </Col>
            ))}
          </Row>
        )}
      </Spin>

      {/* ── 创建弹窗 ── */}
      <Modal title={<span><ExperimentOutlined style={{ color: '#f5576c', marginRight: 8 }} />新建研究方向</span>}
        open={createModalOpen} onOk={handleCreate} onCancel={() => setCreateModalOpen(false)}
        okText="创建" cancelText="取消" width={560}
        okButtonProps={{ style: { borderRadius: 10 } }} cancelButtonProps={{ style: { borderRadius: 10 } }}>
        <Space direction="vertical" style={{ width: '100%' }} size={12}>
          <Input size="large" style={{ borderRadius: 10 }} placeholder="方向名称，如：多模态大模型对齐" value={newProjectName} onChange={e => setNewProjectName(e.target.value)} prefix={<ExperimentOutlined style={{ color: '#f5576c' }} />} />
          <TextArea style={{ borderRadius: 10 }} placeholder="简要描述研究方向..." value={newProjectDesc} onChange={e => setNewProjectDesc(e.target.value)} rows={3} />
          <Input style={{ borderRadius: 10 }} placeholder="关键词（逗号分隔），如：RLHF, alignment, reward modeling" value={newProjectKeywords} onChange={e => setNewProjectKeywords(e.target.value)} prefix={<Tag color="blue" style={{ margin: 0 }}>🏷️</Tag>} />
          <Divider style={{ fontSize: 13, margin: '4px 0' }}><BookOutlined style={{ color: '#f5576c' }} /> 关联论文（可选）</Divider>
          <Text type="secondary" style={{ fontSize: 12 }}>关联论文后，Idea 生成将优先基于这些论文进行分析</Text>
          <Input.Search placeholder="搜索论文..." value={paperSearch} onChange={e => setPaperSearch(e.target.value)} onSearch={handlePaperSearch} loading={searching} enterButton={<SearchOutlined />} style={{ borderRadius: 10 }} />
          {searchResults.length > 0 && (
            <div style={{ maxHeight: 200, overflowY: 'auto', border: '1px solid #f0f0f0', borderRadius: 10, padding: 4 }}>
              {searchResults.map((p: any) => {
                const sel = selectedPaperIds.includes(p.id);
                return (
                  <div key={p.id} onClick={() => togglePaper(p.id)} style={{ padding: '8px 10px', cursor: 'pointer', borderRadius: 8, background: sel ? '#fff0f2' : 'transparent', display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2, border: sel ? '1px solid #ffa39e' : '1px solid transparent', transition: 'all 0.2s' }}>
                    {sel ? <CheckCircleFilled style={{ color: '#f5576c', fontSize: 16 }} /> : <div style={{ width: 16, height: 16, borderRadius: '50%', border: '2px solid #d9d9d9' }} />}
                    <Text style={{ fontSize: 13, flex: 1 }} ellipsis>{p.title}</Text>
                    {p.year && <Tag style={{ fontSize: 11, borderRadius: 6 }}>{p.year}</Tag>}
                  </div>
                );
              })}
            </div>
          )}
          {selectedPaperIds.length > 0 && <Text type="secondary" style={{ fontSize: 12 }}>✅ 已选择 {selectedPaperIds.length} 篇论文</Text>}
        </Space>
      </Modal>
    </div>
  );
};

export default ResearchPage;
