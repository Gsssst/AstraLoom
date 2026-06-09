import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { join } from 'node:path';

const root = new URL('..', import.meta.url).pathname;
const papersPage = readFileSync(join(root, 'src/pages/PapersPage.tsx'), 'utf8');

test('paper library search sends shared importance filter to backend', () => {
  assert.match(papersPage, /filterImportance/);
  assert.match(papersPage, /importance_label:\s*filterImportance === 'all' \? undefined : filterImportance/);
  assert.match(papersPage, /filterImportance\]/);
});

test('paper library exposes all important and interesting filter options', () => {
  assert.match(papersPage, /标记不限/);
  assert.match(papersPage, /value: 'important'/);
  assert.match(papersPage, /paperImportanceMeta\.important\.label/);
  assert.match(papersPage, /value: 'interesting'/);
  assert.match(papersPage, /paperImportanceMeta\.interesting\.label/);
});
