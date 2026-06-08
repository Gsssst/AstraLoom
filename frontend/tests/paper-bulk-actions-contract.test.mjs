import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

const papersPageSource = readFileSync(
  new URL('../src/pages/PapersPage.tsx', import.meta.url),
  'utf8',
);
const responsiveSource = readFileSync(
  new URL('../src/styles/responsive.css', import.meta.url),
  'utf8',
);

test('selected papers can be exported from already-loaded metadata', () => {
  assert.match(papersPageSource, /type SelectedExportFormat = 'bibtex' \| 'markdown' \| 'json'/);
  assert.match(papersPageSource, /buildSelectedBibtex/);
  assert.match(papersPageSource, /buildSelectedMarkdown/);
  assert.match(papersPageSource, /buildSelectedJson/);
  assert.match(papersPageSource, /selectedExportConfig/);
  assert.match(papersPageSource, /downloadTextFile/);
  assert.match(papersPageSource, /text\/x-bibtex/);
  assert.match(papersPageSource, /text\/markdown/);
  assert.match(papersPageSource, /application\/json/);
  assert.match(papersPageSource, /selected-papers-\$\{today\}/);
  assert.doesNotMatch(papersPageSource, /\/papers\/export-selected/);
});

test('bulk reading status reuses the existing per-paper workflow with partial result feedback', () => {
  assert.match(papersPageSource, /handleBulkReadStatus/);
  assert.match(papersPageSource, /Promise\.allSettled/);
  assert.match(papersPageSource, /api\.put\(`\/papers\/\$\{paper\.id\}\/read-status`, \{ status \}\)/);
  assert.match(papersPageSource, /successfulIds/);
  assert.match(papersPageSource, /failedCount/);
  assert.match(papersPageSource, /阅读状态更新完成：成功/);
  assert.match(papersPageSource, /fetchReadingCounts/);
});

test('bulk action bar groups selected-paper actions without losing existing workflows', () => {
  assert.match(papersPageSource, /paper-bulk-action-bar/);
  assert.match(papersPageSource, /role="toolbar"/);
  assert.match(papersPageSource, /已选 \{selectedCount\} 篇/);
  assert.match(papersPageSource, /paper-bulk-action-section-wide/);
  assert.match(papersPageSource, /加入分类/);
  assert.match(papersPageSource, /新建分类/);
  assert.match(papersPageSource, /阅读状态/);
  assert.match(papersPageSource, /BibTeX/);
  assert.match(papersPageSource, /Markdown/);
  assert.match(papersPageSource, /JSON/);
  assert.match(papersPageSource, /组会报告/);
  assert.match(papersPageSource, /handleBatchTagSelected/);
  assert.match(papersPageSource, /清空选择/);
});

test('paper library exposes owner filter, importer tags, and custom group report prompt', () => {
  assert.match(papersPageSource, /const paperSearchSources = \['local', 'mine'/);
  assert.match(papersPageSource, /value: 'mine', label: '👤 我的'/);
  assert.match(papersPageSource, /owner = source === 'mine' \? 'mine' : undefined/);
  assert.match(papersPageSource, /source: searchSource, owner/);
  assert.match(papersPageSource, /imported_by_username/);
  assert.match(papersPageSource, /导入：\{paper\.imported_by_username\}/);
  assert.match(papersPageSource, /reportPrompt/);
  assert.match(papersPageSource, /custom_prompt: reportPrompt\.trim\(\) \|\| undefined/);
  assert.match(papersPageSource, /自定义汇报要求/);
});

test('bulk action bar has responsive hooks for narrow screens', () => {
  assert.match(responsiveSource, /\.paper-bulk-action-bar/);
  assert.match(responsiveSource, /\.paper-bulk-action-count/);
  assert.match(responsiveSource, /\.paper-bulk-action-section/);
  assert.match(responsiveSource, /\.paper-bulk-action-label/);
  assert.match(responsiveSource, /\.paper-bulk-action-select/);
  assert.match(responsiveSource, /@media \(max-width: 767px\)/);
  assert.match(responsiveSource, /width: calc\(100vw - 20px\)/);
  assert.match(responsiveSource, /flex-wrap: wrap/);
  assert.match(responsiveSource, /overflow-y: auto/);
});
