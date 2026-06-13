import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

const guideSource = readFileSync(
  new URL('../src/components/WorkflowStepGuide.tsx', import.meta.url),
  'utf8',
);
const papersPageSource = readFileSync(
  new URL('../src/pages/PapersPage.tsx', import.meta.url),
  'utf8',
);
const researchPageSource = readFileSync(
  new URL('../src/pages/ResearchPage.tsx', import.meta.url),
  'utf8',
);
const writingPageSource = readFileSync(
  new URL('../src/pages/WritingPage.tsx', import.meta.url),
  'utf8',
);

test('workflow step guide supports shared route and local actions', () => {
  assert.match(guideSource, /export interface WorkflowStep/);
  assert.match(guideSource, /path\?: string/);
  assert.match(guideSource, /onClick\?: \(\) => void/);
  assert.match(guideSource, /navigate\(step\.path\)/);
  assert.match(guideSource, /推荐下一步/);
  assert.match(guideSource, /统一工作流/);
});

test('paper library exposes unified workflow next steps', () => {
  assert.match(papersPageSource, /WorkflowStepGuide/);
  assert.match(papersPageSource, /论文库下一步/);
  assert.match(papersPageSource, /后台自动补齐处理/);
  assert.match(papersPageSource, /查看处理诊断/);
  assert.match(papersPageSource, /管理分类/);
  assert.match(papersPageSource, /去研究方向/);
  assert.match(papersPageSource, /updateSource\('maintenance'\)/);
  assert.match(papersPageSource, /updateSource\('collection'\)/);
});

test('research page exposes unified workflow next steps', () => {
  assert.match(researchPageSource, /WorkflowStepGuide/);
  assert.match(researchPageSource, /研究方向下一步/);
  assert.match(researchPageSource, /准备论文种子/);
  assert.match(researchPageSource, /新建并绑定分类/);
  assert.match(researchPageSource, /沉淀到写作/);
  assert.match(researchPageSource, /setCreateModalOpen\(true\)/);
});

test('writing page exposes unified workflow next steps', () => {
  assert.match(writingPageSource, /WorkflowStepGuide/);
  assert.match(writingPageSource, /写作工作台下一步/);
  assert.match(writingPageSource, /从研究方向开始/);
  assert.match(writingPageSource, /补齐证据与引用/);
  assert.match(writingPageSource, /导出前检查模板/);
  assert.match(writingPageSource, /scrollToWorkbenchTarget\('evidence'\)/);
  assert.match(writingPageSource, /scrollToWorkbenchTarget\('export'\)/);
});
