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

test('proposal review models enriched novelty collision metadata', () => {
  assert.match(researchProjectSource, /collision_risk\?: 'high' \| 'medium' \| 'low' \| 'unknown'/);
  assert.match(researchProjectSource, /similar_work\?: Array/);
  assert.match(researchProjectSource, /source_coverage\?:/);
  assert.match(researchProjectSource, /local_count\?: number/);
  assert.match(researchProjectSource, /external_count\?: number/);
});

test('proposal detail renders collision risk and ranked similar work', () => {
  assert.match(researchProjectSource, /collisionRisk/);
  assert.match(researchProjectSource, /碰撞风险/);
  assert.match(researchProjectSource, /similarWork\.slice\(0, 3\)/);
  assert.match(researchProjectSource, /proposal-similar-work-list/);
  assert.match(researchProjectSource, /相似工作池：本地/);
  assert.match(researchProjectSource, /部分外部源不可用/);
});

test('similar work collision css keeps proposal cards compact', () => {
  assert.match(globalCssSource, /\.proposal-similar-work-list/);
  assert.match(globalCssSource, /\.proposal-similar-work-item/);
  assert.match(globalCssSource, /overflow-wrap: anywhere/);
});
