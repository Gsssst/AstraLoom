import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

const hookSource = readFileSync(
  new URL('../src/hooks/useChatAutoScroll.ts', import.meta.url),
  'utf8',
);
const chatPageSource = readFileSync(
  new URL('../src/pages/ChatPage.tsx', import.meta.url),
  'utf8',
);
const paperDetailSource = readFileSync(
  new URL('../src/pages/PaperDetailPage.tsx', import.meta.url),
  'utf8',
);

test('chat auto-scroll hook tracks bottom proximity and user scroll state', () => {
  assert.match(hookSource, /DEFAULT_BOTTOM_THRESHOLD_PX = 48/);
  assert.match(hookSource, /scrollContainerRef = useRef<HTMLDivElement>\(null\)/);
  assert.match(hookSource, /scrollEndRef = useRef<HTMLDivElement>\(null\)/);
  assert.match(hookSource, /followOutputRef = useRef\(true\)/);
  assert.match(hookSource, /scrollHeight - container\.scrollTop - container\.clientHeight/);
  assert.match(hookSource, /container\.addEventListener\('scroll', syncFollowState, \{ passive: true \}\)/);
  assert.match(hookSource, /if \(!followOutputRef\.current\) return/);
  assert.match(hookSource, /behavior: 'auto'/);
});

test('main chat streams only follow bottom while user remains near bottom', () => {
  assert.match(chatPageSource, /import useChatAutoScroll from '\.\.\/hooks\/useChatAutoScroll'/);
  assert.match(chatPageSource, /scrollContainerRef: chatScrollRef/);
  assert.match(chatPageSource, /scrollEndRef: messagesEndRef/);
  assert.match(chatPageSource, /scrollToBottomIfFollowing/);
  assert.match(chatPageSource, /enableFollowOutput/);
  assert.match(chatPageSource, /useEffect\(\(\) => \{ scrollToBottomIfFollowing\(\); \}, \[messages, pendingMsg, scrollToBottomIfFollowing\]\)/);
  assert.match(chatPageSource, /enableFollowOutput\(\);[\s\S]*setState\(s => \(\{ messages:/);
  assert.match(chatPageSource, /<div ref=\{chatScrollRef\} className="chat-message-list"/);
  assert.doesNotMatch(chatPageSource, /messagesEndRef\.current\?\.scrollIntoView\(\{ behavior: 'smooth' \}\)/);
});

test('paper detail chat uses the same manual-scroll-aware streaming behavior', () => {
  assert.match(paperDetailSource, /import useChatAutoScroll from '\.\.\/hooks\/useChatAutoScroll'/);
  assert.match(paperDetailSource, /scrollContainerRef: paperChatScrollRef/);
  assert.match(paperDetailSource, /scrollEndRef: chatEndRef/);
  assert.match(paperDetailSource, /scrollPaperChatToBottomIfFollowing/);
  assert.match(paperDetailSource, /enablePaperChatFollowOutput/);
  assert.match(paperDetailSource, /useEffect\(\(\) => \{ scrollPaperChatToBottomIfFollowing\(\); \}, \[chatMsgs, scrollPaperChatToBottomIfFollowing\]\)/);
  assert.match(paperDetailSource, /enablePaperChatFollowOutput\(\);[\s\S]*setChatMsgs\(prev => \[\.\.\.prev, userMessage\]\)/);
  assert.match(paperDetailSource, /<div ref=\{paperChatScrollRef\} className="paper-detail-chat-scroll"/);
  assert.doesNotMatch(paperDetailSource, /chatEndRef\.current\?\.scrollIntoView\(\{ behavior: 'smooth' \}\)/);
});
