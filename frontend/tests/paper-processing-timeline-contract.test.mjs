import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

const paperDetailSource = readFileSync(
  new URL('../src/pages/PaperDetailPage.tsx', import.meta.url),
  'utf8',
);
const responsiveSource = readFileSync(
  new URL('../src/styles/responsive.css', import.meta.url),
  'utf8',
);

test('paper detail consumes and renders processing timeline data', () => {
  assert.match(paperDetailSource, /processing_timeline/);
  assert.match(paperDetailSource, /processingTimeline/);
  assert.match(paperDetailSource, /后台处理时间线/);
  assert.match(paperDetailSource, /next_retry_hint/);
  assert.match(paperDetailSource, /timestamp_label/);
  assert.match(paperDetailSource, /paper-processing-timeline-card/);
});

test('paper processing timeline has compact responsive styling', () => {
  assert.match(responsiveSource, /\.paper-processing-timeline-card/);
  assert.match(responsiveSource, /\.paper-processing-timeline-grid/);
  assert.match(responsiveSource, /\.paper-processing-timeline-item/);
  assert.match(responsiveSource, /\.paper-processing-timeline-item\.is-failed/);
  assert.match(responsiveSource, /repeat\(auto-fit, minmax\(168px, 1fr\)\)/);
});
