import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';
import { Button, message } from 'antd';
import { CopyOutlined, CheckOutlined } from '@ant-design/icons';

interface MarkdownProps {
  content: string;
}

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

/** 全局 Markdown 渲染组件，支持 GFM 表格、LaTeX 数学公式 */
const Markdown: React.FC<MarkdownProps> = ({ content }) => {
  return (
    <div className="markdown-body" style={{ lineHeight: 1.8, fontSize: 14 }}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
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
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};

export default Markdown;
