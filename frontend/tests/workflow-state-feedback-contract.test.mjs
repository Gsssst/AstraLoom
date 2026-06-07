import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

const workflowStateSource = readFileSync(
  new URL('../src/components/WorkflowState.tsx', import.meta.url),
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

test('workflow state component exposes shared loading empty unavailable and progress states', () => {
  assert.match(workflowStateSource, /export const WorkflowLoadingState/);
  assert.match(workflowStateSource, /export const WorkflowEmptyState/);
  assert.match(workflowStateSource, /export const WorkflowUnavailableState/);
  assert.match(workflowStateSource, /export const WorkflowProgressState/);
  assert.match(workflowStateSource, /Skeleton/);
  assert.match(workflowStateSource, /Empty/);
  assert.match(workflowStateSource, /Progress/);
  assert.match(workflowStateSource, /percent\?: number/);
});

test('primary workflow pages adopt shared state feedback components', () => {
  for (const source of [papersSource, researchSource, researchProjectSource, writingSource]) {
    assert.match(source, /from '\.\.\/components\/WorkflowState'/);
  }
  assert.match(papersSource, /<WorkflowLoadingState/);
  assert.match(papersSource, /<WorkflowEmptyState/);
  assert.match(researchSource, /<WorkflowLoadingState/);
  assert.match(researchSource, /<WorkflowEmptyState/);
  assert.match(researchProjectSource, /<WorkflowLoadingState/);
  assert.match(researchProjectSource, /<WorkflowUnavailableState/);
  assert.match(researchProjectSource, /<WorkflowProgressState/);
  assert.match(writingSource, /<WorkflowProgressState/);
  assert.match(writingSource, /<WorkflowEmptyState/);
});

test('research project loading and not found states remain inside page shell', () => {
  assert.doesNotMatch(researchProjectSource, /if \(loading\) return <Spin/);
  assert.doesNotMatch(researchProjectSource, /if \(!project\) return <Empty/);
  assert.match(researchProjectSource, /title="研究工作台"[\s\S]*<WorkflowLoadingState/);
  assert.match(researchProjectSource, /当前研究方向不可用[\s\S]*<WorkflowUnavailableState/);
});

test('workflow empty states provide action-oriented copy', () => {
  assert.match(papersSource, /这次外部检索没有返回论文/);
  assert.match(papersSource, /当前状态筛选下没有结果/);
  assert.match(researchSource, /创建第一个方向/);
  assert.match(researchProjectSource, /从论文证据开始生成/);
  assert.match(writingSource, /从研究方向创建草稿/);
});
