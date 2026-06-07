import React from 'react';
import { Button, Card, Empty, Progress, Skeleton, Space, Tag, Typography } from 'antd';
import {
  ClockCircleOutlined,
  ExperimentOutlined,
  LoadingOutlined,
  RocketOutlined,
} from '@ant-design/icons';

const { Text, Title } = Typography;

type WorkflowStateProps = {
  title: React.ReactNode;
  description?: React.ReactNode;
  icon?: React.ReactNode;
  action?: React.ReactNode;
  style?: React.CSSProperties;
};

type WorkflowLoadingStateProps = WorkflowStateProps & {
  rows?: number;
};

type WorkflowProgressStateProps = WorkflowStateProps & {
  percent?: number;
  phase?: React.ReactNode;
  statusText?: React.ReactNode;
  extra?: React.ReactNode;
  compact?: boolean;
};

const stateCardStyle: React.CSSProperties = {
  borderRadius: 14,
  border: '1px solid #f0f0f0',
};

const iconWrapStyle: React.CSSProperties = {
  width: 54,
  height: 54,
  borderRadius: 14,
  background: '#f5f7ff',
  color: '#4f46e5',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  fontSize: 24,
  flexShrink: 0,
};

export const WorkflowLoadingState: React.FC<WorkflowLoadingStateProps> = ({
  title,
  description,
  icon = <LoadingOutlined />,
  action,
  rows = 4,
  style,
}) => (
  <Card style={{ ...stateCardStyle, ...style }} styles={{ body: { padding: 22 } }}>
    <Space align="start" size={16} style={{ width: '100%' }}>
      <div style={iconWrapStyle}>{icon}</div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <Title level={5} style={{ margin: '0 0 4px' }}>{title}</Title>
        {description && <Text type="secondary">{description}</Text>}
        <Skeleton active paragraph={{ rows }} title={false} style={{ marginTop: 16 }} />
        {action && <div style={{ marginTop: 14 }}>{action}</div>}
      </div>
    </Space>
  </Card>
);

export const WorkflowEmptyState: React.FC<WorkflowStateProps> = ({
  title,
  description,
  icon,
  action,
  style,
}) => (
  <Card style={{ ...stateCardStyle, borderStyle: 'dashed', ...style }} styles={{ body: { padding: 34 } }}>
    <Empty
      image={icon ? (
        <div style={{ ...iconWrapStyle, margin: '0 auto', width: 64, height: 64, fontSize: 28 }}>
          {icon}
        </div>
      ) : Empty.PRESENTED_IMAGE_SIMPLE}
      description={(
        <Space direction="vertical" size={6} style={{ alignItems: 'center', maxWidth: 520 }}>
          <Title level={5} style={{ margin: 0 }}>{title}</Title>
          {description && <Text type="secondary">{description}</Text>}
        </Space>
      )}
    >
      {action}
    </Empty>
  </Card>
);

export const WorkflowUnavailableState: React.FC<WorkflowStateProps> = ({
  title,
  description,
  icon = <ExperimentOutlined />,
  action,
  style,
}) => (
  <WorkflowEmptyState
    title={title}
    description={description}
    icon={icon}
    action={action}
    style={style}
  />
);

export const WorkflowProgressState: React.FC<WorkflowProgressStateProps> = ({
  title,
  description,
  percent,
  phase,
  statusText,
  icon = <RocketOutlined />,
  action,
  extra,
  compact = false,
  style,
}) => {
  const hasPercent = typeof percent === 'number';
  return (
    <Card style={{ ...stateCardStyle, ...style }} styles={{ body: { padding: compact ? 14 : 18 } }}>
      <Space align="start" size={14} style={{ width: '100%' }}>
        <div style={{ ...iconWrapStyle, width: compact ? 42 : 54, height: compact ? 42 : 54, fontSize: compact ? 20 : 24 }}>
          {icon}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <Space size={8} wrap>
            <Text strong>{title}</Text>
            {phase && <Tag color="processing">{phase}</Tag>}
            {!hasPercent && <Tag icon={<ClockCircleOutlined />} color="blue">进行中</Tag>}
          </Space>
          {description && <Text type="secondary" style={{ display: 'block', marginTop: 4 }}>{description}</Text>}
          <Progress
            percent={hasPercent ? Math.max(0, Math.min(100, Math.round(percent))) : 100}
            status="active"
            showInfo={hasPercent}
            strokeColor="#4f46e5"
            style={{ marginTop: 10, marginBottom: 0 }}
          />
          {statusText && <Text type="secondary" style={{ display: 'block', marginTop: 4, fontSize: 12 }}>{statusText}</Text>}
          {(extra || action) && (
            <div style={{ marginTop: 10, display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
              <div>{extra}</div>
              <div>{action}</div>
            </div>
          )}
        </div>
      </Space>
    </Card>
  );
};

export const workflowActionButton = (label: React.ReactNode, onClick: () => void, icon?: React.ReactNode) => (
  <Button type="primary" icon={icon} onClick={onClick} style={{ borderRadius: 10 }}>
    {label}
  </Button>
);
