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

test('chat page parses streamed model metadata and first token timing', () => {
  assert.match(chatPageSource, /interface ChatModelMetadata/);
  assert.match(chatPageSource, /setActiveModelInfo\(event\.content\.model\)/);
  assert.match(chatPageSource, /setSendStartedAt\(Date\.now\(\)\)/);
  assert.match(chatPageSource, /setFirstTokenAt\(prev => prev \?\? Date\.now\(\)\)/);
  assert.match(chatPageSource, /markFirstToken\(\);[\s\S]*appendStreamingReasoning/);
  assert.match(chatPageSource, /markFirstToken\(\);[\s\S]*appendStreamingReply/);
});

test('chat page renders compact model capability and stream phase indicators', () => {
  assert.match(chatPageSource, /chat-model-status/);
  assert.match(chatPageSource, /chat-model-badge/);
  assert.match(chatPageSource, /chat-status-chip/);
  assert.match(chatPageSource, /知识库/);
  assert.match(chatPageSource, /联网/);
  assert.match(chatPageSource, /思考/);
  assert.match(chatPageSource, /视觉/);
  assert.match(chatPageSource, /等待首段/);
  assert.match(chatPageSource, /生成中/);
  assert.match(chatPageSource, /chat-stream-phase/);
});

test('chat model status styles are scoped and responsive', () => {
  assert.match(responsiveSource, /\.chat-model-status/);
  assert.match(responsiveSource, /\.chat-model-badge/);
  assert.match(responsiveSource, /\.chat-status-chip\.is-active/);
  assert.match(responsiveSource, /\.chat-stream-status/);
  assert.match(responsiveSource, /@media \(max-width: 767px\)[\s\S]*\.chat-model-status/);
});
