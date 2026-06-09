import React, { useEffect, useMemo, useState } from 'react';
import {
  Button, Card, Col, Drawer, Empty, Form, Input, Row, Select, Space, Spin, Tag, Typography, message,
} from 'antd';
import {
  BookOutlined, EditOutlined, PlusOutlined, ReloadOutlined, SearchOutlined, ToolOutlined,
} from '@ant-design/icons';
import api from '../services/api';
import PageShell from '../components/PageShell';
import { getApiErrorMessage } from '../services/apiError';

const { Text, Paragraph } = Typography;
const { TextArea } = Input;

type ToolKind = 'algorithm' | 'model' | 'dataset' | 'metric' | 'framework' | 'codebase' | 'protocol' | 'other';
type ToolMaturity = 'mature' | 'experimental' | 'concept' | 'unknown';

interface ToolboxPaper {
  id: string;
  title: string;
  year?: number | null;
  source: string;
  relation: string;
  evidence_note?: string | null;
}

interface ToolboxTool {
  id: string;
  name: string;
  kind: ToolKind;
  summary?: string | null;
  use_cases?: string | null;
  limitations?: string | null;
  tags: string[];
  maturity: ToolMaturity;
  papers: ToolboxPaper[];
  updated_at: string;
}

const kindOptions = [
  { value: 'algorithm', label: '算法' },
  { value: 'model', label: '模型' },
  { value: 'dataset', label: '数据集' },
  { value: 'metric', label: '评价指标' },
  { value: 'framework', label: '实验框架' },
  { value: 'codebase', label: '代码库' },
  { value: 'protocol', label: '实验协议' },
  { value: 'other', label: '其他' },
];

const maturityOptions = [
  { value: 'mature', label: '成熟' },
  { value: 'experimental', label: '实验性' },
  { value: 'concept', label: '概念' },
  { value: 'unknown', label: '未知' },
];

const kindLabel = (value: string) => kindOptions.find(item => item.value === value)?.label || value;
const maturityLabel = (value: string) => maturityOptions.find(item => item.value === value)?.label || value;

const ToolboxPage: React.FC = () => {
  const [tools, setTools] = useState<ToolboxTool[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [editingTool, setEditingTool] = useState<ToolboxTool | null>(null);
  const [query, setQuery] = useState('');
  const [kind, setKind] = useState<ToolKind | undefined>();
  const [maturity, setMaturity] = useState<ToolMaturity | undefined>();
  const [tag, setTag] = useState<string | undefined>();
  const [form] = Form.useForm();

  const tagOptions = useMemo(() => {
    const tags = Array.from(new Set(tools.flatMap(tool => tool.tags || []))).sort();
    return tags.map(value => ({ value, label: value }));
  }, [tools]);

  const fetchTools = async () => {
    setLoading(true);
    try {
      const response = await api.get('/toolbox/tools', {
        params: { q: query || undefined, kind, maturity, tag, limit: 80 },
      });
      setTools(response.data.items || []);
    } catch (error) {
      message.error(getApiErrorMessage(error, { fallback: '工具箱加载失败' }));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchTools(); }, [kind, maturity, tag]);

  const openCreate = () => {
    setEditingTool(null);
    form.resetFields();
    form.setFieldsValue({ kind: 'algorithm', maturity: 'unknown', tags: [] });
    setDrawerOpen(true);
  };

  const openEdit = (tool: ToolboxTool) => {
    setEditingTool(tool);
    form.setFieldsValue({
      name: tool.name,
      kind: tool.kind,
      summary: tool.summary,
      use_cases: tool.use_cases,
      limitations: tool.limitations,
      tags: tool.tags || [],
      maturity: tool.maturity,
    });
    setDrawerOpen(true);
  };

  const saveTool = async () => {
    const values = await form.validateFields();
    setSaving(true);
    try {
      const payload = {
        ...values,
        tags: Array.isArray(values.tags) ? values.tags : [],
      };
      if (editingTool) {
        await api.patch(`/toolbox/tools/${editingTool.id}`, payload);
        message.success('工具已更新');
      } else {
        await api.post('/toolbox/tools', payload);
        message.success('工具已加入工具箱');
      }
      setDrawerOpen(false);
      await fetchTools();
    } catch (error) {
      message.error(getApiErrorMessage(error, { fallback: '工具保存失败' }));
    } finally {
      setSaving(false);
    }
  };

  return (
    <PageShell
      title="工具箱"
      subtitle="把论文里的算法、模型、数据集、评价协议和代码工具沉淀成可复用的 idea 生成素材。"
      icon={<ToolOutlined />}
      maxWidth={1280}
    >
      <Card style={{ borderRadius: 16, marginBottom: 16 }}>
        <Row gutter={[10, 10]} align="middle">
          <Col xs={24} md={8}>
            <Input.Search
              allowClear
              placeholder="搜索工具、算法、数据集..."
              value={query}
              onChange={event => setQuery(event.target.value)}
              onSearch={fetchTools}
              prefix={<SearchOutlined />}
            />
          </Col>
          <Col xs={12} md={4}>
            <Select allowClear placeholder="类型" value={kind} onChange={setKind} options={kindOptions} style={{ width: '100%' }} />
          </Col>
          <Col xs={12} md={4}>
            <Select allowClear placeholder="成熟度" value={maturity} onChange={setMaturity} options={maturityOptions} style={{ width: '100%' }} />
          </Col>
          <Col xs={12} md={4}>
            <Select allowClear placeholder="标签" value={tag} onChange={setTag} options={tagOptions} style={{ width: '100%' }} />
          </Col>
          <Col xs={12} md={4}>
            <Button block icon={<ReloadOutlined />} onClick={fetchTools}>刷新</Button>
          </Col>
          <Col xs={24} md={4}>
            <Button block type="primary" icon={<PlusOutlined />} onClick={openCreate}>添加工具</Button>
          </Col>
        </Row>
      </Card>

      <Spin spinning={loading}>
        {tools.length === 0 ? (
          <Card style={{ borderRadius: 16 }}>
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="还没有工具条目">
              <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>添加第一个工具</Button>
            </Empty>
          </Card>
        ) : (
          <Row gutter={[14, 14]}>
            {tools.map(tool => (
              <Col xs={24} md={12} xl={8} key={tool.id}>
                <Card
                  hoverable
                  style={{ borderRadius: 16, height: '100%' }}
                  actions={[
                    <Button type="link" icon={<EditOutlined />} onClick={() => openEdit(tool)}>编辑</Button>,
                  ]}
                >
                  <Space direction="vertical" size={10} style={{ width: '100%' }}>
                    <Space size={8} wrap>
                      <Text strong style={{ fontSize: 16 }}>{tool.name}</Text>
                      <Tag color="blue">{kindLabel(tool.kind)}</Tag>
                      <Tag color={tool.maturity === 'mature' ? 'green' : tool.maturity === 'experimental' ? 'orange' : 'default'}>
                        {maturityLabel(tool.maturity)}
                      </Tag>
                    </Space>
                    <Paragraph type="secondary" ellipsis={{ rows: 2 }} style={{ marginBottom: 0 }}>
                      {tool.summary || '暂无简介'}
                    </Paragraph>
                    {tool.tags?.length ? (
                      <Space size={6} wrap>
                        {tool.tags.map(item => <Tag key={item}>{item}</Tag>)}
                      </Space>
                    ) : null}
                    <div>
                      <Text type="secondary" style={{ fontSize: 12 }}>适用场景</Text>
                      <Paragraph ellipsis={{ rows: 2 }} style={{ marginBottom: 0 }}>{tool.use_cases || '未填写'}</Paragraph>
                    </div>
                    <div>
                      <Text type="secondary" style={{ fontSize: 12 }}>局限性</Text>
                      <Paragraph ellipsis={{ rows: 2 }} style={{ marginBottom: 0 }}>{tool.limitations || '未填写'}</Paragraph>
                    </div>
                    <div>
                      <Text type="secondary" style={{ fontSize: 12 }}><BookOutlined /> 来源论文 {tool.papers?.length || 0}</Text>
                      {tool.papers?.slice(0, 2).map(paper => (
                        <div key={`${tool.id}-${paper.id}`} style={{ marginTop: 6 }}>
                          <Tag color="purple">{paper.relation}</Tag>
                          <Text style={{ fontSize: 12 }}>{paper.title}</Text>
                        </div>
                      ))}
                    </div>
                  </Space>
                </Card>
              </Col>
            ))}
          </Row>
        )}
      </Spin>

      <Drawer
        title={editingTool ? '编辑工具' : '添加工具'}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        width={520}
        extra={<Button type="primary" loading={saving} onClick={saveTool}>保存</Button>}
      >
        <Form layout="vertical" form={form}>
          <Form.Item name="name" label="工具名称" rules={[{ required: true, message: '请输入工具名称' }]}>
            <Input placeholder="例如 GraphRAG、LoRA、DINOv2、BLEU" />
          </Form.Item>
          <Row gutter={12}>
            <Col span={12}>
              <Form.Item name="kind" label="类型" rules={[{ required: true }]}>
                <Select options={kindOptions} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="maturity" label="成熟度" rules={[{ required: true }]}>
                <Select options={maturityOptions} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="summary" label="简介">
            <TextArea rows={3} placeholder="它解决什么问题，核心思想是什么" />
          </Form.Item>
          <Form.Item name="use_cases" label="适用场景">
            <TextArea rows={3} placeholder="什么时候适合用它" />
          </Form.Item>
          <Form.Item name="limitations" label="局限性">
            <TextArea rows={3} placeholder="什么时候不适合用它，成本或风险是什么" />
          </Form.Item>
          <Form.Item name="tags" label="标签">
            <Select mode="tags" tokenSeparators={[',', '，']} placeholder="例如 RAG、多模态、视频理解" />
          </Form.Item>
        </Form>
      </Drawer>
    </PageShell>
  );
};

export default ToolboxPage;
