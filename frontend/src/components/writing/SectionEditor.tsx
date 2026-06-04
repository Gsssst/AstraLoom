import React from 'react';
import { Alert, Button, Input, List, Select, Space, Tag, Typography } from 'antd';
import { AuditOutlined, EditOutlined } from '@ant-design/icons';

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
  checking?: boolean;
  citationCheck?: any;
}

const statusColor = (status?: string) => {
  if (status === 'strong') return 'green';
  if (status === 'partial') return 'gold';
  if (status === 'unchecked') return 'blue';
  return 'red';
};

const SectionEditor: React.FC<SectionEditorProps> = ({
  section,
  onUpdate,
  onFocus,
  onCheckCitations,
  checking,
  citationCheck,
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
            type={citationCheck.summary?.evidence_warning ? 'warning' : 'success'}
            showIcon
            message={
              <Space wrap>
                <Text strong>引用覆盖率 {Math.round((citationCheck.summary?.citation_coverage || 0) * 100)}%</Text>
                <Tag color="green">强 {citationCheck.summary?.strong || 0}</Tag>
                <Tag color="gold">部分 {citationCheck.summary?.partial || 0}</Tag>
                <Tag color="red">弱/缺失 {(citationCheck.summary?.weak || 0) + (citationCheck.summary?.missing || 0)}</Tag>
                <Tag color="blue">未校验 {citationCheck.summary?.unchecked || 0}</Tag>
              </Space>
            }
            description={
              <List
                size="small"
                dataSource={citationCheck.checks || []}
                renderItem={(item: any) => (
                  <List.Item style={{ padding: '6px 0' }}>
                    <div style={{ width: '100%' }}>
                      <Space wrap>
                        <Tag color={statusColor(item.status)}>{item.citation || '无引用'}</Tag>
                        <Text strong>{item.label}</Text>
                        {item.card?.title && <Text type="secondary">{item.card.title}</Text>}
                      </Space>
                      <Text type="secondary" style={{ display: 'block', fontSize: 12, marginTop: 4 }}>
                        {item.explanation}
                      </Text>
                      {item.match_terms?.length > 0 && (
                        <Text type="secondary" style={{ display: 'block', fontSize: 12 }}>
                          命中术语：{item.match_terms.join('、')}
                        </Text>
                      )}
                    </div>
                  </List.Item>
                )}
              />
            }
            style={{ borderRadius: 10 }}
          />
        </div>
      )}
    </div>
  );
};

export default SectionEditor;
