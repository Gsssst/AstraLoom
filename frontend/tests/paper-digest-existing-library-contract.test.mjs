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

test('paper chat share cards render full markdown content instead of excerpts', () => {
  assert.match(digestPageSource, /paperChatShareMessageContent/);
  assert.match(digestPageSource, /item\.content \|\| item\.display_content \|\| item\.excerpt/);
  assert.match(digestPageSource, /<Markdown content=\{paperChatShareMessageContent\(item\)\} \/>/);
});

test('paper chat share cards are collapsed until expanded', () => {
  assert.match(digestPageSource, /expandedShareIds/);
  assert.match(digestPageSource, /togglePaperChatShareExpanded/);
  assert.match(digestPageSource, /expandedShareIds\.has\(digest\.id\)/);
  assert.match(digestPageSource, /paperChatShareMessagePreview/);
  assert.match(digestPageSource, /展开精读/);
  assert.match(digestPageSource, /收起精读/);
  assert.match(digestPageSource, /!expanded \?/);
  assert.match(digestPageSource, /expanded \? '收起精读'/);
});
