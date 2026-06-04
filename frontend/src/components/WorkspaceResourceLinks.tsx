import React, { useEffect, useState } from 'react';
import { AppstoreOutlined, MinusCircleOutlined, PlusOutlined } from '@ant-design/icons';
import { Alert, Button, Card, Empty, List, Space, Tag, Typography, message } from 'antd';
import api from '../services/api';

const { Text } = Typography;

interface WorkspaceLink {
  id: string;
  name: string;
  description?: string;
  role: string;
  linked: boolean;
  can_edit: boolean;
  member_count?: number;
}

interface WorkspaceResourceLinksProps {
  resourceType: 'papers' | 'research_projects' | 'writing_projects';
  resourceId?: string | null;
  title?: string;
}

const WorkspaceResourceLinks: React.FC<WorkspaceResourceLinksProps> = ({
  resourceType,
  resourceId,
  title = '项目空间',
}) => {
  const [spaces, setSpaces] = useState<WorkspaceLink[]>([]);
  const [loading, setLoading] = useState(false);
  const [updatingSpaceId, setUpdatingSpaceId] = useState<string | null>(null);

  const fetchLinks = async () => {
    if (!resourceId) return;
    setLoading(true);
    try {
      const response = await api.get('/workspaces/resource-links', {
        params: { resource_type: resourceType, resource_id: resourceId },
      });
      setSpaces(response.data.spaces || []);
    } catch (error: any) {
      message.error(error.response?.data?.detail || '项目空间关联加载失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLinks();
  }, [resourceType, resourceId]);

  const linkResource = async (space: WorkspaceLink) => {
    if (!resourceId) return;
    setUpdatingSpaceId(space.id);
    try {
      await api.post(`/workspaces/${space.id}/resources`, {
        resource_type: resourceType,
        resource_id: resourceId,
      });
      message.success('已加入项目空间');
      await fetchLinks();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '加入项目空间失败');
    } finally {
      setUpdatingSpaceId(null);
    }
  };

  const unlinkResource = async (space: WorkspaceLink) => {
    if (!resourceId) return;
    setUpdatingSpaceId(space.id);
    try {
      await api.delete(`/workspaces/${space.id}/resources/${resourceType}/${resourceId}`);
      message.success('已从项目空间移除');
      await fetchLinks();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '移除项目空间失败');
    } finally {
      setUpdatingSpaceId(null);
    }
  };

  if (!resourceId) return null;

  const linkedSpaces = spaces.filter(space => space.linked);
  const availableSpaces = spaces.filter(space => !space.linked && space.can_edit);

  return (
    <Card
      size="small"
      title={<Space><AppstoreOutlined />{title}</Space>}
      style={{ borderRadius: 12 }}
      extra={<Button size="small" type="link" onClick={fetchLinks} loading={loading}>刷新</Button>}
    >
      {spaces.length === 0 ? (
        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="还没有可用项目空间" />
      ) : (
        <Space direction="vertical" style={{ width: '100%' }} size={12}>
          {linkedSpaces.length > 0 ? (
            <List
              size="small"
              dataSource={linkedSpaces}
              renderItem={(space) => (
                <List.Item
                  actions={space.can_edit ? [
                    <Button
                      key="unlink"
                      size="small"
                      danger
                      icon={<MinusCircleOutlined />}
                      loading={updatingSpaceId === space.id}
                      onClick={() => unlinkResource(space)}
                    >
                      移出
                    </Button>,
                  ] : []}
                >
                  <List.Item.Meta
                    title={<Space><Text strong>{space.name}</Text><Tag color="green">已加入</Tag><Tag>{space.role}</Tag></Space>}
                    description={space.description || `${space.member_count || 1} 人协作`}
                  />
                </List.Item>
              )}
            />
          ) : (
            <Alert type="info" showIcon message="当前资源还没有加入项目空间" />
          )}

          {availableSpaces.length > 0 && (
            <List
              size="small"
              header={<Text type="secondary">可加入空间</Text>}
              dataSource={availableSpaces}
              renderItem={(space) => (
                <List.Item
                  actions={[
                    <Button
                      key="link"
                      size="small"
                      icon={<PlusOutlined />}
                      loading={updatingSpaceId === space.id}
                      onClick={() => linkResource(space)}
                    >
                      加入
                    </Button>,
                  ]}
                >
                  <List.Item.Meta
                    title={<Space><Text>{space.name}</Text><Tag>{space.role}</Tag></Space>}
                    description={space.description || `${space.member_count || 1} 人协作`}
                  />
                </List.Item>
              )}
            />
          )}

          {availableSpaces.length === 0 && linkedSpaces.length > 0 && (
            <Text type="secondary" style={{ fontSize: 12 }}>
              没有更多可加入的空间，或你在其他空间中没有绑定权限。
            </Text>
          )}
        </Space>
      )}
    </Card>
  );
};

export default WorkspaceResourceLinks;
