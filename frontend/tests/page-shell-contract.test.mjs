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
const actionCenterSource = readFileSync(
  new URL('../src/pages/ActionCenterPage.tsx', import.meta.url),
  'utf8',
);
const paperDigestSource = readFileSync(
  new URL('../src/pages/PaperDigestInboxPage.tsx', import.meta.url),
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
