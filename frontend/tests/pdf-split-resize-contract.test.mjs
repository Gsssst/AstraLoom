import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

const paperDetailSource = readFileSync(
  new URL('../src/pages/PaperDetailPage.tsx', import.meta.url),
  'utf8',
);
const pdfViewerSource = readFileSync(
  new URL('../src/components/PDFViewer.tsx', import.meta.url),
  'utf8',
);

test('paper detail passes active PDF split resize state into the PDF viewer', () => {
  assert.match(paperDetailSource, /const PDF_PANEL_MIN_PERCENT = 30;/);
  assert.match(paperDetailSource, /Math\.max\(rawPercent, PDF_PANEL_MIN_PERCENT\)/);
  assert.match(paperDetailSource, /const \[pdfSplitResizing, setPdfSplitResizing\] = useState\(false\);/);
  assert.match(paperDetailSource, /setPdfSplitResizing\(true\);[\s\S]*?const handlePointerMove/);
  assert.match(paperDetailSource, /const handlePointerUp = \(\) => \{[\s\S]*?setPdfSplitResizing\(false\);/);
  assert.match(paperDetailSource, /setPdfSplitResizing\(false\);[\s\S]*?setPdfPanelWidth\(CHAT_REOPEN_WIDTH_PERCENT\);/);
  assert.match(paperDetailSource, /resizePaused=\{pdfSplitResizing\}/);
});

test('paper detail split snaps closed in both directions and restores either rail', () => {
  assert.match(paperDetailSource, /const PDF_COLLAPSE_THRESHOLD_PERCENT = 24;/);
  assert.match(paperDetailSource, /const CHAT_COLLAPSE_THRESHOLD_PERCENT = 84;/);
  assert.match(paperDetailSource, /const \[chatCollapsed, setChatCollapsed\] = useState\(false\);/);
  assert.match(paperDetailSource, /const \[pdfCollapsed, setPdfCollapsed\] = useState\(false\);/);
  assert.match(paperDetailSource, /rawPercent >= CHAT_COLLAPSE_THRESHOLD_PERCENT[\s\S]*?setPdfCollapsed\(false\);[\s\S]*?setChatCollapsed\(true\);/);
  assert.match(paperDetailSource, /rawPercent <= PDF_COLLAPSE_THRESHOLD_PERCENT[\s\S]*?setChatCollapsed\(false\);[\s\S]*?setPdfCollapsed\(true\);/);
  assert.match(paperDetailSource, /setChatCollapsed\(false\);[\s\S]*?setPdfCollapsed\(false\);[\s\S]*?setPdfPanelWidth\(Math\.min/);
  assert.match(paperDetailSource, /const reopenChatPanel = \(\) => \{[\s\S]*?setChatCollapsed\(false\);[\s\S]*?setPdfCollapsed\(false\);/);
  assert.match(paperDetailSource, /const reopenPdfPanel = \(\) => \{[\s\S]*?setPdfCollapsed\(false\);[\s\S]*?setChatCollapsed\(false\);/);
});

test('collapsed paper split rails leave the opposite panel to fill remaining width', () => {
  assert.match(paperDetailSource, /paper-detail-collapsed-rail paper-detail-pdf-rail/);
  assert.match(paperDetailSource, /paper-detail-collapsed-rail paper-detail-chat-rail/);
  assert.match(paperDetailSource, /aria-label="展开 PDF"/);
  assert.match(paperDetailSource, /aria-label="展开 AI 问答"/);
  assert.match(paperDetailSource, /flexGrow: !isMobile && chatCollapsed \? 1 : 0/);
  assert.match(paperDetailSource, /flexBasis: !isMobile && chatCollapsed \? 0 : 'auto'/);
  assert.match(paperDetailSource, /flexGrow: !isMobile && showPdf && pdfCollapsed \? 1 : 0/);
  assert.match(paperDetailSource, /flexBasis: !isMobile && showPdf && pdfCollapsed \? 0 : 'auto'/);
});

test('pdf viewer freezes page width measurements while split resizing is active', () => {
  assert.match(pdfViewerSource, /resizePaused\?: boolean;/);
  assert.match(pdfViewerSource, /resizePaused = false,/);
  assert.match(pdfViewerSource, /resizePausedRef\.current = resizePaused;/);
  assert.match(pdfViewerSource, /const measurePageWidth = useCallback\(\(\) => \{/);
  assert.match(pdfViewerSource, /const observer = new ResizeObserver\(\(\) => \{[\s\S]*?if \(resizePausedRef\.current\) \{[\s\S]*?clearResizeSettleTimer\(\);[\s\S]*?return;[\s\S]*?\}[\s\S]*?scheduleSettledPageWidthMeasure\(\);/);
  assert.match(pdfViewerSource, /const wasResizePaused = previousResizePausedRef\.current;[\s\S]*?if \(resizePaused \|\| !wasResizePaused\) return;[\s\S]*?window\.requestAnimationFrame\(measurePageWidth\);/);
});

test('pdf viewer debounces outer layout resize transitions before rerendering pages', () => {
  assert.match(pdfViewerSource, /const PDF_RESIZE_SETTLE_MS = 180;/);
  assert.match(pdfViewerSource, /const resizeSettleTimeoutRef = useRef<number \| null>\(null\);/);
  assert.match(pdfViewerSource, /window\.clearTimeout\(resizeSettleTimeoutRef\.current\);/);
  assert.match(pdfViewerSource, /const scheduleSettledPageWidthMeasure = useCallback\(\(\) => \{[\s\S]*?window\.setTimeout\(\(\) => \{[\s\S]*?measurePageWidth\(\);[\s\S]*?\}, PDF_RESIZE_SETTLE_MS\);/);
  assert.match(pdfViewerSource, /observer\.disconnect\(\);[\s\S]*?clearResizeSettleTimer\(\);/);
});
