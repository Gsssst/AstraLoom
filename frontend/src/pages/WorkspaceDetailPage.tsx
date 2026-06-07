import React, { useEffect, useState } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import {
  Alert, Button, Card, Col, Drawer, Empty, Form, Input, List, Modal, Progress, Row, Select, Space, Statistic, Tabs, Tag, Timeline, Typography, message,
} from 'antd';
import {
  AppstoreOutlined, ArrowLeftOutlined, BookOutlined, BugOutlined, CommentOutlined, DeleteOutlined, EditOutlined, ExperimentOutlined,
  LinkOutlined, PlusOutlined, RobotOutlined, RocketOutlined, SendOutlined, TeamOutlined, UserOutlined,
} from '@ant-design/icons';
import api from '../services/api';
import WorkflowStepGuide from '../components/WorkflowStepGuide';
import PageShell from '../components/PageShell';
import { getApiErrorDetails, type ApiErrorDetails } from '../services/apiError';
import Markdown from '../components/Markdown';

const { Title, Text, Paragraph } = Typography;

interface WorkspaceAssistantMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  references?: any[];
  created_at?: string;
}

interface WorkspaceIssue {
  id: string;
  title: string;
  description?: string;
  status: 'open' | 'closed';
  issue_type: string;
  priority: string;
  labels?: string[];
  resource_reference?: any;
  creator_name?: string;
  assignee_name?: string;
  comment_count?: number;
  comments?: any[];
  created_at?: string;
  updated_at?: string;
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
  issue_created: '创建了 Issue',
  issue_updated: '更新了 Issue',
  issue_commented: '评论了 Issue',
  issue_closed: '关闭了 Issue',
  issue_reopened: '重新打开了 Issue',
};

const issueTypeLabel: Record<string, string> = {
  feedback: '反馈',
  bug: 'Bug',
  idea: '想法',
  question: '问题',
  task: '任务',
};

const issuePriorityLabel: Record<string, string> = {
  low: '低',
  medium: '中',
  high: '高',
  urgent: '紧急',
};

const issuePriorityColor: Record<string, string> = {
  low: 'default',
  medium: 'blue',
  high: 'orange',
  urgent: 'red',
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
  const [searchParams] = useSearchParams();
  const linkedIssueId = searchParams.get('issue');
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
  const [issueForm] = Form.useForm();
  const [issueCommentForm] = Form.useForm();
  const [issues, setIssues] = useState<WorkspaceIssue[]>([]);
  const [issueSummary, setIssueSummary] = useState({ open: 0, closed: 0, total: 0 });
  const [issueFilters, setIssueFilters] = useState({ status: 'open', issue_type: 'all', priority: 'all' });
  const [issuesLoading, setIssuesLoading] = useState(false);
  const [issueSaving, setIssueSaving] = useState(false);
  const [issueModalOpen, setIssueModalOpen] = useState(false);
  const [issueDrawerOpen, setIssueDrawerOpen] = useState(false);
  const [selectedIssue, setSelectedIssue] = useState<WorkspaceIssue | null>(null);
  const [activeWorkspaceTab, setActiveWorkspaceTab] = useState('overview');
  const [assistantLoading, setAssistantLoading] = useState(false);
  const [assistantSending, setAssistantSending] = useState(false);
  const [assistantInput, setAssistantInput] = useState('');
  const [assistantMessages, setAssistantMessages] = useState<WorkspaceAssistantMessage[]>([]);
  const [assistantPrompts, setAssistantPrompts] = useState<string[]>([]);
  const [assistantReferences, setAssistantReferences] = useState<any[]>([]);
  const [assistantContextOpen, setAssistantContextOpen] = useState(false);
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

  const fetchIssues = async (filters = issueFilters) => {
    if (!spaceId) return;
    setIssuesLoading(true);
    try {
      const response = await api.get(`/workspaces/${spaceId}/issues`, {
        params: {
          status_filter: filters.status === 'all' ? undefined : filters.status,
          issue_type: filters.issue_type === 'all' ? undefined : filters.issue_type,
          priority: filters.priority === 'all' ? undefined : filters.priority,
          limit: 50,
        },
      });
      setIssues(response.data.issues || []);
      setIssueSummary(response.data.summary || { open: 0, closed: 0, total: 0 });
      setWorkspaceActionError(null);
    } catch (error: any) {
      const detail = getApiErrorDetails(error, { fallback: '反馈 Issue 加载失败' });
      setWorkspaceActionError({ title: '反馈 Issue 加载失败', detail });
      message.warning(detail.message);
    } finally {
      setIssuesLoading(false);
    }
  };

  useEffect(() => { fetchIssues(issueFilters); }, [spaceId, issueFilters.status, issueFilters.issue_type, issueFilters.priority]);

  const handleCreateIssue = async () => {
    const values = await issueForm.validateFields();
    setIssueSaving(true);
    try {
      const response = await api.post(`/workspaces/${spaceId}/issues`, values);
      setIssueModalOpen(false);
      issueForm.resetFields();
      setSelectedIssue(response.data);
      setIssueDrawerOpen(true);
      await fetchIssues(issueFilters);
      setWorkspaceActionError(null);
      message.success('反馈 Issue 已创建');
    } catch (error: any) {
      const detail = getApiErrorDetails(error, { fallback: '创建反馈 Issue 失败' });
      setWorkspaceActionError({ title: '创建反馈 Issue 失败', detail });
      message.warning(detail.message);
    } finally {
      setIssueSaving(false);
    }
  };

  const openIssueDetail = async (issue: WorkspaceIssue) => {
    setSelectedIssue(issue);
    setIssueDrawerOpen(true);
    try {
      const response = await api.get(`/workspaces/${spaceId}/issues/${issue.id}`);
      setSelectedIssue(response.data);
      setWorkspaceActionError(null);
    } catch (error: any) {
      const detail = getApiErrorDetails(error, { fallback: '反馈 Issue 详情加载失败' });
      setWorkspaceActionError({ title: '反馈 Issue 详情加载失败', detail });
      message.warning(detail.message);
    }
  };

  useEffect(() => {
    if (!spaceId || !linkedIssueId) return;
    openIssueDetail({ id: linkedIssueId } as WorkspaceIssue);
    setActiveWorkspaceTab('issues');
  }, [spaceId, linkedIssueId]);

  const updateSelectedIssue = async (updates: Record<string, any>) => {
    if (!selectedIssue) return;
    setIssueSaving(true);
    try {
      const response = await api.patch(`/workspaces/${spaceId}/issues/${selectedIssue.id}`, updates);
      setSelectedIssue(response.data);
      await fetchIssues(issueFilters);
      setWorkspaceActionError(null);
      message.success(updates.status === 'closed' ? 'Issue 已关闭' : updates.status === 'open' ? 'Issue 已重新打开' : 'Issue 已更新');
    } catch (error: any) {
      const detail = getApiErrorDetails(error, { fallback: '更新反馈 Issue 失败' });
      setWorkspaceActionError({ title: '更新反馈 Issue 失败', detail });
      message.warning(detail.message);
    } finally {
      setIssueSaving(false);
    }
  };

  const handleAddIssueComment = async () => {
    if (!selectedIssue) return;
    const values = await issueCommentForm.validateFields();
    setIssueSaving(true);
    try {
      await api.post(`/workspaces/${spaceId}/issues/${selectedIssue.id}/comments`, values);
      issueCommentForm.resetFields();
      const response = await api.get(`/workspaces/${spaceId}/issues/${selectedIssue.id}`);
      setSelectedIssue(response.data);
      await fetchIssues(issueFilters);
      setWorkspaceActionError(null);
      message.success('评论已添加');
    } catch (error: any) {
      const detail = getApiErrorDetails(error, { fallback: '添加 Issue 评论失败' });
      setWorkspaceActionError({ title: '添加 Issue 评论失败', detail });
      message.warning(detail.message);
    } finally {
      setIssueSaving(false);
    }
  };

  const openResourceBinder = (type: string) => {
    if (!canEditResources) return;
    setCandidateType(type);
    setManualMode(false);
    setActiveWorkspaceTab('resources');
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
                    {item.role === 'assistant' ? (
                      <div style={{ maxWidth: '100%', overflow: 'hidden' }}>
                        <Markdown content={item.content} />
                      </div>
                    ) : (
                      <Paragraph style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{item.content}</Paragraph>
                    )}
                    {!!item.references?.length && (
                      <Space wrap size={4}>
                        {item.references.slice(0, 6).map((reference: any, index: number) => (
                          <Tag
                            key={`${reference.resource_type || 'ref'}-${reference.resource_id || index}`}
                            color="geekblue"
                            style={{
                              maxWidth: '100%',
                              cursor: reference.path ? 'pointer' : 'default',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                            }}
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
          <Space direction="vertical" size={6} style={{ width: '100%' }}>
            <Button
              type="text"
              size="small"
              onClick={() => setAssistantContextOpen(open => !open)}
              style={{ alignSelf: 'flex-start', padding: 0, height: 24, color: '#667085' }}
            >
              当前上下文 {assistantReferences.length} 项 · {assistantContextOpen ? '收起' : '展开'}
            </Button>
            {assistantContextOpen && (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, maxWidth: '100%', overflow: 'hidden' }}>
                {assistantReferences.slice(0, 12).map((reference: any, index: number) => (
                  <Tag
                    key={`${reference.resource_type || 'ctx'}-${reference.resource_id || index}`}
                    onClick={() => reference.path && navigate(reference.path)}
                    title={reference.title || reference.source_label}
                    style={{
                      maxWidth: '100%',
                      cursor: reference.path ? 'pointer' : 'default',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {reference.title || reference.source_label}
                  </Tag>
                ))}
              </div>
            )}
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

  const renderIssuePanel = () => (
    <Card
      title={<Space><BugOutlined />反馈 Issue</Space>}
      loading={issuesLoading}
      style={{ borderRadius: 14, marginBottom: 16 }}
      extra={(
        <Button type="primary" size="small" icon={<PlusOutlined />} onClick={() => setIssueModalOpen(true)}>
          提 Issue
        </Button>
      )}
    >
      <Space direction="vertical" size={12} style={{ width: '100%' }}>
        <Row gutter={[8, 8]}>
          <Col xs={12} sm={6}>
            <Statistic title="Open" value={issueSummary.open} valueStyle={{ fontSize: 20, color: '#16a34a' }} />
          </Col>
          <Col xs={12} sm={6}>
            <Statistic title="Closed" value={issueSummary.closed} valueStyle={{ fontSize: 20 }} />
          </Col>
          <Col xs={24} sm={12}>
            <Space wrap style={{ justifyContent: 'flex-end', width: '100%' }}>
              <Select
                size="small"
                value={issueFilters.status}
                style={{ width: 110 }}
                onChange={statusValue => setIssueFilters(prev => ({ ...prev, status: statusValue }))}
                options={[
                  { value: 'open', label: 'Open' },
                  { value: 'closed', label: 'Closed' },
                  { value: 'all', label: '全部' },
                ]}
              />
              <Select
                size="small"
                value={issueFilters.issue_type}
                style={{ width: 112 }}
                onChange={typeValue => setIssueFilters(prev => ({ ...prev, issue_type: typeValue }))}
                options={[
                  { value: 'all', label: '全部类型' },
                  { value: 'feedback', label: '反馈' },
                  { value: 'bug', label: 'Bug' },
                  { value: 'idea', label: '想法' },
                  { value: 'question', label: '问题' },
                  { value: 'task', label: '任务' },
                ]}
              />
              <Select
                size="small"
                value={issueFilters.priority}
                style={{ width: 112 }}
                onChange={priorityValue => setIssueFilters(prev => ({ ...prev, priority: priorityValue }))}
                options={[
                  { value: 'all', label: '全部优先级' },
                  { value: 'low', label: '低' },
                  { value: 'medium', label: '中' },
                  { value: 'high', label: '高' },
                  { value: 'urgent', label: '紧急' },
                ]}
              />
            </Space>
          </Col>
        </Row>

        <List
          dataSource={issues}
          locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无反馈 Issue" /> }}
          renderItem={(issue) => (
            <List.Item
              style={{ cursor: 'pointer', alignItems: 'flex-start' }}
              onClick={() => openIssueDetail(issue)}
              actions={[
                <Space key="comments" size={4}>
                  <CommentOutlined />
                  <Text type="secondary">{issue.comment_count || 0}</Text>
                </Space>,
              ]}
            >
              <List.Item.Meta
                title={(
                  <Space size={6} wrap>
                    <Tag color={issue.status === 'open' ? 'green' : 'default'}>{issue.status}</Tag>
                    <Text strong style={{ maxWidth: 520 }} ellipsis>{issue.title}</Text>
                  </Space>
                )}
                description={(
                  <Space direction="vertical" size={4} style={{ width: '100%' }}>
                    <Space size={6} wrap>
                      <Tag>{issueTypeLabel[issue.issue_type] || issue.issue_type}</Tag>
                      <Tag color={issuePriorityColor[issue.priority] || 'default'}>{issuePriorityLabel[issue.priority] || issue.priority}</Tag>
                      {issue.resource_reference && (
                        <Tag color="purple" onClick={(event) => {
                          event.stopPropagation();
                          if (issue.resource_reference?.path) navigate(issue.resource_reference.path);
                        }}>
                          关联：{issue.resource_reference.title || resourceLabel[issue.resource_reference.resource_type] || issue.resource_reference.resource_type}
                        </Tag>
                      )}
                      {(issue.labels || []).slice(0, 4).map(label => <Tag key={label} color="geekblue">{label}</Tag>)}
                    </Space>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {issue.creator_name || '未知用户'} 创建
                      {issue.updated_at ? ` · 更新于 ${new Date(issue.updated_at).toLocaleString()}` : ''}
                    </Text>
                  </Space>
                )}
              />
            </List.Item>
          )}
        />
      </Space>
    </Card>
  );

  const renderNextActionsCard = () => (
    <Card title="下一步建议" style={{ borderRadius: 14 }}>
      <List
        dataSource={space.next_actions || []}
        locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无下一步建议" /> }}
        renderItem={(item: any) => (
          <List.Item actions={[<Button size="small" icon={<RocketOutlined />} onClick={() => navigate(item.path)} style={{ borderRadius: 8 }}>进入</Button>]}>
            <List.Item.Meta title={item.label} description={item.kind === 'issue' ? '来自高优先级开放 Issue' : '根据当前空间资源覆盖情况自动推荐'} />
          </List.Item>
        )}
      />
    </Card>
  );

  const renderMembersCard = () => (
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
  );

  const renderActivityCard = () => (
    <Card title="最近活动" style={{ borderRadius: 14 }}>
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
  );

  const renderResourceBinder = () => {
    if (!canEditResources) return null;
    return (
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
              style={{ width: 360, maxWidth: '100%' }}
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
    );
  };

  const renderStatusCards = () => (
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
  );

  const renderOverviewTab = () => (
    <Row gutter={[16, 16]}>
      <Col xs={24} xl={16}>
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
        {renderStatusCards()}
        <Alert
          type={dashboard.progress_score >= 70 ? 'success' : dashboard.progress_score >= 35 ? 'info' : 'warning'}
          showIcon
          message={`当前阶段：${dashboard.stage_label || '待搭建'}`}
          description="看板会根据空间内论文、研究方向、写作草稿和最近活动自动判断推进状态。"
          style={{ borderRadius: 12 }}
        />
      </Col>
      <Col xs={24} xl={8}>
        {renderNextActionsCard()}
      </Col>
    </Row>
  );

  const renderResourcesTab = () => (
    <Space direction="vertical" size={16} style={{ width: '100%' }}>
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={8}>{renderResourceList('papers', resources.papers || [])}</Col>
        <Col xs={24} lg={8}>{renderResourceList('research_projects', resources.research_projects || [])}</Col>
        <Col xs={24} lg={8}>{renderResourceList('writing_projects', resources.writing_projects || [])}</Col>
      </Row>
      {renderResourceBinder()}
    </Space>
  );

  const renderAssistantTab = () => (
    <Row gutter={[16, 16]}>
      <Col xs={24} xl={16}>{renderAssistantPanel()}</Col>
      <Col xs={24} xl={8}>{renderNextActionsCard()}</Col>
    </Row>
  );

  const renderActivityTab = () => (
    <Row gutter={[16, 16]}>
      <Col xs={24} lg={10}>{renderMembersCard()}</Col>
      <Col xs={24} lg={14}>{renderActivityCard()}</Col>
    </Row>
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
          <Tabs
            activeKey={activeWorkspaceTab}
            onChange={setActiveWorkspaceTab}
            items={[
              {
                key: 'overview',
                label: <Space><AppstoreOutlined />概览</Space>,
                children: renderOverviewTab(),
              },
              {
                key: 'issues',
                label: <Space><BugOutlined />Issue</Space>,
                children: renderIssuePanel(),
              },
              {
                key: 'resources',
                label: <Space><LinkOutlined />资源</Space>,
                children: renderResourcesTab(),
              },
              {
                key: 'assistant',
                label: <Space><RobotOutlined />助手</Space>,
                children: renderAssistantTab(),
              },
              {
                key: 'activity',
                label: <Space><TeamOutlined />协作动态</Space>,
                children: renderActivityTab(),
              },
            ]}
          />
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

      <Modal
        title="提交反馈 Issue"
        open={issueModalOpen}
        onOk={handleCreateIssue}
        confirmLoading={issueSaving}
        onCancel={() => setIssueModalOpen(false)}
        okText="提交"
      >
        <Form form={issueForm} layout="vertical" initialValues={{ issue_type: 'feedback', priority: 'medium', labels: [] }}>
          <Form.Item name="title" label="标题" rules={[{ required: true, message: '请输入 Issue 标题' }]}>
            <Input placeholder="一句话描述反馈、Bug 或需求" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea placeholder="补充复现步骤、期望结果、相关上下文或建议" autoSize={{ minRows: 4, maxRows: 8 }} />
          </Form.Item>
          <Row gutter={12}>
            <Col span={12}>
              <Form.Item name="issue_type" label="类型">
                <Select options={[
                  { value: 'feedback', label: '反馈' },
                  { value: 'bug', label: 'Bug' },
                  { value: 'idea', label: '想法' },
                  { value: 'question', label: '问题' },
                  { value: 'task', label: '任务' },
                ]} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="priority" label="优先级">
                <Select options={[
                  { value: 'low', label: '低' },
                  { value: 'medium', label: '中' },
                  { value: 'high', label: '高' },
                  { value: 'urgent', label: '紧急' },
                ]} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="labels" label="标签">
            <Select
              mode="tags"
              placeholder="输入标签后回车，例如 ui、体验、研究流程"
              tokenSeparators={[',', '，']}
              options={[
                { value: 'ui', label: 'ui' },
                { value: 'ux', label: 'ux' },
                { value: 'api', label: 'api' },
                { value: 'research-flow', label: 'research-flow' },
              ]}
            />
          </Form.Item>
        </Form>
      </Modal>

      <Drawer
        title={selectedIssue ? (
          <Space wrap>
            <Tag color={selectedIssue.status === 'open' ? 'green' : 'default'}>{selectedIssue.status}</Tag>
            <span>{selectedIssue.title}</span>
          </Space>
        ) : '反馈 Issue'}
        open={issueDrawerOpen}
        onClose={() => setIssueDrawerOpen(false)}
        width={520}
        extra={selectedIssue && canEditResources ? (
          <Button
            loading={issueSaving}
            onClick={() => updateSelectedIssue({ status: selectedIssue.status === 'open' ? 'closed' : 'open' })}
          >
            {selectedIssue.status === 'open' ? '关闭 Issue' : '重新打开'}
          </Button>
        ) : null}
      >
        {selectedIssue ? (
          <Space direction="vertical" size={16} style={{ width: '100%' }}>
            <Space size={6} wrap>
              <Tag>{issueTypeLabel[selectedIssue.issue_type] || selectedIssue.issue_type}</Tag>
              <Tag color={issuePriorityColor[selectedIssue.priority] || 'default'}>
                {issuePriorityLabel[selectedIssue.priority] || selectedIssue.priority}
              </Tag>
              {(selectedIssue.labels || []).map(label => <Tag key={label} color="geekblue">{label}</Tag>)}
            </Space>
            <Text type="secondary" style={{ fontSize: 12 }}>
              {selectedIssue.creator_name || '未知用户'} 创建
              {selectedIssue.created_at ? ` · ${new Date(selectedIssue.created_at).toLocaleString()}` : ''}
              {selectedIssue.assignee_name ? ` · 指派给 ${selectedIssue.assignee_name}` : ''}
            </Text>
            {selectedIssue.resource_reference && (
              <Alert
                type="info"
                showIcon
                style={{ borderRadius: 10 }}
                message="关联资源"
                description={(
                  <Button type="link" style={{ padding: 0 }} onClick={() => selectedIssue.resource_reference?.path && navigate(selectedIssue.resource_reference.path)}>
                    {selectedIssue.resource_reference.title || selectedIssue.resource_reference.resource_id}
                  </Button>
                )}
              />
            )}
            <Card size="small" style={{ borderRadius: 10 }}>
              {selectedIssue.description ? (
                <Paragraph style={{ whiteSpace: 'pre-wrap', marginBottom: 0 }}>{selectedIssue.description}</Paragraph>
              ) : (
                <Text type="secondary">暂无描述</Text>
              )}
            </Card>

            {canEditResources && (
              <Space wrap>
                <Select
                  size="small"
                  value={selectedIssue.priority}
                  style={{ width: 120 }}
                  onChange={value => updateSelectedIssue({ priority: value })}
                  options={[
                    { value: 'low', label: '低优先级' },
                    { value: 'medium', label: '中优先级' },
                    { value: 'high', label: '高优先级' },
                    { value: 'urgent', label: '紧急' },
                  ]}
                />
                <Select
                  size="small"
                  value={selectedIssue.issue_type}
                  style={{ width: 120 }}
                  onChange={value => updateSelectedIssue({ issue_type: value })}
                  options={[
                    { value: 'feedback', label: '反馈' },
                    { value: 'bug', label: 'Bug' },
                    { value: 'idea', label: '想法' },
                    { value: 'question', label: '问题' },
                    { value: 'task', label: '任务' },
                  ]}
                />
              </Space>
            )}

            <div>
              <Title level={5} style={{ marginTop: 0 }}>讨论</Title>
              <List
                dataSource={selectedIssue.comments || []}
                locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无评论" /> }}
                renderItem={(comment: any) => (
                  <List.Item>
                    <List.Item.Meta
                      title={(
                        <Space>
                          <Text strong>{comment.author_name || '未知用户'}</Text>
                          <Text type="secondary" style={{ fontSize: 12 }}>
                            {comment.created_at ? new Date(comment.created_at).toLocaleString() : ''}
                          </Text>
                        </Space>
                      )}
                      description={<Paragraph style={{ whiteSpace: 'pre-wrap', marginBottom: 0 }}>{comment.content}</Paragraph>}
                    />
                  </List.Item>
                )}
              />
            </div>

            <Form form={issueCommentForm} layout="vertical">
              <Form.Item name="content" rules={[{ required: true, message: '请输入评论内容' }]}>
                <Input.TextArea placeholder="补充反馈、处理进展或结论" autoSize={{ minRows: 3, maxRows: 6 }} />
              </Form.Item>
              <Button type="primary" icon={<CommentOutlined />} loading={issueSaving} onClick={handleAddIssueComment}>
                添加评论
              </Button>
            </Form>
          </Space>
        ) : (
          <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="请选择一个 Issue" />
        )}
      </Drawer>
    </PageShell>
  );
};

export default WorkspaceDetailPage;
