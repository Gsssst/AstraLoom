import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

const researchProjectSource = readFileSync(
  new URL('../src/pages/ResearchProjectPage.tsx', import.meta.url),
  'utf8',
);
const globalCssSource = readFileSync(
  new URL('../src/index.css', import.meta.url),
  'utf8',
);

test('proposal review models diversity-aware selection metadata', () => {
  assert.match(researchProjectSource, /selection_rationale\?: string \| null/);
  assert.match(researchProjectSource, /selection_score\?: number \| null/);
  assert.match(researchProjectSource, /diversity_facets\?: string\[\]/);
  assert.match(researchProjectSource, /suppressed_duplicates\?: Array/);
  assert.match(researchProjectSource, /source\?: string/);
});

test('proposal detail renders selection rationale and diversity facets', () => {
  assert.match(researchProjectSource, /review\.selection_rationale/);
  assert.match(researchProjectSource, /选择理由/);
  assert.match(researchProjectSource, /选择分/);
  assert.match(researchProjectSource, /diversityFacets\.slice\(0, 6\)/);
  assert.match(researchProjectSource, /已压制相近候选/);
  assert.match(researchProjectSource, /proposal-selection-signal/);
});

test('selection signal css keeps long facets readable', () => {
  assert.match(globalCssSource, /\.proposal-selection-signal/);
  assert.match(globalCssSource, /background: #fbfaff/);
  assert.match(globalCssSource, /overflow-wrap: anywhere/);
});
