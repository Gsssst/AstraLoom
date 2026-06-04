import React, { useState, useEffect } from 'react';
import { Card, Button, List, Tag, Progress, Space, Modal, Input, Select, Typography, Popconfirm } from 'antd';
import { PlusOutlined, DeleteOutlined, FolderOutlined } from '@ant-design/icons';
import api from '../../services/api';

const { Text } = Typography;

interface Project {
  id: string;
  title: string;
  description: string;
  template_type: string;
  status: string;
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

interface WritingProjectPanelProps {
  onSelectProject: (project: Project) => void;
  selectedProjectId?: string;
  refreshSignal?: number;
}

const WritingProjectPanel: React.FC<WritingProjectPanelProps> = ({ onSelectProject, selectedProjectId, refreshSignal = 0 }) => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [newTemplate, setNewTemplate] = useState('blank');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadProjects();
    loadTemplates();
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

  const handleCreate = async () => {
    if (!newTitle.trim()) return;
    setLoading(true);
    try {
      await api.post('/writing/projects', {
        title: newTitle, description: newDesc, template_type: newTemplate,
      });
      setShowCreate(false);
      setNewTitle(''); setNewDesc(''); setNewTemplate('blank');
      loadProjects();
    } catch { /* ignore */ }
    finally { setLoading(false); }
  };

  const handleDelete = async (id: string) => {
    try {
      await api.delete(`/writing/projects/${id}`);
      loadProjects();
    } catch { /* ignore */ }
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
        renderItem={(project) => (
          <Card
            size="small"
            hoverable
            style={{
              marginBottom: 8, borderRadius: 8,
              border: project.id === selectedProjectId ? '2px solid #667eea' : '1px solid #f0f0f0',
            }}
            onClick={() => onSelectProject(project)}
            extra={
              <Popconfirm title="确定删除？" onConfirm={() => handleDelete(project.id)}>
                <Button size="small" type="text" danger icon={<DeleteOutlined />} />
              </Popconfirm>
            }
          >
            <Text strong ellipsis style={{ fontSize: 13 }}>{project.title}</Text>
            <div style={{ marginTop: 4 }}>
              <Space size="small" wrap>
                <Tag>{project.template_type.toUpperCase()}</Tag>
                <Tag color={project.status === 'complete' ? 'green' : 'blue'}>{project.status}</Tag>
                <Text type="secondary" style={{ fontSize: 11 }}>
                  {project.progress.total_words} 字
                </Text>
              </Space>
            </div>
            <Progress percent={project.progress.percentage} size="small" style={{ marginTop: 4 }}
              format={() => `${project.progress.completed}/${project.progress.total}`} />
          </Card>
        )}
      />

      <Modal title="新建写作项目" open={showCreate} onOk={handleCreate} onCancel={() => setShowCreate(false)}
        confirmLoading={loading}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Input placeholder="项目标题" value={newTitle} onChange={e => setNewTitle(e.target.value)} />
          <Input placeholder="项目描述（可选）" value={newDesc} onChange={e => setNewDesc(e.target.value)} />
          <Select value={newTemplate} onChange={setNewTemplate} style={{ width: '100%' }}
            options={templates.map(t => ({
              value: t.key, label: `${t.name} (${t.section_count} 章节)`,
            }))}
          />
        </Space>
      </Modal>
    </div>
  );
};

export default WritingProjectPanel;
