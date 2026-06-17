import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

const pdfViewerSource = readFileSync(
  new URL('../src/components/PDFViewer.tsx', import.meta.url),
  'utf8',
);
const responsiveCssSource = readFileSync(
  new URL('../src/styles/responsive.css', import.meta.url),
  'utf8',
);

test('pdf viewer renders pages with bounded global zoom state', () => {
  assert.match(pdfViewerSource, /const PDF_ZOOM_MIN = 0\.75;/);
  assert.match(pdfViewerSource, /const PDF_ZOOM_MAX = 4;/);
  assert.match(pdfViewerSource, /const \[zoomScale, setZoomScale\] = useState\(1\);/);
  assert.match(pdfViewerSource, /const \[pageAspectRatios, setPageAspectRatios\]/);
  assert.match(pdfViewerSource, /const getScaledPageSize = useCallback/);
  assert.match(pdfViewerSource, /width=\{pageWidth\}/);
  assert.doesNotMatch(pdfViewerSource, /width=\{effectivePageWidth\}/);
});

test('pdf viewer exposes toolbar zoom controls and current percentage', () => {
  assert.match(pdfViewerSource, /ZoomOutOutlined/);
  assert.match(pdfViewerSource, /ZoomInOutlined/);
  assert.match(pdfViewerSource, /ColumnWidthOutlined/);
  assert.match(pdfViewerSource, /paper-pdf-zoom-controls/);
  assert.match(pdfViewerSource, /paper-pdf-zoom-level/);
  assert.match(pdfViewerSource, /\{zoomPercent\}%/);
});

test('pdf viewer handles modifier wheel zoom without browser page zoom', () => {
  assert.match(pdfViewerSource, /const handlePdfWheel = useCallback\(\(event: WheelEvent\)/);
  assert.match(pdfViewerSource, /!event\.ctrlKey && !event\.metaKey/);
  assert.match(pdfViewerSource, /event\.preventDefault\(\);/);
  assert.match(pdfViewerSource, /container\.addEventListener\('wheel', handlePdfWheel, \{ passive: false \}\)/);
  assert.match(pdfViewerSource, /zoomAroundViewportPoint\(nextScale, \{/);
});

test('pdf zoom styles allow horizontally scrollable zoomed pages without local loupe', () => {
  assert.match(responsiveCssSource, /\.paper-pdf-zoom-controls/);
  assert.match(responsiveCssSource, /\.paper-pdf-pages \{/);
  assert.match(responsiveCssSource, /width: max-content;/);
  assert.match(responsiveCssSource, /min-width: 100%;/);
  assert.doesNotMatch(responsiveCssSource, /paper-pdf-magnifier/);
  assert.doesNotMatch(pdfViewerSource, /magnifierEnabled/);
  assert.doesNotMatch(pdfViewerSource, /clonePageIntoMagnifier/);
});

test('pdf viewer uses transform-based smooth zoom without rerendering every gesture step', () => {
  assert.match(pdfViewerSource, /className="paper-pdf-page-shell"/);
  assert.match(pdfViewerSource, /transform: `scale\(\$\{zoomScale\}\)`/);
  assert.match(pdfViewerSource, /onLoadSuccess=\{\(pdfPage\) => handlePageLoadSuccess\(pdfPage, page\)\}/);
  assert.match(pdfViewerSource, /scrollPdfNodeIntoView\(firstNode\)/);
  assert.match(responsiveCssSource, /\.paper-pdf-page-shell \{/);
  assert.match(responsiveCssSource, /transform-origin: top left;/);
  assert.match(responsiveCssSource, /will-change: transform;/);
});
