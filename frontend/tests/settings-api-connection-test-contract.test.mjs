import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

const settingsSource = readFileSync(
  new URL('../src/pages/SettingsPage.tsx', import.meta.url),
  'utf8',
);

test('settings API tab exposes current model connection test action', () => {
  assert.match(settingsSource, /testingApiConfig/);
  assert.match(settingsSource, /apiConfigTestResult/);
  assert.match(settingsSource, /handleTestApiConfig/);
  assert.match(settingsSource, /settings\/api-config\/test/);
  assert.match(settingsSource, /测试当前模型/);
});

test('settings API tab renders connection test latency and preview', () => {
  assert.match(settingsSource, /连接测试完成/);
  assert.match(settingsSource, /latency_ms/);
  assert.match(settingsSource, /preview/);
  assert.match(settingsSource, /模型连接测试成功/);
  assert.match(settingsSource, /getApiErrorMessage\(e, \{ fallback: '模型连接测试失败' \}\)/);
});
