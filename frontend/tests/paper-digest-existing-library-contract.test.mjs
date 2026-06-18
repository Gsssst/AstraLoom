import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

const digestPageSource = readFileSync(
  new URL('../src/pages/PaperDigestInboxPage.tsx', import.meta.url),
  'utf8',
);

test('paper digest cards disable import for papers already in the library', () => {
  assert.match(digestPageSource, /in_library/);
  assert.match(digestPageSource, /local_paper_id/);
  assert.match(digestPageSource, /alreadyInLibrary/);
  assert.match(digestPageSource, /已在论文库/);
  assert.match(digestPageSource, /<Button size="small" disabled icon=\{<CheckCircleOutlined \/>/);
});

test('paper push center renders paper chat share notifications', () => {
  assert.match(digestPageSource, /category\?: string/);
  assert.match(digestPageSource, /selected_messages/);
  assert.match(digestPageSource, /renderPaperChatShareCard/);
  assert.match(digestPageSource, /digest\.category === 'paper_chat_share'/);
  assert.match(digestPageSource, /论文精读分享/);
  assert.match(digestPageSource, /打开论文/);
  assert.match(digestPageSource, /条推送/);
});
