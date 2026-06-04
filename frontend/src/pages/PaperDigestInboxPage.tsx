import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Alert, Badge, Button, Card, Col, Empty, List, Row, Space, Spin, Tag, Typography, message,
} from 'antd';
import {
  ArrowLeftOutlined, BellOutlined, CalendarOutlined, CheckCircleOutlined,
  ClockCircleOutlined, FilePdfOutlined, ImportOutlined, LikeOutlined,
  LinkOutlined, PlayCircleOutlined, ReadOutlined, StopOutlined, UserOutlined,
} from '@ant-design/icons';
import api from '../services/api';
import Markdown from '../components/Markdown';

const { Text, Title, Paragraph } = Typography;
const heroGradient = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';

interface DigestPaper {
  title: string;
  arxiv_id?: string | null;
  authors?: string[];
  year?: number | null;
  abstract_snippet?: string | null;
  published_at?: string | null;
  source?: string | null;
  source_url?: string | null;
  pdf_url?: string | null;
  remote_id?: string | null;
  remote_ingest_token?: string | null;
  canonical_key?: string | null;
  recommendation_score?: number | null;
  recommendation_reasons?: string[];
}

interface DigestNotification {
  id: string;
  title: string;
  content?: string | null;
  is_read: boolean;
  created_at?: string | null;
  metadata?: {
    papers?: DigestPaper[];
    keywords?: string[];
    is_test?: boolean;
    paper_count?: number;
    feedback?: Record<string, { action?: string } | string>;
  } | null;
}

const PaperDigestInboxPage: React.FC = () => {
  const navigate = useNavigate();
  const [digests, setDigests] = useState<DigestNotification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [markingRead, setMarkingRead] = useState(false);
  const [ingestingIds, setIngestingIds] = useState<Set<string>>(new Set());
  const [ingestedIds, setIngestedIds] = useState<Set<string>>(new Set());
  const [localPaperIds, setLocalPaperIds] = useState<Record<string, string>>({});
  const [readingLoopStatus, setReadingLoopStatus] = useState<Record<string, 'unread' | 'reading'>>({});
  const [feedbackLoadingKeys, setFeedbackLoadingKeys] = useState<Set<string>>(new Set());

  const loadDigests = useCallback(async () => {
    setLoading(true);
    try {
      const [digestResponse, unreadResponse] = await Promise.all([
        api.get('/notifications/digests?limit=50'),
        api.get('/notifications/digests/unread-count'),
      ]);
      setDigests(digestResponse.data);
      setUnreadCount(unreadResponse.data.unread_count || 0);
    } catch (error: any) {
      message.error(error.response?.data?.detail || '加载论文推送失败');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadDigests(); }, [loadDigests]);

  const handleMarkAllRead = async () => {
    if (!unreadCount) return;
    setMarkingRead(true);
    try {
      await api.post('/notifications/digests/read-all');
      setDigests(previous => previous.map(digest => ({ ...digest, is_read: true })));
      setUnreadCount(0);
      window.dispatchEvent(new Event('notifications:refresh'));
      message.success('论文推送已全部标记为已读');
    } catch (error: any) {
      message.error(error.response?.data?.detail || '操作失败');
    } finally {
      setMarkingRead(false);
    }
  };

  const paperKey = (paper: DigestPaper) => (
    paper.canonical_key
    || (paper.arxiv_id ? `arxiv:${paper.arxiv_id.replace(/v\d+$/, '').toLowerCase()}` : '')
    || `${paper.source || 'remote'}:${paper.remote_id || paper.title}`
  );

  const handleIngest = async (paper: DigestPaper): Promise<string | null> => {
    const remoteId = paper.remote_id || paper.arxiv_id;
    if (!remoteId) {
      message.warning('这条历史推荐缺少远程论文标识，暂时无法直接入库');
      return null;
    }
    const key = paperKey(paper);
    if (localPaperIds[key]) return localPaperIds[key];
    setIngestingIds(previous => new Set(previous).add(key));
    try {
      const response = await api.post('/papers/ingest-personal', {
        source: paper.source || 'arxiv',
        remote_id: remoteId,
        remote_ingest_token: paper.remote_ingest_token,
        auto_download: false,
      });
      const paperId = response.data.paper_ids?.[0];
      setIngestedIds(previous => new Set(previous).add(key));
      if (paperId) setLocalPaperIds(previous => ({ ...previous, [key]: paperId }));
      message.success('已加入你的论文库');
      return paperId || null;
    } catch (error: any) {
      message.error(error.response?.data?.detail || '加入论文库失败');
      return null;
    } finally {
      setIngestingIds(previous => {
        const next = new Set(previous);
        next.delete(key);
        return next;
      });
    }
  };

  const handleSendToReadingQueue = async (paper: DigestPaper, status: 'unread' | 'reading') => {
    const key = paperKey(paper);
    const paperId = await handleIngest(paper);
    if (!paperId) return;
    try {
      await api.put(`/papers/${paperId}/read-status`, { status });
      setReadingLoopStatus(previous => ({ ...previous, [key]: status }));
      message.success(status === 'reading' ? '已开始阅读，正在打开论文详情' : '已加入待读列表');
      if (status === 'reading') navigate(`/papers/${paperId}`);
    } catch (error: any) {
      message.error(error.response?.data?.detail || '更新阅读状态失败');
    }
  };

  const handleFeedback = async (digestId: string, paper: DigestPaper, action: 'interested' | 'later' | 'dismissed') => {
    const key = paperKey(paper);
    setFeedbackLoadingKeys(previous => new Set(previous).add(key));
    try {
      if (action === 'later') {
        const paperId = await handleIngest(paper);
        if (!paperId) return;
        await api.put(`/papers/${paperId}/read-status`, { status: 'unread' });
        setReadingLoopStatus(previous => ({ ...previous, [key]: 'unread' }));
      }
      await api.post(`/notifications/digests/${digestId}/feedback`, { paper_key: key, action });
      setDigests(previous => previous.map(digest => (
        digest.id === digestId
          ? {
            ...digest,
            metadata: {
              ...(digest.metadata || {}),
              feedback: {
                ...(digest.metadata?.feedback || {}),
                [key]: { action },
              },
            },
          }
          : digest
      )));
      message.success(action === 'dismissed' ? '已减少此类推荐' : action === 'later' ? '已加入待读列表' : '已记录你的兴趣');
    } catch (error: any) {
      message.error(error.response?.data?.detail || '记录反馈失败');
    } finally {
      setFeedbackLoadingKeys(previous => {
        const next = new Set(previous);
        next.delete(key);
        return next;
      });
    }
  };

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto' }}>
      <div style={{ background: heroGradient, borderRadius: 18, padding: '22px 28px', marginBottom: 16, color: '#fff', position: 'relative', overflow: 'hidden' }}>
        <div style={{ position: 'absolute', right: 30, top: -46, fontSize: 160, opacity: 0.08 }}><BellOutlined /></div>
        <Space direction="vertical" size={4}>
          <Button type="text" icon={<ArrowLeftOutlined />} onClick={() => navigate('/papers')} style={{ color: 'rgba(255,255,255,0.9)', paddingInline: 0 }}>返回论文库</Button>
          <Space size={14} align="center">
            <div style={{ width: 52, height: 52, borderRadius: 16, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(255,255,255,0.18)', fontSize: 25 }}><ReadOutlined /></div>
            <div>
              <Title level={3} style={{ color: '#fff', margin: 0 }}>论文推送中心</Title>
              <Text style={{ color: 'rgba(255,255,255,0.76)' }}>阅读每日摘要，挑选真正值得进入知识库的论文</Text>
            </div>
          </Space>
        </Space>
      </div>

      <Card style={{ borderRadius: 14, marginBottom: 14, border: '1px solid #eee' }} styles={{ body: { padding: '12px 18px' } }}>
        <Row align="middle" justify="space-between" gutter={[12, 12]}>
          <Col>
            <Space size={10} wrap>
              <Text strong>推送历史</Text>
              <Tag color="purple">{digests.length} 次摘要</Tag>
              <Badge count={unreadCount} size="small"><Tag color={unreadCount ? 'blue' : 'default'}>未读推送</Tag></Badge>
            </Space>
          </Col>
          <Col>
            <Button icon={<CheckCircleOutlined />} disabled={!unreadCount} loading={markingRead} onClick={handleMarkAllRead} style={{ borderRadius: 9 }}>全部标记已读</Button>
          </Col>
        </Row>
      </Card>

      <Spin spinning={loading}>
        {digests.length ? (
          <List
            dataSource={digests}
            renderItem={digest => {
              const metadata = digest.metadata || {};
              const papers = metadata.papers || [];
              return (
                <Card
                  key={digest.id}
                  style={{
                    marginBottom: 14, borderRadius: 16,
                    border: digest.is_read ? '1px solid #f0f0f0' : '1px solid #d6e4ff',
                    boxShadow: digest.is_read ? 'none' : '0 8px 24px rgba(102,126,234,0.08)',
                  }}
                  styles={{ body: { padding: 20 } }}
                >
                  <Row align="top" justify="space-between" gutter={[12, 12]}>
                    <Col flex="auto">
                      <Space size={8} wrap>
                        {!digest.is_read && <Badge status="processing" />}
                        <Title level={4} style={{ margin: 0 }}>{digest.title}</Title>
                        {metadata.is_test && <Tag color="gold">测试推送</Tag>}
                      </Space>
                      <div style={{ marginTop: 8 }}>
                        <Space size={6} wrap>
                          <Tag icon={<CalendarOutlined />}>{digest.created_at ? new Date(digest.created_at).toLocaleString() : '时间未知'}</Tag>
                          {(metadata.keywords || []).map(keyword => <Tag color="geekblue" key={keyword}>{keyword}</Tag>)}
                        </Space>
                      </div>
                    </Col>
                    <Col><Text type="secondary">{metadata.paper_count ?? papers.length} 篇推荐</Text></Col>
                  </Row>

                  <div style={{ margin: '18px 0', padding: '14px 16px', borderRadius: 12, background: '#fafaff', border: '1px solid #f0efff' }}>
                    <Markdown content={digest.content || '本次推送暂无摘要内容。'} />
                  </div>

                  {papers.length ? (
                    <List
                      size="small"
                      dataSource={papers}
                      renderItem={(paper, index) => {
                        const arxivId = paper.arxiv_id || '';
                        const cleanArxivId = arxivId.replace(/v\d+$/, '');
                        const key = paperKey(paper);
                        const ingested = ingestedIds.has(key) || !!localPaperIds[key];
                        const loopStatus = readingLoopStatus[key];
                        const rawFeedback = metadata.feedback?.[key];
                        const currentFeedback = typeof rawFeedback === 'string' ? rawFeedback : rawFeedback?.action;
                        return (
                          <List.Item style={{ padding: '14px 0', alignItems: 'flex-start' }}>
                            <div style={{ width: '100%' }}>
                              <Row gutter={[12, 10]} wrap={false}>
                                <Col>
                                  <div style={{ width: 30, height: 30, borderRadius: 9, background: '#f0f2ff', color: '#667eea', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700 }}>{index + 1}</div>
                                </Col>
                                <Col flex="auto">
                                  <Text strong style={{ fontSize: 15 }}>{paper.title}</Text>
                                  <div style={{ marginTop: 7 }}>
                                    <Space size={5} wrap>
                                      {paper.year && <Tag icon={<CalendarOutlined />} color="blue">{paper.year}</Tag>}
                                      {(paper.authors || []).map(author => <Tag key={author} icon={<UserOutlined />}>{author}</Tag>)}
                                      {arxivId && <Tag color="#b31b1b">arXiv:{arxivId}</Tag>}
                                      {paper.source && <Tag color="cyan">{paper.source}</Tag>}
                                      {paper.recommendation_score != null && <Tag color="purple">推荐分 {(paper.recommendation_score * 100).toFixed(0)}</Tag>}
                                      {loopStatus === 'unread' && <Tag color="blue">已加入待读</Tag>}
                                      {loopStatus === 'reading' && <Tag color="green">阅读中</Tag>}
                                    </Space>
                                  </div>
                                  {!!paper.recommendation_reasons?.length && (
                                    <div style={{ marginTop: 7 }}>
                                      <Space size={4} wrap>
                                        {paper.recommendation_reasons.map(reason => <Tag key={reason} bordered={false} color="geekblue">{reason}</Tag>)}
                                      </Space>
                                    </div>
                                  )}
                                  {paper.abstract_snippet && <Paragraph type="secondary" style={{ margin: '8px 0 0', fontSize: 13, lineHeight: 1.7 }}>{paper.abstract_snippet}</Paragraph>}
                                  <Space size={6} wrap style={{ marginTop: 9 }}>
                                    {(paper.source_url || arxivId) && <Button size="small" icon={<LinkOutlined />} href={paper.source_url || `https://arxiv.org/abs/${cleanArxivId}`} target="_blank" rel="noreferrer">查看来源</Button>}
                                    {(paper.pdf_url || arxivId) && <Button size="small" icon={<FilePdfOutlined />} href={paper.pdf_url || `https://arxiv.org/pdf/${cleanArxivId}`} target="_blank" rel="noreferrer">打开 PDF</Button>}
                                    {ingested ? (
                                      <Tag icon={<CheckCircleOutlined />} color="green">已加入论文库</Tag>
                                    ) : (
                                      <Button size="small" type="primary" ghost icon={<ImportOutlined />} disabled={!paper.remote_id && !arxivId} loading={ingestingIds.has(key)} onClick={() => handleIngest(paper)}>加入论文库</Button>
                                    )}
                                    <Button size="small" icon={<ClockCircleOutlined />} loading={ingestingIds.has(key)} type={loopStatus === 'unread' ? 'primary' : 'default'} onClick={() => handleSendToReadingQueue(paper, 'unread')}>加入待读</Button>
                                    <Button size="small" icon={<PlayCircleOutlined />} loading={ingestingIds.has(key)} type={loopStatus === 'reading' ? 'primary' : 'default'} onClick={() => handleSendToReadingQueue(paper, 'reading')}>开始阅读</Button>
                                    <Button size="small" icon={<LikeOutlined />} type={currentFeedback === 'interested' ? 'primary' : 'default'} loading={feedbackLoadingKeys.has(key)} onClick={() => handleFeedback(digest.id, paper, 'interested')}>感兴趣</Button>
                                    <Button size="small" icon={<ClockCircleOutlined />} type={currentFeedback === 'later' ? 'primary' : 'default'} loading={feedbackLoadingKeys.has(key)} onClick={() => handleFeedback(digest.id, paper, 'later')}>稍后阅读</Button>
                                    <Button size="small" danger icon={<StopOutlined />} type={currentFeedback === 'dismissed' ? 'primary' : 'default'} loading={feedbackLoadingKeys.has(key)} onClick={() => handleFeedback(digest.id, paper, 'dismissed')}>不感兴趣</Button>
                                  </Space>
                                </Col>
                              </Row>
                            </div>
                          </List.Item>
                        );
                      }}
                    />
                  ) : (
                    <Alert type="info" showIcon message="这次推送没有匹配到论文" description="推送链路工作正常，可以调整订阅关键词后再次测试。" />
                  )}
                </Card>
              );
            }}
          />
        ) : (
          <Card style={{ borderRadius: 16, padding: 54, textAlign: 'center', border: '2px dashed #e8e8e8' }}>
            <Empty description="暂无论文推送">
              <Button type="primary" onClick={() => navigate('/settings')} style={{ borderRadius: 9 }}>前往设置订阅关键词</Button>
            </Empty>
          </Card>
        )}
      </Spin>
    </div>
  );
};

export default PaperDigestInboxPage;
