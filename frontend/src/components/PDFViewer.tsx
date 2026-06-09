import React, { useState, useCallback, useEffect, useRef } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { Alert, Spin, Button, Space, Typography, InputNumber } from 'antd';
import { LeftOutlined, RightOutlined } from '@ant-design/icons';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

const pdfWorkerUrl = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString();
pdfjs.GlobalWorkerOptions.workerSrc = pdfWorkerUrl;
if (typeof window !== 'undefined' && 'Worker' in window && !pdfjs.GlobalWorkerOptions.workerPort) {
  try {
    pdfjs.GlobalWorkerOptions.workerPort = new Worker(pdfWorkerUrl, { type: 'module' });
  } catch (error) {
    console.warn('PDF worker initialization fell back to workerSrc.', error);
  }
}

const { Text } = Typography;

interface PDFViewerProps {
  url: string;
  onTextSelect?: (text: string, pageNumber: number, position: { x: number; y: number }) => void;
  targetPage?: number | null;
}

const PDFViewer: React.FC<PDFViewerProps> = ({ url, onTextSelect, targetPage }) => {
  const [numPages, setNumPages] = useState(0);
  const [pageNumber, setPageNumber] = useState(1);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [pageWidth, setPageWidth] = useState(700);
  const contentRef = useRef<HTMLDivElement>(null);
  const resolvedUrl = React.useMemo(() => {
    if (!url) return '';
    if (typeof window === 'undefined') return url;
    return new URL(url, window.location.origin).toString();
  }, [url]);
  const documentFile = React.useMemo(() => ({ url: resolvedUrl }), [resolvedUrl]);

  const onDocLoad = useCallback(({ numPages }: any) => {
    setNumPages(numPages);
    setPageNumber(current => Math.min(Math.max(current, 1), numPages || 1));
    setLoadError(null);
    setLoading(false);
  }, []);

  const onDocLoadError = useCallback((error: Error) => {
    setLoading(false);
    setNumPages(0);
    setLoadError(error?.message || 'PDF 加载失败');
  }, []);

  useEffect(() => {
    setLoading(true);
    setLoadError(null);
    setNumPages(0);
    setPageNumber(1);
  }, [resolvedUrl]);

  useEffect(() => {
    const container = contentRef.current;
    if (!container) return;

    const updatePageWidth = () => {
      setPageWidth(Math.max(280, Math.min(container.clientWidth - 24, 900)));
    };
    updatePageWidth();

    const observer = new ResizeObserver(updatePageWidth);
    observer.observe(container);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!targetPage || targetPage < 1) return;
    setPageNumber(current => {
      const bounded = numPages ? Math.min(targetPage, numPages) : targetPage;
      return current === bounded ? current : bounded;
    });
  }, [targetPage, numPages]);

  // 文本选择事件
  const handleMouseUp = useCallback(() => {
    if (!onTextSelect) return;
    setTimeout(() => {
      const sel = window.getSelection();
      const text = sel?.toString().trim();
      if (text && text.length > 5 && text.length < 800) {
        const range = sel?.rangeCount ? sel.getRangeAt(0) : null;
        const rect = range?.getBoundingClientRect();
        onTextSelect(text, pageNumber, {
          x: rect ? rect.left + rect.width / 2 : window.innerWidth / 2,
          y: rect ? rect.top - 12 : 96,
        });
      }
    }, 100);
  }, [onTextSelect, pageNumber]);

  if (!url) return <Text type="secondary">PDF 不可用</Text>;

  return (
    <div className="paper-pdf-viewer" onMouseUp={handleMouseUp}>
      {/* 导航栏 */}
      <div style={{
        display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 12,
        padding: '8px 12px', borderBottom: '1px solid #f0f0f0', background: '#fafafa',
        flexShrink: 0,
      }}>
        <Button size="small" icon={<LeftOutlined />} disabled={pageNumber <= 1} onClick={() => setPageNumber(p => p - 1)} />
        <Space size={4}>
          <InputNumber size="small" min={1} max={numPages} value={pageNumber} onChange={v => v && setPageNumber(v)} style={{ width: 50 }} />
          <Text type="secondary" style={{ fontSize: 12 }}>/ {numPages}</Text>
        </Space>
        <Button size="small" icon={<RightOutlined />} disabled={pageNumber >= numPages} onClick={() => setPageNumber(p => p + 1)} />
        <Text type="secondary" style={{ fontSize: 12 }}>划词可加入提问</Text>
      </div>

      {/* PDF 内容 */}
      <div ref={contentRef} className="paper-pdf-scroll">
        {loading && <Spin style={{ marginTop: 40 }} />}
        {loadError && (
          <Alert
            type="error"
            showIcon
            style={{ margin: 16, textAlign: 'left' }}
            message="PDF 加载失败"
            description={`请确认 ${resolvedUrl} 返回 application/pdf。浏览器错误：${loadError}`}
          />
        )}
        <Document
          file={documentFile}
          onLoadSuccess={onDocLoad}
          onLoadError={onDocLoadError}
          loading={<Spin style={{ marginTop: 40 }} />}
          error={null}
        >
          <div className="paper-pdf-page">
            <Page
              pageNumber={pageNumber}
              renderTextLayer={true}
              renderAnnotationLayer={true}
              width={pageWidth}
            />
          </div>
        </Document>
      </div>
    </div>
  );
};

export default PDFViewer;
