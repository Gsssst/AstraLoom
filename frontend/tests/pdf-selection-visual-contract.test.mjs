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
  assert.match(pdfViewerSource, /onTextSelect\(text, pageNumber, \{/);
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
  assert.match(pdfViewerSource, /setLoadError\('PDF 加载超时/);
  assert.match(pdfViewerSource, /直接打开 PDF/);
  assert.match(pdfViewerSource, /href=\{resolvedUrl\}/);
});

test('production frontend serves pdf worker module assets as javascript', () => {
  assert.match(frontendNginxSource, /application\/javascript js mjs;/);
  assert.match(frontendNginxSource, /location \/assets\//);
});

test('pdf viewer initializes an explicit module worker port', () => {
  assert.match(pdfViewerSource, /const pdfWorkerUrl = new URL\(/);
  assert.match(pdfViewerSource, /pdfjs\.GlobalWorkerOptions\.workerSrc = pdfWorkerUrl/);
  assert.match(pdfViewerSource, /pdfjs\.GlobalWorkerOptions\.workerPort = new Worker\(pdfWorkerUrl, \{ type: 'module' \}\)/);
});

test('pdf text selection uses a lighter separated highlight treatment', () => {
  assert.match(responsiveCssSource, /\.paper-pdf-page \.react-pdf__Page__textContent ::selection/);
  assert.match(responsiveCssSource, /background: rgba\(72, 145, 255, 0\.22\)/);
  assert.match(responsiveCssSource, /background: rgba\(72, 145, 255, 0\.2\)/);
  assert.match(responsiveCssSource, /\.paper-pdf-page \.react-pdf__Page__textContent span \{\n  line-height: 1;/);
  assert.match(responsiveCssSource, /\.paper-pdf-page \.react-pdf__Page__textContent \.markedContent/);
});
