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
  assert.match(chatPageSource, /chat-model-badge/);
  assert.match(chatPageSource, /chat-status-popover/);
  assert.match(chatPageSource, /statusPopoverContent/);
  assert.match(chatPageSource, /statusRows/);
  assert.match(chatPageSource, /chat-toolbar-primary-controls/);
  assert.match(chatPageSource, /chat-icon-pill/);
  assert.match(chatPageSource, /知识库/);
  assert.match(chatPageSource, /联网/);
  assert.match(chatPageSource, /思考/);
  assert.match(chatPageSource, /视觉/);
  assert.match(chatPageSource, /等待首段/);
  assert.match(chatPageSource, /生成中/);
  assert.match(chatPageSource, /chat-stream-phase/);
});

test('chat model status styles are scoped and responsive', () => {
  assert.match(responsiveSource, /\.chat-model-badge/);
  assert.match(responsiveSource, /\.chat-toolbar-primary-controls/);
  assert.match(responsiveSource, /\.chat-status-popover/);
  assert.match(responsiveSource, /\.chat-status-row-state\.is-active/);
  assert.match(responsiveSource, /\.chat-icon-pill/);
  assert.match(responsiveSource, /\.chat-stream-status/);
  assert.match(responsiveSource, /@media \(max-width: 767px\)[\s\S]*\.chat-toolbar-primary-controls/);
});

test('chat toolbar keeps secondary actions in compact affordances', () => {
  assert.match(chatPageSource, /searchPopoverContent/);
  assert.match(chatPageSource, /toolbarMenuItems/);
  assert.match(chatPageSource, /导出对话/);
  assert.match(chatPageSource, /清空当前对话/);
  assert.match(chatPageSource, /搜索当前对话/);
});
