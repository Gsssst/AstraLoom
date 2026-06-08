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

test('pdf viewer scopes page-level selection styles', () => {
  assert.match(pdfViewerSource, /className="paper-pdf-page"/);
  assert.match(pdfViewerSource, /renderTextLayer=\{true\}/);
  assert.match(pdfViewerSource, /onTextSelect\(text, pageNumber, \{/);
  assert.match(pdfViewerSource, /getBoundingClientRect\(\)/);
});

test('pdf text selection uses a lighter separated highlight treatment', () => {
  assert.match(responsiveCssSource, /\.paper-pdf-page \.react-pdf__Page__textContent ::selection/);
  assert.match(responsiveCssSource, /background: rgba\(72, 145, 255, 0\.22\)/);
  assert.match(responsiveCssSource, /background: rgba\(72, 145, 255, 0\.2\)/);
  assert.match(responsiveCssSource, /\.paper-pdf-page \.react-pdf__Page__textContent span \{\n  line-height: 1;/);
  assert.match(responsiveCssSource, /\.paper-pdf-page \.react-pdf__Page__textContent \.markedContent/);
});
