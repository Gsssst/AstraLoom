import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Button, Card, Col, Empty, Form, Input, List, Modal, Row, Select, Space, Statistic, Tag, Typography, message,
} from 'antd';
import {
  ArrowLeftOutlined, BookOutlined, DeleteOutlined, EditOutlined, ExperimentOutlined,
  PlusOutlined, TeamOutlined, UserOutlined,
} from '@ant-design/icons';
import api from '../services/api';

const { Title, Text, Paragraph } = Typography;

const resourceIcon: Record<string, React.ReactNode> = {
  papers: <BookOutlined />,
  research_projects: <ExperimentOutlined />,
  writing_projects: <EditOutlined />,
};

const resourceLabel: Record<string, string> = {
  papers: '论文',
  research_projects: '研究方向',
  writing_projects: '写作草稿',
};

const WorkspaceDetailPage: React.FC = () => {
  const { spaceId } = useParams();
  const navigate = useNavigate();
  const [space, setSpace] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [memberModalOpen, setMemberModalOpen] = useState(false);
  const [memberSaving, setMemberSaving] = useState(false);
  const [memberForm] = Form.useForm();

  const fetchSpace = async () => {
    if (!spaceId) return;
    setLoading(true);
    try {
      const response = await api.get(`/workspaces/${spaceId}`);
      setSpace(response.data);
    } catch {
      message.error('项目空间加载失败');
      navigate('/workspaces');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchSpace(); }, [spaceId]);

  const handleAddMember = async () => {
    const values = await memberForm.validateFields();
    setMemberSaving(true);
    try {
      const response = await api.post(`/workspaces/${spaceId}/members`, values);
      setSpace(response.data);
      setMemberModalOpen(false);
      memberForm.resetFields();
      message.success('成员已更新');
    } catch (error: any) {
      message.error(error.response?.data?.detail || '添加成员失败');
    } finally {
      setMemberSaving(false);
    }
  };

  const handleRemoveMember = async (userId: string) => {
    try {
      const response = await api.delete(`/workspaces/${spaceId}/members/${userId}`);
      setSpace(response.data);
      message.success('成员已移除');
    } catch (error: any) {
      message.error(error.response?.data?.detail || '移除成员失败');
    }
  };

  const renderResourceList = (type: string, items: any[]) => (
    <Card title={<Space>{resourceIcon[type]}{resourceLabel[type]}</Space>} style={{ borderRadius: 14, height: '100%' }}>
      {items?.length ? (
        <List
          dataSource={items}
          renderItem={(item) => (
            <List.Item style={{ cursor: 'pointer' }} onClick={() => navigate(item.path)}>
              <List.Item.Meta
                title={<Text strong ellipsis>{item.title}</Text>}
                description={<Text type="secondary" ellipsis>{item.subtitle}</Text>}
              />
            </List.Item>
          )}
        />
      ) : (
        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无资源" />
      )}
    </Card>
  );

  const summary = space?.summary || {};
  const resources = summary.linked_resources?.papers?.length || summary.linked_resources?.research_projects?.length || summary.linked_resources?.writing_projects?.length
    ? summary.linked_resources
    : summary.recent_resources || {};

  return (
    <div style={{ maxWidth: 1280, margin: '0 auto' }}>
      <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/workspaces')} style={{ marginBottom: 12, borderRadius: 8 }}>
        返回项目空间
      </Button>
      <Card loading={loading} style={{ borderRadius: 18, marginBottom: 18 }}>
        {space && (
          <Row justify="space-between" align="top" gutter={[16, 16]}>
            <Col flex="auto">
              <Space wrap>
                <Tag color={space.role === 'owner' ? 'purple' : 'blue'}>{space.role}</Tag>
                <Tag icon={<TeamOutlined />}>{space.member_count} 人协作</Tag>
              </Space>
              <Title level={2} style={{ margin: '10px 0 4px' }}>{space.name}</Title>
              <Paragraph type="secondary" style={{ maxWidth: 720 }}>{space.description || '暂无空间描述。建议补充目标、当前问题和下一步计划。'}</Paragraph>
            </Col>
            <Col>
              <Space>
                <Button icon={<BookOutlined />} onClick={() => navigate('/papers')} style={{ borderRadius: 8 }}>论文库</Button>
                <Button icon={<ExperimentOutlined />} onClick={() => navigate('/research')} style={{ borderRadius: 8 }}>研究方向</Button>
                <Button icon={<EditOutlined />} onClick={() => navigate('/writing')} style={{ borderRadius: 8 }}>写作</Button>
              </Space>
            </Col>
          </Row>
        )}
      </Card>

      {space && (
        <>
          <Row gutter={[16, 16]} style={{ marginBottom: 18 }}>
            <Col xs={24} md={8}><Card style={{ borderRadius: 14 }}><Statistic title="论文线索" value={(resources.papers || []).length} prefix={<BookOutlined />} /></Card></Col>
            <Col xs={24} md={8}><Card style={{ borderRadius: 14 }}><Statistic title="研究方向" value={(resources.research_projects || []).length} prefix={<ExperimentOutlined />} /></Card></Col>
            <Col xs={24} md={8}><Card style={{ borderRadius: 14 }}><Statistic title="写作草稿" value={(resources.writing_projects || []).length} prefix={<EditOutlined />} /></Card></Col>
          </Row>

          <Row gutter={[16, 16]} style={{ marginBottom: 18 }}>
            <Col xs={24} lg={8}>{renderResourceList('papers', resources.papers || [])}</Col>
            <Col xs={24} lg={8}>{renderResourceList('research_projects', resources.research_projects || [])}</Col>
            <Col xs={24} lg={8}>{renderResourceList('writing_projects', resources.writing_projects || [])}</Col>
          </Row>

          <Row gutter={[16, 16]}>
            <Col xs={24} lg={14}>
              <Card title="下一步建议" style={{ borderRadius: 14 }}>
                <List
                  dataSource={space.next_actions || []}
                  renderItem={(item: any) => (
                    <List.Item actions={[<Button size="small" onClick={() => navigate(item.path)} style={{ borderRadius: 8 }}>进入</Button>]}>
                      <List.Item.Meta title={item.label} description="根据当前空间资源覆盖情况自动推荐" />
                    </List.Item>
                  )}
                />
              </Card>
            </Col>
            <Col xs={24} lg={10}>
              <Card
                title="成员"
                style={{ borderRadius: 14 }}
                extra={space.role === 'owner' && <Button size="small" icon={<PlusOutlined />} onClick={() => setMemberModalOpen(true)}>添加</Button>}
              >
                <List
                  dataSource={space.members || []}
                  renderItem={(member: any) => (
                    <List.Item actions={space.role === 'owner' && member.role !== 'owner' ? [
                      <Button danger size="small" icon={<DeleteOutlined />} onClick={() => handleRemoveMember(member.user_id)} />,
                    ] : []}>
                      <List.Item.Meta
                        avatar={<UserOutlined />}
                        title={<Space><Text strong>{member.display_name || member.username}</Text><Tag>{member.role}</Tag></Space>}
                        description={member.email}
                      />
                    </List.Item>
                  )}
                />
              </Card>
            </Col>
          </Row>
        </>
      )}

      <Modal title="添加空间成员" open={memberModalOpen} onOk={handleAddMember} confirmLoading={memberSaving} onCancel={() => setMemberModalOpen(false)} okText="添加">
        <Form form={memberForm} layout="vertical" initialValues={{ role: 'viewer' }}>
          <Form.Item name="account" label="用户名或邮箱" rules={[{ required: true, message: '请输入用户名或邮箱' }]}>
            <Input placeholder="例如 gst 或 researcher@example.com" />
          </Form.Item>
          <Form.Item name="role" label="角色">
            <Select options={[{ value: 'viewer', label: 'viewer：只读' }, { value: 'editor', label: 'editor：编辑者' }]} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default WorkspaceDetailPage;
