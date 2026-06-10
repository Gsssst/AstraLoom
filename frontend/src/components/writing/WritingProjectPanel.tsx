import React, { useState, useEffect } from 'react';
import { Alert, Card, Button, List, Tag, Progress, Space, Modal, Input, Select, Typography, Popconfirm, message } from 'antd';
import { PlusOutlined, DeleteOutlined, FolderOutlined } from '@ant-design/icons';
import api from '../../services/api';

const { Text } = Typography;

interface Project {
  id: string;
  title: string;
  description: string;
  template_type: string;
  status: string;
  metadata_json?: any;
  sections: any[];
  progress: { percentage: number; completed: number; total: number; total_words: number };
  created_at: string;
  updated_at: string;
}

interface Template {
  key: string;
  name: string;
  description: string;
  section_count: number;
}

interface ResearchProjectOption {
  id: string;
  name: string;
  description?: string;
}

interface CollectionOption {
  id: string;
  name: string;
  paper_count?: number;
  children?: CollectionOption[];
}

interface WritingProjectPanelProps {
  onSelectProject: (project: Project) => void;
  onProjectDeleted?: (projectId: string) => void;
  selectedProjectId?: string;
  refreshSignal?: number;
}

const normalizeProject = (project: any): Project | null => {
  if (!project?.id) return null;
  const sections = Array.isArray(project.sections) ? project.sections : [];
  const rawProgress = project.progress || {};
  const progress = {
    percentage: Number(rawProgress.percentage || 0),
    completed: Number(rawProgress.completed || 0),
    total: Number(rawProgress.total || sections.length || 0),
    total_words: Number(rawProgress.total_words || 0),
  };
  return {
    ...project,
    id: String(project.id),
    title: project.title || 'Untitled',
    description: project.description || '',
    template_type: project.template_type || 'blank',
    status: project.status || 'draft',
    metadata_json: project.metadata_json || {},
    sections,
    progress,
  };
};

const WritingProjectPanel: React.FC<WritingProjectPanelProps> = ({
  onSelectProject,
  onProjectDeleted,
  selectedProjectId,
  refreshSignal = 0,
}) => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [researchProjects, setResearchProjects] = useState<ResearchProjectOption[]>([]);
  const [collections, setCollections] = useState<CollectionOption[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [newTemplate, setNewTemplate] = useState('blank');
  const [writingType, setWritingType] = useState('paper');
  const [targetVenue, setTargetVenue] = useState('');
  const [targetYear, setTargetYear] = useState('');
  const [selectedResearchProjectId, setSelectedResearchProjectId] = useState<string | undefined>();
  const [selectedCollectionIds, setSelectedCollectionIds] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadProjects();
    loadTemplates();
    loadContextOptions();
  }, [refreshSignal]);

  const loadProjects = async () => {
    try {
      const res = await api.get('/writing/projects');
      setProjects(res.data.projects || []);
    } catch { /* ignore */ }
  };

  const loadTemplates = async () => {
    try {
      const res = await api.get('/writing/projects/templates');
      setTemplates(res.data.templates || []);
    } catch { /* ignore */ }
  };

  const flattenCollections = (items: CollectionOption[], depth = 0): { value: string; label: string }[] => items.flatMap(item => [
    { value: item.id, label: `${'　'.repeat(depth)}${item.name}（${item.paper_count || 0}）` },
    ...flattenCollections(item.children || [], depth + 1),
  ]);

  const loadContextOptions = async () => {
    try {
      const [researchRes, foldersRes] = await Promise.all([
        api.get('/research/projects'),
        api.get('/folders/'),
      ]);
      setResearchProjects(researchRes.data || []);
      setCollections(foldersRes.data || []);
    } catch {
      // Context binding is optional; project creation still works without these selectors.
    }
  };

  const handleCreate = async () => {
    if (loading) return;
    if (!newTitle.trim()) {
      message.warning('请先填写项目标题');
      return;
    }
    setLoading(true);
    try {
      const response = await api.post('/writing/projects', {
        title: newTitle,
        description: newDesc,
        template_type: newTemplate,
        writing_type: writingType,
        target_venue: targetVenue,
        target_year: targetYear,
        research_project_id: selectedResearchProjectId,
        collection_ids: selectedCollectionIds,
      });
      const project = normalizeProject(response.data);
      if (!project) throw new Error('写作项目创建成功，但返回数据不完整');
      setShowCreate(false);
      setNewTitle(''); setNewDesc(''); setNewTemplate('blank');
      setWritingType('paper'); setTargetVenue(''); setTargetYear('');
      setSelectedResearchProjectId(undefined); setSelectedCollectionIds([]);
      onSelectProject(project);
      await loadProjects();
      message.success('写作项目已创建');
    } catch (error) {
      const fallback = error instanceof Error ? error.message : '创建写作项目失败';
      message.error(fallback || '创建写作项目失败');
    }
    finally { setLoading(false); }
  };

  const handleDelete = async (id: string) => {
    try {
      await api.delete(`/writing/projects/${id}`);
      setProjects(prev => prev.filter(project => project.id !== id));
      onProjectDeleted?.(id);
      await loadProjects();
      message.success('项目已删除');
    } catch {
      message.error('删除写作项目失败');
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <Text strong><FolderOutlined /> 我的项目</Text>
        <Button type="primary" size="small" icon={<PlusOutlined />} onClick={() => setShowCreate(true)}>
          新建
        </Button>
      </div>

      <List
        size="small"
        dataSource={projects}
        locale={{ emptyText: '暂无项目，点击"新建"创建' }}
        renderItem={(rawProject) => {
          const project = normalizeProject(rawProject);
          if (!project) return null;
          return (
          <Card
            size="small"
            hoverable
            style={{
              marginBottom: 8, borderRadius: 8,
              border: project.id === selectedProjectId ? '2px solid #667eea' : '1px solid #f0f0f0',
            }}
            onClick={() => onSelectProject(project)}
            extra={
              <span onClick={event => event.stopPropagation()}>
                <Popconfirm
                  title="确定删除？"
                  onConfirm={(event) => {
                    event?.stopPropagation?.();
                    handleDelete(project.id);
                  }}
                  onCancel={(event) => event?.stopPropagation?.()}
                >
                  <Button
                    size="small"
                    type="text"
                    danger
                    icon={<DeleteOutlined />}
                    onClick={event => event.stopPropagation()}
                  />
                </Popconfirm>
              </span>
            }
          >
            <Text strong ellipsis style={{ fontSize: 13 }}>{project.title}</Text>
            <div style={{ marginTop: 4 }}>
              <Space size="small" wrap>
                <Tag>{project.template_type.toUpperCase()}</Tag>
                <Tag color={project.status === 'complete' ? 'green' : 'blue'}>{project.status}</Tag>
                {project.metadata_json?.writing_context?.research_project_name && (
                  <Tag color="purple">方向：{project.metadata_json.writing_context.research_project_name}</Tag>
                )}
                {project.metadata_json?.writing_context?.collection_names?.length > 0 && (
                  <Tag color="geekblue">分类 {project.metadata_json.writing_context.collection_names.length}</Tag>
                )}
                <Text type="secondary" style={{ fontSize: 11 }}>
                  {project.progress.total_words} 字
                </Text>
              </Space>
            </div>
            <Progress percent={project.progress.percentage} size="small" style={{ marginTop: 4 }}
              format={() => `${project.progress.completed}/${project.progress.total}`} />
          </Card>
          );
        }}
      />

      <Modal title="新建写作项目" open={showCreate} onOk={handleCreate} onCancel={() => setShowCreate(false)}
        confirmLoading={loading}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Input placeholder="项目标题" value={newTitle} onChange={e => setNewTitle(e.target.value)} />
          <Input placeholder="项目描述（可选）" value={newDesc} onChange={e => setNewDesc(e.target.value)} />
          <Select
            value={writingType}
            onChange={(value) => {
              setWritingType(value);
              if (value === 'grant') setNewTemplate('nsfc');
              if (value === 'survey' && newTemplate === 'blank') setNewTemplate('survey');
            }}
            style={{ width: '100%' }}
            options={[
              { value: 'paper', label: '论文写作' },
              { value: 'survey', label: '综述写作' },
              { value: 'grant', label: '本子/申请书' },
            ]}
          />
          <Alert
            type="info"
            showIcon
            message="这里选择的是章节结构模板"
            description="ACL/CVPR/NeurIPS 等只用于生成常见论文结构，不代表当前年度官方投稿格式。正式投稿前应导入或核对会议官网模板。"
            style={{ borderRadius: 8 }}
          />
          <Select value={newTemplate} onChange={setNewTemplate} style={{ width: '100%' }}
            options={templates.map(t => ({
              value: t.key, label: `${t.name} 结构 (${t.section_count} 章节)`,
            }))}
          />
          <Space.Compact style={{ width: '100%' }}>
            <Input placeholder="目标会议/期刊，如 CVPR" value={targetVenue} onChange={e => setTargetVenue(e.target.value)} />
            <Input placeholder="年份，如 2026" value={targetYear} onChange={e => setTargetYear(e.target.value)} style={{ width: 120 }} />
          </Space.Compact>
          <Select
            allowClear
            showSearch
            placeholder="绑定研究方向（可选）"
            value={selectedResearchProjectId}
            onChange={setSelectedResearchProjectId}
            style={{ width: '100%' }}
            optionFilterProp="label"
            options={researchProjects.map(project => ({
              value: project.id,
              label: project.name,
            }))}
          />
          <Select
            mode="multiple"
            allowClear
            placeholder="绑定论文分类（可多选，作为写作证据库）"
            value={selectedCollectionIds}
            onChange={setSelectedCollectionIds}
            style={{ width: '100%' }}
            options={flattenCollections(collections)}
          />
        </Space>
      </Modal>
    </div>
  );
};

export default WritingProjectPanel;
