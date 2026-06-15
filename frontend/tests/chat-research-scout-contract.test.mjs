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

const backendChatSource = readFileSync(
  new URL('../../backend/app/api/chat_sessions.py', import.meta.url),
  'utf8',
);

test('chat page exposes Research Scout mode and sends assistant_mode', () => {
  assert.match(chatPageSource, /type ChatAssistantMode = 'general' \| 'research_scout'/);
  assert.match(chatPageSource, /chat-assistant-mode-select/);
  assert.match(chatPageSource, /论文猎手/);
  assert.match(chatPageSource, /handleAssistantModeChange/);
  assert.match(chatPageSource, /assistant_mode: assistantMode/);
  assert.match(chatPageSource, /effectiveWebSearch = assistantMode === 'research_scout' \|\| webSearch/);
  assert.match(chatPageSource, /effectiveSearchDepth = assistantMode === 'research_scout' \? 'deep' : searchDepth/);
  assert.match(chatPageSource, /论文猎手正在联网检索学术来源/);
  assert.match(chatPageSource, /已切换到论文猎手，并自动开启联网深度学术检索/);
});

test('chat page renders Research Scout candidate cards', () => {
  assert.match(chatPageSource, /interface ResearchScoutCandidate/);
  assert.match(chatPageSource, /research_scout/);
  assert.match(chatPageSource, /renderResearchScoutCards/);
  assert.match(chatPageSource, /research-scout-cards/);
  assert.match(chatPageSource, /论文猎手候选/);
  assert.match(chatPageSource, /继续分析/);
});

test('Research Scout cards support ingestion and follow-up search loops', () => {
  assert.match(chatPageSource, /handleResearchScoutIngest/);
  assert.match(chatPageSource, /\/papers\/ingest-personal/);
  assert.match(chatPageSource, /remote_ingest_token: paper\.ingest_token/);
  assert.match(chatPageSource, /加入论文库/);
  assert.match(chatPageSource, /\['baseline', 'survey', 'latest', 'counterexample'\]/);
  assert.match(chatPageSource, /continueScoutSearch/);
});

test('Research Scout styles are scoped', () => {
  assert.match(responsiveSource, /\.chat-assistant-mode-select/);
  assert.match(responsiveSource, /\.research-scout-cards/);
  assert.match(responsiveSource, /\.research-scout-grid/);
  assert.match(responsiveSource, /\.research-scout-card/);
  assert.match(responsiveSource, /\.research-scout-refine-button/);
  assert.match(responsiveSource, /\.chat-message-row/);
  assert.match(responsiveSource, /\.chat-message-bubble/);
  assert.match(responsiveSource, /\.chat-reference-strip/);
});

test('backend streams Research Scout metadata from scholarly discovery', () => {
  assert.match(backendChatSource, /assistant_mode: Literal\["general", "research_scout"\]/);
  assert.match(backendChatSource, /RESEARCH_SCOUT_LIMITS/);
  assert.match(backendChatSource, /search_scholarly_papers\(/);
  assert.match(backendChatSource, /source="scholarly"/);
  assert.match(backendChatSource, /_build_research_scout_context/);
  assert.match(backendChatSource, /"research_scout": \{/);
  assert.match(backendChatSource, /论文猎手已整理/);
});
