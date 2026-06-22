import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

const settingsSource = readFileSync(
  new URL('../src/pages/SettingsPage.tsx', import.meta.url),
  'utf8',
);

test('settings API tab describes model selection as a personal preference', () => {
  assert.match(settingsSource, /我的提供商/);
  assert.match(settingsSource, /我的模型/);
  assert.match(settingsSource, /服务端默认/);
  assert.match(settingsSource, /个人偏好/);
  assert.match(settingsSource, /模型选择是个人偏好/);
  assert.match(settingsSource, /保存后只影响自己的聊天、论文问答、写作和研究生成/);
});

test('settings API tab no longer gates model preference save and test by admin role', () => {
  assert.match(settingsSource, /disabled=\{!selectedApiOption\?\.configured\}/);
  assert.match(settingsSource, /disabled=\{!apiConfig\.configured\}/);
  assert.doesNotMatch(settingsSource, /profile\?\.role !== 'admin' \|\| !selectedApiOption\?\.configured/);
  assert.doesNotMatch(settingsSource, /profile\?\.role !== 'admin' \|\| !apiConfig\.configured/);
});
