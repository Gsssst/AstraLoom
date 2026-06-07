import React, { useState } from 'react';
import { Alert, Button, Empty, Form, Input, List, Modal, Select, Space, Tag, Typography, message } from 'antd';
import { BugOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { getApiErrorDetails } from '../services/apiError';

const { Text } = Typography;

interface WorkspaceIssueReporterProps {
  resourceType: string;
  resourceId: string;
  resourceTitle: string;
  resourcePath: string;
}

const WorkspaceIssueReporter: React.FC<WorkspaceIssueReporterProps> = ({
  resourceType,
  resourceId,
  resourceTitle,
  resourcePath,
}) => {
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [open, setOpen] = useState(false);
  const [spaces, setSpaces] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [errorText, setErrorText] = useState('');

  const loadSpaces = async () => {
    setOpen(true);
    setLoading(true);
    setErrorText('');
    try {
      const response = await api.get('/workspaces/resource-links', {
        params: { resource_type: resourceType, resource_id: resourceId },
      });
      const linkedSpaces = (response.data.spaces || []).filter((space: any) => space.linked);
      setSpaces(linkedSpaces);
      if (linkedSpaces[0]) form.setFieldsValue({ space_id: linkedSpaces[0].id });
    } catch (error: any) {
      const detail = getApiErrorDetails(error, { fallback: '项目空间加载失败' });
      setErrorText(detail.message);
    } finally {
      setLoading(false);
    }
  };

  const submitIssue = async () => {
    const values = await form.validateFields();
    setSubmitting(true);
    try {
      const response = await api.post(`/workspaces/${values.space_id}/issues`, {
        title: values.title,
        description: values.description || '',
        issue_type: values.issue_type || 'feedback',
        priority: values.priority || 'medium',
        labels: values.labels || [],
        resource_reference: {
          resource_type: resourceType,
          resource_id: resourceId,
          title: resourceTitle,
          path: resourcePath,
          source_label: '资源反馈',
        },
      });
      message.success('反馈 Issue 已提交');
      setOpen(false);
      form.resetFields();
      navigate(`/workspaces/${values.space_id}?issue=${response.data.id}`);
    } catch (error: any) {
      const detail = getApiErrorDetails(error, { fallback: '反馈 Issue 提交失败' });
      setErrorText(detail.message);
      message.warning(detail.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <Button size="small" icon={<BugOutlined />} onClick={loadSpaces}>
        提 Issue
      </Button>
      <Modal
        title="向项目空间提交 Issue"
        open={open}
        onCancel={() => setOpen(false)}
        onOk={submitIssue}
        confirmLoading={submitting}
        okButtonProps={{ disabled: loading || !spaces.length }}
        okText="提交"
      >
        <Space direction="vertical" size={12} style={{ width: '100%' }}>
          {errorText && <Alert type="warning" showIcon message={errorText} />}
          <Text type="secondary">当前资源：{resourceTitle}</Text>
          {spaces.length ? (
            <Form
              form={form}
              layout="vertical"
              initialValues={{ issue_type: 'feedback', priority: 'medium', labels: [] }}
            >
              <Form.Item name="space_id" label="项目空间" rules={[{ required: true, message: '请选择项目空间' }]}>
                <Select
                  loading={loading}
                  options={spaces.map(space => ({
                    value: space.id,
                    label: `${space.name}（${space.role}）`,
                  }))}
                />
              </Form.Item>
              <Form.Item name="title" label="标题" rules={[{ required: true, message: '请输入 Issue 标题' }]}>
                <Input placeholder="描述这个资源的问题、建议或后续任务" />
              </Form.Item>
              <Form.Item name="description" label="描述">
                <Input.TextArea autoSize={{ minRows: 3, maxRows: 6 }} placeholder="补充上下文、现象、期望结果或处理建议" />
              </Form.Item>
              <Space size={8} style={{ width: '100%' }}>
                <Form.Item name="issue_type" label="类型" style={{ flex: 1 }}>
                  <Select options={[
                    { value: 'feedback', label: '反馈' },
                    { value: 'bug', label: 'Bug' },
                    { value: 'idea', label: '想法' },
                    { value: 'question', label: '问题' },
                    { value: 'task', label: '任务' },
                  ]} />
                </Form.Item>
                <Form.Item name="priority" label="优先级" style={{ flex: 1 }}>
                  <Select options={[
                    { value: 'low', label: '低' },
                    { value: 'medium', label: '中' },
                    { value: 'high', label: '高' },
                    { value: 'urgent', label: '紧急' },
                  ]} />
                </Form.Item>
              </Space>
              <Form.Item name="labels" label="标签">
                <Select mode="tags" tokenSeparators={[',', '，']} placeholder="例如 ui、证据、写作" />
              </Form.Item>
            </Form>
          ) : (
            <List
              loading={loading}
              locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="这个资源还没有绑定项目空间" /> }}
              dataSource={spaces}
              renderItem={space => <List.Item><Tag>{space.name}</Tag></List.Item>}
            />
          )}
        </Space>
      </Modal>
    </>
  );
};

export default WorkspaceIssueReporter;
