import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

const settingsSource = readFileSync(
  new URL('../src/pages/SettingsPage.tsx', import.meta.url),
  'utf8',
);

test('settings subscription exposes configurable daily send hour', () => {
  assert.match(settingsSource, /subSendHour/);
  assert.match(settingsSource, /send_hour: subSendHour/);
  assert.match(settingsSource, /每日推送时间（北京时间）/);
  assert.match(settingsSource, /Array\.from\(\{ length: 24 \}/);
});
