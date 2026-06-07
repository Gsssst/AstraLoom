import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Button, Card, Col, Empty, Form, Input, List, Modal, Progress, Row, Space, Tag, Typography, message,
} from 'antd';
import {
  AppstoreOutlined, PlusOutlined, TeamOutlined, BookOutlined, ExperimentOutlined, EditOutlined,
} from '@ant-design/icons';
import api from '../services/api';
import PageShell from '../components/PageShell';

const { Title, Text, Paragraph } = Typography;
const launchpadResourceMeta = [
  { key: 'linked_papers', label: '论文', icon: <BookOutlined /> },
  { key: 'linked_research_projects', label: '方向', icon: <ExperimentOutlined /> },
  { key: 'linked_writing_projects', label: '写作', icon: <EditOutlined /> },
];

const WorkspacesPage: React.FC = () => {
  const navigate = useNavigate();
  const [spaces, setSpaces] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form] = Form.useForm();

  const fetchSpaces = async () => {
    setLoading(true);
    try {
      const response = await api.get('/workspaces');
      setSpaces(response.data.workspaces || []);
    } catch {
      message.error('项目空间加载失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchSpaces(); }, []);

  const handleCreate = async () => {
    const values = await form.validateFields();
    setCreating(true);
    try {
      const response = await api.post('/workspaces', values);
      message.success('项目空间已创建');
      setModalOpen(false);
      form.resetFields();
      navigate(`/workspaces/${response.data.id}`);
    } catch {
      message.error('创建项目空间失败');
    } finally {
      setCreating(false);
    }
  };

  return (
    <PageShell
      title="项目空间"
      subtitle="把论文、研究方向、写作草稿和团队成员放进同一个科研工作台。"
      icon={<AppstoreOutlined />}
      maxWidth={1180}
      actions={(
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)} style={{ borderRadius: 10 }}>
          新建空间
        </Button>
      )}
    >
      <Card style={{ borderRadius: 16 }} loading={loading}>
        {spaces.length ? (
          <List
            grid={{ gutter: 16, xs: 1, md: 2, xl: 3 }}
            dataSource={spaces}
            renderItem={(space) => (
              <List.Item>
                <Card hoverable onClick={() => navigate(`/workspaces/${space.id}`)} style={{ borderRadius: 14, minHeight: 246 }}>
                  <Space direction="vertical" style={{ width: '100%' }} size={10}>
                    <Space wrap style={{ width: '100%', justifyContent: 'space-between' }}>
                      <Space wrap>
                        <Tag color={space.role === 'owner' ? 'purple' : 'blue'}>{space.role}</Tag>
                        <Tag icon={<TeamOutlined />}>{space.member_count || 1} 人</Tag>
                      </Space>
                      <Tag color="geekblue">{space.dashboard?.stage_label || '科研看板'}</Tag>
                    </Space>
                    <Title level={4} style={{ margin: 0 }} ellipsis={{ rows: 1 }}>{space.name}</Title>
                    <Paragraph type="secondary" ellipsis={{ rows: 2 }} style={{ minHeight: 44, marginBottom: 2 }}>
                      {space.description || '暂无描述，建议补充研究目标、当前阶段和协作范围。'}
                    </Paragraph>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                      <Progress
                        percent={space.dashboard?.progress_score || 0}
                        size="small"
                        strokeColor={{ '0%': '#667eea', '100%': '#764ba2' }}
                        style={{ flex: 1 }}
                      />
                      <Text type="secondary" style={{ fontSize: 12 }}>推进度</Text>
                    </div>
                    <Row gutter={[8, 8]}>
                      {launchpadResourceMeta.map(item => (
                        <Col span={8} key={item.key}>
                          <div style={{ border: '1px solid #f0edff', borderRadius: 10, padding: '8px 6px', textAlign: 'center', background: '#fbfaff' }}>
                            <Space size={4} style={{ color: '#6f5bd6' }}>
                              {item.icon}
                              <Text strong>{space.summary?.counts?.[item.key] || 0}</Text>
                            </Space>
                            <Text type="secondary" style={{ display: 'block', fontSize: 12 }}>{item.label}</Text>
                          </div>
                        </Col>
                      ))}
                    </Row>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      打开后可绑定论文、方向和写作项目，并查看下一步建议。
                    </Text>
                  </Space>
                </Card>
              </List.Item>
            )}
          />
        ) : (
          <Empty description="还没有项目空间。创建一个空间，把当前研究工作串起来。" />
        )}
      </Card>

      <Modal title="新建项目空间" open={modalOpen} onOk={handleCreate} confirmLoading={creating} onCancel={() => setModalOpen(false)} okText="创建">
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="空间名称" rules={[{ required: true, message: '请输入空间名称' }]}>
            <Input placeholder="例如：Video Grounding 综述与实验" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={3} placeholder="这个空间要解决什么研究问题？当前有哪些论文、Idea 或写作任务？" />
          </Form.Item>
        </Form>
      </Modal>
    </PageShell>
  );
};

export default WorkspacesPage;
