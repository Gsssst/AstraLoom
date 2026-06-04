import React, { useState, useCallback, useEffect, useRef } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { Spin, Button, Space, Typography, InputNumber } from 'antd';
import { LeftOutlined, RightOutlined } from '@ant-design/icons';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString();

const { Text } = Typography;

interface PDFViewerProps {
  url: string;
  onTextSelect?: (text: string, pageNumber: number) => void;
  targetPage?: number | null;
}

const PDFViewer: React.FC<PDFViewerProps> = ({ url, onTextSelect, targetPage }) => {
  const [numPages, setNumPages] = useState(0);
  const [pageNumber, setPageNumber] = useState(1);
  const [loading, setLoading] = useState(true);
  const [pageWidth, setPageWidth] = useState(700);
  const contentRef = useRef<HTMLDivElement>(null);

  const onDocLoad = useCallback(({ numPages }: any) => {
    setNumPages(numPages);
    setLoading(false);
  }, []);

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
        onTextSelect(text, pageNumber);
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
        <Document file={url} onLoadSuccess={onDocLoad} loading={<Spin style={{ marginTop: 40 }} />}>
          <Page
            pageNumber={pageNumber}
            renderTextLayer={true}
            renderAnnotationLayer={true}
            width={pageWidth}
          />
        </Document>
      </div>
    </div>
  );
};

export default PDFViewer;
