import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Alert, Button, Card, Col, Empty, Form, Input, List, Modal, Progress, Row, Select, Space, Statistic, Tag, Timeline, Typography, message,
} from 'antd';
import {
  AppstoreOutlined, ArrowLeftOutlined, BookOutlined, DeleteOutlined, EditOutlined, ExperimentOutlined,
  LinkOutlined, PlusOutlined, RobotOutlined, RocketOutlined, SendOutlined, TeamOutlined, UserOutlined,
} from '@ant-design/icons';
import api from '../services/api';
import WorkflowStepGuide from '../components/WorkflowStepGuide';
import PageShell from '../components/PageShell';
import { getApiErrorDetails, type ApiErrorDetails } from '../services/apiError';

const { Title, Text, Paragraph } = Typography;

interface WorkspaceAssistantMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  references?: any[];
  created_at?: string;
}

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

const dashboardCardIcon: Record<string, React.ReactNode> = {
  papers: <BookOutlined />,
  research_projects: <ExperimentOutlined />,
  writing_projects: <EditOutlined />,
  activity: <TeamOutlined />,
};

const dashboardCardColor: Record<string, string> = {
  papers: '#4f7cff',
  research_projects: '#8b5cf6',
  writing_projects: '#16a34a',
  activity: '#f59e0b',
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
  const [assistantLoading, setAssistantLoading] = useState(false);
  const [assistantSending, setAssistantSending] = useState(false);
  const [assistantInput, setAssistantInput] = useState('');
  const [assistantMessages, setAssistantMessages] = useState<WorkspaceAssistantMessage[]>([]);
  const [assistantPrompts, setAssistantPrompts] = useState<string[]>([]);
  const [assistantReferences, setAssistantReferences] = useState<any[]>([]);
  const [workspaceActionError, setWorkspaceActionError] = useState<{ title: string; detail: ApiErrorDetails } | null>(null);

  const fetchSpace = async () => {
    if (!spaceId) return;
    setLoading(true);
    try {
      const response = await api.get(`/workspaces/${spaceId}`);
      setSpace(response.data);
      setWorkspaceActionError(null);
    } catch (error: any) {
      const detail = getApiErrorDetails(error, { fallback: '项目空间加载失败' });
      setWorkspaceActionError({ title: '项目空间加载失败', detail });
      message.warning(detail.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchSpace(); }, [spaceId]);

  const fetchAssistantState = async () => {
    if (!spaceId) return;
    setAssistantLoading(true);
    try {
      const response = await api.get(`/workspaces/${spaceId}/assistant`);
      setAssistantMessages(response.data.messages || []);
      setAssistantPrompts(response.data.quick_prompts || []);
      setAssistantReferences(response.data.references || []);
      setWorkspaceActionError(null);
    } catch (error: any) {
      const detail = getApiErrorDetails(error, { fallback: '项目空间 AI 助手加载失败' });
      setWorkspaceActionError({ title: 'AI 助手加载失败', detail });
      message.warning(detail.message);
    } finally {
      setAssistantLoading(false);
    }
  };

  useEffect(() => { fetchAssistantState(); }, [spaceId]);

  const fetchCandidates = async (type = candidateType, q = candidateQuery) => {
    if (!spaceId || !canEditResources) return;
    setCandidateLoading(true);
    try {
      const response = await api.get(`/workspaces/${spaceId}/resource-candidates`, {
        params: { resource_type: type, q: q || undefined, limit: 12 },
      });
      setCandidates(response.data.items || []);
      setWorkspaceActionError(null);
    } catch (error: any) {
      const detail = getApiErrorDetails(error, { fallback: '候选资源加载失败' });
      setWorkspaceActionError({ title: '候选资源加载失败', detail });
      message.warning(detail.message);
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
      setWorkspaceActionError(null);
      message.success('成员已更新');
    } catch (error: any) {
      const detail = getApiErrorDetails(error, { fallback: '添加成员失败' });
      setWorkspaceActionError({ title: '添加成员失败', detail });
      message.warning(detail.message);
    } finally {
      setMemberSaving(false);
    }
  };

  const handleRemoveMember = async (userId: string) => {
    try {
      const response = await api.delete(`/workspaces/${spaceId}/members/${userId}`);
      setSpace(response.data);
      setWorkspaceActionError(null);
      message.success('成员已移除');
    } catch (error: any) {
      const detail = getApiErrorDetails(error, { fallback: '移除成员失败' });
      setWorkspaceActionError({ title: '移除成员失败', detail });
      message.warning(detail.message);
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
      setWorkspaceActionError(null);
      message.success('资源已绑定到空间');
    } catch (error: any) {
      const detail = getApiErrorDetails(error, { fallback: '绑定资源失败' });
      setWorkspaceActionError({ title: '绑定资源失败', detail });
      message.warning(detail.message);
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
      setWorkspaceActionError(null);
      await fetchCandidates(candidateType, candidateQuery);
      message.success('资源已绑定到空间');
    } catch (error: any) {
      const detail = getApiErrorDetails(error, { fallback: '绑定资源失败' });
      setWorkspaceActionError({ title: '绑定资源失败', detail });
      message.warning(detail.message);
    } finally {
      setResourceSaving(false);
    }
  };

  const handleUnlinkResource = async (resourceType: string, resourceId: string) => {
    try {
      const response = await api.delete(`/workspaces/${spaceId}/resources/${resourceType}/${resourceId}`);
      setSpace(response.data);
      setWorkspaceActionError(null);
      message.success('资源已从空间移除');
    } catch (error: any) {
      const detail = getApiErrorDetails(error, { fallback: '移除资源失败' });
      setWorkspaceActionError({ title: '移除资源失败', detail });
      message.warning(detail.message);
    }
  };

  const openResourceBinder = (type: string) => {
    if (!canEditResources) return;
    setCandidateType(type);
    setManualMode(false);
    setTimeout(() => {
      document.getElementById('workspace-resource-binder')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 0);
  };

  const sendAssistantMessage = async (contentOverride?: string) => {
    const content = (contentOverride ?? assistantInput).trim();
    if (!spaceId || !content) return;
    setAssistantSending(true);
    if (!contentOverride) setAssistantInput('');
    try {
      const response = await api.post(`/workspaces/${spaceId}/assistant/send`, { content });
      setAssistantMessages(prev => [...prev, response.data.message, response.data.reply]);
      setAssistantReferences(response.data.references || []);
      setWorkspaceActionError(null);
    } catch (error: any) {
      if (!contentOverride) setAssistantInput(content);
      const detail = getApiErrorDetails(error, { fallback: '项目空间 AI 助手发送失败' });
      setWorkspaceActionError({ title: 'AI 助手发送失败', detail });
      message.warning(detail.message);
    } finally {
      setAssistantSending(false);
    }
  };

  const renderResourceList = (type: string, items: any[]) => (
    <Card title={<Space>{resourceIcon[type]}{resourceLabel[type]}</Space>} style={{ borderRadius: 14, height: '100%' }}>
      {items?.length ? (
        <List
          dataSource={items}
          renderItem={(item) => (
            <List.Item
              style={{ cursor: 'pointer', overflow: 'hidden', alignItems: 'flex-start' }}
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
                style={{ minWidth: 0, overflow: 'hidden' }}
                title={<Text strong ellipsis style={{ display: 'block', maxWidth: '100%' }}>{item.title}</Text>}
                description={(
                  <Space direction="vertical" size={2} style={{ width: '100%', minWidth: 0 }}>
                    <Text type="secondary" ellipsis style={{ display: 'block', maxWidth: '100%' }}>{item.subtitle}</Text>
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

  const renderAssistantPanel = () => (
    <Card
      title={<Space><RobotOutlined />项目空间 AI 助手</Space>}
      loading={assistantLoading}
      style={{ borderRadius: 14, marginBottom: 16 }}
    >
      <Space direction="vertical" size={12} style={{ width: '100%' }}>
        <Text type="secondary" style={{ fontSize: 13 }}>
          基于当前空间的论文、研究方向、写作草稿和活动记录回答。不会自动修改空间内容。
        </Text>

        <Space wrap size={6}>
          {assistantPrompts.map(prompt => (
            <Button
              key={prompt}
              size="small"
              onClick={() => sendAssistantMessage(prompt)}
              disabled={assistantSending}
              style={{ borderRadius: 8 }}
            >
              {prompt.length > 18 ? `${prompt.slice(0, 18)}...` : prompt}
            </Button>
          ))}
        </Space>

        <div style={{ maxHeight: 340, overflowY: 'auto', paddingRight: 4 }}>
          {assistantMessages.length ? (
            <Space direction="vertical" size={10} style={{ width: '100%' }}>
              {assistantMessages.map(item => (
                <div
                  key={item.id}
                  style={{
                    padding: '10px 12px',
                    borderRadius: item.role === 'user' ? '12px 12px 4px 12px' : '4px 12px 12px 12px',
                    background: item.role === 'user' ? '#f3f6ff' : '#f8fafc',
                    border: '1px solid #eef0f4',
                  }}
                >
                  <Space direction="vertical" size={6} style={{ width: '100%' }}>
                    <Text strong style={{ fontSize: 12 }}>{item.role === 'user' ? '你' : 'AI 助手'}</Text>
                    <Paragraph style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{item.content}</Paragraph>
                    {!!item.references?.length && (
                      <Space wrap size={4}>
                        {item.references.slice(0, 6).map((reference: any, index: number) => (
                          <Tag
                            key={`${reference.resource_type || 'ref'}-${reference.resource_id || index}`}
                            color="geekblue"
                            style={{ cursor: reference.path ? 'pointer' : 'default' }}
                            onClick={() => reference.path && navigate(reference.path)}
                          >
                            {reference.source_label || '空间引用'}：{reference.title || reference.resource_type}
                          </Tag>
                        ))}
                      </Space>
                    )}
                  </Space>
                </div>
              ))}
            </Space>
          ) : (
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="还没有空间对话，可以先点一个快捷问题" />
          )}
        </div>

        {!!assistantReferences.length && (
          <Space wrap size={4}>
            <Text type="secondary" style={{ fontSize: 12 }}>当前上下文：</Text>
            {assistantReferences.slice(0, 8).map((reference: any, index: number) => (
              <Tag
                key={`${reference.resource_type || 'ctx'}-${reference.resource_id || index}`}
                onClick={() => reference.path && navigate(reference.path)}
                style={{ cursor: reference.path ? 'pointer' : 'default' }}
              >
                {reference.title || reference.source_label}
              </Tag>
            ))}
          </Space>
        )}

        <Input.TextArea
          value={assistantInput}
          onChange={event => setAssistantInput(event.target.value)}
          placeholder="问这个项目空间：比如当前进展、证据缺口、下一步计划、写作提纲..."
          autoSize={{ minRows: 2, maxRows: 5 }}
          disabled={assistantSending}
          style={{ borderRadius: 10 }}
        />
        <Button
          type="primary"
          icon={<SendOutlined />}
          loading={assistantSending}
          disabled={!assistantInput.trim()}
          onClick={() => sendAssistantMessage()}
          style={{ borderRadius: 10, alignSelf: 'flex-end' }}
        >
          发送给空间助手
        </Button>
      </Space>
    </Card>
  );

  const summary = space?.summary || {};
  const dashboard = space?.dashboard || {};
  const resources = summary.linked_resources?.papers?.length || summary.linked_resources?.research_projects?.length || summary.linked_resources?.writing_projects?.length
    ? summary.linked_resources
    : summary.recent_resources || {};
  const statusCards = dashboard.status_cards || [];

  return (
    <PageShell
      title={space?.name || '项目空间详情'}
      subtitle={space?.description || '查看空间资源、成员、活动和下一步推进建议。'}
      icon={<AppstoreOutlined />}
      maxWidth={1280}
      actions={(
        <>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/workspaces')} style={{ borderRadius: 8 }}>
            返回项目空间
          </Button>
          <Button icon={<BookOutlined />} onClick={() => navigate('/papers')} style={{ borderRadius: 8 }}>论文库</Button>
          <Button icon={<ExperimentOutlined />} onClick={() => navigate('/research')} style={{ borderRadius: 8 }}>研究方向</Button>
          <Button icon={<EditOutlined />} onClick={() => navigate('/writing')} style={{ borderRadius: 8 }}>写作</Button>
        </>
      )}
    >
      {workspaceActionError ? (
        <Alert
          type={workspaceActionError.detail.severity === 'error' ? 'error' : 'warning'}
          showIcon
          closable
          onClose={() => setWorkspaceActionError(null)}
          style={{ borderRadius: 12, marginBottom: 16 }}
          message={`${workspaceActionError.title}：${workspaceActionError.detail.message}`}
          description={(
            <Space direction="vertical" size={6}>
              <Text>{workspaceActionError.detail.recovery}</Text>
              <Space size={6} wrap>
                <Tag color="orange">{workspaceActionError.detail.category}</Tag>
                <Tag color={workspaceActionError.detail.retryable ? 'blue' : 'default'}>
                  {workspaceActionError.detail.retryable ? '可重试' : '需先处理条件'}
                </Tag>
                {workspaceActionError.detail.status && <Tag>HTTP {workspaceActionError.detail.status}</Tag>}
              </Space>
            </Space>
          )}
        />
      ) : null}

      <Card loading={loading} style={{ borderRadius: 18, marginBottom: 18 }}>
        {space && (
          <Row justify="space-between" align="top" gutter={[16, 16]}>
            <Col flex="auto">
              <Space wrap>
                <Tag color={space.role === 'owner' ? 'purple' : 'blue'}>{space.role}</Tag>
                <Tag icon={<TeamOutlined />}>{space.member_count} 人协作</Tag>
                <Tag color="geekblue">{dashboard.stage_label || '科研看板'}</Tag>
              </Space>
              <Title level={2} style={{ margin: '10px 0 4px' }}>{space.name}</Title>
              <Paragraph type="secondary" style={{ maxWidth: 720 }}>{space.description || '暂无空间描述。建议补充目标、当前问题和下一步计划。'}</Paragraph>
            </Col>
            <Col>
              <Progress
                type="circle"
                percent={dashboard.progress_score || 0}
                size={82}
                strokeColor={{ '0%': '#667eea', '100%': '#764ba2' }}
              />
            </Col>
          </Row>
        )}
      </Card>

      {space && (
        <>
          <WorkflowStepGuide
            title="项目空间启动台"
            subtitle={canEditResources ? '把论文、研究方向和写作项目收进同一个空间，再从这里继续推进。' : '你当前是只读成员，可以从这里查看资源并进入对应模块。'}
            style={{ marginBottom: 18 }}
            steps={[
              {
                key: 'bind-papers',
                title: canEditResources ? '绑定核心论文' : '查看核心论文',
                description: canEditResources ? '先把相关论文加入空间，后续方向生成和写作都能共享上下文。' : '从已绑定论文进入阅读与问答，理解空间当前证据基础。',
                actionLabel: canEditResources ? '选择论文' : '查看论文资源',
                status: 'recommended',
                icon: <BookOutlined />,
                onClick: canEditResources ? () => openResourceBinder('papers') : undefined,
                path: canEditResources ? undefined : '/papers',
              },
              {
                key: 'research-projects',
                title: canEditResources ? '创建或绑定方向' : '查看研究方向',
                description: canEditResources ? '把分类论文沉淀成研究方向，让 idea 和实验计划挂到空间里。' : '查看空间内已有方向、idea 和验证状态。',
                actionLabel: canEditResources ? '去研究方向' : '进入研究方向',
                status: 'ready',
                icon: <ExperimentOutlined />,
                path: '/research',
              },
              {
                key: 'writing-projects',
                title: '推进写作项目',
                description: '把已验证的 idea、证据卡片和引用校验收束到论文或本子草稿。',
                actionLabel: '打开写作工作台',
                status: dashboard.resource_balance?.writing_projects ? 'ready' : 'optional',
                icon: <EditOutlined />,
                path: '/writing',
              },
            ]}
          />

          <Row gutter={[16, 16]} style={{ marginBottom: 18 }}>
            {statusCards.map((card: any) => (
              <Col xs={12} md={6} key={card.key}>
                <Card style={{ borderRadius: 14, borderTop: `3px solid ${dashboardCardColor[card.key] || '#667eea'}` }} styles={{ body: { padding: 16 } }}>
                  <Statistic
                    title={card.label}
                    value={card.count}
                    prefix={<span style={{ color: dashboardCardColor[card.key] }}>{dashboardCardIcon[card.key]}</span>}
                  />
                  <Space size={6} style={{ marginTop: 8 }}>
                    <Tag color={card.status === 'ready' ? 'green' : 'gold'}>{card.status_label}</Tag>
                    <Text type="secondary" style={{ fontSize: 12 }}>{card.hint}</Text>
                  </Space>
                </Card>
              </Col>
            ))}
          </Row>

          <Row gutter={[16, 16]}>
            <Col xs={24} xl={16}>
              <Alert
                type={dashboard.progress_score >= 70 ? 'success' : dashboard.progress_score >= 35 ? 'info' : 'warning'}
                showIcon
                message={`当前阶段：${dashboard.stage_label || '待搭建'}`}
                description="看板会根据空间内论文、研究方向、写作草稿和最近活动自动判断推进状态。"
                style={{ borderRadius: 12, marginBottom: 16 }}
              />
              <Row gutter={[16, 16]} style={{ marginBottom: 18 }}>
                <Col xs={24} lg={8}>{renderResourceList('papers', resources.papers || [])}</Col>
                <Col xs={24} lg={8}>{renderResourceList('research_projects', resources.research_projects || [])}</Col>
                <Col xs={24} lg={8}>{renderResourceList('writing_projects', resources.writing_projects || [])}</Col>
              </Row>

              {canEditResources && (
                <Card id="workspace-resource-binder" title={<Space><LinkOutlined />绑定空间资源</Space>} style={{ borderRadius: 14 }}>
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
            </Col>
            <Col xs={24} xl={8}>
              {renderAssistantPanel()}
              <Card title="下一步建议" style={{ borderRadius: 14 }}>
                <List
                  dataSource={space.next_actions || []}
                  renderItem={(item: any) => (
                    <List.Item actions={[<Button size="small" icon={<RocketOutlined />} onClick={() => navigate(item.path)} style={{ borderRadius: 8 }}>进入</Button>]}>
                      <List.Item.Meta title={item.label} description="根据当前空间资源覆盖情况自动推荐" />
                    </List.Item>
                  )}
                />
              </Card>
              <Card
                title="成员"
                style={{ borderRadius: 14, marginTop: 16 }}
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
              <Card title="最近活动" style={{ borderRadius: 14, marginTop: 16 }}>
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
    </PageShell>
  );
};

export default WorkspaceDetailPage;
