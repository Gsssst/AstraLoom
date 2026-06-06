import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

const chatPageSource = readFileSync(
  new URL('../src/pages/ChatPage.tsx', import.meta.url),
  'utf8',
);

test('chat send handler accepts an explicit prompt override', () => {
  assert.match(chatPageSource, /const handleSend = async \(overrideContent\?: string\)/);
  assert.match(chatPageSource, /const hasOverride = typeof overrideContent === 'string'/);
  assert.match(chatPageSource, /const text = \(hasOverride \? overrideContent : input\)\.trim\(\)/);
  assert.match(chatPageSource, /if \(!hasOverride\) setInput\(''\)/);
});

test('regeneration menu actions send explicit prompts without timeout state races', () => {
  assert.doesNotMatch(chatPageSource, /setTimeout\(\s*\(\)\s*=>\s*handleSend/);
  assert.match(chatPageSource, /handleSend\('请重新回答'\)/);
  assert.match(chatPageSource, /handleSend\('请用更有创意的角度回答'\)/);
  assert.match(chatPageSource, /handleSend\('请精确严谨地重新回答'\)/);
  assert.match(chatPageSource, /handleToggleRag\(false\); handleSend\('请重新回答'\)/);
});
