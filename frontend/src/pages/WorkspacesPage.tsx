import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Button, Card, Col, Empty, Form, Input, List, Modal, Row, Space, Tag, Typography, message,
} from 'antd';
import {
  AppstoreOutlined, PlusOutlined, TeamOutlined, BookOutlined, ExperimentOutlined, EditOutlined,
} from '@ant-design/icons';
import api from '../services/api';

const { Title, Text, Paragraph } = Typography;

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
    <div style={{ maxWidth: 1180, margin: '0 auto' }}>
      <Card
        style={{
          borderRadius: 18,
          marginBottom: 20,
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: '#fff',
          overflow: 'hidden',
        }}
        styles={{ body: { padding: 28 } }}
      >
        <Row align="middle" justify="space-between" gutter={[16, 16]}>
          <Col>
            <Space size={14}>
              <div style={{
                width: 56, height: 56, borderRadius: 16, background: 'rgba(255,255,255,0.18)',
                display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 26,
              }}>
                <AppstoreOutlined />
              </div>
              <div>
                <Title level={2} style={{ color: '#fff', margin: 0 }}>项目空间</Title>
                <Text style={{ color: 'rgba(255,255,255,0.78)' }}>把论文、研究方向、写作草稿和团队成员放进同一个科研工作台</Text>
              </div>
            </Space>
          </Col>
          <Col>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)} style={{ borderRadius: 10, background: '#fff', color: '#667eea' }}>
              新建空间
            </Button>
          </Col>
        </Row>
      </Card>

      <Card style={{ borderRadius: 16 }} loading={loading}>
        {spaces.length ? (
          <List
            grid={{ gutter: 16, xs: 1, md: 2, xl: 3 }}
            dataSource={spaces}
            renderItem={(space) => (
              <List.Item>
                <Card hoverable onClick={() => navigate(`/workspaces/${space.id}`)} style={{ borderRadius: 14, minHeight: 190 }}>
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Space wrap>
                      <Tag color={space.role === 'owner' ? 'purple' : 'blue'}>{space.role}</Tag>
                      <Tag icon={<TeamOutlined />}>{space.member_count || 1} 人</Tag>
                    </Space>
                    <Title level={4} style={{ margin: 0 }}>{space.name}</Title>
                    <Paragraph type="secondary" ellipsis={{ rows: 2 }} style={{ minHeight: 44 }}>
                      {space.description || '暂无描述，建议补充研究目标、当前阶段和协作范围。'}
                    </Paragraph>
                    <Space wrap>
                      <Tag icon={<BookOutlined />}>论文库</Tag>
                      <Tag icon={<ExperimentOutlined />}>研究方向</Tag>
                      <Tag icon={<EditOutlined />}>写作</Tag>
                    </Space>
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
    </div>
  );
};

export default WorkspacesPage;
