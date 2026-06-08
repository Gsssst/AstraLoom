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

test('paper detail uses one contextual selection menu for content and PDF selections', () => {
  assert.match(paperDetailSource, /interface PaperSelectionMenu/);
  assert.match(paperDetailSource, /const \[selectionMenu, setSelectionMenu\]/);
  assert.match(paperDetailSource, /const menuHalfWidth = window\.innerWidth < 768 \? 24 : 180/);
  assert.match(paperDetailSource, /source: 'content'/);
  assert.match(paperDetailSource, /source: 'pdf'/);
  assert.doesNotMatch(paperDetailSource, /selectionPopup/);
  assert.doesNotMatch(paperDetailSource, /handleSelectionAsk/);
});

test('PDF text selection reports coordinates without auto-inserting a quote card', () => {
  assert.match(pdfViewerSource, /onTextSelect\?: \(text: string, pageNumber: number, position: \{ x: number; y: number \}\) => void/);
  assert.match(pdfViewerSource, /getBoundingClientRect\(\)/);
  assert.match(paperDetailSource, /const handlePdfTextSelect = \(text: string, pageNumber: number, position: \{ x: number; y: number \}\)/);
  assert.doesNotMatch(paperDetailSource, /const handlePdfTextSelect = \(text: string, pageNumber: number\) => \{\n\s*setPdfQuote/);
});

test('selection actions route text to chat, explanation, annotations, clipboard, and notes', () => {
  assert.match(paperDetailSource, /handleSelectionAddToQuestion/);
  assert.match(paperDetailSource, /handleSelectionExplain/);
  assert.match(paperDetailSource, /handleSelectionSaveAnnotation/);
  assert.match(paperDetailSource, /handleSelectionCopy/);
  assert.match(paperDetailSource, /handleSelectionAppendToNotes/);
  assert.match(paperDetailSource, /navigator\.clipboard\.writeText/);
  assert.match(paperDetailSource, /setNotes\(current => current \? `\$\{current\.trimEnd\(\)\}\\n\\n\$\{block\}` : block\)/);
  assert.match(paperDetailSource, /setPdfQuote\(\{ text: selected\.text, pageNumber: selected\.pageNumber \}\)/);
});

test('selection menu is styled as a compact responsive toolbar', () => {
  assert.match(paperDetailSource, /role="toolbar"/);
  assert.match(paperDetailSource, /aria-label="选中文本操作"/);
  assert.match(paperDetailSource, /className=\{`paper-selection-menu/);
  assert.match(responsiveCssSource, /\.paper-selection-menu/);
  assert.match(responsiveCssSource, /max-width: calc\(100vw - 28px\)/);
  assert.match(responsiveCssSource, /backdrop-filter: blur\(12px\)/);
  assert.match(responsiveCssSource, /@media \(max-width: 767px\)/);
});
