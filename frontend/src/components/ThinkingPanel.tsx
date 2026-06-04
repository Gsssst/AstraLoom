import React, { useState, useEffect, useRef } from 'react';
import { Typography } from 'antd';
import { BulbOutlined, CaretRightOutlined, CaretDownOutlined } from '@ant-design/icons';

const { Text } = Typography;

interface ThinkingPanelProps {
  reasoningText: string;
  isStreaming: boolean;
  startTime?: number;
}

const ThinkingPanel: React.FC<ThinkingPanelProps> = ({ reasoningText, isStreaming, startTime }) => {
  const [expanded, setExpanded] = useState(false);
  const contentRef = useRef<HTMLDivElement>(null);
  const [elapsed, setElapsed] = useState('0.0s');

  // 计时器
  useEffect(() => {
    if (!isStreaming || !startTime) return;
    const timer = setInterval(() => {
      setElapsed(((Date.now() - startTime) / 1000).toFixed(1) + 's');
    }, 200);
    return () => clearInterval(timer);
  }, [isStreaming, startTime]);

  // 自动滚动
  useEffect(() => {
    if (expanded && contentRef.current) {
      contentRef.current.scrollTop = contentRef.current.scrollHeight;
    }
  }, [reasoningText, expanded]);

  if (!reasoningText && !isStreaming) return null;

  return (
    <div style={{
      marginBottom: 8,
      borderRadius: 8,
      border: '1px solid #e8d5a3',
      background: '#fefcf5',
      overflow: 'hidden',
    }}>
      {/* 折叠栏 */}
      <div
        onClick={() => setExpanded(!expanded)}
        style={{
          padding: '6px 12px',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          userSelect: 'none',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <BulbOutlined style={{ color: '#faad14' }} />
          <Text style={{ fontSize: 12, color: '#8c7a3c' }}>
            {isStreaming ? `思考中... (${elapsed})` : `思考完成 (${elapsed})`}
          </Text>
        </div>
        {expanded ? <CaretDownOutlined style={{ color: '#bbb' }} /> : <CaretRightOutlined style={{ color: '#bbb' }} />}
      </div>

      {/* 展开内容 */}
      {expanded && (
        <div
          ref={contentRef}
          style={{
            maxHeight: 300,
            overflowY: 'auto',
            padding: '8px 12px',
            borderTop: '1px solid #f0e5c0',
            background: '#fdfaf0',
            fontFamily: "'SF Mono', 'Fira Code', 'Menlo', 'Consolas', monospace",
            fontSize: 12,
            lineHeight: 1.7,
            color: '#8c7a3c',
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
          }}
        >
          {reasoningText || (isStreaming ? '思考中...' : '')}
        </div>
      )}
    </div>
  );
};

export default ThinkingPanel;
