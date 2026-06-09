import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { join } from 'node:path';

const root = new URL('..', import.meta.url).pathname;
const read = (path) => readFileSync(join(root, path), 'utf8');

test('bilingual dictionaries keep matching zh/en keys', () => {
  const source = read('src/i18n/messages.ts');
  const zhKeys = [...source.matchAll(/'([^']+)':\s*'[^']*'/g)]
    .map((match) => match[1]);
  const enStart = source.indexOf('  en: {');
  assert.ok(enStart > 0, 'English dictionary must exist');

  const zhSource = source.slice(source.indexOf('  zh: {'), enStart);
  const enSource = source.slice(enStart);
  const zh = [...zhSource.matchAll(/'([^']+)':\s*'[^']*'/g)].map((match) => match[1]).sort();
  const en = [...enSource.matchAll(/'([^']+)':\s*'[^']*'/g)].map((match) => match[1]).sort();

  assert.deepEqual(en, zh);
  assert.ok(zhKeys.includes('header.language'));
  assert.ok(zhKeys.includes('settings.language.title'));
});

test('App wires selected language into Ant Design ConfigProvider locale', () => {
  const app = read('src/App.tsx');
  assert.match(app, /const language = useLocaleStore\(\(s\) => s\.language\)/);
  assert.match(app, /locale=\{antdLocales\[language\]\}/);
});

test('global header and settings expose language controls', () => {
  const layout = read('src/components/AppLayout.tsx');
  const settings = read('src/pages/SettingsPage.tsx');

  assert.match(layout, /setLanguage/);
  assert.match(layout, /GlobalOutlined/);
  assert.match(layout, /header\.language/);
  assert.match(settings, /settings\.language\.title/);
  assert.match(settings, /Segmented/);
});
