import React from 'react';
import { Tag, Tooltip } from 'antd';
import { CheckCircleFilled, WarningFilled, CloseCircleFilled, QuestionCircleFilled } from '@ant-design/icons';

interface CitationVerifyResult {
  index: string;
  status: 'verified' | 'uncertain' | 'likely_hallucination' | 'error';
  confidence: 'high' | 'medium' | 'low';
  sources?: Record<string, string>;
  verified_title?: string;
  suggestion?: { title: string; similarity: number };
}

interface CitationVerifyBadgeProps {
  result: CitationVerifyResult;
  showDetail?: boolean;
}

const statusConfig = {
  verified: { icon: <CheckCircleFilled />, color: 'green', label: '已验证' },
  uncertain: { icon: <WarningFilled />, color: 'orange', label: '待核实' },
  likely_hallucination: { icon: <CloseCircleFilled />, color: 'red', label: '疑似幻觉' },
  error: { icon: <QuestionCircleFilled />, color: 'default', label: '验证失败' },
};

const CitationVerifyBadge: React.FC<CitationVerifyBadgeProps> = ({ result, showDetail }) => {
  const config = statusConfig[result.status] || statusConfig.error;

  const tooltipContent = (
    <div>
      <div>[{result.index}] {result.verified_title || '未知引用'}</div>
      <div>状态: {config.label} (置信度: {result.confidence})</div>
      {result.sources && (
        <div>
          来源: S2={result.sources.semantic_scholar} CR={result.sources.crossref} arXiv={result.sources.arxiv}
        </div>
      )}
      {result.suggestion && (
        <div style={{ marginTop: 4 }}>
          建议替换: {result.suggestion.title} (相似度: {result.suggestion.similarity})
        </div>
      )}
    </div>
  );

  return (
    <Tooltip title={tooltipContent}>
      <Tag icon={config.icon} color={config.color} style={{ cursor: 'pointer' }}>
        [{result.index}]
        {showDetail && ` ${config.label}`}
      </Tag>
    </Tooltip>
  );
};

export default CitationVerifyBadge;
