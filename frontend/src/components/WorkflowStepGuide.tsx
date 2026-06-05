import React from 'react';
import { Button, Card, Col, Row, Space, Tag, Typography } from 'antd';
import { ArrowRightOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

const { Text, Title } = Typography;

export type WorkflowStepStatus = 'recommended' | 'ready' | 'optional' | 'blocked';

export interface WorkflowStep {
  key: string;
  title: string;
  description: string;
  actionLabel: string;
  icon?: React.ReactNode;
  path?: string;
  onClick?: () => void;
  status?: WorkflowStepStatus;
}

interface WorkflowStepGuideProps {
  title: string;
  subtitle?: string;
  steps: WorkflowStep[];
  style?: React.CSSProperties;
}

const statusMeta: Record<WorkflowStepStatus, { label: string; color: string }> = {
  recommended: { label: '推荐下一步', color: 'purple' },
  ready: { label: '可执行', color: 'blue' },
  optional: { label: '可选', color: 'default' },
  blocked: { label: '需准备', color: 'gold' },
};

const WorkflowStepGuide: React.FC<WorkflowStepGuideProps> = ({ title, subtitle, steps, style }) => {
  const navigate = useNavigate();

  const handleStep = (step: WorkflowStep) => {
    if (step.onClick) {
      step.onClick();
      return;
    }
    if (step.path) {
      navigate(step.path);
    }
  };

  return (
    <Card
      size="small"
      style={{ borderRadius: 16, border: '1px solid #ece8ff', background: 'linear-gradient(180deg, #ffffff 0%, #fbf9ff 100%)', ...style }}
      styles={{ body: { padding: 16 } }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'flex-start', marginBottom: 12, flexWrap: 'wrap' }}>
        <div>
          <Title level={5} style={{ margin: 0 }}>{title}</Title>
          {subtitle && <Text type="secondary" style={{ fontSize: 13 }}>{subtitle}</Text>}
        </div>
        <Tag color="purple" style={{ borderRadius: 999, marginInlineEnd: 0 }}>统一工作流</Tag>
      </div>
      <Row gutter={[12, 12]}>
        {steps.slice(0, 3).map(step => {
          const meta = statusMeta[step.status || 'optional'];
          return (
            <Col xs={24} md={8} key={step.key}>
              <div
                style={{
                  height: '100%',
                  border: '1px solid #f0edff',
                  background: '#fff',
                  borderRadius: 14,
                  padding: 14,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 10,
                }}
              >
                <Space align="start" size={10}>
                  <div style={{
                    width: 34,
                    height: 34,
                    borderRadius: 12,
                    background: '#f3efff',
                    color: '#7c5ce4',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                  }}>
                    {step.icon || <ArrowRightOutlined />}
                  </div>
                  <div style={{ minWidth: 0 }}>
                    <Space size={6} wrap>
                      <Text strong>{step.title}</Text>
                      <Tag color={meta.color} style={{ borderRadius: 999, marginInlineEnd: 0 }}>{meta.label}</Tag>
                    </Space>
                    <Text type="secondary" style={{ fontSize: 12, display: 'block', marginTop: 4 }}>{step.description}</Text>
                  </div>
                </Space>
                <Button
                  size="small"
                  type={step.status === 'recommended' ? 'primary' : 'default'}
                  onClick={() => handleStep(step)}
                  style={{ borderRadius: 999, alignSelf: 'flex-start', marginTop: 'auto' }}
                >
                  {step.actionLabel}
                </Button>
              </div>
            </Col>
          );
        })}
      </Row>
    </Card>
  );
};

export default WorkflowStepGuide;
