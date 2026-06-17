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
const frontendNginxSource = readFileSync(
  new URL('../nginx-frontend.conf', import.meta.url),
  'utf8',
);

test('pdf viewer scopes page-level selection styles', () => {
  assert.match(pdfViewerSource, /className="paper-pdf-page"/);
  assert.match(pdfViewerSource, /renderTextLayer=\{true\}/);
  assert.match(pdfViewerSource, /onTextSelect\(text, selectedPage, \{/);
  assert.match(pdfViewerSource, /getBoundingClientRect\(\)/);
});

test('pdf viewer uses production-safe url descriptor and diagnostics', () => {
  assert.match(pdfViewerSource, /new URL\(url, window\.location\.origin\)\.toString\(\)/);
  assert.match(pdfViewerSource, /url: resolvedUrl/);
  assert.match(pdfViewerSource, /file=\{documentFile\}/);
  assert.match(pdfViewerSource, /onLoadError=\{onDocLoadError\}/);
  assert.match(pdfViewerSource, /message="PDF 加载失败"/);
  assert.match(pdfViewerSource, /返回 application\/pdf/);
});

test('pdf viewer uses conservative full-file loading for proxied pdfs', () => {
  assert.match(pdfViewerSource, /disableRange: true/);
  assert.match(pdfViewerSource, /disableStream: true/);
  assert.match(pdfViewerSource, /disableAutoFetch: true/);
});

test('pdf viewer surfaces loading timeouts with a direct fallback link', () => {
  assert.match(pdfViewerSource, /PDF_LOAD_TIMEOUT_MS = 20000/);
  assert.match(pdfViewerSource, /setNativeFallback\(true\)/);
  assert.match(pdfViewerSource, /setLoadError\('PDF\.js 加载超时/);
  assert.match(pdfViewerSource, /直接打开 PDF/);
  assert.match(pdfViewerSource, /href=\{resolvedUrl\}/);
});

test('pdf viewer falls back to native browser preview when pdfjs stalls', () => {
  assert.match(pdfViewerSource, /const \[nativeFallback, setNativeFallback\]/);
  assert.match(pdfViewerSource, /const retryEnhancedReader = useCallback/);
  assert.match(pdfViewerSource, /已切换到原生 PDF 预览/);
  assert.match(pdfViewerSource, /重试增强阅读器/);
  assert.match(pdfViewerSource, /className="paper-pdf-native-frame"/);
  assert.match(pdfViewerSource, /src=\{resolvedUrl\}/);
});

test('production frontend serves pdf worker module assets as javascript', () => {
  assert.match(frontendNginxSource, /location ~ \^\/assets\/pdf\\\.worker\\\.min-\.\*\\\.mjs\$/);
  assert.match(frontendNginxSource, /application\/javascript js mjs;/);
  assert.match(frontendNginxSource, /application\/javascript mjs;/);
  assert.match(frontendNginxSource, /max-age=300, must-revalidate/);
  assert.match(frontendNginxSource, /location \/assets\//);
});

test('pdf viewer lets pdfjs initialize and test the bundled worker source', () => {
  assert.match(pdfViewerSource, /const pdfWorkerUrl = new URL\(/);
  assert.match(pdfViewerSource, /const versionedPdfWorkerUrl = `\$\{pdfWorkerUrl\}\?v=2026-06-10-1`/);
  assert.match(pdfViewerSource, /pdfjs\.GlobalWorkerOptions\.workerSrc = versionedPdfWorkerUrl/);
  assert.doesNotMatch(pdfViewerSource, /GlobalWorkerOptions\.workerPort\s*=/);
  assert.doesNotMatch(pdfViewerSource, /new Worker\(pdfWorkerUrl/);
});

test('pdf text selection uses a lighter separated highlight treatment', () => {
  assert.match(responsiveCssSource, /\.paper-pdf-page \.react-pdf__Page__textContent ::selection/);
  assert.match(responsiveCssSource, /background: rgba\(72, 145, 255, 0\.22\)/);
  assert.match(responsiveCssSource, /background: rgba\(72, 145, 255, 0\.2\)/);
  assert.match(responsiveCssSource, /\.paper-pdf-page \.react-pdf__Page__textContent span \{\n  line-height: 1;/);
  assert.match(responsiveCssSource, /\.paper-pdf-page \.react-pdf__Page__textContent \.markedContent/);
});

test('native pdf fallback fills the reader panel', () => {
  assert.match(responsiveCssSource, /\.paper-pdf-scroll-native/);
  assert.match(responsiveCssSource, /\.paper-pdf-native-fallback/);
  assert.match(responsiveCssSource, /\.paper-pdf-native-frame/);
  assert.match(responsiveCssSource, /min-height: 420px/);
});
