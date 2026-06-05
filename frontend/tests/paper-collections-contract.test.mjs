import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

const papersPageSource = readFileSync(
  new URL('../src/pages/PapersPage.tsx', import.meta.url),
  'utf8',
);
const researchPageSource = readFileSync(
  new URL('../src/pages/ResearchPage.tsx', import.meta.url),
  'utf8',
);
const researchDetailSource = readFileSync(
  new URL('../src/pages/ResearchProjectPage.tsx', import.meta.url),
  'utf8',
);

test('paper library exposes user collections as a first-class source', () => {
  assert.match(papersPageSource, /自定义分类/);
  assert.match(papersPageSource, /api\.get\('\/folders\/'\)/);
  assert.match(papersPageSource, /\/diagnostics/);
  assert.match(papersPageSource, /ready_for_idea/);
  assert.match(papersPageSource, /api\.get\(`\/folders\/\$\{selectedCollectionId\}\/papers`\)/);
  assert.match(papersPageSource, /\/coverage/);
  assert.match(papersPageSource, /\/recommendations/);
  assert.match(papersPageSource, /主题覆盖分析/);
  assert.match(papersPageSource, /补论文推荐/);
  assert.match(papersPageSource, /补经典/);
  assert.match(papersPageSource, /补近期/);
  assert.match(papersPageSource, /补缺口/);
  assert.match(papersPageSource, /api\.post\(`\/folders\/\$\{targetCollectionId\}\/papers`/);
  assert.match(papersPageSource, /入库并加入当前分类/);
  assert.match(papersPageSource, /api\.delete\(`\/folders\/\$\{selectedCollectionId\}\/papers\/\$\{paper\.id\}`/);
  assert.match(papersPageSource, /已入库并加入目标分类/);
});

test('paper library exposes a first-class maintenance center', () => {
  assert.match(papersPageSource, /维护中心/);
  assert.match(papersPageSource, /\/papers\/maintenance\/health/);
  assert.match(papersPageSource, /\/papers\/maintenance\/recommendations/);
  assert.match(papersPageSource, /\/papers\/maintenance\/search-diagnostics/);
  assert.match(papersPageSource, /\/papers\/maintenance\/rebuild-bm25/);
  assert.match(papersPageSource, /\/papers\/maintenance\/backfill-embeddings\?limit=20/);
  assert.match(papersPageSource, /\/papers\/maintenance\/backfill-full-text\?limit=5/);
  assert.match(papersPageSource, /知识库维护中心/);
  assert.match(papersPageSource, /分类健康度/);
  assert.match(papersPageSource, /需要管理员权限/);
  assert.match(papersPageSource, /BM25 分支解释|分支解释/);
});

test('paper library makes external search and ingest transparent', () => {
  assert.match(papersPageSource, /providerGuidance/);
  assert.match(papersPageSource, /综合学术检索/);
  assert.match(papersPageSource, /Semantic Scholar/);
  assert.match(papersPageSource, /OpenAlex/);
  assert.match(papersPageSource, /Google Scholar/);
  assert.match(papersPageSource, /开放 PDF/);
  assert.match(papersPageSource, /未返回 PDF/);
  assert.match(papersPageSource, /来源页/);
  assert.match(papersPageSource, /可一键入库/);
  assert.match(papersPageSource, /缺少远程 ID/);
  assert.match(papersPageSource, /入库目标：论文库/);
  assert.match(papersPageSource, /这次外部检索没有返回论文/);
  assert.match(papersPageSource, /放宽年份/);
  assert.match(papersPageSource, /换一批/);
  assert.match(papersPageSource, /做检索诊断/);
});

test('research direction creation can import collection paper ids as seeds', () => {
  assert.match(researchPageSource, /从论文分类一键导入种子论文/);
  assert.match(researchPageSource, /selectedCollectionIds/);
  assert.match(researchPageSource, /collection_ids: selectedCollectionIds/);
  assert.match(researchPageSource, /api\.get\(`\/folders\/\$\{id\}\/paper-ids`\)/);
  assert.match(researchPageSource, /new Set\(\[\.\.\.selectedPaperIds, \.\.\.collectionPaperIds\.flat\(\)\]\)/);
});

test('research detail exposes collection provenance in idea evidence', () => {
  assert.match(researchDetailSource, /collection_names/);
  assert.match(researchDetailSource, /collection_sources/);
  assert.match(researchDetailSource, /来自分类/);
});
