import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

const pageShellSource = readFileSync(
  new URL('../src/components/PageShell.tsx', import.meta.url),
  'utf8',
);
const pageShellStyles = readFileSync(
  new URL('../src/styles/page-shell.css', import.meta.url),
  'utf8',
);
const settingsSource = readFileSync(
  new URL('../src/pages/SettingsPage.tsx', import.meta.url),
  'utf8',
);
const workspacesSource = readFileSync(
  new URL('../src/pages/WorkspacesPage.tsx', import.meta.url),
  'utf8',
);
const workspaceDetailSource = readFileSync(
  new URL('../src/pages/WorkspaceDetailPage.tsx', import.meta.url),
  'utf8',
);
const actionCenterSource = readFileSync(
  new URL('../src/pages/ActionCenterPage.tsx', import.meta.url),
  'utf8',
);
const paperDigestSource = readFileSync(
  new URL('../src/pages/PaperDigestInboxPage.tsx', import.meta.url),
  'utf8',
);
const adminSource = readFileSync(
  new URL('../src/pages/AdminPage.tsx', import.meta.url),
  'utf8',
);
const papersSource = readFileSync(
  new URL('../src/pages/PapersPage.tsx', import.meta.url),
  'utf8',
);
const researchSource = readFileSync(
  new URL('../src/pages/ResearchPage.tsx', import.meta.url),
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

test('page shell exposes stable layout class hooks', () => {
  for (const className of [
    'page-shell',
    'page-shell-header',
    'page-shell-heading',
    'page-shell-icon',
    'page-shell-title-block',
    'page-shell-title',
    'page-shell-subtitle',
    'page-shell-actions',
    'page-shell-body',
  ]) {
    assert.match(pageShellSource + pageShellStyles, new RegExp(className));
  }
});

test('page shell supports title subtitle actions and configurable width', () => {
  assert.match(pageShellSource, /title: React\.ReactNode/);
  assert.match(pageShellSource, /subtitle\?: React\.ReactNode/);
  assert.match(pageShellSource, /actions\?: React\.ReactNode/);
  assert.match(pageShellSource, /maxWidth\?: number \| string/);
  assert.match(pageShellSource, /style=\{\{ maxWidth:/);
  assert.match(pageShellStyles, /@media \(max-width: 768px\)/);
});

test('settings page adopts the shared page shell without replacing tabs', () => {
  assert.match(settingsSource, /import PageShell from '\.\.\/components\/PageShell'/);
  assert.match(settingsSource, /<PageShell/);
  assert.match(settingsSource, /title="系统设置"/);
  assert.match(settingsSource, /maxWidth=\{860\}/);
  assert.match(settingsSource, /<Tabs activeKey=\{undefined\} defaultActiveKey="profile" items=\{tabs\}/);
  assert.doesNotMatch(settingsSource, /heroGradient/);
});

test('workspaces page adopts page shell with create action', () => {
  assert.match(workspacesSource, /import PageShell from '\.\.\/components\/PageShell'/);
  assert.match(workspacesSource, /<PageShell/);
  assert.match(workspacesSource, /title="项目空间"/);
  assert.match(workspacesSource, /maxWidth=\{1180\}/);
  assert.match(workspacesSource, /actions=\{\(/);
  assert.match(workspacesSource, /新建空间/);
  assert.match(workspacesSource, /setModalOpen\(true\)/);
  assert.match(workspacesSource, /<Modal title="新建项目空间"/);
  assert.doesNotMatch(workspacesSource, /linear-gradient\(135deg, #667eea 0%, #764ba2 100%\)/);
});

test('workspace detail page adopts page shell with recovery guidance', () => {
  assert.match(workspaceDetailSource, /import PageShell from '\.\.\/components\/PageShell'/);
  assert.match(workspaceDetailSource, /<PageShell/);
  assert.match(workspaceDetailSource, /title=\{space\?\.name \|\| '项目空间详情'\}/);
  assert.match(workspaceDetailSource, /maxWidth=\{1280\}/);
  assert.match(workspaceDetailSource, /返回项目空间/);
  assert.match(workspaceDetailSource, /论文库/);
  assert.match(workspaceDetailSource, /研究方向/);
  assert.match(workspaceDetailSource, /写作/);
  assert.match(workspaceDetailSource, /getApiErrorDetails/);
  assert.match(workspaceDetailSource, /workspaceActionError/);
  assert.match(workspaceDetailSource, /workspaceActionError\.detail\.recovery/);
  assert.match(workspaceDetailSource, /需先处理条件/);
  assert.doesNotMatch(workspaceDetailSource, /navigate\('\/workspaces'\);\n    } finally/);
});

test('action center adopts page shell with summary content', () => {
  assert.match(actionCenterSource, /import PageShell from '\.\.\/components\/PageShell'/);
  assert.match(actionCenterSource, /<PageShell/);
  assert.match(actionCenterSource, /title="行动中心"/);
  assert.match(actionCenterSource, /maxWidth=\{1280\}/);
  assert.match(actionCenterSource, /<Statistic title="行动项"/);
  assert.match(actionCenterSource, /<Statistic title="高优先级"/);
  assert.doesNotMatch(actionCenterSource, /linear-gradient\(135deg, #667eea 0%, #764ba2 100%\)/);
});

test('paper digest inbox adopts page shell with recovery guidance', () => {
  assert.match(paperDigestSource, /import PageShell from '\.\.\/components\/PageShell'/);
  assert.match(paperDigestSource, /<PageShell/);
  assert.match(paperDigestSource, /title="论文推送中心"/);
  assert.match(paperDigestSource, /maxWidth=\{1100\}/);
  assert.match(paperDigestSource, /返回论文库/);
  assert.match(paperDigestSource, /getApiErrorDetails/);
  assert.match(paperDigestSource, /digestActionError/);
  assert.match(paperDigestSource, /digestActionError\.detail\.recovery/);
  assert.match(paperDigestSource, /需先处理条件/);
  assert.doesNotMatch(paperDigestSource, /heroGradient/);
});

test('admin page adopts page shell with recovery guidance', () => {
  assert.match(adminSource, /import PageShell from '\.\.\/components\/PageShell'/);
  assert.match(adminSource, /<PageShell/);
  assert.match(adminSource, /title="管理员后台"/);
  assert.match(adminSource, /maxWidth=\{1320\}/);
  assert.match(adminSource, /刷新/);
  assert.match(adminSource, /getApiErrorDetails/);
  assert.match(adminSource, /adminActionError/);
  assert.match(adminSource, /adminActionError\.detail\.recovery/);
  assert.match(adminSource, /需先处理条件/);
  assert.doesNotMatch(adminSource, /heroGradient/);
});

test('papers page adopts page shell while preserving paper workflows', () => {
  assert.match(papersSource, /import PageShell from '\.\.\/components\/PageShell'/);
  assert.match(papersSource, /<PageShell/);
  assert.match(papersSource, /title="论文库"/);
  assert.match(papersSource, /maxWidth=\{1100\}/);
  assert.match(papersSource, /论文推送/);
  assert.match(papersSource, /维护中心/);
  assert.match(papersSource, /<WorkflowStepGuide/);
  assert.match(papersSource, /<Input\.Search/);
  assert.doesNotMatch(papersSource, /heroGradient/);
});

test('research page adopts page shell while preserving direction workflows', () => {
  assert.match(researchSource, /import PageShell from '\.\.\/components\/PageShell'/);
  assert.match(researchSource, /<PageShell/);
  assert.match(researchSource, /title="研究方向"/);
  assert.match(researchSource, /maxWidth=\{1100\}/);
  assert.match(researchSource, /新建方向/);
  assert.match(researchSource, /setCreateModalOpen\(true\)/);
  assert.match(researchSource, /<WorkflowStepGuide/);
  assert.match(researchSource, /<Modal title=\{<span><ExperimentOutlined/);
  assert.doesNotMatch(researchSource, /heroGradient/);
});

test('research project page adopts page shell while preserving workbench workflows', () => {
  assert.match(researchProjectSource, /import PageShell from '\.\.\/components\/PageShell'/);
  assert.match(researchProjectSource, /<PageShell/);
  assert.match(researchProjectSource, /title=\{project\?\.name \|\| '研究工作台'\}/);
  assert.match(researchProjectSource, /maxWidth=\{1280\}/);
  assert.match(researchProjectSource, /返回研究方向/);
  assert.match(researchProjectSource, /生成 Proposal/);
  assert.match(researchProjectSource, /<Tabs activeKey=\{activeWorkbenchTab\}/);
  assert.doesNotMatch(researchProjectSource, /heroGradient/);
});

test('writing page adopts page shell while preserving assistant modes and tabs', () => {
  assert.match(writingSource, /import PageShell from '\.\.\/components\/PageShell'/);
  assert.match(writingSource, /<PageShell/);
  assert.match(writingSource, /title=\{assistantMode === 'paper' \? '写作工作台' : '基金申请助手'\}/);
  assert.match(writingSource, /maxWidth=\{assistantMode === 'paper' && activeTab === 'project' \? 1360 : 980\}/);
  assert.match(writingSource, /<Segmented/);
  assert.match(writingSource, /value=\{assistantMode\}/);
  assert.match(writingSource, /<Tabs[\s\S]*activeKey=\{activeTab\}/);
  assert.match(writingSource, /<WorkflowStepGuide/);
  assert.doesNotMatch(writingSource, /heroGradient/);
});
