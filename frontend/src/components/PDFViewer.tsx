import React, { useState, useCallback, useEffect, useRef } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { Alert, Spin, Button, Space, Typography, InputNumber, Tooltip } from 'antd';
import { ZoomInOutlined } from '@ant-design/icons';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

const pdfWorkerUrl = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString();
const versionedPdfWorkerUrl = `${pdfWorkerUrl}?v=2026-06-10-1`;
pdfjs.GlobalWorkerOptions.workerSrc = versionedPdfWorkerUrl;

const { Text } = Typography;
const PDF_LOAD_TIMEOUT_MS = 20000;
const PDF_EVIDENCE_LOCATOR_RETRY_MS = 180;
const PDF_EVIDENCE_LOCATOR_MAX_ATTEMPTS = 14;
const PDF_EVIDENCE_HIGHLIGHT_MS = 6500;
const PDF_MAGNIFIER_SIZE = 224;
const PDF_MAGNIFIER_SCALE = 2.15;
const PDF_MAGNIFIER_OFFSET = 18;

interface PDFTargetLocator {
  page: number;
  snippet?: string | null;
  requestId: number;
}

interface PDFTargetLocatorResult {
  requestId: number;
  page: number;
  matched: boolean;
  reason?: 'no_snippet' | 'native_fallback' | 'not_found';
}

interface PDFViewerProps {
  url: string;
  onTextSelect?: (text: string, pageNumber: number, position: { x: number; y: number }) => void;
  onPageChange?: (pageNumber: number) => void;
  targetPage?: number | null;
  targetLocator?: PDFTargetLocator | null;
  onTargetLocatorResult?: (result: PDFTargetLocatorResult) => void;
}

interface PDFMagnifierState {
  visible: boolean;
  page: number | null;
  left: number;
  top: number;
  pageWidth: number;
  pageHeight: number;
  transform: string;
}

const PDFViewer: React.FC<PDFViewerProps> = ({
  url,
  onTextSelect,
  onPageChange,
  targetPage,
  targetLocator,
  onTargetLocatorResult,
}) => {
  const [numPages, setNumPages] = useState(0);
  const [pageNumber, setPageNumber] = useState(1);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [nativeFallback, setNativeFallback] = useState(false);
  const [pageWidth, setPageWidth] = useState(700);
  const [magnifierEnabled, setMagnifierEnabled] = useState(false);
  const [magnifierState, setMagnifierState] = useState<PDFMagnifierState>({
    visible: false,
    page: null,
    left: 0,
    top: 0,
    pageWidth: 0,
    pageHeight: 0,
    transform: '',
  });
  const contentRef = useRef<HTMLDivElement>(null);
  const magnifierContentRef = useRef<HTMLDivElement>(null);
  const pageRefs = useRef<Map<number, HTMLDivElement>>(new Map());
  const activeEvidenceHighlightRef = useRef<HTMLElement[]>([]);
  const evidenceHighlightTimeoutRef = useRef<number | null>(null);
  const handledTargetPageRef = useRef<number | null>(null);
  const handledLocatorRequestIdsRef = useRef<Set<number>>(new Set());
  const resolvedUrl = React.useMemo(() => {
    if (!url) return '';
    if (typeof window === 'undefined') return url;
    return new URL(url, window.location.origin).toString();
  }, [url]);
  const documentFile = React.useMemo(() => ({
    url: resolvedUrl,
    disableRange: true,
    disableStream: true,
    disableAutoFetch: true,
  }), [resolvedUrl]);

  const clearEvidenceHighlight = useCallback(() => {
    if (evidenceHighlightTimeoutRef.current) {
      window.clearTimeout(evidenceHighlightTimeoutRef.current);
      evidenceHighlightTimeoutRef.current = null;
    }
    activeEvidenceHighlightRef.current.forEach(node => node.classList.remove('paper-pdf-evidence-hit'));
    activeEvidenceHighlightRef.current = [];
  }, []);

  const hideMagnifier = useCallback(() => {
    setMagnifierState(current => (current.visible ? { ...current, visible: false } : current));
  }, []);

  const copyCanvasPixelsToClone = useCallback((sourcePage: HTMLElement, clonedPage: HTMLElement) => {
    const sourceCanvases = Array.from(sourcePage.querySelectorAll<HTMLCanvasElement>('canvas'));
    const clonedCanvases = Array.from(clonedPage.querySelectorAll<HTMLCanvasElement>('canvas'));
    sourceCanvases.forEach((sourceCanvas, index) => {
      const clonedCanvas = clonedCanvases[index];
      if (!clonedCanvas) return;
      try {
        clonedCanvas.width = sourceCanvas.width;
        clonedCanvas.height = sourceCanvas.height;
        clonedCanvas.style.width = sourceCanvas.style.width;
        clonedCanvas.style.height = sourceCanvas.style.height;
        const context = clonedCanvas.getContext('2d');
        context?.drawImage(sourceCanvas, 0, 0);
      } catch {
        // Some browser security modes can block canvas copying. The text layer
        // still remains visible in the loupe, so keep the magnifier usable.
      }
    });
  }, []);

  const clonePageIntoMagnifier = useCallback((page: number | null) => {
    const target = magnifierContentRef.current;
    if (!target || !page) return;
    const sourcePage = pageRefs.current.get(page)?.querySelector<HTMLElement>('.react-pdf__Page');
    if (!sourcePage) return;
    const existingPage = target.querySelector<HTMLElement>('.react-pdf__Page');
    if (existingPage?.dataset.magnifierPage === String(page)) return;

    const clonedPage = sourcePage.cloneNode(true) as HTMLElement;
    clonedPage.dataset.magnifierPage = String(page);
    clonedPage.classList.add('paper-pdf-magnifier-page-clone');
    clonedPage.setAttribute('aria-hidden', 'true');
    copyCanvasPixelsToClone(sourcePage, clonedPage);
    target.replaceChildren(clonedPage);
  }, [copyCanvasPixelsToClone]);

  const onDocLoad = useCallback(({ numPages }: any) => {
    setNumPages(numPages);
    setPageNumber(current => {
      const nextPage = Math.min(Math.max(current, 1), numPages || 1);
      onPageChange?.(nextPage);
      return nextPage;
    });
    setLoadError(null);
    setNativeFallback(false);
    setLoading(false);
  }, [onPageChange]);

  const onDocLoadError = useCallback((error: Error) => {
    setLoading(false);
    setNumPages(0);
    setLoadError(error?.message || 'PDF 加载失败');
    setNativeFallback(true);
  }, []);

  const retryEnhancedReader = useCallback(() => {
    setNativeFallback(false);
    setLoading(true);
    setLoadError(null);
    setNumPages(0);
    setPageNumber(1);
  }, []);

  useEffect(() => {
    clearEvidenceHighlight();
    hideMagnifier();
    handledTargetPageRef.current = null;
    handledLocatorRequestIdsRef.current.clear();
    setLoading(true);
    setLoadError(null);
    setNativeFallback(false);
    setNumPages(0);
    setPageNumber(1);
  }, [clearEvidenceHighlight, hideMagnifier, resolvedUrl]);

  useEffect(() => {
    if (!magnifierEnabled || !magnifierState.visible) return;
    clonePageIntoMagnifier(magnifierState.page);
  }, [clonePageIntoMagnifier, magnifierEnabled, magnifierState.page, magnifierState.visible]);

  useEffect(() => {
    if (magnifierEnabled && !nativeFallback) return;
    hideMagnifier();
    magnifierContentRef.current?.replaceChildren();
  }, [hideMagnifier, magnifierEnabled, nativeFallback]);

  useEffect(() => {
    if (!resolvedUrl || !loading || loadError || nativeFallback) return;
    const timeout = window.setTimeout(() => {
      setLoading(false);
      setNativeFallback(true);
      setLoadError('PDF.js 加载超时，已切换到浏览器原生 PDF 预览。');
    }, PDF_LOAD_TIMEOUT_MS);
    return () => window.clearTimeout(timeout);
  }, [loadError, loading, nativeFallback, resolvedUrl]);

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
    const bounded = numPages ? Math.min(targetPage, numPages) : targetPage;
    if (handledTargetPageRef.current === bounded) return;
    handledTargetPageRef.current = bounded;
    setPageNumber(current => {
      if (current === bounded) return current;
      onPageChange?.(bounded);
      return bounded;
    });
    window.requestAnimationFrame(() => {
      pageRefs.current.get(bounded)?.scrollIntoView({ block: 'start', behavior: 'smooth' });
    });
  }, [targetPage, numPages, onPageChange]);

  useEffect(() => () => clearEvidenceHighlight(), [clearEvidenceHighlight]);

  const normalizeEvidenceSearchText = useCallback((value: string) => (
    value
      .normalize('NFKD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/[\u2010-\u2015\u2212]/g, '-')
      .replace(/[\u2018\u2019\u201A\u201B]/g, "'")
      .replace(/[\u201C\u201D\u201E\u201F]/g, '"')
      .replace(/\u00AD/g, '')
      .replace(/\s+/g, ' ')
      .trim()
      .toLowerCase()
  ), []);

  const evidenceSearchQueries = useCallback((snippet: string) => {
    const normalized = normalizeEvidenceSearchText(snippet);
    if (!normalized) return [];

    const queries = new Set<string>([normalized]);
    const sentenceParts = normalized
      .split(/(?<=[.!?;:。！？；：])\s+/)
      .map(item => item.trim())
      .filter(item => item.length >= 24);

    sentenceParts.slice(0, 4).forEach(item => queries.add(item));

    if (normalized.length > 180) queries.add(normalized.slice(0, 180).trim());
    if (normalized.length > 260) {
      const middleStart = Math.max(0, Math.floor(normalized.length / 2) - 90);
      queries.add(normalized.slice(middleStart, middleStart + 180).trim());
    }

    const words = normalized.split(' ').filter(Boolean);
    if (words.length > 14) queries.add(words.slice(0, 14).join(' '));

    return Array.from(queries).filter(item => item.length >= 12);
  }, [normalizeEvidenceSearchText]);

  const findEvidenceSnippetInPage = useCallback((page: number, snippet: string) => {
    const pageNode = pageRefs.current.get(page);
    if (!pageNode) return false;

    const spans = Array.from(
      pageNode.querySelectorAll<HTMLElement>('.react-pdf__Page__textContent span'),
    ).filter(span => Boolean(span.textContent?.trim()));
    if (spans.length === 0) return false;

    let searchableText = '';
    const spanBySearchIndex: HTMLElement[] = [];
    spans.forEach((span, index) => {
      const normalized = normalizeEvidenceSearchText(span.textContent || '');
      if (!normalized) return;
      if (searchableText && index > 0) {
        searchableText += ' ';
        spanBySearchIndex.push(span);
      }
      for (const char of normalized) {
        searchableText += char;
        spanBySearchIndex.push(span);
      }
    });

    if (!searchableText) return false;

    for (const query of evidenceSearchQueries(snippet)) {
      const start = searchableText.indexOf(query);
      if (start < 0) continue;

      const end = start + query.length;
      const matchedSpans = new Set<HTMLElement>();
      for (let index = start; index < end; index += 1) {
        const span = spanBySearchIndex[index];
        if (span) matchedSpans.add(span);
      }
      const matchedNodes = Array.from(matchedSpans);
      const firstNode = matchedNodes[0];
      if (!firstNode) return false;

      clearEvidenceHighlight();
      matchedNodes.forEach(node => node.classList.add('paper-pdf-evidence-hit'));
      activeEvidenceHighlightRef.current = matchedNodes;
      firstNode.scrollIntoView({ block: 'center', inline: 'nearest', behavior: 'smooth' });
      evidenceHighlightTimeoutRef.current = window.setTimeout(clearEvidenceHighlight, PDF_EVIDENCE_HIGHLIGHT_MS);
      return true;
    }

    return false;
  }, [clearEvidenceHighlight, evidenceSearchQueries, normalizeEvidenceSearchText]);

  useEffect(() => {
    if (!targetLocator || targetLocator.page < 1) return;
    if (handledLocatorRequestIdsRef.current.has(targetLocator.requestId)) return;
    handledLocatorRequestIdsRef.current.add(targetLocator.requestId);

    const bounded = numPages ? Math.min(targetLocator.page, numPages) : targetLocator.page;
    setPageNumber(current => {
      if (current === bounded) return current;
      onPageChange?.(bounded);
      return bounded;
    });
    window.requestAnimationFrame(() => {
      pageRefs.current.get(bounded)?.scrollIntoView({ block: 'start', behavior: 'smooth' });
    });

    const snippet = targetLocator.snippet?.trim();
    if (!snippet) {
      onTargetLocatorResult?.({
        requestId: targetLocator.requestId,
        page: bounded,
        matched: false,
        reason: 'no_snippet',
      });
      return;
    }

    if (nativeFallback) {
      onTargetLocatorResult?.({
        requestId: targetLocator.requestId,
        page: bounded,
        matched: false,
        reason: 'native_fallback',
      });
      return;
    }

    let cancelled = false;
    let attempts = 0;
    let retryTimer: number | null = null;

    const tryLocate = () => {
      if (cancelled) return;
      attempts += 1;
      if (findEvidenceSnippetInPage(bounded, snippet)) {
        onTargetLocatorResult?.({
          requestId: targetLocator.requestId,
          page: bounded,
          matched: true,
        });
        return;
      }
      if (attempts >= PDF_EVIDENCE_LOCATOR_MAX_ATTEMPTS) {
        onTargetLocatorResult?.({
          requestId: targetLocator.requestId,
          page: bounded,
          matched: false,
          reason: 'not_found',
        });
        return;
      }
      retryTimer = window.setTimeout(tryLocate, PDF_EVIDENCE_LOCATOR_RETRY_MS);
    };

    retryTimer = window.setTimeout(tryLocate, PDF_EVIDENCE_LOCATOR_RETRY_MS);
    return () => {
      cancelled = true;
      if (retryTimer) window.clearTimeout(retryTimer);
    };
  }, [findEvidenceSnippetInPage, nativeFallback, numPages, onPageChange, onTargetLocatorResult, targetLocator]);

  const syncCurrentPageFromScroll = useCallback(() => {
    const container = contentRef.current;
    if (!container || !numPages) return;

    const readingLine = container.getBoundingClientRect().top + 80;
    let closestPage = pageNumber;
    let closestDistance = Number.POSITIVE_INFINITY;

    pageRefs.current.forEach((node, page) => {
      const rect = node.getBoundingClientRect();
      const distance = Math.abs(rect.top - readingLine);
      if (distance < closestDistance) {
        closestDistance = distance;
        closestPage = page;
      }
    });

    if (closestPage !== pageNumber) {
      setPageNumber(closestPage);
      onPageChange?.(closestPage);
    }
  }, [numPages, onPageChange, pageNumber]);

  const handlePdfScroll = useCallback(() => {
    hideMagnifier();
    syncCurrentPageFromScroll();
  }, [hideMagnifier, syncCurrentPageFromScroll]);

  const handlePageJump = useCallback((page: number | null) => {
    if (!page) return;
    const bounded = Math.min(Math.max(page, 1), numPages || page);
    setPageNumber(bounded);
    onPageChange?.(bounded);
    pageRefs.current.get(bounded)?.scrollIntoView({ block: 'start', behavior: 'smooth' });
  }, [numPages, onPageChange]);

  const pageNumbers = React.useMemo(
    () => Array.from({ length: numPages }, (_, index) => index + 1),
    [numPages],
  );

  // 文本选择事件
  const handleMouseUp = useCallback(() => {
    if (!onTextSelect) return;
    setTimeout(() => {
      const sel = window.getSelection();
      const text = sel?.toString().trim();
      if (text && text.length > 5 && text.length < 800) {
        const range = sel?.rangeCount ? sel.getRangeAt(0) : null;
        const rect = range?.getBoundingClientRect();
        const selectionNode = sel?.anchorNode instanceof Element ? sel.anchorNode : sel?.anchorNode?.parentElement;
        const selectedPage = Number(selectionNode?.closest<HTMLElement>('.paper-pdf-page')?.dataset.pageNumber) || pageNumber;
        onTextSelect(text, selectedPage, {
          x: rect ? rect.left + rect.width / 2 : window.innerWidth / 2,
          y: rect ? rect.top - 12 : 96,
        });
      }
    }, 100);
  }, [onTextSelect, pageNumber]);

  const toggleMagnifier = useCallback(() => {
    setMagnifierEnabled(current => {
      if (current) hideMagnifier();
      return !current;
    });
  }, [hideMagnifier]);

  const handlePageMouseMove = useCallback((event: React.MouseEvent<HTMLDivElement>, page: number) => {
    if (!magnifierEnabled || nativeFallback) return;
    const renderedPage = pageRefs.current.get(page)?.querySelector<HTMLElement>('.react-pdf__Page');
    const container = contentRef.current;
    if (!renderedPage || !container) return;

    const pageRect = renderedPage.getBoundingClientRect();
    const pointerX = event.clientX - pageRect.left;
    const pointerY = event.clientY - pageRect.top;
    if (pointerX < 0 || pointerY < 0 || pointerX > pageRect.width || pointerY > pageRect.height) {
      hideMagnifier();
      return;
    }

    const containerRect = container.getBoundingClientRect();
    let left = event.clientX + PDF_MAGNIFIER_OFFSET;
    let top = event.clientY + PDF_MAGNIFIER_OFFSET;
    if (left + PDF_MAGNIFIER_SIZE > containerRect.right - 8) {
      left = event.clientX - PDF_MAGNIFIER_SIZE - PDF_MAGNIFIER_OFFSET;
    }
    if (top + PDF_MAGNIFIER_SIZE > containerRect.bottom - 8) {
      top = event.clientY - PDF_MAGNIFIER_SIZE - PDF_MAGNIFIER_OFFSET;
    }
    left = Math.max(containerRect.left + 8, Math.min(left, containerRect.right - PDF_MAGNIFIER_SIZE - 8));
    top = Math.max(containerRect.top + 8, Math.min(top, containerRect.bottom - PDF_MAGNIFIER_SIZE - 8));

    setMagnifierState({
      visible: true,
      page,
      left,
      top,
      pageWidth: pageRect.width,
      pageHeight: pageRect.height,
      transform: `translate(${PDF_MAGNIFIER_SIZE / 2 - pointerX * PDF_MAGNIFIER_SCALE}px, ${PDF_MAGNIFIER_SIZE / 2 - pointerY * PDF_MAGNIFIER_SCALE}px) scale(${PDF_MAGNIFIER_SCALE})`,
    });
  }, [hideMagnifier, magnifierEnabled, nativeFallback]);

  if (!url) return <Text type="secondary">PDF 不可用</Text>;

  return (
    <div className={`paper-pdf-viewer${magnifierEnabled ? ' is-magnifier-enabled' : ''}`} onMouseUp={handleMouseUp}>
      {/* 导航栏 */}
      <div style={{
        display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 12,
        padding: '8px 12px', borderBottom: '1px solid #f0f0f0', background: '#fafafa',
        flexShrink: 0,
      }}>
        <Space size={4}>
          <InputNumber size="small" min={1} max={numPages} value={pageNumber} disabled={nativeFallback} onChange={handlePageJump} style={{ width: 58 }} />
          <Text type="secondary" style={{ fontSize: 12 }}>/ {nativeFallback ? '-' : numPages}</Text>
        </Space>
        <Text type="secondary" style={{ fontSize: 12 }}>{nativeFallback ? '原生预览' : '滚动阅读 · 划词可加入提问'}</Text>
        <Tooltip title={nativeFallback ? '原生预览不支持局部放大' : '局部放大'}>
          <Button
            size="small"
            type={magnifierEnabled ? 'primary' : 'default'}
            icon={<ZoomInOutlined />}
            disabled={nativeFallback || loading || !!loadError}
            className={`paper-pdf-magnifier-toggle${magnifierEnabled ? ' is-active' : ''}`}
            aria-pressed={magnifierEnabled}
            onClick={toggleMagnifier}
          />
        </Tooltip>
      </div>

      {/* PDF 内容 */}
      <div ref={contentRef} className={`paper-pdf-scroll${nativeFallback ? ' paper-pdf-scroll-native' : ''}`} onScroll={handlePdfScroll}>
        {nativeFallback ? (
          <div className="paper-pdf-native-fallback">
            <Alert
              type="warning"
              showIcon
              className="paper-pdf-native-notice"
              message="已切换到原生 PDF 预览"
              description={
                <Space direction="vertical" size={8}>
                  <Text>
                    {loadError || '增强阅读器暂时无法渲染该 PDF。原生预览可以继续阅读，但划词加入提问不可用。'}
                  </Text>
                  <Space wrap>
                    <Button size="small" onClick={retryEnhancedReader}>
                      重试增强阅读器
                    </Button>
                    <Button size="small" href={resolvedUrl} target="_blank" rel="noreferrer">
                      直接打开 PDF
                    </Button>
                  </Space>
                </Space>
              }
            />
            <iframe
              className="paper-pdf-native-frame"
              title="PDF 原生预览"
              src={resolvedUrl}
            />
          </div>
        ) : (
          <>
            {loading && <Spin style={{ marginTop: 40 }} />}
            {loadError && (
              <Alert
                type="error"
                showIcon
                style={{ margin: 16, textAlign: 'left' }}
                message="PDF 加载失败"
                description={
                  <Space direction="vertical" size={8}>
                    <Text>
                      请确认 {resolvedUrl} 返回 application/pdf。浏览器错误：{loadError}
                    </Text>
                    <Button size="small" href={resolvedUrl} target="_blank" rel="noreferrer">
                      直接打开 PDF
                    </Button>
                  </Space>
                }
              />
            )}
            <Document
              file={documentFile}
              onLoadSuccess={onDocLoad}
              onLoadError={onDocLoadError}
              loading={<Spin style={{ marginTop: 40 }} />}
              error={null}
            >
              <div className="paper-pdf-pages">
                {pageNumbers.map(page => (
                  <div
                    key={page}
                    className="paper-pdf-page"
                    data-page-number={page}
                    onMouseMove={event => handlePageMouseMove(event, page)}
                    onMouseLeave={hideMagnifier}
                    ref={(node) => {
                      if (node) pageRefs.current.set(page, node);
                      else pageRefs.current.delete(page);
                    }}
                  >
                    <Page
                      pageNumber={page}
                      renderTextLayer={true}
                      renderAnnotationLayer={true}
                      width={pageWidth}
                    />
                  </div>
                ))}
              </div>
            </Document>
          </>
        )}
      </div>
      {magnifierEnabled && magnifierState.visible && !nativeFallback && (
        <div
          className="paper-pdf-magnifier"
          style={{
            left: magnifierState.left,
            top: magnifierState.top,
            width: PDF_MAGNIFIER_SIZE,
            height: PDF_MAGNIFIER_SIZE,
          }}
        >
          <div className="paper-pdf-magnifier-crosshair" />
          <div
            ref={magnifierContentRef}
            className="paper-pdf-magnifier-content"
            style={{
              width: magnifierState.pageWidth,
              height: magnifierState.pageHeight,
              transform: magnifierState.transform,
            }}
          />
        </div>
      )}
    </div>
  );
};

export default PDFViewer;
