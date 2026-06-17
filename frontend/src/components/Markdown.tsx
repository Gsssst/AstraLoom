import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';
import { Button, message } from 'antd';
import { CopyOutlined, CheckOutlined } from '@ant-design/icons';

export interface MarkdownEvidenceLink {
  id: string;
  label?: string;
  title?: string;
  disabled?: boolean;
  onClick?: () => void;
}

interface MarkdownProps {
  content: string;
  evidenceLinks?: Record<string, MarkdownEvidenceLink>;
}

const FENCED_CODE_BLOCK_RE = /(```[\s\S]*?```|~~~[\s\S]*?~~~)/g;
const LATEX_COMMAND_RE = /\\[a-zA-Z]+/;
const LATEX_STRUCTURE_RE = /(?:[_^{}]|\\[,;! ]|\\[()[\]]|\\[{}]|\\[|]\s*\\|[=<>]\s*\\|\\\||\\&|\\\\)/;
const LATEX_OPERATOR_RE = /(?:=|\\leq?|\\geq?|\\neq|\\approx|\\sim|\\times|\\cdot|\\pm|\\mp|\\sum|\\prod|\\int|\\frac|\\sqrt)/;

const looksLikeLatexMath = (value: string) => {
  const expression = value.trim();
  if (!expression || expression.length < 3) return false;
  if (/^[A-Za-z]?\d+$/.test(expression)) return false;
  if (/^E\d+(?:[,;\s]+E\d+)*$/.test(expression)) return false;
  if (LATEX_COMMAND_RE.test(expression)) return true;
  if (LATEX_OPERATOR_RE.test(expression)) return true;
  if (LATEX_STRUCTURE_RE.test(expression) && /[A-Za-z0-9]/.test(expression)) return true;
  return false;
};

const normalizeMathInTextSegment = (segment: string) => {
  const normalizedDelimiters = segment
    .replace(/\\\[\s*([\s\S]*?)\s*\\\]/g, (_, expression: string) => `\n$$\n${expression.trim()}\n$$\n`)
    .replace(/\\\(([\s\S]*?)\\\)/g, (_, expression: string) => `$${expression.trim()}$`);

  return normalizedDelimiters
    .split('\n')
    .map((line) => {
      const match = line.match(/^(\s*)\[\s*(.+?)\s*\](\s*)$/);
      if (!match) return line;

      const [, prefix, expression, suffix] = match;
      if (!looksLikeLatexMath(expression)) return line;
      return `${prefix}$$\n${expression.trim()}\n${prefix}$$${suffix}`;
    })
    .join('\n');
};

export const normalizeMarkdownMath = (value: string) => {
  if (!value) return value;
  return value
    .split(FENCED_CODE_BLOCK_RE)
    .map((segment) => {
      if (segment.startsWith('```') || segment.startsWith('~~~')) return segment;
      return normalizeMathInTextSegment(segment);
    })
    .join('');
};

const CodeBlock: React.FC<{ children: string; className?: string }> = ({ children, className }) => {
  const [copied, setCopied] = useState(false);
  const handleCopy = () => {
    navigator.clipboard.writeText(children).then(() => {
      setCopied(true); setTimeout(() => setCopied(false), 2000);
      message.success('已复制');
    });
  };
  return (
    <div style={{ position: 'relative' }}>
      <Button
        size="small" type="text"
        icon={copied ? <CheckOutlined style={{ color: '#52c41a' }} /> : <CopyOutlined />}
        onClick={handleCopy}
        style={{
          position: 'absolute', top: 8, right: 8, zIndex: 1,
          color: '#999', fontSize: 12,
        }}
      />
      <pre style={{ background: '#1e1e1e', color: '#d4d4d4', padding: '16px 40px 16px 16px', borderRadius: 8, overflow: 'auto', fontSize: 13, lineHeight: 1.5 }}>
        <code className={className}>{children}</code>
      </pre>
    </div>
  );
};

const EVIDENCE_MARKER_RE = /\[(E\d+)\]/g;
const EVIDENCE_LINK_PREFIX = '#paper-evidence-';

export const linkMarkdownEvidenceMarkers = (
  value: string,
  evidenceLinks?: Record<string, MarkdownEvidenceLink>,
) => {
  if (!value || !evidenceLinks) return value;
  return value
    .split(FENCED_CODE_BLOCK_RE)
    .map((segment) => {
      if (segment.startsWith('```') || segment.startsWith('~~~')) return segment;
      return segment.replace(/\[(E\d+)\](?!\()/gi, (marker, rawId: string) => {
        const id = rawId.toUpperCase();
        return evidenceLinks[id] ? `[${id}](${EVIDENCE_LINK_PREFIX}${id})` : marker;
      });
    })
    .join('');
};

const renderEvidenceLinkedText = (
  children: React.ReactNode,
  evidenceLinks?: Record<string, MarkdownEvidenceLink>,
) => {
  if (!evidenceLinks || typeof children !== 'string' || !/\[E\d+\]/.test(children)) {
    return children;
  }

  EVIDENCE_MARKER_RE.lastIndex = 0;
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;
  while ((match = EVIDENCE_MARKER_RE.exec(children)) !== null) {
    const [marker, id] = match;
    if (match.index > lastIndex) parts.push(children.slice(lastIndex, match.index));
    const link = evidenceLinks[id];
    if (link) {
      parts.push(
        <button
          key={`${id}-${match.index}`}
          type="button"
          className={`markdown-evidence-link ${link.disabled ? 'is-disabled' : ''}`}
          title={link.title}
          disabled={link.disabled}
          onClick={link.onClick}
        >
          {link.label || marker}
        </button>,
      );
    } else {
      parts.push(marker);
    }
    lastIndex = match.index + marker.length;
  }
  if (lastIndex < children.length) parts.push(children.slice(lastIndex));
  return parts;
};

/** 全局 Markdown 渲染组件，支持 GFM 表格、LaTeX 数学公式 */
const Markdown: React.FC<MarkdownProps> = ({ content, evidenceLinks }) => {
  const normalizedContent = linkMarkdownEvidenceMarkers(normalizeMarkdownMath(content), evidenceLinks);

  return (
    <div className="markdown-body app-markdown" style={{ lineHeight: 1.8, fontSize: 14 }}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeKatex]}
        components={{
          // 代码块渲染
          code({ node, className, children, ...props }: any) {
            const match = /language-(\w+)/.exec(className || '');
            const inline = !match;
            return inline ? (
              <code className={className} {...props} style={{
                background: '#f5f5f5', padding: '2px 6px', borderRadius: 4,
                fontSize: '0.9em', fontFamily: 'monospace',
              }}>
                {children}
              </code>
            ) : (
              <CodeBlock className={className}>{String(children)}</CodeBlock>
            );
          },
          // 表格渲染
          table({ children }) {
            return (
              <div style={{ overflowX: 'auto', margin: '12px 0' }}>
                <table style={{
                  borderCollapse: 'collapse', width: '100%',
                  border: '1px solid #e5e5e5',
                }}>
                  {children}
                </table>
              </div>
            );
          },
          th({ children }) {
            return <th style={{ border: '1px solid #e5e5e5', padding: '8px 12px', background: '#f5f5f5', fontWeight: 600, textAlign: 'left' }}>{children}</th>;
          },
          td({ children }) {
            return <td style={{ border: '1px solid #e5e5e5', padding: '8px 12px' }}>{children}</td>;
          },
          // 链接在新窗口打开
          a({ href, children }) {
            const evidenceMatch = String(href || '').match(/^#paper-evidence-(E\d+)$/i);
            if (evidenceMatch) {
              const id = evidenceMatch[1].toUpperCase();
              const link = evidenceLinks?.[id];
              return (
                <button
                  type="button"
                  className={`markdown-evidence-link ${link?.disabled ? 'is-disabled' : ''}`}
                  title={link?.title}
                  disabled={link?.disabled}
                  onClick={link?.onClick}
                >
                  {link?.label || `[${id}]`}
                </button>
              );
            }
            return <a href={href} target="_blank" rel="noopener noreferrer">{children}</a>;
          },
          // 引用块
          blockquote({ children }) {
            return <blockquote style={{
              borderLeft: '4px solid #1677ff', padding: '8px 16px',
              margin: '12px 0', background: '#f0f5ff', borderRadius: '0 8px 8px 0',
              color: '#555',
            }}>{children}</blockquote>;
          },
          text({ children }) {
            return <>{renderEvidenceLinkedText(children, evidenceLinks)}</>;
          },
        }}
      >
        {normalizedContent}
      </ReactMarkdown>
    </div>
  );
};

export default Markdown;
