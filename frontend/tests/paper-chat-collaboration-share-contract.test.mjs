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

test('paper detail exposes direct user multi-message sharing controls', () => {
  assert.match(paperDetailSource, /shareSelectionMode/);
  assert.match(paperDetailSource, /'选择推送'/);
  assert.match(paperDetailSource, /toggleShareMessageSelection\(idx\)/);
  assert.match(paperDetailSource, />推送这段<\/Button>/);
  assert.match(paperDetailSource, /api\.get\(`\/papers\/\$\{paperId\}\/share-recipients`/);
  assert.match(paperDetailSource, /api\.post\(`\/papers\/\$\{paperId\}\/share-chat-insight`/);
  assert.match(paperDetailSource, /recipient_user_ids: chatShare\.allUsers \? \[\] : chatShare\.recipientIds/);
  assert.match(paperDetailSource, /all_users: chatShare\.allUsers/);
  assert.match(paperDetailSource, /selected_messages: selectedShareMessages\.map/);
});

test('paper chat share modal shows searchable recipients and selected-message preview', () => {
  assert.match(paperDetailSource, /title="推送论文 AI 精读"/);
  assert.match(paperDetailSource, /okText="推送给用户"/);
  assert.match(paperDetailSource, /mode="multiple"/);
  assert.match(paperDetailSource, /placeholder="搜索用户名、邮箱或显示名"/);
  assert.match(paperDetailSource, />\s*推送所有用户\s*<\/Button>/);
  assert.match(paperDetailSource, /将推送给所有活跃用户/);
  assert.match(paperDetailSource, /已选择 \{selectedShareMessages\.length\} 条对话/);
  assert.match(paperDetailSource, /placeholder="可选：补充你为什么推荐大家看这段对话"/);
  assert.match(responsiveSource, /\.paper-chat-share-preview/);
  assert.match(responsiveSource, /\.paper-chat-share-message-preview/);
});

test('global notifications route paper chat share events to source papers', () => {
  assert.match(appLayoutSource, /paper_chat_share: \{ labelKey: 'notifications\.category\.paperChatShare'/);
  assert.match(appLayoutSource, /item\.category === 'paper_chat_share'/);
  assert.match(appLayoutSource, /metadata\.paper_id\) return `\/papers\/\$\{metadata\.paper_id\}`/);
  assert.match(appLayoutSource, /renderNotificationDescription/);
  assert.match(appLayoutSource, /notification-paper-share-preview/);
  assert.match(appLayoutSource, /selected_messages/);
  assert.match(appLayoutSource, />\s*打开论文\s*<\/Button>/);
  assert.match(responsiveSource, /\.notification-paper-share-message/);
  assert.match(messagesSource, /'notifications\.category\.paperChatShare': '论文精读分享'/);
  assert.match(messagesSource, /'notifications\.category\.paperChatShare': 'Paper Reading Share'/);
});
