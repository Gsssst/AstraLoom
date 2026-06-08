import React from 'react';
import { Card, Empty, Space, Tag, Tooltip, Typography } from 'antd';
import { NodeIndexOutlined } from '@ant-design/icons';

const { Text } = Typography;

export interface ResearchGraphNode {
  id: string;
  label: string;
  type: string;
  status?: string;
  weight?: number;
  href?: string;
}

export interface ResearchGraphEdge {
  from: string;
  to: string;
  label: string;
  strength?: 'strong' | 'medium' | 'weak';
}

interface ResearchKnowledgeGraphProps {
  title?: React.ReactNode;
  nodes: ResearchGraphNode[];
  edges: ResearchGraphEdge[];
  compact?: boolean;
  maxNodes?: number;
}

const typeColor: Record<string, string> = {
  paper: 'geekblue',
  evidence: 'gold',
  idea: 'purple',
  writing: 'cyan',
  section: 'blue',
  citation: 'green',
  experiment: 'volcano',
  note: 'magenta',
};

const edgeColor: Record<string, string> = {
  strong: 'green',
  medium: 'blue',
  weak: 'default',
};

const ResearchKnowledgeGraph: React.FC<ResearchKnowledgeGraphProps> = ({
  title = '研究知识图谱',
  nodes,
  edges,
  compact = false,
  maxNodes = 10,
}) => {
  const visibleNodes = nodes.slice(0, maxNodes);
  const nodeById = new Map(nodes.map(node => [node.id, node]));
  const visibleNodeIds = new Set(visibleNodes.map(node => node.id));
  const visibleEdges = edges
    .filter(edge => visibleNodeIds.has(edge.from) && visibleNodeIds.has(edge.to))
    .slice(0, compact ? 5 : 8);

  return (
    <Card
      size="small"
      className="research-knowledge-graph"
      title={<Space size={6}><NodeIndexOutlined /><span>{title}</span></Space>}
      extra={<Tag color="purple">{nodes.length} 节点</Tag>}
      style={{ borderRadius: 12 }}
    >
      {visibleNodes.length ? (
        <Space direction="vertical" size={10} style={{ width: '100%' }}>
          <div className="research-graph-node-grid">
            {visibleNodes.map(node => (
              <Tooltip key={node.id} title={`${node.type}${node.status ? ` · ${node.status}` : ''}`}>
                <a
                  className="research-graph-node"
                  href={node.href}
                  onClick={event => { if (!node.href) event.preventDefault(); }}
                >
                  <Tag color={typeColor[node.type] || 'default'}>{node.type}</Tag>
                  <Text strong ellipsis>{node.label}</Text>
                  {node.status && <Text type="secondary">{node.status}</Text>}
                </a>
              </Tooltip>
            ))}
          </div>
          {visibleEdges.length > 0 && (
            <div className="research-graph-edge-list">
              {visibleEdges.map((edge, index) => {
                const from = nodeById.get(edge.from);
                const to = nodeById.get(edge.to);
                return (
                  <div className="research-graph-edge" key={`${edge.from}-${edge.to}-${index}`}>
                    <Text ellipsis>{from?.label || edge.from}</Text>
                    <Tag color={edgeColor[edge.strength || 'weak']}>{edge.label}</Tag>
                    <Text ellipsis>{to?.label || edge.to}</Text>
                  </div>
                );
              })}
            </div>
          )}
        </Space>
      ) : (
        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无可连接的研究对象" />
      )}
    </Card>
  );
};

export default ResearchKnowledgeGraph;
