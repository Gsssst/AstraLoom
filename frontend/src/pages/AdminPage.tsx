import React, { useEffect, useState } from 'react';
import {
  Alert, Avatar, Button, Card, Col, Input, Row, Select, Space,
  Statistic, Switch, Table, Tag, Timeline, Typography, message,
} from 'antd';
import {
  AuditOutlined, DatabaseOutlined, ReloadOutlined, SafetyCertificateOutlined,
  TeamOutlined, UserOutlined,
} from '@ant-design/icons';
import api from '../services/api';
import { useAuthStore } from '../stores/useAuthStore';
import PageShell from '../components/PageShell';
import { getApiErrorDetails, type ApiErrorDetails } from '../services/apiError';

const { Text, Paragraph } = Typography;

const cardStyle = { borderRadius: 14, border: '1px solid #f0f0f0' };
const activityLabel: Record<string, string> = {
  space_created: '创建项目空间',
  space_updated: '更新项目空间',
  space_deleted: '删除项目空间',
  member_added: '添加成员',
  member_updated: '更新成员',
  member_removed: '移除成员',
  resource_linked: '绑定资源',
  resource_unlinked: '移除资源',
};

const AdminPage: React.FC = () => {
  const user = useAuthStore((state) => state.user);
  const [overview, setOverview] = useState<any>(null);
  const [users, setUsers] = useState<any[]>([]);
  const [workspaces, setWorkspaces] = useState<any[]>([]);
  const [activities, setActivities] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [userQuery, setUserQuery] = useState('');
  const [workspaceQuery, setWorkspaceQuery] = useState('');
  const [updatingUserId, setUpdatingUserId] = useState<string | null>(null);
  const [adminActionError, setAdminActionError] = useState<{ title: string; detail: ApiErrorDetails } | null>(null);

  const isAdmin = user?.role === 'admin';

  const fetchAdminData = async () => {
    if (!isAdmin) return;
    setLoading(true);
    try {
      const [overviewRes, usersRes, spacesRes, activitiesRes] = await Promise.all([
        api.get('/admin/overview'),
        api.get('/admin/users', { params: { query: userQuery || undefined } }),
        api.get('/admin/workspaces', { params: { query: workspaceQuery || undefined } }),
        api.get('/admin/workspace-activities', { params: { limit: 20 } }),
      ]);
      setOverview(overviewRes.data);
      setUsers(usersRes.data.users || []);
      setWorkspaces(spacesRes.data.workspaces || []);
      setActivities(activitiesRes.data.activities || []);
      setAdminActionError(null);
    } catch (error: any) {
      const detail = getApiErrorDetails(error, { fallback: '管理员数据加载失败' });
      setAdminActionError({ title: '管理员数据加载失败', detail });
      message.warning(detail.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAdminData();
  }, [isAdmin]);

  const updateUser = async (target: any, updates: any) => {
    setUpdatingUserId(target.id);
    try {
      const response = await api.patch(`/admin/users/${target.id}`, updates);
      setUsers(prev => prev.map(item => item.id === target.id ? response.data : item));
      setAdminActionError(null);
      message.success('用户权限已更新');
      await fetchAdminData();
    } catch (error: any) {
      const detail = getApiErrorDetails(error, { fallback: '用户更新失败' });
      setAdminActionError({ title: '用户更新失败', detail });
      message.warning(detail.message);
    } finally {
      setUpdatingUserId(null);
    }
  };

  if (!isAdmin) {
    return (
      <Card style={{ ...cardStyle, maxWidth: 760, margin: '60px auto' }}>
        <Alert
          type="warning"
          showIcon
          message="需要管理员权限"
          description="当前账号不是管理员，无法访问系统治理台。"
        />
      </Card>
    );
  }

  const counts = overview?.counts || {};

  return (
    <PageShell
      title="管理员后台"
      subtitle="用户权限、项目空间与系统治理概览。"
      icon={<SafetyCertificateOutlined />}
      maxWidth={1320}
      actions={(
        <Button icon={<ReloadOutlined />} onClick={fetchAdminData} loading={loading} style={{ borderRadius: 10 }}>
          刷新
        </Button>
      )}
    >
      {adminActionError ? (
        <Alert
          type={adminActionError.detail.severity === 'error' ? 'error' : 'warning'}
          showIcon
          closable
          onClose={() => setAdminActionError(null)}
          style={{ borderRadius: 12, marginBottom: 16 }}
          message={`${adminActionError.title}：${adminActionError.detail.message}`}
          description={(
            <Space direction="vertical" size={6}>
              <Text>{adminActionError.detail.recovery}</Text>
              <Space size={6} wrap>
                <Tag color="orange">{adminActionError.detail.category}</Tag>
                <Tag color={adminActionError.detail.retryable ? 'blue' : 'default'}>
                  {adminActionError.detail.retryable ? '可重试' : '需先处理条件'}
                </Tag>
                {adminActionError.detail.status && <Tag>HTTP {adminActionError.detail.status}</Tag>}
              </Space>
            </Space>
          )}
        />
      ) : null}

      {overview?.risk_hints?.length > 0 && (
        <Alert
          type="warning"
          showIcon
          message="治理提醒"
          description={overview.risk_hints.join(' ')}
          style={{ borderRadius: 12, marginBottom: 16 }}
        />
      )}

      <Row gutter={[16, 16]} style={{ marginBottom: 18 }}>
        <Col xs={12} md={6}><Card style={cardStyle}><Statistic title="用户" value={counts.users || 0} prefix={<UserOutlined />} /></Card></Col>
        <Col xs={12} md={6}><Card style={cardStyle}><Statistic title="活跃用户" value={counts.active_users || 0} prefix={<TeamOutlined />} /></Card></Col>
        <Col xs={12} md={6}><Card style={cardStyle}><Statistic title="管理员" value={counts.admins || 0} prefix={<SafetyCertificateOutlined />} /></Card></Col>
        <Col xs={12} md={6}><Card style={cardStyle}><Statistic title="项目空间" value={counts.project_spaces || 0} prefix={<AuditOutlined />} /></Card></Col>
        <Col xs={12} md={6}><Card style={cardStyle}><Statistic title="论文" value={counts.papers || 0} prefix={<DatabaseOutlined />} /></Card></Col>
        <Col xs={12} md={6}><Card style={cardStyle}><Statistic title="研究方向" value={counts.research_projects || 0} /></Card></Col>
        <Col xs={12} md={6}><Card style={cardStyle}><Statistic title="写作项目" value={counts.writing_projects || 0} /></Card></Col>
      </Row>

      <Card
        title="用户权限管理"
        style={{ ...cardStyle, marginBottom: 18 }}
        extra={
          <Space>
            <Input.Search
              allowClear
              placeholder="搜索用户名/邮箱"
              value={userQuery}
              onChange={e => setUserQuery(e.target.value)}
              onSearch={fetchAdminData}
              style={{ width: 260 }}
            />
          </Space>
        }
      >
        <Table
          rowKey="id"
          loading={loading}
          dataSource={users}
          pagination={{ pageSize: 8 }}
          columns={[
            {
              title: '用户',
              render: (_: any, record: any) => (
                <Space>
                  <Avatar src={record.avatar} icon={<UserOutlined />} />
                  <div>
                    <Text strong>{record.display_name || record.username}</Text>
                    <Text type="secondary" style={{ display: 'block', fontSize: 12 }}>{record.email}</Text>
                  </div>
                </Space>
              ),
            },
            {
              title: '角色',
              dataIndex: 'role',
              width: 180,
              render: (_: string, record: any) => (
                <Select
                  value={record.role}
                  style={{ width: 130 }}
                  loading={updatingUserId === record.id}
                  onChange={role => updateUser(record, { role })}
                  options={[
                    { value: 'user', label: '普通用户' },
                    { value: 'admin', label: '管理员' },
                  ]}
                />
              ),
            },
            {
              title: '状态',
              dataIndex: 'is_active',
              width: 140,
              render: (_: boolean, record: any) => (
                <Switch
                  checked={record.is_active}
                  checkedChildren="启用"
                  unCheckedChildren="停用"
                  loading={updatingUserId === record.id}
                  onChange={checked => updateUser(record, { is_active: checked })}
                />
              ),
            },
            {
              title: '创建时间',
              dataIndex: 'created_at',
              width: 190,
              render: (value: string) => value ? new Date(value).toLocaleString() : '-',
            },
          ]}
        />
      </Card>

      <Card
        title="项目空间治理"
        style={{ ...cardStyle, marginBottom: 18 }}
        extra={
          <Input.Search
            allowClear
            placeholder="搜索空间名称"
            value={workspaceQuery}
            onChange={e => setWorkspaceQuery(e.target.value)}
            onSearch={fetchAdminData}
            style={{ width: 260 }}
          />
        }
      >
        <Paragraph type="secondary">
          当前版本提供空间所有者、成员角色和资源协作状态可见性。
        </Paragraph>
        <Table
          rowKey="id"
          loading={loading}
          dataSource={workspaces}
          pagination={{ pageSize: 8 }}
          columns={[
            {
              title: '空间',
              render: (_: any, record: any) => (
                <div>
                  <Text strong>{record.name}</Text>
                  <Text type="secondary" style={{ display: 'block', fontSize: 12 }}>{record.description || '暂无描述'}</Text>
                </div>
              ),
            },
            {
              title: 'Owner',
              render: (_: any, record: any) => record.owner ? (
                <Space>
                  <Avatar size={24} src={record.owner.avatar} icon={<UserOutlined />} />
                  <Text>{record.owner.display_name || record.owner.username}</Text>
                </Space>
              ) : <Tag color="red">缺失</Tag>,
            },
            {
              title: '成员',
              dataIndex: 'member_count',
              width: 100,
            },
            {
              title: '角色分布',
              render: (_: any, record: any) => (
                <Space wrap>
                  <Tag color="purple">owner {record.role_counts?.owner || 0}</Tag>
                  <Tag color="blue">editor {record.role_counts?.editor || 0}</Tag>
                  <Tag>viewer {record.role_counts?.viewer || 0}</Tag>
                </Space>
              ),
            },
            {
              title: '状态',
              dataIndex: 'status',
              width: 110,
              render: (status: string) => <Tag color={status === 'active' ? 'green' : 'default'}>{status}</Tag>,
            },
          ]}
        />
      </Card>

      <Card title="最近空间活动" style={cardStyle}>
        {activities.length ? (
          <Timeline
            items={activities.map((item: any) => ({
              children: (
                <Space direction="vertical" size={2}>
                  <Text>
                    <Text strong>{item.actor_name}</Text> {activityLabel[item.action] || item.action}
                    {item.resource_type && <Tag style={{ marginLeft: 8 }}>{item.resource_type}</Tag>}
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
          <Alert type="info" showIcon message="暂无空间活动" description="创建空间、绑定资源或管理成员后，这里会出现治理时间线。" />
        )}
      </Card>
    </PageShell>
  );
};

export default AdminPage;
