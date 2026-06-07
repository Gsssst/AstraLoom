import React from 'react';
import { Alert, Space, Tag, Typography } from 'antd';
import type { ApiErrorDetails } from '../services/apiError';

const { Text } = Typography;

type ApiErrorAlertProps = {
  title: string;
  detail: ApiErrorDetails;
  onClose?: () => void;
  style?: React.CSSProperties;
};

const ApiErrorAlert: React.FC<ApiErrorAlertProps> = ({
  title,
  detail,
  onClose,
  style,
}) => (
  <Alert
    type={detail.severity === 'error' ? 'error' : 'warning'}
    showIcon
    closable={!!onClose}
    onClose={onClose}
    style={{ borderRadius: 12, marginBottom: 16, ...style }}
    message={`${title}：${detail.message}`}
    description={(
      <Space direction="vertical" size={6}>
        <Text>{detail.recovery}</Text>
        <Space size={6} wrap>
          <Tag color="orange">{detail.category}</Tag>
          <Tag color={detail.retryable ? 'blue' : 'default'}>
            {detail.retryable ? '可重试' : '需先处理条件'}
          </Tag>
          {detail.status && <Tag>HTTP {detail.status}</Tag>}
        </Space>
      </Space>
    )}
  />
);

export default ApiErrorAlert;
