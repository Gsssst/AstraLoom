import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

const detailSource = readFileSync(
  new URL('../src/pages/WorkspaceDetailPage.tsx', import.meta.url),
  'utf8',
);
const issueReporterSource = readFileSync(
  new URL('../src/components/WorkspaceIssueReporter.tsx', import.meta.url),
  'utf8',
);
const paperDetailSource = readFileSync(
  new URL('../src/pages/PaperDetailPage.tsx', import.meta.url),
  'utf8',
);
const researchProjectSource = readFileSync(
  new URL('../src/pages/ResearchProjectPage.tsx', import.meta.url),
  'utf8',
);
const writingSource = readFileSync(
  new URL('../src/pages/WritingPage.tsx', import.meta.url),
  'utf8',
);

test('workspace detail organizes feedback workflow into tabs', () => {
  assert.match(detailSource, /useSearchParams/);
  assert.match(detailSource, /const linkedIssueId = searchParams\.get\('issue'\)/);
  assert.match(detailSource, /const \[activeWorkspaceTab, setActiveWorkspaceTab\] = useState\('overview'\)/);
  assert.match(detailSource, /<Tabs/);
  for (const key of ['overview', 'issues', 'resources', 'assistant', 'activity']) {
    assert.match(detailSource, new RegExp(`key: '${key}'`));
  }
  assert.match(detailSource, /setActiveWorkspaceTab\('issues'\)/);
  assert.match(detailSource, /openIssueDetail\(\{ id: linkedIssueId \} as WorkspaceIssue\)/);
  assert.match(detailSource, /setActiveWorkspaceTab\('resources'\)/);
});

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

test('workspace issue list and drawer show linked resource references', () => {
  assert.match(detailSource, /resource_reference\?: any/);
  assert.match(detailSource, /issue\.resource_reference/);
  assert.match(detailSource, /关联：\{issue\.resource_reference\.title/);
  assert.match(detailSource, /selectedIssue\.resource_reference/);
  assert.match(detailSource, /关联资源/);
  assert.match(detailSource, /navigate\(selectedIssue\.resource_reference\.path\)/);
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

test('resource pages can submit workspace-linked feedback issues', () => {
  assert.match(issueReporterSource, /api\.get\('\/workspaces\/resource-links'/);
  assert.match(issueReporterSource, /filter\(\(space: any\) => space\.linked\)/);
  assert.match(issueReporterSource, /api\.post\(`\/workspaces\/\$\{values\.space_id\}\/issues`/);
  assert.match(issueReporterSource, /resource_reference: \{/);
  assert.match(issueReporterSource, /navigate\(`\/workspaces\/\$\{values\.space_id\}\?issue=\$\{response\.data\.id\}`\)/);
  assert.match(issueReporterSource, /okButtonProps=\{\{ disabled: loading \|\| !spaces\.length \}\}/);
  assert.match(issueReporterSource, /这个资源还没有绑定项目空间/);

  for (const source of [paperDetailSource, researchProjectSource, writingSource]) {
    assert.match(source, /import WorkspaceIssueReporter from '\.\.\/components\/WorkspaceIssueReporter'/);
    assert.match(source, /<WorkspaceIssueReporter/);
  }
});

test('paper detail exposes cached AI insight cards', () => {
  assert.match(paperDetailSource, /interface PaperInsight/);
  assert.match(paperDetailSource, /paperInsight/);
  assert.match(paperDetailSource, /insightLoading/);
  assert.match(paperDetailSource, /handleGenerateInsights/);
  assert.match(paperDetailSource, /api\.get\(`\/papers\/\$\{paperId\}\/insights`, \{ params: \{ refresh \} \}\)/);
  assert.match(paperDetailSource, /AI 论文洞察/);
  assert.match(paperDetailSource, /核心贡献/);
  assert.match(paperDetailSource, /可借鉴方法/);
  assert.match(paperDetailSource, /可复现实验/);
  assert.match(paperDetailSource, /研究方向关联/);
});
