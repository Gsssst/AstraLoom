import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

const paperDetailSource = readFileSync(
  new URL('../src/pages/PaperDetailPage.tsx', import.meta.url),
  'utf8',
);

test('paper detail chat exposes a stop control for streamed answers', () => {
  assert.match(paperDetailSource, /paperChatAbortControllerRef = useRef<AbortController \| null>\(null\)/);
  assert.match(paperDetailSource, /paperChatCancelRequestedRef = useRef\(false\)/);
  assert.match(paperDetailSource, /const handleStopPaperChatGeneration = \(\) =>/);
  assert.match(paperDetailSource, /paperChatAbortControllerRef\.current\.abort\(\)/);
  assert.match(paperDetailSource, /finishPaperChatStreamingMessages\(\)/);
  assert.match(paperDetailSource, /icon=\{<StopOutlined \/>}/);
  assert.match(paperDetailSource, />停止<\/Button>/);
});

test('paper detail chat aborts fetch without adding generic failure text', () => {
  assert.match(paperDetailSource, /const controller = new AbortController\(\)/);
  assert.match(paperDetailSource, /signal: controller\.signal/);
  assert.match(paperDetailSource, /error\?\.name === 'AbortError'/);
  assert.match(paperDetailSource, /paperChatCancelRequestedRef\.current \|\| error\?\.name === 'AbortError'/);
});
