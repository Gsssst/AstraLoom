import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

const paperDetailSource = readFileSync(
  new URL('../src/pages/PaperDetailPage.tsx', import.meta.url),
  'utf8',
);
const responsiveCssSource = readFileSync(
  new URL('../src/styles/responsive.css', import.meta.url),
  'utf8',
);

test('paper detail toolbar has separate title and actions flex regions', () => {
  assert.match(paperDetailSource, /<div className="paper-detail-toolbar-main">/);
  assert.match(paperDetailSource, /className="paper-detail-toolbar-actions" wrap/);
  assert.match(paperDetailSource, /className="paper-detail-title"/);
});

test('paper detail toolbar truncates long titles before overlapping actions', () => {
  assert.match(responsiveCssSource, /\.paper-detail-toolbar \{[\s\S]*?display: grid;/);
  assert.match(responsiveCssSource, /\.paper-detail-toolbar \{[\s\S]*?grid-template-columns: minmax\(0, 1fr\) auto;/);
  assert.match(responsiveCssSource, /\.paper-detail-toolbar-main \{[\s\S]*?min-width: 0;/);
  assert.match(responsiveCssSource, /\.paper-detail-toolbar-main \{[\s\S]*?overflow: hidden;/);
  assert.match(responsiveCssSource, /\.paper-detail-title \{[\s\S]*?min-width: 0;/);
  assert.match(responsiveCssSource, /\.paper-detail-title \{[\s\S]*?flex: 1 1 auto;/);
  assert.match(responsiveCssSource, /\.paper-detail-title\.ant-typography \{[\s\S]*?text-overflow: ellipsis;/);
  assert.match(responsiveCssSource, /\.paper-detail-toolbar-actions \{[\s\S]*?flex: 0 0 auto;/);
  assert.match(responsiveCssSource, /\.paper-detail-toolbar-actions \{[\s\S]*?max-width: min\(100%, 62vw\);/);
  assert.match(responsiveCssSource, /\.paper-detail-toolbar-actions \{[\s\S]*?justify-content: flex-end;/);
});

test('paper detail toolbar keeps mobile wrapping explicit', () => {
  assert.match(responsiveCssSource, /@media \(max-width: 767px\)[\s\S]*\.paper-detail-toolbar \{[\s\S]*?grid-template-columns: minmax\(0, 1fr\);/);
  assert.match(responsiveCssSource, /\.paper-detail-toolbar-actions \{[\s\S]*?width: 100%;/);
  assert.match(responsiveCssSource, /\.paper-detail-toolbar-actions \{[\s\S]*?justify-content: flex-start;/);
});
