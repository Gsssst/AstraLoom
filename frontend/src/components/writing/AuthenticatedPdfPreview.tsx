import React, { useEffect, useState } from 'react';
import { Alert, Button, Space, Spin, Typography } from 'antd';
import { EyeOutlined } from '@ant-design/icons';
import api from '../../services/api';

const { Text } = Typography;

interface AuthenticatedPdfPreviewProps {
  previewUrl?: string;
  title?: string;
  height?: number;
}

const AuthenticatedPdfPreview: React.FC<AuthenticatedPdfPreviewProps> = ({
  previewUrl,
  title = 'PDF 预览',
  height = 420,
}) => {
  const [blobUrl, setBlobUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    let objectUrl = '';

    const loadPdf = async () => {
      if (!previewUrl) return;
      setLoading(true);
      setError('');
      setBlobUrl('');
      try {
        const apiUrl = previewUrl.startsWith('/api/') ? previewUrl.slice(4) : previewUrl;
        const response = await api.get(apiUrl, { responseType: 'blob' });
        objectUrl = URL.createObjectURL(response.data);
        if (active) setBlobUrl(objectUrl);
      } catch {
        if (active) setError('PDF 预览加载失败，请重新运行 LaTeX 预览检查。');
      } finally {
        if (active) setLoading(false);
      }
    };

    loadPdf();

    return () => {
      active = false;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [previewUrl]);

  if (!previewUrl) return null;

  return (
    <div style={{ border: '1px solid #e5e7eb', borderRadius: 8, overflow: 'hidden', background: '#fff' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8, padding: '8px 10px', borderBottom: '1px solid #eef0f3' }}>
        <Space size={6}>
          <EyeOutlined />
          <Text strong>{title}</Text>
        </Space>
        <Button size="small" href={blobUrl || undefined} target="_blank" rel="noreferrer" disabled={!blobUrl}>
          打开
        </Button>
      </div>
      {loading && (
        <div style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Spin tip="正在加载 PDF 预览" />
        </div>
      )}
      {!loading && error && (
        <div style={{ padding: 12 }}>
          <Alert type="warning" showIcon message={error} />
        </div>
      )}
      {!loading && !error && blobUrl && (
        <iframe
          title={title}
          src={blobUrl}
          style={{ width: '100%', height, border: 0, display: 'block' }}
        />
      )}
    </div>
  );
};

export default AuthenticatedPdfPreview;
