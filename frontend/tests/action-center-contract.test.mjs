import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

const actionCenterSource = readFileSync(
  new URL('../src/pages/ActionCenterPage.tsx', import.meta.url),
  'utf8',
);

test('action center can execute API maintenance actions', () => {
  assert.match(actionCenterSource, /item\.action_type === 'api'/);
  assert.match(actionCenterSource, /api\.request\(/);
  assert.match(actionCenterSource, /url: item\.endpoint/);
  assert.match(actionCenterSource, /await fetchActions\(\)/);
});

test('action center keeps diagnostics transparent after maintenance', () => {
  assert.match(actionCenterSource, /lastActionResult/);
  assert.match(actionCenterSource, /formatActionResult/);
  assert.match(actionCenterSource, /管理员维护/);
  assert.match(actionCenterSource, /查看位置/);
});
