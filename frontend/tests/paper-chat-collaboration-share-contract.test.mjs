import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

const paperDetailSource = readFileSync(
  new URL('../src/pages/PaperDetailPage.tsx', import.meta.url),
  'utf8',
);
const appLayoutSource = readFileSync(
  new URL('../src/components/AppLayout.tsx', import.meta.url),
  'utf8',
);
const messagesSource = readFileSync(
  new URL('../src/i18n/messages.ts', import.meta.url),
  'utf8',
);
const responsiveSource = readFileSync(
  new URL('../src/styles/responsive.css', import.meta.url),
  'utf8',
);

test('paper detail exposes a share-to-members action on assistant answers', () => {
  assert.match(paperDetailSource, /openPaperChatShareModal\(msg, idx\)/);
  assert.match(paperDetailSource, />推送成员<\/Button>/);
  assert.match(paperDetailSource, /api\.get\(`\/papers\/\$\{paperId\}\/share-targets`\)/);
  assert.match(paperDetailSource, /api\.post\(`\/papers\/\$\{paperId\}\/share-chat-insight`/);
});

test('paper chat share modal shows workspace target, note, and empty state guidance', () => {
  assert.match(paperDetailSource, /title="推送论文 AI 精读"/);
  assert.match(paperDetailSource, /okText="推送给成员"/);
  assert.match(paperDetailSource, /这篇论文还没有绑定到你所在的项目空间/);
  assert.match(paperDetailSource, /placeholder="可选：补充你为什么推荐大家看这段回答"/);
  assert.match(responsiveSource, /\.paper-chat-share-preview/);
});

test('global notifications route paper chat share events to source papers', () => {
  assert.match(appLayoutSource, /paper_chat_share: \{ labelKey: 'notifications\.category\.paperChatShare'/);
  assert.match(appLayoutSource, /item\.category === 'paper_chat_share'/);
  assert.match(appLayoutSource, /metadata\.paper_id\) return `\/papers\/\$\{metadata\.paper_id\}`/);
  assert.match(messagesSource, /'notifications\.category\.paperChatShare': '论文精读分享'/);
  assert.match(messagesSource, /'notifications\.category\.paperChatShare': 'Paper Reading Share'/);
});
