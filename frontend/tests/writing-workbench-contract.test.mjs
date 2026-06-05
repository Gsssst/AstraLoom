import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

const writingPageSource = readFileSync(
  new URL('../src/pages/WritingPage.tsx', import.meta.url),
  'utf8',
);
const projectPanelSource = readFileSync(
  new URL('../src/components/writing/WritingProjectPanel.tsx', import.meta.url),
  'utf8',
);

test('writing assistant exposes paper and grant workbench modes', () => {
  assert.match(writingPageSource, /写论文助手/);
  assert.match(writingPageSource, /写本子助手/);
  assert.match(writingPageSource, /论文项目工作台/);
});

test('writing page defaults to project-first paper workflow', () => {
  assert.match(writingPageSource, /useState(?:<[^>]+>)?\('paper'\)/);
  assert.match(writingPageSource, /useState\('project'\)/);
  assert.doesNotMatch(writingPageSource, /key: 'grant', label:/);
});

test('project creation clarifies structure templates are not official submission formats', () => {
  assert.match(projectPanelSource, /章节结构模板/);
  assert.match(projectPanelSource, /不代表当前年度官方投稿格式/);
  assert.match(projectPanelSource, /会议官网模板/);
});

test('paper workbench exposes official submission template profile panel', () => {
  assert.match(writingPageSource, /投稿目标与官方模板/);
  assert.match(writingPageSource, /会议格式每年可能变化/);
  assert.match(writingPageSource, /检查并绑定/);
});
