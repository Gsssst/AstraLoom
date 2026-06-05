import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Alert, Button, Card, Col, Empty, List, Row, Space, Spin, Statistic, Tag, Typography, message,
} from 'antd';
import {
  BookOutlined, CheckCircleOutlined, EditOutlined, ExperimentOutlined,
  RightOutlined, ThunderboltOutlined, AppstoreOutlined,
} from '@ant-design/icons';
import api from '../services/api';

const { Title, Text, Paragraph } = Typography;

const groupConfig: Record<string, { label: string; icon: React.ReactNode; color: string }> = {
  papers: { label: '论文与知识库', icon: <BookOutlined />, color: '#4f7cff' },
  research: { label: '研究方向', icon: <ExperimentOutlined />, color: '#f5576c' },
  writing: { label: '写作助手', icon: <EditOutlined />, color: '#16a34a' },
  workspaces: { label: '项目空间', icon: <AppstoreOutlined />, color: '#764ba2' },
};

const priorityConfig: Record<string, { label: string; color: string }> = {
  high: { label: '优先处理', color: 'red' },
  medium: { label: '建议推进', color: 'gold' },
  low: { label: '可安排', color: 'blue' },
};

const formatActionResult = (payload: any) => {
  if (!payload || typeof payload !== 'object') return '动作已完成，行动中心已刷新。';
  const parts = [
    payload.processed !== undefined ? `处理 ${payload.processed}` : null,
    payload.success !== undefined ? `成功 ${payload.success}` : null,
    payload.failed !== undefined ? `失败 ${payload.failed}` : null,
    payload.skipped !== undefined ? `跳过 ${payload.skipped}` : null,
  ].filter(Boolean);
  return parts.length ? `${parts.join('，')}。` : '动作已完成，行动中心已刷新。';
};

const ActionCenterPage: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [runningActionId, setRunningActionId] = useState<string | null>(null);
  const [lastActionResult, setLastActionResult] = useState<{ title: string; detail: string } | null>(null);
  const [data, setData] = useState<any>({ summary: {}, actions: [] });

  const fetchActions = async () => {
    setLoading(true);
    try {
      const response = await api.get('/workflow/actions');
      setData(response.data || { summary: {}, actions: [] });
    } catch (error: any) {
      message.error(error.response?.data?.detail || '行动中心加载失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchActions(); }, []);

  const runAction = async (item: any) => {
    if (item.action_type !== 'api') {
      navigate(item.path);
      return;
    }
    if (!item.endpoint) {
      message.error('这个行动项缺少可执行入口');
      return;
    }
    setRunningActionId(item.id);
    setLastActionResult(null);
    try {
      const response = await api.request({
        method: item.method || 'POST',
        url: item.endpoint,
      });
      const detail = formatActionResult(response.data);
      setLastActionResult({ title: item.title, detail });
      message.success(`${item.action_label || '维护动作'}已完成`);
      await fetchActions();
    } catch (error: any) {
      const detail = error.response?.data?.detail || '动作执行失败，请稍后重试或进入设置页处理。';
      setLastActionResult({ title: item.title, detail });
      message.error(detail);
    } finally {
      setRunningActionId(null);
    }
  };

  const groupedActions = useMemo(() => {
    const groups: Record<string, any[]> = {};
    for (const action of data.actions || []) {
      groups[action.group] = groups[action.group] || [];
      groups[action.group].push(action);
    }
    return groups;
  }, [data.actions]);

  const summary = data.summary || {};
  const hasActions = (data.actions || []).length > 0;

  return (
    <div style={{ maxWidth: 1280, margin: '0 auto' }}>
      <Card
        style={{
          borderRadius: 22,
          marginBottom: 18,
          overflow: 'hidden',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: '#fff',
        }}
        styles={{ body: { padding: 28 } }}
      >
        <Row justify="space-between" align="middle" gutter={[16, 16]}>
          <Col xs={24} md={16}>
            <Space size={14} align="center">
              <div style={{
                width: 58,
                height: 58,
                borderRadius: 18,
                background: 'rgba(255,255,255,0.18)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 28,
              }}>
                <ThunderboltOutlined />
              </div>
              <div>
                <Title level={2} style={{ color: '#fff', margin: 0 }}>行动中心</Title>
                <Text style={{ color: 'rgba(255,255,255,0.78)' }}>
                  把论文、研究方向、写作和项目空间的下一步集中到一个科研推进面板。
                </Text>
              </div>
            </Space>
          </Col>
          <Col xs={24} md={8}>
            <Row gutter={12}>
              <Col span={12}>
                <Card style={{ borderRadius: 14, background: 'rgba(255,255,255,0.16)', borderColor: 'rgba(255,255,255,0.22)' }} styles={{ body: { padding: 14 } }}>
                  <Statistic title={<span style={{ color: 'rgba(255,255,255,0.75)' }}>行动项</span>} value={summary.total || 0} valueStyle={{ color: '#fff' }} />
                </Card>
              </Col>
              <Col span={12}>
                <Card style={{ borderRadius: 14, background: 'rgba(255,255,255,0.16)', borderColor: 'rgba(255,255,255,0.22)' }} styles={{ body: { padding: 14 } }}>
                  <Statistic title={<span style={{ color: 'rgba(255,255,255,0.75)' }}>高优先级</span>} value={summary.high_priority || 0} valueStyle={{ color: '#fff' }} />
                </Card>
              </Col>
            </Row>
          </Col>
        </Row>
      </Card>

      <Alert
        type="info"
        showIcon
        style={{ borderRadius: 12, marginBottom: 18 }}
        message="行动中心目前是自动生成建议"
        description="它会从现有模块状态推断下一步。知识库维护类行动可以直接执行，其他行动会带你进入对应模块继续处理。"
      />
      {lastActionResult ? (
        <Alert
          type="success"
          showIcon
          closable
          onClose={() => setLastActionResult(null)}
          style={{ borderRadius: 12, marginBottom: 18 }}
          message={`${lastActionResult.title}：${lastActionResult.detail}`}
        />
      ) : null}

      <Spin spinning={loading}>
        {!hasActions && !loading ? (
          <Card style={{ borderRadius: 18 }}>
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description="暂时没有可推进的行动项"
            >
              <Button type="primary" onClick={() => navigate('/papers')}>去论文库开始</Button>
            </Empty>
          </Card>
        ) : (
          <Row gutter={[16, 16]}>
            {Object.entries(groupConfig).map(([group, config]) => {
              const actions = groupedActions[group] || [];
              return (
                <Col xs={24} lg={12} key={group}>
                  <Card
                    title={(
                      <Space>
                        <span style={{ color: config.color }}>{config.icon}</span>
                        {config.label}
                        <Tag color="default">{actions.length}</Tag>
                      </Space>
                    )}
                    style={{ borderRadius: 18, height: '100%' }}
                  >
                    {actions.length ? (
                      <List
                        dataSource={actions}
                        renderItem={(item: any) => {
                          const priority = priorityConfig[item.priority] || priorityConfig.low;
                          const isApiAction = item.action_type === 'api';
                          return (
                            <List.Item
                              actions={[
                                isApiAction && item.path ? (
                                  <Button key="details" type="link" onClick={() => navigate(item.path)}>
                                    查看位置
                                  </Button>
                                ) : null,
                                <Button
                                  key="go"
                                  type={isApiAction ? 'primary' : 'link'}
                                  size={isApiAction ? 'small' : 'middle'}
                                  loading={runningActionId === item.id}
                                  onClick={() => runAction(item)}
                                >
                                  {item.action_label || (isApiAction ? '执行' : '进入')} {!isApiAction ? <RightOutlined /> : null}
                                </Button>,
                              ].filter(Boolean)}
                            >
                              <List.Item.Meta
                                avatar={<CheckCircleOutlined style={{ color: config.color, fontSize: 20, marginTop: 4 }} />}
                                title={(
                                  <Space wrap>
                                    <Text strong>{item.title}</Text>
                                    <Tag color={priority.color}>{priority.label}</Tag>
                                    {item.requires_admin ? <Tag color="purple">管理员维护</Tag> : null}
                                  </Space>
                                )}
                                description={(
                                  <Space direction="vertical" size={4}>
                                    <Paragraph type="secondary" style={{ margin: 0 }}>{item.description}</Paragraph>
                                    <Text type="secondary" style={{ fontSize: 12 }}>来源：{item.source}</Text>
                                  </Space>
                                )}
                              />
                            </List.Item>
                          );
                        }}
                      />
                    ) : (
                      <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="这一组暂时没有建议" />
                    )}
                  </Card>
                </Col>
              );
            })}
          </Row>
        )}
      </Spin>
    </div>
  );
};

export default ActionCenterPage;
