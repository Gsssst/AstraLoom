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

test('paper library exposes user collections as a first-class source', () => {
  assert.match(papersPageSource, /自定义分类/);
  assert.match(papersPageSource, /api\.get\('\/folders\/'\)/);
  assert.match(papersPageSource, /api\.get\(`\/folders\/\$\{selectedCollectionId\}\/papers`\)/);
  assert.match(papersPageSource, /api\.post\(`\/folders\/\$\{targetCollectionId\}\/papers`/);
  assert.match(papersPageSource, /api\.delete\(`\/folders\/\$\{selectedCollectionId\}\/papers\/\$\{paper\.id\}`/);
});

test('research direction creation can import collection paper ids as seeds', () => {
  assert.match(researchPageSource, /从论文分类一键导入种子论文/);
  assert.match(researchPageSource, /selectedCollectionIds/);
  assert.match(researchPageSource, /api\.get\(`\/folders\/\$\{id\}\/paper-ids`\)/);
  assert.match(researchPageSource, /new Set\(\[\.\.\.selectedPaperIds, \.\.\.collectionPaperIds\.flat\(\)\]\)/);
});
