import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

const detailSource = readFileSync(
  new URL('../src/pages/WorkspaceDetailPage.tsx', import.meta.url),
  'utf8',
);

test('workspace detail exposes feedback issue panel and filters', () => {
  assert.match(detailSource, /反馈 Issue/);
  assert.match(detailSource, /renderIssuePanel/);
  assert.match(detailSource, /issueSummary\.open/);
  assert.match(detailSource, /issueSummary\.closed/);
  assert.match(detailSource, /issueFilters/);
  assert.match(detailSource, /status_filter: filters\.status === 'all' \? undefined : filters\.status/);
  assert.match(detailSource, /issue_type: filters\.issue_type === 'all' \? undefined : filters\.issue_type/);
  assert.match(detailSource, /priority: filters\.priority === 'all' \? undefined : filters\.priority/);
});

test('workspace detail creates issues and opens issue discussion drawer', () => {
  assert.match(detailSource, /handleCreateIssue/);
  assert.match(detailSource, /api\.post\(`\/workspaces\/\$\{spaceId\}\/issues`, values\)/);
  assert.match(detailSource, /setIssueModalOpen\(false\)/);
  assert.match(detailSource, /setIssueDrawerOpen\(true\)/);
  assert.match(detailSource, /<Drawer/);
  assert.match(detailSource, /selectedIssue\.comments/);
});

test('workspace detail supports comments and role-aware triage controls', () => {
  assert.match(detailSource, /handleAddIssueComment/);
  assert.match(detailSource, /api\.post\(`\/workspaces\/\$\{spaceId\}\/issues\/\$\{selectedIssue\.id\}\/comments`, values\)/);
  assert.match(detailSource, /updateSelectedIssue/);
  assert.match(detailSource, /api\.patch\(`\/workspaces\/\$\{spaceId\}\/issues\/\$\{selectedIssue\.id\}`, updates\)/);
  assert.match(detailSource, /selectedIssue && canEditResources/);
  assert.match(detailSource, /selectedIssue\.status === 'open' \? '关闭 Issue' : '重新打开'/);
});
