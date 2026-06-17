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
const responsiveCssSource = readFileSync(
  new URL('../src/styles/responsive.css', import.meta.url),
  'utf8',
);

test('PDF viewer accepts evidence locator requests with snippet and request id', () => {
  assert.match(pdfViewerSource, /interface PDFTargetLocator/);
  assert.match(pdfViewerSource, /page: number/);
  assert.match(pdfViewerSource, /snippet\?: string \| null/);
  assert.match(pdfViewerSource, /requestId: number/);
  assert.match(pdfViewerSource, /targetLocator\?: PDFTargetLocator \| null/);
  assert.match(pdfViewerSource, /onTargetLocatorResult\?: \(result: PDFTargetLocatorResult\) => void/);
});

test('PDF viewer searches rendered page text layer for normalized evidence snippets', () => {
  assert.match(pdfViewerSource, /normalizeEvidenceSearchText/);
  assert.match(pdfViewerSource, /evidenceSearchQueries/);
  assert.match(pdfViewerSource, /findEvidenceSnippetInPage/);
  assert.match(pdfViewerSource, /\.react-pdf__Page__textContent span/);
  assert.match(pdfViewerSource, /searchableText\.indexOf\(query\)/);
  assert.match(pdfViewerSource, /spanBySearchIndex/);
  assert.match(pdfViewerSource, /PDF_EVIDENCE_LOCATOR_MAX_ATTEMPTS/);
  assert.match(pdfViewerSource, /PDF_EVIDENCE_LOCATOR_RETRY_MS/);
});

test('PDF viewer consumes page and evidence locator targets only once', () => {
  assert.match(pdfViewerSource, /handledTargetPageRef = useRef<number \| null>\(null\)/);
  assert.match(pdfViewerSource, /handledLocatorRequestIdsRef = useRef<Set<number>>\(new Set\(\)\)/);
  assert.match(pdfViewerSource, /handledTargetPageRef\.current = null/);
  assert.match(pdfViewerSource, /handledLocatorRequestIdsRef\.current\.clear\(\)/);
  assert.match(pdfViewerSource, /if \(handledTargetPageRef\.current === bounded\) return/);
  assert.match(pdfViewerSource, /handledTargetPageRef\.current = bounded/);
  assert.match(pdfViewerSource, /handledLocatorRequestIdsRef\.current\.has\(targetLocator\.requestId\)/);
  assert.match(pdfViewerSource, /handledLocatorRequestIdsRef\.current\.add\(targetLocator\.requestId\)/);
});

test('PDF viewer scrolls and highlights matched evidence text spans', () => {
  assert.match(pdfViewerSource, /paper-pdf-evidence-hit/);
  assert.match(pdfViewerSource, /firstNode\.scrollIntoView\(\{ block: 'center'/);
  assert.match(pdfViewerSource, /PDF_EVIDENCE_HIGHLIGHT_MS/);
  assert.match(pdfViewerSource, /clearEvidenceHighlight/);
  assert.match(responsiveCssSource, /span\.paper-pdf-evidence-hit/);
  assert.match(responsiveCssSource, /background: rgba\(255, 229, 143, 0\.46\)/);
});

test('paper detail forwards evidence snippets into the PDF locator from citation clicks', () => {
  assert.match(paperDetailSource, /interface PaperPdfTargetLocator/);
  assert.match(paperDetailSource, /pdfLocatorRequestIdRef = useRef\(0\)/);
  assert.match(paperDetailSource, /const \[targetPdfLocator, setTargetPdfLocator\]/);
  assert.match(paperDetailSource, /pdfLocatorRequestIdRef\.current \+= 1/);
  assert.match(paperDetailSource, /setTargetPdfLocator\(\{\s*page,\s*snippet: ref\.snippet,\s*requestId: pdfLocatorRequestIdRef\.current,\s*\}\)/s);
  assert.match(paperDetailSource, /targetLocator=\{targetPdfLocator\}/);
  assert.match(paperDetailSource, /onTargetLocatorResult=\{\(result\) =>/);
  assert.match(paperDetailSource, /暂未在文本层精确匹配引用片段/);
});
