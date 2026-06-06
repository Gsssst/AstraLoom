import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

const chatPageSource = readFileSync(
  new URL('../src/pages/ChatPage.tsx', import.meta.url),
  'utf8',
);

const responsiveSource = readFileSync(
  new URL('../src/styles/responsive.css', import.meta.url),
  'utf8',
);

test('chat page wires stream requests through AbortController', () => {
  assert.match(chatPageSource, /abortControllerRef = useRef<AbortController \| null>\(null\)/);
  assert.match(chatPageSource, /cancelRequestedRef = useRef\(false\)/);
  assert.match(chatPageSource, /const controller = new AbortController\(\)/);
  assert.match(chatPageSource, /abortControllerRef\.current = controller/);
  assert.match(chatPageSource, /signal: controller\.signal/);
});

test('chat page handles user cancellation without generic assistant error', () => {
  assert.match(chatPageSource, /const handleStopGeneration = \(\) =>/);
  assert.match(chatPageSource, /cancelRequestedRef\.current = true/);
  assert.match(chatPageSource, /abortControllerRef\.current\.abort\(\)/);
  assert.match(chatPageSource, /e\?\.name !== 'AbortError'/);
  assert.match(chatPageSource, /finishStreamingMessages\(\)/);
  assert.match(chatPageSource, /useChatSessionStore\.setState\(\{ sending: false \}\)/);
});

test('chat page exposes stop controls while sending', () => {
  assert.match(chatPageSource, /chat-stop-inline-button/);
  assert.match(chatPageSource, /chat-stop-button/);
  assert.match(chatPageSource, /停止生成/);
  assert.match(chatPageSource, /<StopOutlined \/>/);
  assert.match(responsiveSource, /\.chat-stop-inline-button/);
  assert.match(responsiveSource, /\.chat-stop-button/);
});
