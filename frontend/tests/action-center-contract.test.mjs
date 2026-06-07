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

test('action center persists structured error recovery guidance', () => {
  assert.match(actionCenterSource, /getApiErrorDetails/);
  assert.match(actionCenterSource, /lastActionError/);
  assert.match(actionCenterSource, /setLastActionError/);
  assert.match(actionCenterSource, /行动中心加载失败/);
  assert.match(actionCenterSource, /动作执行失败，请稍后重试或进入设置页处理。/);
  assert.match(actionCenterSource, /lastActionError\.detail\.recovery/);
  assert.match(actionCenterSource, /lastActionError\.detail\.category/);
  assert.match(actionCenterSource, /lastActionError\.detail\.retryable/);
  assert.match(actionCenterSource, /需先处理条件/);
});
