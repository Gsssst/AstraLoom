import React, { useState, useEffect } from 'react';
import {
  Alert, Card, Button, Input, Typography, Space, message, Tabs,
  Descriptions, Divider, Tag, Statistic, Row, Col, Switch, Radio, Avatar,
  Progress, List, Empty, Segmented, Select,
} from 'antd';
import {
  UserOutlined, BellOutlined, SettingOutlined,
  SaveOutlined, LockOutlined, ApiOutlined, ExportOutlined,
  BarChartOutlined, TeamOutlined, BgColorsOutlined, SendOutlined,
  ReloadOutlined, SearchOutlined, DatabaseOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { getApiErrorDetails, getApiErrorMessage, type ApiErrorDetails } from '../services/apiError';
import { useThemeStore, THEME_PRESETS } from '../stores/useThemeStore';
import { useAuthStore, type User } from '../stores/useAuthStore';

const { Title, Text } = Typography;
const { TextArea } = Input;

const heroGradient = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
const cardStyle = { borderRadius: 14, border: '1px solid #f0f0f0' };
const inputStyle = { borderRadius: 10 };

const SettingsPage: React.FC = () => {
  const navigate = useNavigate();
  const isAuthenticated = !!localStorage.getItem('access_token');

  const [profile, setProfile] = useState<any>(null);
  const [email, setEmail] = useState('');
  const [saving, setSaving] = useState(false);
  const [oldPwd, setOldPwd] = useState('');
  const [newPwd, setNewPwd] = useState('');
  const [changingPwd, setChangingPwd] = useState(false);
  const [apiConfig, setApiConfig] = useState<any>(null);
  const [selectedApiProvider, setSelectedApiProvider] = useState('');
  const [selectedApiModel, setSelectedApiModel] = useState('');
  const [savingApiConfig, setSavingApiConfig] = useState(false);
  const [testingApiConfig, setTestingApiConfig] = useState(false);
  const [apiConfigTestResult, setApiConfigTestResult] = useState<any>(null);
  const [apiConfigTestError, setApiConfigTestError] = useState<ApiErrorDetails | null>(null);
  const [myUsage, setMyUsage] = useState<any>(null);
  const [allUsage, setAllUsage] = useState<any>(null);
  const [usageTab, setUsageTab] = useState<string>('my');
  const [subKeywords, setSubKeywords] = useState('');
  const [subEmail, setSubEmail] = useState(false);
  const [subPush, setSubPush] = useState(true);
  const [subSaving, setSubSaving] = useState(false);
  const [subTesting, setSubTesting] = useState(false);
  const [subLoaded, setSubLoaded] = useState(false);
  const [subEmailAvailable, setSubEmailAvailable] = useState(false);
  const [subLastSentAt, setSubLastSentAt] = useState<string | null>(null);
  const [subSendHour, setSubSendHour] = useState(8);
  const [subTestResult, setSubTestResult] = useState<any>(null);
  const [kbHealth, setKbHealth] = useState<any>(null);
  const [kbLoading, setKbLoading] = useState(false);
  const [kbAction, setKbAction] = useState<string | null>(null);
  const [kbQuery, setKbQuery] = useState('');
  const [kbDiagnostics, setKbDiagnostics] = useState<any>(null);
  const [kbDiagTab, setKbDiagTab] = useState<string>('hybrid');
  const [kbDiagLoading, setKbDiagLoading] = useState(false);
  const [kbRecommendations, setKbRecommendations] = useState<any[]>([]);
  const { current: currentTheme, setTheme, showThinking, setShowThinking } = useThemeStore();

  const syncProfileIdentity = (updates: Partial<User>) => {
    setProfile((c: any) => c ? { ...c, ...updates } : c);
    useAuthStore.getState().updateUser(updates);
  };

  useEffect(() => {
    if (!isAuthenticated) { navigate('/login'); return; }
    api.get('/settings/profile').then(res => { setProfile(res.data); setEmail(res.data.email); if (res.data.role === 'admin') api.get('/usage/all-stats').then(r => setAllUsage(r.data)).catch(() => {}); }).catch(error => message.error(getApiErrorMessage(error, { fallback: '个人资料加载失败' })));
    api.get('/settings/api-config').then(res => { setApiConfig(res.data); setSelectedApiProvider(res.data.provider); setSelectedApiModel(res.data.model); }).catch(error => message.error(getApiErrorMessage(error, { fallback: '模型配置加载失败' })));
    api.get('/usage/my-stats').then(res => setMyUsage(res.data)).catch(() => {});
    api.get('/notifications/subscription').then(res => { setSubKeywords((res.data.keywords || []).join(', ')); setSubEmail(res.data.email_enabled); setSubPush(res.data.push_enabled); setSubEmailAvailable(res.data.email_available); setSubLastSentAt(res.data.last_sent_at); setSubSendHour(res.data.send_hour ?? 8); setSubLoaded(true); }).catch(error => message.error(getApiErrorMessage(error, { fallback: '通知订阅加载失败' })));
  }, [isAuthenticated, navigate]);

  const fetchKbHealth = async () => {
    if (profile?.role !== 'admin') return;
    setKbLoading(true);
    try {
      const [healthRes, recommendationsRes] = await Promise.all([
        api.get('/papers/maintenance/health'),
        api.get('/papers/maintenance/recommendations'),
      ]);
      setKbHealth(healthRes.data);
      setKbRecommendations(recommendationsRes.data || []);
    } catch (e: any) {
      message.error(getApiErrorMessage(e, { fallback: '知识库状态读取失败' }));
    } finally {
      setKbLoading(false);
    }
  };

  useEffect(() => {
    if (profile?.role === 'admin') fetchKbHealth();
  }, [profile?.role]);

  const runKbAction = async (action: string, url: string) => {
    setKbAction(action);
    try {
      const res = await api.post(url);
      message.success(`维护完成：成功 ${res.data.success || 0}，失败 ${res.data.failed || 0}，跳过 ${res.data.skipped || 0}`);
      await fetchKbHealth();
    } catch (e: any) {
      message.error(getApiErrorMessage(e, { fallback: '维护操作失败' }));
    } finally {
      setKbAction(null);
    }
  };

  const runKbDiagnostics = async () => {
    if (!kbQuery.trim()) {
      message.warning('请输入要诊断的检索词');
      return;
    }
    setKbDiagLoading(true);
    try {
      const res = await api.get('/papers/maintenance/search-diagnostics', { params: { q: kbQuery.trim(), top_k: 5 } });
      setKbDiagnostics(res.data);
      setKbDiagTab('hybrid');
    } catch (e: any) {
      message.error(getApiErrorMessage(e, { fallback: '检索诊断失败' }));
    } finally {
      setKbDiagLoading(false);
    }
  };

  const subscriptionPayload = () => ({ keywords: subKeywords.split(/[,，]/).map(k => k.trim()).filter(Boolean), email_enabled: subEmail, push_enabled: subPush, frequency: 'daily', send_hour: subSendHour });
  const syncSubscription = (data: any) => { setSubKeywords((data.keywords || []).join(', ')); setSubEmail(data.email_enabled); setSubPush(data.push_enabled); setSubEmailAvailable(data.email_available); setSubLastSentAt(data.last_sent_at); setSubSendHour(data.send_hour ?? 8); };
  const handleSaveSub = async () => { setSubSaving(true); try { const r = await api.put('/notifications/subscription', subscriptionPayload()); syncSubscription(r.data); message.success('订阅已更新'); } catch (e: any) { message.error(getApiErrorMessage(e, { fallback: '订阅保存失败' })); } finally { setSubSaving(false); } };
  const handleTestSub = async () => {
    setSubTesting(true);
    setSubTestResult(null);
    try {
      const saved = await api.put('/notifications/subscription', subscriptionPayload());
      syncSubscription(saved.data);
      const r = await api.post('/notifications/subscription/test');
      setSubTestResult(r.data);
      setSubLastSentAt(r.data.sent_at || saved.data.last_sent_at);
      window.dispatchEvent(new Event('notifications:refresh'));
      message.success('测试推送已发送，请查看右上角通知铃铛');
    } catch (e: any) {
      message.error(getApiErrorMessage(e, { fallback: '测试推送失败' }));
    } finally {
      setSubTesting(false);
    }
  };
  const handleSaveProfile = async () => { setSaving(true); try { const r = await api.put('/settings/profile', { email }); syncProfileIdentity(r.data); message.success('已更新'); } catch (error) { message.error(getApiErrorMessage(error, { fallback: '资料保存失败' })); } finally { setSaving(false); } };
  const handleChangePwd = async () => { if (!oldPwd || !newPwd) { message.warning('请填写完整'); return; } if (newPwd.length < 6) { message.warning('新密码至少6位'); return; } setChangingPwd(true); try { await api.post('/settings/change-password', { old_password: oldPwd, new_password: newPwd }); message.success('密码已修改'); setOldPwd(''); setNewPwd(''); } catch (e: any) { message.error(getApiErrorMessage(e, { fallback: '密码修改失败' })); } finally { setChangingPwd(false); } };
  const handleExport = async (fmt: string) => { try { const r = await api.post('/writing/export', { format: fmt }); const blob = new Blob([fmt === 'csv' ? '﻿' + r.data.data : r.data.data], { type: fmt === 'csv' ? 'text/csv;charset=utf-8' : 'text/plain' }); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = `papers.${fmt}`; a.click(); URL.revokeObjectURL(url); message.success('导出成功'); } catch (error) { message.error(getApiErrorMessage(error, { fallback: '导出失败' })); } };
  const handleSaveApiConfig = async () => {
    if (!selectedApiProvider) {
      message.warning('请选择模型');
      return;
    }
    setSavingApiConfig(true);
    try {
      const r = await api.put('/settings/api-config', { provider: selectedApiProvider, model: selectedApiModel });
      setApiConfig(r.data);
      setSelectedApiProvider(r.data.provider);
      setSelectedApiModel(r.data.model);
      setApiConfigTestResult(null);
      setApiConfigTestError(null);
      message.success('模型配置已切换');
    } catch (e: any) {
      message.error(getApiErrorMessage(e, { fallback: '模型配置保存失败' }));
    } finally {
      setSavingApiConfig(false);
    }
  };
  const handleTestApiConfig = async () => {
    setTestingApiConfig(true);
    setApiConfigTestResult(null);
    setApiConfigTestError(null);
    try {
      const r = await api.post('/settings/api-config/test');
      setApiConfigTestResult(r.data);
      message.success(`模型连接测试成功：${r.data.latency_ms}ms`);
    } catch (e: any) {
      const details = getApiErrorDetails(e, { fallback: '模型连接测试失败' });
      setApiConfigTestError(details);
      message.warning(details.message);
    } finally {
      setTestingApiConfig(false);
    }
  };

  // ══════════════════════════════════════
  //  Tab: Theme
  // ══════════════════════════════════════
  const themeTab = (
    <div>
      <Radio.Group value={currentTheme.id} onChange={e => setTheme(e.target.value)} style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
        {THEME_PRESETS.map(t => {
          const isActive = currentTheme.id === t.id;
          return (
            <Radio.Button key={t.id} value={t.id} style={{ height: 'auto', padding: '20px 24px', borderRadius: 14, border: isActive ? `2px solid ${t.token.colorPrimary}` : '1px solid #f0f0f0', background: isActive ? `${t.token.colorPrimary}08` : '#fff', transition: 'all 0.25s', cursor: 'pointer', minWidth: 140 }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 36, marginBottom: 10 }}>{t.icon}</div>
                <div style={{ fontWeight: 700, marginBottom: 6, fontSize: 14 }}>{t.name}</div>
                <div style={{ display: 'flex', gap: 6, justifyContent: 'center' }}>
                  <div style={{ width: 20, height: 20, borderRadius: 6, background: t.token.colorPrimary }} />
                  {t.token.colorBgLayout && <div style={{ width: 20, height: 20, borderRadius: 6, background: t.token.colorBgLayout, border: '1px solid #e5e5e5' }} />}
                </div>
                {isActive && <div style={{ marginTop: 8, color: t.token.colorPrimary, fontWeight: 600, fontSize: 12 }}>✓ 当前</div>}
              </div>
            </Radio.Button>
          );
        })}
      </Radio.Group>

      <Divider style={{ margin: '20px 0' }} />
      <Card style={{ ...cardStyle, maxWidth: 500 }} styles={{ body: { padding: '16px 20px' } }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <Text strong style={{ fontSize: 14 }}>💭 显示 AI 思考过程</Text>
            <br /><Text type="secondary" style={{ fontSize: 12 }}>开启后展示支持模型的推理过程（可折叠）</Text>
          </div>
          <Switch checked={showThinking} onChange={setShowThinking} />
        </div>
      </Card>
    </div>
  );

  // ══════════════════════════════════════
  //  Tab: Profile
  // ══════════════════════════════════════
  const profileTab = profile && (
    <div style={{ maxWidth: 520 }}>
      {/* Avatar card */}
      <Card style={{ ...cardStyle, marginBottom: 20 }} styles={{ body: { padding: 24 } }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
          <div style={{ position: 'relative', cursor: 'pointer' }} onClick={() => { const el = document.createElement('input'); el.type = 'file'; el.accept = 'image/*'; el.onchange = async (e: any) => { const f = e.target.files?.[0]; if (!f) return; const fd = new FormData(); fd.append('file', f); try { const r = await api.post('/settings/upload-avatar', fd, { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 30000 }); syncProfileIdentity({ avatar: r.data.avatar }); message.success('头像已更新'); } catch (error) { message.error(getApiErrorMessage(error, { fallback: '头像上传失败' })); } }; el.click(); }}>
            <Avatar size={72} src={profile.avatar} icon={<UserOutlined />} style={{ background: 'linear-gradient(135deg, #667eea, #764ba2)', fontSize: 28 }} />
            <div style={{ position: 'absolute', bottom: 0, right: 0, background: '#667eea', borderRadius: '50%', width: 24, height: 24, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 14, border: '2px solid #fff' }}>+</div>
          </div>
          <div>
            <Text strong style={{ fontSize: 18 }}>{profile.display_name || profile.username}</Text>
            <br /><Text type="secondary">{profile.email}</Text>
            <br /><Tag color={profile.role === 'admin' ? 'red' : 'blue'} style={{ borderRadius: 6, marginTop: 4 }}>{profile.role === 'admin' ? '管理员' : '普通用户'}</Tag>
          </div>
        </div>
      </Card>

      {/* Display name + email */}
      <Card style={cardStyle} title={<span style={{ fontWeight: 600 }}>📝 基本信息</span>} styles={{ body: { padding: '12px 20px 20px' } }}>
        <Space direction="vertical" style={{ width: '100%' }} size={12}>
          <div>
            <Text strong style={{ fontSize: 13 }}>显示名称</Text>
            <Space.Compact style={{ width: '100%', marginTop: 4 }}>
              <Input style={inputStyle} placeholder="显示名称" value={profile.display_name || ''} onChange={e => setProfile({ ...profile, display_name: e.target.value })} />
              <Button type="primary" icon={<SaveOutlined />} loading={saving} onClick={async () => { setSaving(true); try { const r = await api.put('/settings/profile', { display_name: profile.display_name }); syncProfileIdentity(r.data); message.success('已更新'); } catch (error) { message.error(getApiErrorMessage(error, { fallback: '显示名称保存失败' })); } finally { setSaving(false); } }} style={{ borderRadius: '0 10px 10px 0' }}>保存</Button>
            </Space.Compact>
          </div>
          <div>
            <Text strong style={{ fontSize: 13 }}>邮箱</Text>
            <Space.Compact style={{ width: '100%', marginTop: 4 }}>
              <Input style={inputStyle} value={email} onChange={e => setEmail(e.target.value)} />
              <Button type="primary" icon={<SaveOutlined />} loading={saving} onClick={handleSaveProfile} style={{ borderRadius: '0 10px 10px 0' }}>保存</Button>
            </Space.Compact>
          </div>
        </Space>
      </Card>

      {/* Password */}
      <Card style={{ ...cardStyle, marginTop: 16 }} title={<span style={{ fontWeight: 600 }}>🔒 修改密码</span>} styles={{ body: { padding: '12px 20px 20px' } }}>
        <Space direction="vertical" style={{ width: '100%' }} size={10}>
          <Input.Password style={inputStyle} prefix={<LockOutlined />} placeholder="原密码" value={oldPwd} onChange={e => setOldPwd(e.target.value)} />
          <Input.Password style={inputStyle} prefix={<LockOutlined />} placeholder="新密码（至少6位）" value={newPwd} onChange={e => setNewPwd(e.target.value)} />
          <Button type="primary" icon={<LockOutlined />} loading={changingPwd} onClick={handleChangePwd} block style={{ borderRadius: 10, height: 40 }}>修改密码</Button>
        </Space>
      </Card>
    </div>
  );

  // ══════════════════════════════════════
  //  Tab: API
  // ══════════════════════════════════════
  const selectedApiOption = (apiConfig?.options || []).find((item: any) => item.provider === selectedApiProvider);
  const apiTab = apiConfig && (
    <Card style={{ ...cardStyle, maxWidth: 680 }} styles={{ body: { padding: 24 } }}>
      <Space direction="vertical" style={{ width: '100%' }} size={16}>
        <Descriptions column={1} bordered size="small" labelStyle={{ fontWeight: 600 }}>
          <Descriptions.Item label="当前提供商"><Tag color="purple" style={{ borderRadius: 6 }}>{apiConfig.provider}</Tag></Descriptions.Item>
          <Descriptions.Item label="当前模型"><Text code>{apiConfig.model}</Text></Descriptions.Item>
          <Descriptions.Item label="API 地址"><Text code style={{ fontSize: 12 }}>{apiConfig.api_base || '未配置'}</Text></Descriptions.Item>
          <Descriptions.Item label="API Key">
            <Tag color={apiConfig.has_api_key ? 'green' : 'red'} style={{ borderRadius: 6 }}>{apiConfig.has_api_key ? '已配置' : '未配置'}</Tag>
          </Descriptions.Item>
        </Descriptions>

        <Divider style={{ margin: 0 }} />

        <div>
          <Text strong>模型选择</Text>
          <Select
            value={selectedApiProvider}
            onChange={(provider) => {
              const option = (apiConfig.options || []).find((item: any) => item.provider === provider);
              setSelectedApiProvider(provider);
              setSelectedApiModel(option?.model || '');
            }}
            options={(apiConfig.options || []).map((item: any) => ({
              value: item.provider,
              label: `${item.label} · ${item.model}${item.configured ? '' : ' · 未配置'}`,
              disabled: !item.configured,
            }))}
            style={{ width: '100%', marginTop: 8 }}
          />
        </div>

        {selectedApiOption && (
          <Card size="small" style={{ borderRadius: 12, background: '#fafafa' }}>
            <Space direction="vertical" style={{ width: '100%' }} size={8}>
              <Space size={8} wrap>
                <Tag color={selectedApiOption.configured ? 'green' : 'orange'} style={{ borderRadius: 6 }}>
                  {selectedApiOption.configured ? '服务端已配置' : '等待服务端配置'}
                </Tag>
                <Tag color={selectedApiOption.supports_thinking ? 'blue' : 'default'} style={{ borderRadius: 6 }}>
                  {selectedApiOption.supports_thinking ? '支持思考流' : '普通内容流'}
                </Tag>
              </Space>
              <Text type="secondary" style={{ fontSize: 12 }}>
                Base URL: <Text code>{selectedApiOption.api_base || selectedApiOption.api_base_env}</Text>
              </Text>
              <Text type="secondary" style={{ fontSize: 12 }}>
                API Key: <Text code>{selectedApiOption.api_key_env}</Text> · Model: <Text code>{selectedApiOption.model_env}</Text>
              </Text>
            </Space>
          </Card>
        )}

        <Space wrap>
          <Button
            type="primary"
            icon={<SaveOutlined />}
            loading={savingApiConfig}
            disabled={profile?.role !== 'admin' || !selectedApiOption?.configured}
            onClick={handleSaveApiConfig}
            style={{ borderRadius: 10, width: 160 }}
          >
            保存模型
          </Button>
          <Button
            icon={<ApiOutlined />}
            loading={testingApiConfig}
            disabled={profile?.role !== 'admin' || !apiConfig.configured}
            onClick={handleTestApiConfig}
            style={{ borderRadius: 10 }}
          >
            测试当前模型
          </Button>
        </Space>

        {apiConfigTestResult && (
          <Alert
            type={apiConfigTestResult.ok ? 'success' : 'warning'}
            showIcon
            style={{ borderRadius: 10 }}
            message={`连接测试完成：${apiConfigTestResult.provider} / ${apiConfigTestResult.model}`}
            description={`耗时 ${apiConfigTestResult.latency_ms}ms；回复预览：${apiConfigTestResult.preview || '无内容'}`}
          />
        )}

        {apiConfigTestError && (
          <Alert
            type={apiConfigTestError.severity === 'error' ? 'error' : 'warning'}
            showIcon
            style={{ borderRadius: 10 }}
            message={`连接测试失败：${apiConfigTestError.message}`}
            description={
              <Space direction="vertical" size={6}>
                <Text>{apiConfigTestError.recovery}</Text>
                <Space size={6} wrap>
                  <Tag color="orange">{apiConfigTestError.category}</Tag>
                  <Tag color={apiConfigTestError.retryable ? 'blue' : 'default'}>
                    {apiConfigTestError.retryable ? '可重试' : '需先处理配置'}
                  </Tag>
                  {apiConfigTestError.status && <Tag>HTTP {apiConfigTestError.status}</Tag>}
                </Space>
              </Space>
            }
          />
        )}

        <Alert
          type="info"
          showIcon
          style={{ borderRadius: 10 }}
          message="API Key 和 Base URL 只从服务器环境变量读取"
          description="GPT-5.5 兼容接口请在 .env 中配置 OPENAI_COMPATIBLE_API_BASE、OPENAI_COMPATIBLE_API_KEY 和 OPENAI_COMPATIBLE_MODEL。要让重启后仍默认使用它，再设置 LLM_PROVIDER=openai-compatible。"
        />
      </Space>
    </Card>
  );

  // ══════════════════════════════════════
  //  Tab: Data
  // ══════════════════════════════════════
  const renderDiagnosticList = (items: any[] = []) => (
    items.length ? (
      <List
        size="small"
        dataSource={items}
        renderItem={(item: any, index) => (
          <List.Item style={{ padding: '10px 0' }}>
            <div style={{ width: '100%' }}>
              <Space size={8} wrap>
                <Tag color="blue" style={{ borderRadius: 8 }}>{index + 1}</Tag>
                <Text strong>{item.title}</Text>
                <Tag style={{ borderRadius: 8 }}>score {item.score}</Tag>
                {item.year && <Tag color="geekblue" style={{ borderRadius: 8 }}>{item.year}</Tag>}
                {item.source && <Tag color="purple" style={{ borderRadius: 8 }}>{item.source}</Tag>}
              </Space>
              <div style={{ marginTop: 6 }}>
                <Space size={6} wrap>
                  <Tag color={item.has_full_text ? 'green' : 'default'} style={{ borderRadius: 8 }}>
                    {item.has_full_text ? '有全文' : '缺全文'}
                  </Tag>
                  <Tag color={item.has_embedding ? 'green' : 'default'} style={{ borderRadius: 8 }}>
                    {item.has_embedding ? '有向量' : '缺向量'}
                  </Tag>
                  {(item.match_sources || []).map((source: string) => (
                    <Tag key={source} color="cyan" style={{ borderRadius: 8 }}>命中 {source}</Tag>
                  ))}
                </Space>
              </div>
            </div>
          </List.Item>
        )}
      />
    ) : <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="没有诊断结果" />
  );

  const recommendationColor = (severity: string) => (
    severity === 'high' ? 'red' : severity === 'medium' ? 'orange' : 'blue'
  );

  const dataTab = (
    <div style={{ maxWidth: 760 }}>
      <Card style={cardStyle} title={<span style={{ fontWeight: 600 }}>📥 导出论文数据</span>} styles={{ body: { padding: '16px 20px' } }}>
        <Space size={12}>
          <Button size="large" icon={<ExportOutlined />} onClick={() => handleExport('bib')} style={{ borderRadius: 10, height: 44, fontWeight: 500 }}>导出 BibTeX</Button>
          <Button size="large" icon={<ExportOutlined />} onClick={() => handleExport('csv')} style={{ borderRadius: 10, height: 44, fontWeight: 500 }}>导出 CSV</Button>
        </Space>
      </Card>

      <Card style={{ ...cardStyle, marginTop: 16 }} title={<span style={{ fontWeight: 600 }}>📊 知识库统计</span>} styles={{ body: { padding: '16px 20px' } }}>
        <Row gutter={16}>
          <Col span={12}><Card size="small" style={{ borderRadius: 12, border: '1px solid #f0f0f0' }}><Statistic title="数据库版本" value={apiConfig?.model?.split('-').pop() || '...'} prefix={<ApiOutlined />} /></Card></Col>
          <Col span={12}><Card size="small" style={{ borderRadius: 12, border: '1px solid #f0f0f0' }}><Statistic title="环境" value={apiConfig?.has_api_key ? '✅ 生产就绪' : '⚠️ 待配置'} valueStyle={{ color: apiConfig?.has_api_key ? '#52c41a' : '#faad14' }} /></Card></Col>
        </Row>
      </Card>

      {profile?.role === 'admin' ? (
        <Card
          style={{ ...cardStyle, marginTop: 16 }}
          title={<span style={{ fontWeight: 600 }}><DatabaseOutlined /> 知识库检索维护</span>}
          extra={<Button size="small" icon={<ReloadOutlined />} loading={kbLoading} onClick={fetchKbHealth}>刷新</Button>}
          styles={{ body: { padding: '16px 20px' } }}
        >
          <Alert
            type="info"
            showIcon
            style={{ borderRadius: 10, marginBottom: 16 }}
            message="这里负责维护论文库能不能被检索到"
            description="全文覆盖影响论文页 AI 问答，向量覆盖影响语义检索，BM25 索引影响关键词检索。库变大之后，先看这里就能知道是不是索引欠账。"
          />
          {kbHealth ? (
            <>
              <Row gutter={[12, 12]}>
                <Col span={8}>
                  <Card size="small" style={{ borderRadius: 12 }}>
                    <Statistic title="论文总数" value={kbHealth.total_papers} />
                  </Card>
                </Col>
                <Col span={8}>
                  <Card size="small" style={{ borderRadius: 12 }}>
                    <Statistic title="全文覆盖" value={Math.round((kbHealth.full_text_coverage || 0) * 100)} suffix="%" />
                    <Progress percent={Math.round((kbHealth.full_text_coverage || 0) * 100)} size="small" showInfo={false} />
                  </Card>
                </Col>
                <Col span={8}>
                  <Card size="small" style={{ borderRadius: 12 }}>
                    <Statistic title="向量覆盖" value={Math.round((kbHealth.embedding_coverage || 0) * 100)} suffix="%" />
                    <Progress percent={Math.round((kbHealth.embedding_coverage || 0) * 100)} size="small" showInfo={false} />
                  </Card>
                </Col>
              </Row>

              <Space size={8} wrap style={{ marginTop: 14 }}>
                <Tag color={kbHealth.bm25_index?.ready ? 'green' : 'orange'} style={{ borderRadius: 8 }}>
                  BM25：{kbHealth.bm25_index?.ready ? `已索引 ${kbHealth.bm25_index.indexed_papers} 篇` : '尚未构建'}
                </Tag>
                <Tag style={{ borderRadius: 8 }}>缺全文 {kbHealth.missing_full_text}</Tag>
                <Tag style={{ borderRadius: 8 }}>缺向量 {kbHealth.missing_embeddings}</Tag>
                <Tag style={{ borderRadius: 8 }}>arXiv 论文 {kbHealth.arxiv_papers}</Tag>
              </Space>

              <Space style={{ width: '100%', marginTop: 16 }} wrap>
                <Button icon={<ReloadOutlined />} loading={kbAction === 'bm25'} onClick={() => runKbAction('bm25', '/papers/maintenance/rebuild-bm25')} style={{ borderRadius: 10 }}>
                  重建 BM25
                </Button>
                <Button loading={kbAction === 'embeddings'} onClick={() => runKbAction('embeddings', '/papers/maintenance/backfill-embeddings?limit=20')} style={{ borderRadius: 10 }}>
                  补 20 篇向量
                </Button>
                <Button loading={kbAction === 'fulltext'} onClick={() => runKbAction('fulltext', '/papers/maintenance/backfill-full-text?limit=5')} style={{ borderRadius: 10 }}>
                  补 5 篇全文
                </Button>
              </Space>

              {kbRecommendations.length > 0 && (
                <>
                  <Divider style={{ margin: '18px 0' }} />
                  <Text strong>系统建议优先维护</Text>
                  <Row gutter={[12, 12]} style={{ marginTop: 10 }}>
                    {kbRecommendations.map((rec: any) => (
                      <Col span={8} key={rec.id}>
                        <Card size="small" style={{ borderRadius: 12, height: '100%' }}>
                          <Space direction="vertical" size={8} style={{ width: '100%' }}>
                            <Space size={6} wrap>
                              <Tag color={recommendationColor(rec.severity)} style={{ borderRadius: 8 }}>{rec.severity}</Tag>
                              <Text strong>{rec.title}</Text>
                            </Space>
                            <Text type="secondary" style={{ fontSize: 12 }}>{rec.reason}</Text>
                            {rec.sample_papers?.length > 0 && (
                              <div>
                                {rec.sample_papers.slice(0, 2).map((paper: any) => (
                                  <Tag key={paper.id} style={{ borderRadius: 8, marginTop: 4 }}>{paper.title?.slice(0, 18)}{paper.title?.length > 18 ? '...' : ''}</Tag>
                                ))}
                              </div>
                            )}
                            <Button size="small" type="primary" loading={kbAction === rec.id} onClick={() => runKbAction(rec.id, rec.action_endpoint)} style={{ borderRadius: 8 }}>
                              {rec.action_label}
                            </Button>
                          </Space>
                        </Card>
                      </Col>
                    ))}
                  </Row>
                </>
              )}

              <Divider style={{ margin: '18px 0' }} />
              <Row gutter={16}>
                <Col span={12}>
                  <Text strong>缺全文样本</Text>
                  {renderDiagnosticList((kbHealth.missing_full_text_samples || []).map((p: any) => ({ ...p, score: '-', has_full_text: false, has_embedding: true })))}
                </Col>
                <Col span={12}>
                  <Text strong>缺向量样本</Text>
                  {renderDiagnosticList((kbHealth.missing_embedding_samples || []).map((p: any) => ({ ...p, score: '-', has_full_text: true, has_embedding: false })))}
                </Col>
              </Row>

              <Divider style={{ margin: '18px 0' }} />
              <Text strong>检索诊断</Text>
              <Space.Compact style={{ width: '100%', marginTop: 8 }}>
                <Input value={kbQuery} onChange={e => setKbQuery(e.target.value)} onPressEnter={runKbDiagnostics} placeholder="例如：video grounding 或 introduction token pruning" />
                <Button type="primary" icon={<SearchOutlined />} loading={kbDiagLoading} onClick={runKbDiagnostics}>诊断</Button>
              </Space.Compact>
              {kbDiagnostics && (
                <div style={{ marginTop: 14 }}>
                  <Alert
                    type={kbDiagnostics.hybrid?.length ? 'success' : 'warning'}
                    showIcon
                    style={{ borderRadius: 10, marginBottom: 12 }}
                    message={kbDiagnostics.summary}
                    description={kbDiagnostics.query_terms?.length ? `标准化查询词：${kbDiagnostics.query_terms.join('、')}` : '没有提取到稳定查询词'}
                  />
                  <Segmented
                    value={kbDiagTab}
                    onChange={value => setKbDiagTab(String(value))}
                    options={[
                      { label: `Hybrid (${kbDiagnostics.hybrid?.length || 0})`, value: 'hybrid' },
                      { label: `BM25 (${kbDiagnostics.bm25?.length || 0})`, value: 'bm25' },
                      { label: `Dense (${kbDiagnostics.dense?.length || 0})`, value: 'dense' },
                    ]}
                  />
                  <div style={{ marginTop: 12 }}>
                    {renderDiagnosticList(kbDiagnostics[kbDiagTab] || [])}
                  </div>
                  {kbDiagnostics.branch_explanations?.[kbDiagTab]?.length > 0 && (
                    <Alert
                      type="info"
                      showIcon
                      style={{ marginTop: 12, borderRadius: 10 }}
                      message={`${kbDiagTab.toUpperCase()} 分支解释`}
                      description={
                        <ul style={{ margin: '4px 0 0 18px', padding: 0 }}>
                          {kbDiagnostics.branch_explanations[kbDiagTab].map((note: string, index: number) => <li key={index}>{note}</li>)}
                        </ul>
                      }
                    />
                  )}
                  {kbDiagnostics.recommended_actions?.length > 0 && (
                    <Alert
                      type="warning"
                      showIcon
                      style={{ marginTop: 12, borderRadius: 10 }}
                      message="这次诊断建议"
                      description={kbDiagnostics.recommended_actions.map((rec: any) => rec.title).join('、')}
                    />
                  )}
                  {kbDiagnostics.errors && Object.keys(kbDiagnostics.errors).length > 0 && (
                    <Alert type="warning" showIcon style={{ marginTop: 12, borderRadius: 10 }} message="部分检索分支失败" description={JSON.stringify(kbDiagnostics.errors)} />
                  )}
                </div>
              )}
            </>
          ) : (
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={kbLoading ? '正在读取知识库状态...' : '暂无知识库状态'} />
          )}
        </Card>
      ) : (
        <Alert type="warning" showIcon style={{ marginTop: 16, borderRadius: 10 }} message="知识库维护仅管理员可见" />
      )}
    </div>
  );

  // ══════════════════════════════════════
  //  Tab: Subscription
  // ══════════════════════════════════════
  const subTab = subLoaded && (
    <Card style={{ ...cardStyle, maxWidth: 680 }} styles={{ body: { padding: 24 } }}>
      <Space size={4} style={{ marginBottom: 16 }}>
        <BellOutlined style={{ color: '#faad14', fontSize: 18 }} />
        <Title level={5} style={{ margin: 0 }}>arXiv 每日推送</Title>
      </Space>
      <Text type="secondary">设置关注关键词和每日推送时间。系统会按北京时间自动检索最新论文，并通过站内通知发送摘要。</Text>
      <Alert
        type="info"
        showIcon
        style={{ marginTop: 16, borderRadius: 10 }}
        message="站内推送已接入实时测试"
        description={subLastSentAt ? `最近一次推送：${new Date(subLastSentAt).toLocaleString()}` : '保存关键词后，可以点击“保存并测试推送”立即验证通知链路。'}
      />
      <div style={{ marginTop: 20 }}>
        <Text strong style={{ fontSize: 13, display: 'block', marginBottom: 6 }}>关键词（逗号分隔）</Text>
        <TextArea style={{ ...inputStyle, marginBottom: 20 }} rows={3} placeholder="例如：large language model, RLHF, multimodal alignment" value={subKeywords} onChange={e => setSubKeywords(e.target.value)} />
        <Text strong style={{ fontSize: 13, display: 'block', marginBottom: 6 }}>每日推送时间（北京时间）</Text>
        <Select
          value={subSendHour}
          onChange={setSubSendHour}
          style={{ width: 180, marginBottom: 20 }}
          options={Array.from({ length: 24 }, (_, hour) => ({ value: hour, label: `${String(hour).padStart(2, '0')}:00` }))}
        />
        <Space direction="vertical" size={12}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <Switch checked={subPush} onChange={setSubPush} />
            <span>🔔 站内推送通知</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <Switch checked={subEmail} onChange={setSubEmail} disabled={!subEmailAvailable} />
            <span>📧 邮箱推送</span>
            {!subEmailAvailable && <Tag color="default">待配置邮件服务</Tag>}
          </div>
        </Space>
        {subTestResult && (
          <Alert
            type={subTestResult.paper_count > 0 ? 'success' : 'warning'}
            showIcon
            style={{ marginTop: 20, borderRadius: 10 }}
            message={subTestResult.message}
            description={`关键词：${(subTestResult.keywords || []).join('、')}`}
          />
        )}
        <Space style={{ width: '100%', marginTop: 24 }} wrap>
          <Button icon={<SaveOutlined />} loading={subSaving} onClick={handleSaveSub} style={{ borderRadius: 10, height: 40 }}>保存订阅设置</Button>
          <Button type="primary" icon={<SendOutlined />} loading={subTesting} onClick={handleTestSub} style={{ borderRadius: 10, height: 40 }}>保存并测试推送</Button>
        </Space>
      </div>
    </Card>
  );

  // ══════════════════════════════════════
  //  Tab: Usage
  // ══════════════════════════════════════
  const usageTabContent = myUsage && (
    <div style={{ maxWidth: 760 }}>
      <Tabs size="small" activeKey={usageTab} onChange={setUsageTab}
        items={[
          {
            key: 'my', label: <span><UserOutlined /> 我的用量</span>,
            children: (
              <Row gutter={[12, 12]}>
                {[
                  { title: '总调用次数', value: myUsage.total_calls, suffix: '次' },
                  { title: '总 Token', value: myUsage.total_tokens?.toLocaleString(), suffix: '' },
                  { title: '今日 Token', value: myUsage.today_tokens?.toLocaleString(), suffix: '', color: '#1677ff' },
                  { title: '本月 Token', value: myUsage.month_tokens?.toLocaleString(), suffix: '' },
                  { title: '输入 Token', value: myUsage.total_prompt_tokens?.toLocaleString(), suffix: '' },
                  { title: '输出 Token', value: myUsage.total_completion_tokens?.toLocaleString(), suffix: '' },
                  { title: '估算费用 (¥)', value: myUsage.estimated_cost?.toFixed(4), suffix: '', color: '#cf1322', span: 12 },
                  { title: '估算费用 (＄)', value: (myUsage.estimated_cost / 7.2)?.toFixed(4), suffix: '', color: '#cf1322', span: 12 },
                ].map((s, i) => (
                  <Col span={s.span || 8} key={i}>
                    <Card size="small" hoverable style={{ borderRadius: 12, border: '1px solid #f0f0f0', textAlign: 'center' }}>
                      <Statistic title={s.title} value={s.value} suffix={s.suffix} valueStyle={{ color: s.color, fontSize: 22, fontWeight: 700 }} />
                    </Card>
                  </Col>
                ))}
              </Row>
            ),
          },
          allUsage && {
            key: 'all', label: <span><TeamOutlined /> 全部账号</span>,
            children: (
              <div>
                <Row gutter={[12, 12]} style={{ marginBottom: 16 }}>
                  <Col span={8}><Card size="small" style={{ borderRadius: 12, textAlign: 'center' }}><Statistic title="总 Token" value={allUsage.grand_total_tokens?.toLocaleString()} valueStyle={{ fontSize: 22, fontWeight: 700 }} /></Card></Col>
                  <Col span={8}><Card size="small" style={{ borderRadius: 12, textAlign: 'center' }}><Statistic title="总费用 (¥)" value={allUsage.grand_total_cost?.toFixed(4)} precision={4} valueStyle={{ color: '#cf1322', fontSize: 22, fontWeight: 700 }} /></Card></Col>
                  <Col span={8}><Card size="small" style={{ borderRadius: 12, textAlign: 'center' }}><Statistic title="账号数" value={allUsage.users?.length} valueStyle={{ fontSize: 22, fontWeight: 700 }} /></Card></Col>
                </Row>
                {allUsage.users?.map((u: any, i: number) => (
                  <Card key={i} size="small" hoverable style={{ marginBottom: 8, borderRadius: 12 }}>
                    <Row align="middle" justify="space-between">
                      <Col><Space><UserOutlined style={{ color: '#667eea' }} /><Text strong>{u.username}</Text>{u.user_id && <Tag style={{ borderRadius: 6 }}>{u.user_id.slice(0, 8)}...</Tag>}</Space></Col>
                      <Col><Space size={6} wrap>
                        <Tag color="blue" style={{ borderRadius: 6 }}>{u.total_tokens?.toLocaleString()} tokens</Tag>
                        <Tag color="orange" style={{ borderRadius: 6 }}>{u.total_calls} 次</Tag>
                        <Tag color="red" style={{ borderRadius: 6 }}>¥{u.estimated_cost?.toFixed(4)}</Tag>
                      </Space></Col>
                    </Row>
                  </Card>
                ))}
              </div>
            ),
          },
        ].filter(Boolean) as any}
      />
    </div>
  );

  const tabs = [
    { key: 'profile', label: <span><UserOutlined /> 个人资料</span>, children: profileTab },
    { key: 'theme', label: <span><BgColorsOutlined /> 主题</span>, children: themeTab },
    { key: 'api', label: <span><ApiOutlined /> API</span>, children: apiTab },
    { key: 'data', label: <span><ExportOutlined /> 数据</span>, children: dataTab },
    { key: 'subscription', label: <span><BellOutlined /> 推送</span>, children: subTab },
    { key: 'usage', label: <span><BarChartOutlined /> 用量</span>, children: usageTabContent },
  ];

  return (
    <div style={{ maxWidth: 860, margin: '0 auto' }}>
      {/* Hero */}
      <div style={{ background: heroGradient, borderRadius: 16, padding: '24px 32px', marginBottom: 24, color: '#fff', position: 'relative', overflow: 'hidden' }}>
        <div style={{ position: 'absolute', right: -10, top: -25, fontSize: 120, opacity: 0.08 }}>⚙️</div>
        <Space size={12}>
          <div style={{ width: 48, height: 48, borderRadius: 14, background: 'rgba(255,255,255,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 24 }}><SettingOutlined /></div>
          <div>
            <Title level={3} style={{ color: '#fff', margin: 0 }}>系统设置</Title>
            <Text style={{ color: 'rgba(255,255,255,0.75)', fontSize: 13 }}>主题配色 · 个人资料 · API 配置 · 数据管理 · Token 用量</Text>
          </div>
        </Space>
      </div>

      <Tabs activeKey={undefined} defaultActiveKey="profile" items={tabs}
        style={{ '--ant-primary-color': '#667eea' } as any}
        tabBarStyle={{ marginBottom: 20 }}
      />
    </div>
  );
};

export default SettingsPage;
