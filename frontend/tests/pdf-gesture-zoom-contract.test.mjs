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
  assert.match(pdfViewerSource, /const PDF_ZOOM_STEP = 0\.15;/);
  assert.match(pdfViewerSource, /const \[zoomScale, setZoomScale\] = useState\(1\);/);
  assert.match(pdfViewerSource, /const \[pageAspectRatios, setPageAspectRatios\]/);
  assert.match(pdfViewerSource, /const getScaledPageSize = useCallback/);
  assert.match(pdfViewerSource, /const renderedPageWidth = pageSize\.width;/);
  assert.match(pdfViewerSource, /width=\{renderedPageWidth\}/);
  assert.doesNotMatch(pdfViewerSource, /width=\{pageWidth\}/);
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
  assert.match(pdfViewerSource, /const PDF_WHEEL_ZOOM_SENSITIVITY = 0\.006;/);
  assert.match(pdfViewerSource, /const PDF_WHEEL_ZOOM_MAX_DELTA = 0\.24;/);
  assert.match(pdfViewerSource, /const handlePdfWheel = useCallback\(\(event: WheelEvent\)/);
  assert.match(pdfViewerSource, /!event\.ctrlKey && !event\.metaKey/);
  assert.match(pdfViewerSource, /event\.preventDefault\(\);/);
  assert.match(pdfViewerSource, /const rawDelta = -event\.deltaY \* PDF_WHEEL_ZOOM_SENSITIVITY;/);
  assert.match(pdfViewerSource, /Math\.max\(-PDF_WHEEL_ZOOM_MAX_DELTA, Math\.min\(PDF_WHEEL_ZOOM_MAX_DELTA, rawDelta\)\)/);
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

test('pdf viewer uses high-resolution page rendering instead of transform-scaled canvas zoom', () => {
  assert.match(pdfViewerSource, /className="paper-pdf-page-shell"/);
  assert.match(pdfViewerSource, /style=\{\{ width: renderedPageWidth \}\}/);
  assert.match(pdfViewerSource, /width=\{renderedPageWidth\}/);
  assert.doesNotMatch(pdfViewerSource, /transform: `scale\(\$\{zoomScale\}\)`/);
  assert.match(pdfViewerSource, /onLoadSuccess=\{\(pdfPage\) => handlePageLoadSuccess\(pdfPage, page\)\}/);
  assert.match(pdfViewerSource, /scrollPdfNodeIntoView\(firstNode\)/);
  assert.match(responsiveCssSource, /\.paper-pdf-page-shell \{/);
  assert.doesNotMatch(responsiveCssSource, /transform-origin: top left;/);
  assert.doesNotMatch(responsiveCssSource, /will-change: transform;/);
});
