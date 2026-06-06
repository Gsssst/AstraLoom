import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

const researchProjectSource = readFileSync(
  new URL('../src/pages/ResearchProjectPage.tsx', import.meta.url),
  'utf8',
);

test('research project page exposes idea validation loop', () => {
  assert.match(researchProjectSource, /\/research\/ideas\/\$\{ideaId\}\/validation/);
  assert.match(researchProjectSource, /验证闭环/);
  assert.match(researchProjectSource, /写作准备度|writing_readiness/);
  assert.match(researchProjectSource, /撞车风险/);
  assert.match(researchProjectSource, /最小实验检查清单/);
  assert.match(researchProjectSource, /相关\/冲突工作/);
});

test('validation panel surfaces readiness, risks, checklist, and next actions', () => {
  assert.match(researchProjectSource, /readinessColors/);
  assert.match(researchProjectSource, /feasibility_risks/);
  assert.match(researchProjectSource, /experiment_checklist/);
  assert.match(researchProjectSource, /next_actions/);
  assert.match(researchProjectSource, /experiment_completeness/);
});

test('research project page exposes experiment execution pack', () => {
  assert.match(researchProjectSource, /\/research\/ideas\/\$\{ideaId\}\/execution-pack/);
  assert.match(researchProjectSource, /实验推进包/);
  assert.match(researchProjectSource, /minimum_tasks/);
  assert.match(researchProjectSource, /success_metrics/);
  assert.match(researchProjectSource, /从 Proposal 到实验的执行路线/);
  assert.match(researchProjectSource, /executionData\.next_actions/);
});

test('research project page does not block core loading on related paper recommendations', () => {
  assert.match(researchProjectSource, /const loadRelatedPapers = async \(id: string\) =>/);
  assert.match(researchProjectSource, /loadRelatedPapers\(projectId\);/);
  assert.match(researchProjectSource, /setRelatedPapers\(\[\]\)/);
  assert.doesNotMatch(
    researchProjectSource,
    /Promise\.all\(\[[\s\S]*recommended-papers[\s\S]*\]\)\.catch/,
  );
  assert.match(researchProjectSource, /<Card title="相关论文" loading=\{papersLoading\}/);
});
