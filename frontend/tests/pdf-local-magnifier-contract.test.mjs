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

test('pdf viewer exposes a toggleable local magnifier control', () => {
  assert.match(pdfViewerSource, /magnifierEnabled/);
  assert.match(pdfViewerSource, /ZoomInOutlined/);
  assert.match(pdfViewerSource, /paper-pdf-magnifier-toggle/);
  assert.match(pdfViewerSource, /aria-pressed=\{magnifierEnabled\}/);
  assert.match(pdfViewerSource, /disabled=\{nativeFallback \|\| loading \|\| !!loadError\}/);
});

test('pdf magnifier follows rendered pdf pages without changing page scale', () => {
  assert.match(pdfViewerSource, /handlePageMouseMove/);
  assert.match(pdfViewerSource, /pageRefs\.current\.get\(page\)\?\.querySelector<HTMLElement>\('\.react-pdf__Page'\)/);
  assert.match(pdfViewerSource, /clonePageIntoMagnifier/);
  assert.match(pdfViewerSource, /copyCanvasPixelsToClone/);
  assert.match(pdfViewerSource, /paper-pdf-magnifier-content/);
  assert.match(pdfViewerSource, /transform: magnifierState\.transform/);
});

test('pdf magnifier styles are clipped and non-interactive', () => {
  assert.match(responsiveCssSource, /\.paper-pdf-viewer\.is-magnifier-enabled \.paper-pdf-page/);
  assert.match(responsiveCssSource, /\.paper-pdf-magnifier \{/);
  assert.match(responsiveCssSource, /pointer-events: none;/);
  assert.match(responsiveCssSource, /\.paper-pdf-magnifier-content/);
  assert.match(responsiveCssSource, /\.paper-pdf-magnifier-page-clone/);
});
