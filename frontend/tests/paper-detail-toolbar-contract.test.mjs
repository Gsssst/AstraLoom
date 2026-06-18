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
  assert.match(paperDetailSource, /className="paper-detail-toolbar-main"/);
  assert.match(paperDetailSource, /className="paper-detail-toolbar-actions"/);
  assert.match(paperDetailSource, /className="paper-detail-title"/);
});

test('paper detail toolbar truncates long titles before overlapping actions', () => {
  assert.match(responsiveCssSource, /\.paper-detail-toolbar-main \{[\s\S]*?min-width: 0;/);
  assert.match(responsiveCssSource, /\.paper-detail-toolbar-main \{[\s\S]*?overflow: hidden;/);
  assert.match(responsiveCssSource, /\.paper-detail-title \{[\s\S]*?min-width: 0;/);
  assert.match(responsiveCssSource, /\.paper-detail-title \{[\s\S]*?flex: 1 1 auto;/);
  assert.match(responsiveCssSource, /\.paper-detail-toolbar-actions \{[\s\S]*?flex: 0 1 auto;/);
  assert.match(responsiveCssSource, /\.paper-detail-toolbar-actions \{[\s\S]*?justify-content: flex-end;/);
});

test('paper detail toolbar keeps mobile wrapping explicit', () => {
  assert.match(responsiveCssSource, /\.paper-detail-toolbar-actions \{[\s\S]*?width: 100%;/);
  assert.match(responsiveCssSource, /\.paper-detail-toolbar-actions \{[\s\S]*?justify-content: flex-start;/);
});
