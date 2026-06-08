import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Alert, Button, Collapse, Input, List, Select, Space, Tag, Typography, message } from 'antd';
import {
  AuditOutlined, BulbOutlined, CheckCircleOutlined, CodeOutlined,
  CopyOutlined, EditOutlined, EyeOutlined, RobotOutlined, RocketOutlined,
} from '@ant-design/icons';

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
  onPreviewLatex?: (section: Section) => void;
  onSectionAiAction?: (section: Section, action: SectionAiAction) => void;
  checking?: boolean;
  qualityChecking?: boolean;
  previewing?: boolean;
  citationCheck?: any;
  qualityCheck?: any;
  latexPreview?: any;
  aiRunning?: boolean;
  aiRunningAction?: string;
  aiStatus?: string;
  aiOutput?: string;
}

type SectionAiAction = 'draft' | 'improve' | 'insert_evidence' | 'claim_safety' | 'polish' | 'repair_latex';

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

const latexPreviewType = (preview?: any) => {
  if (!preview) return 'info';
  if (preview.success) return preview.warnings?.length ? 'warning' : 'success';
  return 'error';
};

const sectionAiActions: { key: SectionAiAction; label: string; icon: React.ReactNode }[] = [
  { key: 'draft', label: '起草本节', icon: <RocketOutlined /> },
  { key: 'improve', label: '改进论证', icon: <BulbOutlined /> },
  { key: 'insert_evidence', label: '补证据引用', icon: <AuditOutlined /> },
  { key: 'claim_safety', label: 'Claim 安全', icon: <CheckCircleOutlined /> },
  { key: 'polish', label: '润色源码', icon: <EditOutlined /> },
  { key: 'repair_latex', label: '修复 LaTeX', icon: <CodeOutlined /> },
];

const SectionEditor: React.FC<SectionEditorProps> = ({
  section,
  onUpdate,
  onFocus,
  onCheckCitations,
  onCheckQuality,
  onPreviewLatex,
  onSectionAiAction,
  checking,
  qualityChecking,
  previewing,
  citationCheck,
  qualityCheck,
  latexPreview,
  aiRunning,
  aiRunningAction,
  aiStatus,
  aiOutput,
}) => {
  const [draftTitle, setDraftTitle] = useState(section.title || '');
  const [draftContent, setDraftContent] = useState(section.content || '');
  const [draftStatus, setDraftStatus] = useState(section.status || 'draft');
  const saveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const latestDraftRef = useRef({ title: draftTitle, content: draftContent, status: draftStatus });

  useEffect(() => {
    setDraftTitle(section.title || '');
    setDraftContent(section.content || '');
    setDraftStatus(section.status || 'draft');
  }, [section.id]);

  useEffect(() => {
    latestDraftRef.current = { title: draftTitle, content: draftContent, status: draftStatus };
  }, [draftTitle, draftContent, draftStatus]);

  useEffect(() => () => {
    if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
  }, []);

  const buildDraftSection = useCallback((patch?: Partial<Section>): Section => ({
    ...section,
    title: patch?.title ?? latestDraftRef.current.title,
    content: patch?.content ?? latestDraftRef.current.content,
    status: patch?.status ?? latestDraftRef.current.status,
    word_count: (patch?.content ?? latestDraftRef.current.content).length,
  }), [section]);

  const scheduleSave = useCallback(() => {
    if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
    saveTimerRef.current = setTimeout(() => {
      onUpdate(section.id, {
        title: latestDraftRef.current.title,
        content: latestDraftRef.current.content,
        status: latestDraftRef.current.status,
      });
      saveTimerRef.current = null;
    }, 800);
  }, [onUpdate, section.id]);

  const flushDraft = useCallback((patch?: Partial<Section>) => {
    if (saveTimerRef.current) {
      clearTimeout(saveTimerRef.current);
      saveTimerRef.current = null;
    }
    const payload = patch || {
      title: latestDraftRef.current.title,
      content: latestDraftRef.current.content,
      status: latestDraftRef.current.status,
    };
    onUpdate(section.id, payload);
    return buildDraftSection(payload);
  }, [buildDraftSection, onUpdate, section.id]);

  const handleTitleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const title = e.target.value;
    setDraftTitle(title);
    latestDraftRef.current = { ...latestDraftRef.current, title };
    scheduleSave();
  };

  const handleContentChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const content = e.target.value;
    setDraftContent(content);
    latestDraftRef.current = { ...latestDraftRef.current, content };
    scheduleSave();
  };

  const handleStatusChange = (status: string) => {
    setDraftStatus(status);
    latestDraftRef.current = { ...latestDraftRef.current, status };
    flushDraft({ title: latestDraftRef.current.title, content: latestDraftRef.current.content, status });
  };

  const handleCopyAiOutput = async () => {
    if (!aiOutput) return;
    await navigator.clipboard.writeText(aiOutput);
    message.success('已复制 AI 建议');
  };

  return (
    <div style={{ marginBottom: 8 }}>
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        marginBottom: 8,
      }}>
        <Input
          value={draftTitle}
          onChange={handleTitleChange}
          onBlur={() => flushDraft()}
          variant="borderless"
          size="large"
          style={{ fontWeight: 600, fontSize: 16, paddingLeft: 0 }}
          prefix={<EditOutlined style={{ color: '#999' }} />}
        />
        <Space>
          {onPreviewLatex && (
            <Button
              size="small"
              icon={<CodeOutlined />}
              loading={previewing}
              onClick={() => onPreviewLatex(flushDraft())}
              style={{ borderRadius: 8 }}
            >
              LaTeX 预览检查
            </Button>
          )}
          {onCheckQuality && (
            <Button
              size="small"
              icon={<CheckCircleOutlined />}
              loading={qualityChecking}
              onClick={() => onCheckQuality(flushDraft())}
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
              onClick={() => onCheckCitations(flushDraft())}
              style={{ borderRadius: 8 }}
            >
              校验引用
            </Button>
          )}
          <Select
            size="small"
            value={draftStatus}
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
            {draftContent.length} 字
          </Text>
        </Space>
      </div>
      <div style={{ marginBottom: 8 }}>
        <Space size={6} wrap>
          <Tag color="geekblue" icon={<CodeOutlined />}>LaTeX 源码</Tag>
          <Text type="secondary" style={{ fontSize: 12 }}>
            当前章节内容会作为 LaTeX body 保存，保留公式、命令、引用、label、表格和 figure 环境。
          </Text>
        </Space>
      </div>
      <TextArea
        value={draftContent}
        onChange={handleContentChange}
        onFocus={() => onFocus?.(section)}
        onBlur={() => flushDraft()}
        rows={18}
        placeholder={'输入本章节 LaTeX 源码，例如：\\paragraph{Motivation} ... \\cite{smith2024}\\n\\begin{equation}\\n  \\mathcal{L}=...\\n\\end{equation}'}
        style={{
          borderRadius: 8,
          fontSize: 13,
          lineHeight: 1.65,
          fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace',
        }}
      />
      {latexPreview && (
        <div style={{ marginTop: 8 }}>
          <Alert
            type={latexPreviewType(latexPreview) as any}
            showIcon
            message={
              <Space wrap>
                <Text strong>
                  {latexPreview.compiler_available === false
                    ? (latexPreview.success ? '源码级检查通过' : '源码级检查发现问题')
                    : (latexPreview.success ? 'LaTeX 检查通过' : 'LaTeX 检查未通过')}
                </Text>
                <Tag color={latexPreview.success ? 'green' : 'red'}>{latexPreview.scope === 'manuscript' ? '整篇' : '当前章节'}</Tag>
                {latexPreview.compiler_available === false && <Tag color="gold">未安装 pdflatex</Tag>}
                <Tag color={(latexPreview.errors || []).length ? 'red' : 'green'}>错误 {(latexPreview.errors || []).length}</Tag>
                <Tag color={(latexPreview.warnings || []).length ? 'gold' : 'green'}>警告 {(latexPreview.warnings || []).length}</Tag>
              </Space>
            }
            description={
              <Space direction="vertical" size={8} style={{ width: '100%' }}>
                {(latexPreview.errors || []).length > 0 && (
                  <List
                    size="small"
                    dataSource={latexPreview.errors}
                    renderItem={(item: string) => (
                      <List.Item style={{ padding: '4px 0' }}>
                        <Text type="danger" style={{ overflowWrap: 'anywhere' }}>{item}</Text>
                      </List.Item>
                    )}
                  />
                )}
                {(latexPreview.warnings || []).length > 0 && (
                  <List
                    size="small"
                    dataSource={latexPreview.warnings}
                    renderItem={(item: string) => (
                      <List.Item style={{ padding: '4px 0' }}>
                        <Text type="secondary" style={{ overflowWrap: 'anywhere' }}>{item}</Text>
                      </List.Item>
                    )}
                  />
                )}
                {latexPreview.log && (
                  <Collapse
                    size="small"
                    ghost
                    items={[{
                      key: 'latex-log',
                      label: '查看编译日志',
                      children: (
                        <pre style={{
                          margin: 0,
                          maxHeight: 220,
                          overflow: 'auto',
                          whiteSpace: 'pre-wrap',
                          fontSize: 12,
                          lineHeight: 1.55,
                        }}>
                          {latexPreview.log}
                        </pre>
                      ),
                    }]}
                  />
                )}
                {latexPreview.pdf_preview_url && (
                  <div style={{ border: '1px solid #e5e7eb', borderRadius: 8, overflow: 'hidden', background: '#fff' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8, padding: '8px 10px', borderBottom: '1px solid #eef0f3' }}>
                      <Space size={6}>
                        <EyeOutlined />
                        <Text strong>PDF 预览</Text>
                      </Space>
                      <Button size="small" href={latexPreview.pdf_preview_url} target="_blank" rel="noreferrer">
                        打开
                      </Button>
                    </div>
                    <iframe
                      title="LaTeX PDF preview"
                      src={latexPreview.pdf_preview_url}
                      style={{ width: '100%', height: 420, border: 0, display: 'block' }}
                    />
                  </div>
                )}
              </Space>
            }
            style={{ borderRadius: 10 }}
          />
        </div>
      )}
      {onSectionAiAction && (
        <div style={{ marginTop: 12, padding: 12, borderRadius: 10, border: '1px solid #e6f4ff', background: '#f6fbff' }}>
          <RowLikeHeader
            title={<Space><RobotOutlined /> 当前章节 AI 助手</Space>}
            extra={<Tag color="blue">{section.title || '未命名章节'}</Tag>}
          />
          <Text type="secondary" style={{ display: 'block', fontSize: 12, marginBottom: 10 }}>
            AI 请求会带上当前章节标题、LaTeX 源码、项目上下文、证据卡、引用校验和 LaTeX 诊断，只处理当前章节。
          </Text>
          <Space size={8} wrap>
            {sectionAiActions.map(action => (
              <Button
                key={action.key}
                size="small"
                icon={action.icon}
                loading={aiRunning && aiRunningAction === action.key}
                disabled={aiRunning && aiRunningAction !== action.key}
                onClick={() => onSectionAiAction(flushDraft(), action.key)}
                style={{ borderRadius: 8 }}
              >
                {action.label}
              </Button>
            ))}
          </Space>
          {(aiStatus || aiOutput) && (
            <div style={{ marginTop: 10 }}>
              <Alert
                type={aiRunning ? 'info' : aiOutput ? 'success' : 'warning'}
                showIcon
                message={aiStatus || 'AI 建议已生成'}
                description={aiOutput ? (
                  <Space direction="vertical" style={{ width: '100%' }} size={8}>
                    <pre style={{
                      margin: 0,
                      maxHeight: 260,
                      overflow: 'auto',
                      whiteSpace: 'pre-wrap',
                      fontSize: 12,
                      lineHeight: 1.6,
                      background: '#fff',
                      border: '1px solid #f0f0f0',
                      borderRadius: 8,
                      padding: 10,
                    }}>
                      {aiOutput}
                    </pre>
                    <Button size="small" icon={<CopyOutlined />} onClick={handleCopyAiOutput} style={{ borderRadius: 8 }}>
                      复制 AI 建议
                    </Button>
                  </Space>
                ) : undefined}
                style={{ borderRadius: 10 }}
              />
            </div>
          )}
        </div>
      )}
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

const RowLikeHeader: React.FC<{ title: React.ReactNode; extra?: React.ReactNode }> = ({ title, extra }) => (
  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8, marginBottom: 6 }}>
    <Text strong>{title}</Text>
    {extra}
  </div>
);

export default SectionEditor;
