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
const sectionEditorSource = readFileSync(
  new URL('../src/components/writing/SectionEditor.tsx', import.meta.url),
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

test('paper workbench exposes consolidated project summary and next actions', () => {
  assert.match(writingPageSource, /workbench-summary/);
  assert.match(writingPageSource, /写作工作台总览/);
  assert.match(writingPageSource, /建议下一步/);
  assert.match(writingPageSource, /章节进度/);
  assert.match(writingPageSource, /证据覆盖/);
  assert.match(writingPageSource, /引用风险/);
  assert.match(writingPageSource, /投稿模板/);
  assert.match(writingPageSource, /去处理/);
});

test('citation recommendation UI exposes evidence decision loop', () => {
  assert.match(writingPageSource, /引用决策概览/);
  assert.match(writingPageSource, /decision_label/);
  assert.match(writingPageSource, /decision_action/);
  assert.match(writingPageSource, /decision_warning/);
  assert.match(writingPageSource, /支持证据/);
  assert.match(writingPageSource, /基线方法/);
  assert.match(writingPageSource, /反例\/局限/);
  assert.match(writingPageSource, /谨慎使用/);
});

test('section citation diagnostics expose actionable next steps', () => {
  assert.match(sectionEditorSource, /校验引用/);
  assert.match(sectionEditorSource, /建议下一步/);
  assert.match(sectionEditorSource, /decision_action/);
  assert.match(sectionEditorSource, /decision_warning/);
});

test('section editor exposes draft quality coaching', () => {
  assert.match(sectionEditorSource, /质量评估/);
  assert.match(sectionEditorSource, /章节质量/);
  assert.match(sectionEditorSource, /rewrite_actions/);
  assert.match(sectionEditorSource, /dimensions/);
  assert.match(writingPageSource, /sections\/quality-check/);
  assert.match(writingPageSource, /qualityChecks/);
  assert.match(writingPageSource, /handleCheckSectionQuality/);
});

test('writing project creation supports context binding', () => {
  assert.match(projectPanelSource, /api\.get\('\/research\/projects'\)/);
  assert.match(projectPanelSource, /api\.get\('\/folders\/'\)/);
  assert.match(projectPanelSource, /writing_type/);
  assert.match(projectPanelSource, /target_venue/);
  assert.match(projectPanelSource, /target_year/);
  assert.match(projectPanelSource, /research_project_id/);
  assert.match(projectPanelSource, /collection_ids/);
  assert.match(projectPanelSource, /绑定研究方向/);
  assert.match(projectPanelSource, /绑定论文分类/);
  assert.match(writingPageSource, /研究方向：/);
  assert.match(writingPageSource, /论文分类/);
});
