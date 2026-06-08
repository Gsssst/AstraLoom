import React from 'react';
import { Alert, Button, Input, List, Select, Space, Tag, Typography } from 'antd';
import { AuditOutlined, CheckCircleOutlined, EditOutlined } from '@ant-design/icons';

const { TextArea } = Input;
const { Text } = Typography;

interface Section {
  id: string;
  title: string;
  content: string;
  order: number;
  status: string;
  word_count: number;
}

interface SectionEditorProps {
  section: Section;
  onUpdate: (sectionId: string, data: Partial<Section>) => void;
  onFocus?: (section: Section) => void;
  onCheckCitations?: (section: Section) => void;
  onCheckQuality?: (section: Section) => void;
  checking?: boolean;
  qualityChecking?: boolean;
  citationCheck?: any;
  qualityCheck?: any;
}

const statusColor = (status?: string) => {
  if (status === 'strong') return 'green';
  if (status === 'partial') return 'gold';
  if (status === 'unchecked') return 'blue';
  return 'red';
};

const safetyAlertType = (status?: string) => {
  if (status === 'low_risk') return 'success';
  if (status === 'no_claims') return 'info';
  return 'warning';
};

const SectionEditor: React.FC<SectionEditorProps> = ({
  section,
  onUpdate,
  onFocus,
  onCheckCitations,
  onCheckQuality,
  checking,
  qualityChecking,
  citationCheck,
  qualityCheck,
}) => {
  const handleTitleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onUpdate(section.id, { title: e.target.value });
  };

  const handleContentChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    onUpdate(section.id, { content: e.target.value });
  };

  const handleStatusChange = (status: string) => {
    onUpdate(section.id, { status });
  };

  return (
    <div style={{ marginBottom: 8 }}>
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        marginBottom: 4,
      }}>
        <Input
          value={section.title}
          onChange={handleTitleChange}
          variant="borderless"
          size="large"
          style={{ fontWeight: 600, fontSize: 16, paddingLeft: 0 }}
          prefix={<EditOutlined style={{ color: '#999' }} />}
        />
        <Space>
          {onCheckQuality && (
            <Button
              size="small"
              icon={<CheckCircleOutlined />}
              loading={qualityChecking}
              onClick={() => onCheckQuality(section)}
              style={{ borderRadius: 8 }}
            >
              质量评估
            </Button>
          )}
          {onCheckCitations && (
            <Button
              size="small"
              icon={<AuditOutlined />}
              loading={checking}
              onClick={() => onCheckCitations(section)}
              style={{ borderRadius: 8 }}
            >
              校验引用
            </Button>
          )}
          <Select
            size="small"
            value={section.status}
            onChange={handleStatusChange}
            variant="borderless"
            style={{ width: 100 }}
            options={[
              { value: 'draft', label: '📝 草稿' },
              { value: 'writing', label: '✍️ 写作中' },
              { value: 'polished', label: '✨ 已润色' },
              { value: 'complete', label: '✅ 完成' },
            ]}
          />
          <Text type="secondary" style={{ fontSize: 11, whiteSpace: 'nowrap' }}>
            {section.word_count} 字
          </Text>
        </Space>
      </div>
      <TextArea
        value={section.content || ''}
        onChange={handleContentChange}
        onFocus={() => onFocus?.(section)}
        rows={8}
        placeholder="开始写作..."
        style={{ borderRadius: 8, fontSize: 14, lineHeight: 1.8 }}
      />
      {citationCheck && (
        <div style={{ marginTop: 8 }}>
          <Alert
            type={(citationCheck.summary?.evidence_warning || citationCheck.claim_safety_summary?.risky) ? 'warning' : 'success'}
            showIcon
            message={
              <Space wrap>
                <Text strong>引用覆盖率 {Math.round((citationCheck.summary?.citation_coverage || 0) * 100)}%</Text>
                <Tag color="green">强 {citationCheck.summary?.strong || 0}</Tag>
                <Tag color="gold">部分 {citationCheck.summary?.partial || 0}</Tag>
                <Tag color="red">弱/缺失 {(citationCheck.summary?.weak || 0) + (citationCheck.summary?.missing || 0)}</Tag>
                <Tag color="blue">未校验 {citationCheck.summary?.unchecked || 0}</Tag>
                {citationCheck.claim_safety_summary && (
                  <Tag color={citationCheck.claim_safety_summary.risky ? 'red' : 'green'}>
                    Claim 风险 {citationCheck.claim_safety_summary.risky || 0}
                  </Tag>
                )}
              </Space>
            }
            description={
              <Space direction="vertical" style={{ width: '100%' }} size={8}>
                {citationCheck.claim_safety_summary && (
                  <Alert
                    type={safetyAlertType(citationCheck.claim_safety_summary.status) as any}
                    showIcon
                    message={
                      <Space wrap>
                        <Text strong>Claim 安全检查：{citationCheck.claim_safety_summary.status_label}</Text>
                        <Tag color="green">稳 {citationCheck.claim_safety_summary.strong || 0}</Tag>
                        <Tag color="gold">部分 {citationCheck.claim_safety_summary.partial || 0}</Tag>
                        <Tag color="red">缺引用 {citationCheck.claim_safety_summary.missing || 0}</Tag>
                        <Tag color="red">弱支撑 {citationCheck.claim_safety_summary.weak || 0}</Tag>
                        <Tag color="blue">外部未校验 {citationCheck.claim_safety_summary.unchecked || 0}</Tag>
                      </Space>
                    }
                    description={citationCheck.claim_safety_summary.next_action}
                    style={{ borderRadius: 8, padding: '8px 10px' }}
                  />
                )}
                {(citationCheck.claim_diagnostics || []).length > 0 && (
                  <List
                    size="small"
                    dataSource={(citationCheck.claim_diagnostics || []).filter((item: any) => ['missing', 'weak', 'unchecked'].includes(item.status)).slice(0, 6)}
                    locale={{ emptyText: '未发现高风险 claim' }}
                    renderItem={(item: any) => (
                      <List.Item style={{ padding: '6px 0' }}>
                        <div style={{ width: '100%', minWidth: 0 }}>
                          <Space wrap>
                            <Tag color={statusColor(item.status)}>{item.label}</Tag>
                            {(item.citations || []).map((citation: string) => <Tag key={citation}>{citation}</Tag>)}
                            {(item.evidence_titles || []).map((title: string) => <Text key={title} type="secondary">{title}</Text>)}
                          </Space>
                          <Text style={{ display: 'block', fontSize: 12, marginTop: 4, overflowWrap: 'anywhere' }}>
                            {item.sentence}
                          </Text>
                          <Text type="secondary" style={{ display: 'block', fontSize: 12, marginTop: 4 }}>
                            建议：{item.decision_action}{item.decision_warning ? `；${item.decision_warning}` : ''}
                          </Text>
                        </div>
                      </List.Item>
                    )}
                  />
                )}
                <List
                  size="small"
                  dataSource={citationCheck.checks || []}
                  renderItem={(item: any) => (
                    <List.Item style={{ padding: '6px 0' }}>
                      <div style={{ width: '100%' }}>
                        <Space wrap>
                          <Tag color={statusColor(item.status)}>{item.citation || '无引用'}</Tag>
                          <Text strong>{item.label}</Text>
                          {item.decision_label && <Tag color={statusColor(item.status)}>{item.decision_label}</Tag>}
                          {item.card?.title && <Text type="secondary">{item.card.title}</Text>}
                        </Space>
                        <Text type="secondary" style={{ display: 'block', fontSize: 12, marginTop: 4 }}>
                          {item.explanation}
                        </Text>
                        {item.decision_action && (
                          <Alert
                            type={item.status === 'weak' || item.status === 'missing' ? 'warning' : 'info'}
                            showIcon
                            message="建议下一步"
                            description={`${item.decision_action}${item.decision_warning ? `：${item.decision_warning}` : ''}`}
                            style={{ borderRadius: 8, marginTop: 6, padding: '6px 10px' }}
                          />
                        )}
                        {item.match_terms?.length > 0 && (
                          <Text type="secondary" style={{ display: 'block', fontSize: 12 }}>
                            命中术语：{item.match_terms.join('、')}
                          </Text>
                        )}
                      </div>
                    </List.Item>
                      )}
                />
              </Space>
            }
            style={{ borderRadius: 10 }}
          />
        </div>
      )}
      {qualityCheck && (
        <div style={{ marginTop: 8 }}>
          <Alert
            type={qualityCheck.status === 'ready' ? 'success' : qualityCheck.status === 'needs_revision' ? 'warning' : 'error'}
            showIcon
            message={
              <Space wrap>
                <Text strong>章节质量 {qualityCheck.overall_score || 0}/100</Text>
                <Tag color={qualityCheck.status === 'ready' ? 'green' : qualityCheck.status === 'needs_revision' ? 'gold' : 'red'}>
                  {qualityCheck.status_label}
                </Tag>
                <Tag color="blue">引用 {qualityCheck.metrics?.citation_count || 0}</Tag>
                <Tag color="purple">字数 {qualityCheck.metrics?.word_count || 0}</Tag>
              </Space>
            }
            description={
              <Space direction="vertical" style={{ width: '100%' }} size={8}>
                <Text type="secondary">{qualityCheck.summary}</Text>
                <Space size={6} wrap>
                  {(qualityCheck.dimensions || []).map((item: any) => (
                    <Tag key={item.key} color={item.status === 'pass' ? 'green' : item.status === 'partial' ? 'gold' : 'red'}>
                      {item.label} · {item.status === 'pass' ? '通过' : item.status === 'partial' ? '部分' : '不足'}
                    </Tag>
                  ))}
                </Space>
                {(qualityCheck.rewrite_actions || []).length > 0 && (
                  <List
                    size="small"
                    dataSource={qualityCheck.rewrite_actions}
                    renderItem={(item: any) => (
                      <List.Item style={{ padding: '4px 0' }}>
                        <Text type="secondary"><Text strong>{item.label}：</Text>{item.action}</Text>
                      </List.Item>
                    )}
                  />
                )}
              </Space>
            }
            style={{ borderRadius: 10 }}
          />
        </div>
      )}
    </div>
  );
};

export default SectionEditor;
