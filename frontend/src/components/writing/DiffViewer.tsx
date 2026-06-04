import React, { useState } from 'react';
import { Button, Space, Tag, Tooltip, message } from 'antd';
import { CheckOutlined, CloseOutlined } from '@ant-design/icons';

interface DiffHunk {
  index: number;
  type: 'equal' | 'add' | 'delete' | 'replace';
  original: string;
  polished: string;
  position: number;
  accepted: boolean | null;
}

interface DiffViewerProps {
  original: string;
  polished: string;
  diff: { hunks: DiffHunk[]; stats: { additions: number; deletions: number; equal: number; replacements: number } };
  onApply: (result: string) => void;
  onCancel: () => void;
}

const DiffViewer: React.FC<DiffViewerProps> = ({ diff, onApply, onCancel }) => {
  const [acceptedIndices, setAcceptedIndices] = useState<Set<number>>(new Set());
  const [rejectedIndices, setRejectedIndices] = useState<Set<number>>(new Set());

  const toggleAccept = (index: number) => {
    const newAccepted = new Set(acceptedIndices);
    const newRejected = new Set(rejectedIndices);
    if (newAccepted.has(index)) {
      newAccepted.delete(index);
    } else {
      newAccepted.add(index);
      newRejected.delete(index);
    }
    setAcceptedIndices(newAccepted);
    setRejectedIndices(newRejected);
  };

  const toggleReject = (index: number) => {
    const newRejected = new Set(rejectedIndices);
    const newAccepted = new Set(acceptedIndices);
    if (newRejected.has(index)) {
      newRejected.delete(index);
    } else {
      newRejected.add(index);
      newAccepted.delete(index);
    }
    setRejectedIndices(newRejected);
    setAcceptedIndices(newAccepted);
  };

  const handleAcceptAll = () => {
    setAcceptedIndices(new Set(diff.hunks.filter(h => h.type !== 'equal').map(h => h.index)));
    setRejectedIndices(new Set());
  };

  const handleRejectAll = () => {
    setRejectedIndices(new Set(diff.hunks.filter(h => h.type !== 'equal').map(h => h.index)));
    setAcceptedIndices(new Set());
  };

  const handleApply = () => {
    // Equal hunks always accepted; for others, check if explicitly accepted
    const allAccepted = new Set(acceptedIndices);
    diff.hunks.filter(h => h.type === 'equal').forEach(h => allAccepted.add(h.index));

    const parts: string[] = [];
    const sorted = [...diff.hunks].sort((a, b) => a.position - b.position);
    for (const hunk of sorted) {
      if (allAccepted.has(hunk.index)) {
        if (hunk.type === 'add' || hunk.type === 'replace') parts.push(hunk.polished);
        else if (hunk.type === 'equal') parts.push(hunk.original);
        // delete accepted → skip
      } else {
        if (hunk.type === 'equal' || hunk.type === 'delete' || hunk.type === 'replace') parts.push(hunk.original);
        // add rejected → skip
      }
    }
    onApply(parts.join(' '));
    message.success('已应用选中的修改');
  };

  const hunkColor = (type: string) => {
    switch (type) {
      case 'add': return { bg: '#e6ffec', border: '#34d058', label: '+ 新增' };
      case 'delete': return { bg: '#ffeef0', border: '#d73a49', label: '- 删除' };
      case 'replace': return { bg: '#fff5e6', border: '#f0883e', label: '~ 修改' };
      default: return { bg: 'transparent', border: 'transparent', label: '' };
    }
  };

  const changeCount = diff.stats.additions + diff.stats.deletions + diff.stats.replacements;

  return (
    <div style={{ border: '1px solid #e8e8e8', borderRadius: 8, overflow: 'hidden' }}>
      <div style={{
        padding: '8px 16px', background: '#fafafa', borderBottom: '1px solid #e8e8e8',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      }}>
        <Space>
          <Tag color="blue">{changeCount} 处修改</Tag>
          <Tag color="green">{diff.stats.additions} 新增</Tag>
          <Tag color="red">{diff.stats.deletions} 删除</Tag>
          <Tag color="orange">{diff.stats.replacements} 替换</Tag>
        </Space>
        <Space>
          <Button size="small" onClick={handleAcceptAll}>全部接受</Button>
          <Button size="small" onClick={handleRejectAll}>全部拒绝</Button>
        </Space>
      </div>

      <div style={{ maxHeight: 500, overflowY: 'auto', padding: 8 }}>
        {diff.hunks.map((hunk) => {
          const colors = hunkColor(hunk.type);
          const isAccepted = acceptedIndices.has(hunk.index);
          const isRejected = rejectedIndices.has(hunk.index);
          const isEqual = hunk.type === 'equal';

          return (
            <div key={hunk.index} style={{
              marginBottom: 4, padding: 6, borderRadius: 6,
              background: colors.bg, borderLeft: `3px solid ${colors.border}`,
              opacity: isRejected ? 0.4 : 1,
            }}>
              {!isEqual && (
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                  <Tag color={isAccepted ? 'green' : 'default'} style={{ fontSize: 11 }}>
                    {colors.label}
                    {isAccepted ? ' ✓' : isRejected ? ' ✗' : ''}
                  </Tag>
                  <Space size="small">
                    <Tooltip title="接受此修改">
                      <Button size="small" type={isAccepted ? 'primary' : 'text'} icon={<CheckOutlined />}
                        onClick={() => toggleAccept(hunk.index)} />
                    </Tooltip>
                    <Tooltip title="拒绝此修改">
                      <Button size="small" type={isRejected ? 'primary' : 'text'} danger icon={<CloseOutlined />}
                        onClick={() => toggleReject(hunk.index)} />
                    </Tooltip>
                  </Space>
                </div>
              )}
              <div style={{ display: 'flex', gap: 12 }}>
                {hunk.type === 'replace' ? (
                  <>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 11, color: '#d73a49', marginBottom: 2 }}>原文:</div>
                      <div style={{ fontSize: 13, color: '#d73a49', textDecoration: 'line-through' }}>{hunk.original}</div>
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 11, color: '#34d058', marginBottom: 2 }}>润色:</div>
                      <div style={{ fontSize: 13, color: '#34d058' }}>{hunk.polished}</div>
                    </div>
                  </>
                ) : hunk.type === 'add' ? (
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 11, color: '#34d058', marginBottom: 2 }}>新增:</div>
                    <div style={{ fontSize: 13, color: '#34d058' }}>{hunk.polished}</div>
                  </div>
                ) : hunk.type === 'delete' ? (
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 11, color: '#d73a49', marginBottom: 2 }}>删除:</div>
                    <div style={{ fontSize: 13, color: '#d73a49', textDecoration: 'line-through' }}>{hunk.original}</div>
                  </div>
                ) : (
                  <div style={{ flex: 1, fontSize: 13, color: '#666' }}>{hunk.original}</div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <div style={{ padding: '8px 16px', borderTop: '1px solid #e8e8e8', display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
        <Button onClick={onCancel}>取消</Button>
        <Button type="primary" onClick={handleApply}>应用选中的修改</Button>
      </div>
    </div>
  );
};

export default DiffViewer;
