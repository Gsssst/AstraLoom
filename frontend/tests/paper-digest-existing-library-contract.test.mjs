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
