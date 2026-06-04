import React from 'react';
import { Steps, Button, Space, Tag, Typography } from 'antd';
import { LoadingOutlined, CheckCircleOutlined, CloseCircleOutlined, StopOutlined } from '@ant-design/icons';

const { Text } = Typography;

interface PipelineProgressProps {
  phases: string[];
  currentPhase: string | null;
  phaseStatuses: Record<string, 'pending' | 'running' | 'complete' | 'error'>;
  statusText: string;
  onCancel: () => void;
}

const phaseLabels: Record<string, string> = {
  selector: '检索相关论文',
  reader: '深度阅读分析',
  writer: '生成内容',
  reviewer: '审阅质量',
  citation: '验证引用',
};

const PipelineProgress: React.FC<PipelineProgressProps> = ({
  phases, currentPhase, phaseStatuses, statusText, onCancel,
}) => {
  const stepItems = phases.map((phase) => {
    const status = phaseStatuses[phase] || 'pending';
    return {
      title: phaseLabels[phase] || phase,
      status: status as 'wait' | 'process' | 'finish' | 'error',
      icon: status === 'running' ? <LoadingOutlined /> :
            status === 'complete' ? <CheckCircleOutlined /> :
            status === 'error' ? <CloseCircleOutlined /> : undefined,
    };
  });

  const currentStep = phases.indexOf(currentPhase || '');

  return (
    <div style={{ padding: '12px 16px', background: '#fafafa', borderRadius: 8, border: '1px solid #e8e8e8' }}>
      <Steps
        size="small"
        current={currentStep >= 0 ? currentStep : 0}
        items={stepItems}
        style={{ marginBottom: 8 }}
      />
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Space>
          {currentPhase && (
            <Tag color="processing">{phaseLabels[currentPhase] || currentPhase}</Tag>
          )}
          <Text type="secondary" style={{ fontSize: 12 }}>{statusText}</Text>
        </Space>
        <Button size="small" icon={<StopOutlined />} onClick={onCancel} danger>
          取消
        </Button>
      </div>
    </div>
  );
};

export default PipelineProgress;
