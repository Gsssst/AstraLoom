import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Button, Card, Col, Empty, Form, Input, List, Modal, Row, Select, Space, Statistic, Tag, Timeline, Typography, message,
} from 'antd';
import {
  ArrowLeftOutlined, BookOutlined, DeleteOutlined, EditOutlined, ExperimentOutlined,
  LinkOutlined, PlusOutlined, TeamOutlined, UserOutlined,
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

const activityLabel: Record<string, string> = {
  space_created: '创建了项目空间',
  space_updated: '更新了项目空间',
  space_deleted: '删除了项目空间',
  member_added: '添加了成员',
  member_updated: '更新了成员角色',
  member_removed: '移除了成员',
  resource_linked: '绑定了资源',
  resource_unlinked: '移除了资源',
};

const WorkspaceDetailPage: React.FC = () => {
  const { spaceId } = useParams();
  const navigate = useNavigate();
  const [space, setSpace] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [memberModalOpen, setMemberModalOpen] = useState(false);
  const [memberSaving, setMemberSaving] = useState(false);
  const [memberForm] = Form.useForm();
  const [resourceForm] = Form.useForm();
  const [resourceSaving, setResourceSaving] = useState(false);
  const [candidateType, setCandidateType] = useState('papers');
  const [candidateQuery, setCandidateQuery] = useState('');
  const [candidates, setCandidates] = useState<any[]>([]);
  const [candidateLoading, setCandidateLoading] = useState(false);
  const [manualMode, setManualMode] = useState(false);

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

  const fetchCandidates = async (type = candidateType, q = candidateQuery) => {
    if (!spaceId || !canEditResources) return;
    setCandidateLoading(true);
    try {
      const response = await api.get(`/workspaces/${spaceId}/resource-candidates`, {
        params: { resource_type: type, q: q || undefined, limit: 12 },
      });
      setCandidates(response.data.items || []);
    } catch (error: any) {
      message.error(error.response?.data?.detail || '候选资源加载失败');
    } finally {
      setCandidateLoading(false);
    }
  };

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

  const canEditResources = space?.role === 'owner' || space?.role === 'editor';

  useEffect(() => {
    if (canEditResources) fetchCandidates(candidateType, candidateQuery);
  }, [canEditResources, candidateType, spaceId]);

  const handleLinkResource = async () => {
    const values = await resourceForm.validateFields();
    setResourceSaving(true);
    try {
      const response = await api.post(`/workspaces/${spaceId}/resources`, values);
      setSpace(response.data);
      resourceForm.resetFields();
      message.success('资源已绑定到空间');
    } catch (error: any) {
      message.error(error.response?.data?.detail || '绑定资源失败');
    } finally {
      setResourceSaving(false);
    }
  };

  const handleBindCandidate = async (candidate: any) => {
    setResourceSaving(true);
    try {
      const response = await api.post(`/workspaces/${spaceId}/resources`, {
        resource_type: candidate.type,
        resource_id: candidate.id,
      });
      setSpace(response.data);
      await fetchCandidates(candidateType, candidateQuery);
      message.success('资源已绑定到空间');
    } catch (error: any) {
      message.error(error.response?.data?.detail || '绑定资源失败');
    } finally {
      setResourceSaving(false);
    }
  };

  const handleUnlinkResource = async (resourceType: string, resourceId: string) => {
    try {
      const response = await api.delete(`/workspaces/${spaceId}/resources/${resourceType}/${resourceId}`);
      setSpace(response.data);
      message.success('资源已从空间移除');
    } catch (error: any) {
      message.error(error.response?.data?.detail || '移除资源失败');
    }
  };

  const renderResourceList = (type: string, items: any[]) => (
    <Card title={<Space>{resourceIcon[type]}{resourceLabel[type]}</Space>} style={{ borderRadius: 14, height: '100%' }}>
      {items?.length ? (
        <List
          dataSource={items}
          renderItem={(item) => (
            <List.Item
              style={{ cursor: 'pointer' }}
              onClick={() => navigate(item.path)}
              actions={canEditResources && !item.legacy ? [
                <Button
                  key="unlink"
                  size="small"
                  danger
                  icon={<DeleteOutlined />}
                  onClick={(event) => {
                    event.stopPropagation();
                    handleUnlinkResource(type, item.id);
                  }}
                />,
              ] : []}
            >
              <List.Item.Meta
                title={<Text strong ellipsis>{item.title}</Text>}
                description={(
                  <Space direction="vertical" size={2}>
                    <Text type="secondary" ellipsis>{item.subtitle}</Text>
                    {item.legacy && <Tag color="gold">旧链接</Tag>}
                  </Space>
                )}
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

          {canEditResources && (
            <Card title={<Space><LinkOutlined />绑定空间资源</Space>} style={{ borderRadius: 14, marginBottom: 18 }}>
              <Space direction="vertical" style={{ width: '100%' }} size={12}>
                <Space wrap>
                  <Select
                    value={candidateType}
                    style={{ width: 160 }}
                    onChange={(value) => {
                      setCandidateType(value);
                      setCandidates([]);
                    }}
                    options={[
                      { value: 'papers', label: '论文' },
                      { value: 'research_projects', label: '研究方向' },
                      { value: 'writing_projects', label: '写作草稿' },
                    ]}
                  />
                  <Input.Search
                    allowClear
                    placeholder={`搜索${resourceLabel[candidateType] || '资源'}标题或描述`}
                    value={candidateQuery}
                    onChange={event => setCandidateQuery(event.target.value)}
                    onSearch={value => fetchCandidates(candidateType, value)}
                    style={{ width: 360 }}
                  />
                  <Button onClick={() => fetchCandidates(candidateType, candidateQuery)} loading={candidateLoading}>
                    刷新候选
                  </Button>
                  <Button type="link" onClick={() => setManualMode(value => !value)}>
                    {manualMode ? '收起手动 ID' : '手动输入 ID'}
                  </Button>
                </Space>

                <List
                  loading={candidateLoading}
                  dataSource={candidates}
                  locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无候选资源，换个关键词试试" /> }}
                  renderItem={(item: any) => (
                    <List.Item
                      actions={[
                        item.linked ? (
                          <Tag color="green">已绑定</Tag>
                        ) : (
                          <Button
                            type="primary"
                            size="small"
                            icon={<LinkOutlined />}
                            loading={resourceSaving}
                            onClick={() => handleBindCandidate(item)}
                          >
                            绑定
                          </Button>
                        ),
                      ]}
                    >
                      <List.Item.Meta
                        avatar={resourceIcon[item.type]}
                        title={<Text strong>{item.title}</Text>}
                        description={<Text type="secondary">{item.subtitle}</Text>}
                      />
                    </List.Item>
                  )}
                />

                {manualMode && (
                  <Form form={resourceForm} layout="inline" initialValues={{ resource_type: candidateType }} style={{ gap: 8 }}>
                    <Form.Item name="resource_type" rules={[{ required: true }]}>
                      <Select
                        style={{ width: 160 }}
                        options={[
                          { value: 'papers', label: '论文' },
                          { value: 'research_projects', label: '研究方向' },
                          { value: 'writing_projects', label: '写作草稿' },
                        ]}
                      />
                    </Form.Item>
                    <Form.Item name="resource_id" rules={[{ required: true, message: '请输入资源 ID' }]} style={{ flex: 1, minWidth: 280 }}>
                      <Input placeholder="粘贴论文、研究方向或写作项目 ID" />
                    </Form.Item>
                    <Form.Item>
                      <Button icon={<LinkOutlined />} loading={resourceSaving} onClick={handleLinkResource}>
                        用 ID 绑定
                      </Button>
                    </Form.Item>
                  </Form>
                )}
              </Space>
            </Card>
          )}

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

          <Card title="最近活动" style={{ borderRadius: 14, marginTop: 18 }}>
            {space.activities?.length ? (
              <Timeline
                items={space.activities.map((item: any) => ({
                  children: (
                    <Space direction="vertical" size={2}>
                      <Text>
                        <Text strong>{item.actor_name}</Text> {activityLabel[item.action] || item.action}
                        {item.resource_type && <Tag style={{ marginLeft: 8 }}>{resourceLabel[item.resource_type] || item.resource_type}</Tag>}
                      </Text>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {item.created_at ? new Date(item.created_at).toLocaleString() : ''}
                        {item.metadata_json?.title ? ` · ${item.metadata_json.title}` : ''}
                      </Text>
                    </Space>
                  ),
                }))}
              />
            ) : (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无活动记录" />
            )}
          </Card>
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
