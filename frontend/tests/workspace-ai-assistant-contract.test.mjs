import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

const detailSource = readFileSync(
  new URL('../src/pages/WorkspaceDetailPage.tsx', import.meta.url),
  'utf8',
);

test('workspace detail loads workspace-scoped assistant state', () => {
  assert.match(detailSource, /fetchAssistantState/);
  assert.match(detailSource, /api\.get\(`\/workspaces\/\$\{spaceId\}\/assistant`\)/);
  assert.match(detailSource, /setAssistantMessages\(response\.data\.messages \|\| \[\]\)/);
  assert.match(detailSource, /setAssistantPrompts\(response\.data\.quick_prompts \|\| \[\]\)/);
  assert.match(detailSource, /setAssistantReferences\(response\.data\.references \|\| \[\]\)/);
});

test('workspace detail sends assistant messages without clearing failed input', () => {
  assert.match(detailSource, /sendAssistantMessage/);
  assert.match(detailSource, /api\.post\(`\/workspaces\/\$\{spaceId\}\/assistant\/send`, \{ content \}\)/);
  assert.match(detailSource, /setAssistantMessages\(prev => \[\.\.\.prev, response\.data\.message, response\.data\.reply\]\)/);
  assert.match(detailSource, /if \(!contentOverride\) setAssistantInput\(content\)/);
  assert.match(detailSource, /AI 助手发送失败/);
});

test('workspace detail renders assistant panel with prompts messages and references', () => {
  assert.match(detailSource, /项目空间 AI 助手/);
  assert.match(detailSource, /renderAssistantPanel/);
  assert.match(detailSource, /assistantPrompts\.map/);
  assert.match(detailSource, /assistantMessages\.map/);
  assert.match(detailSource, /item\.references\.slice\(0, 6\)/);
  assert.match(detailSource, /assistantReferences\.slice\(0, 8\)/);
  assert.match(detailSource, /发送给空间助手/);
  assert.match(detailSource, /基于当前空间的论文、研究方向、写作草稿和活动记录回答/);
});
