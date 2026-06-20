import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

const researchProjectSource = readFileSync(
  new URL('../src/pages/ResearchProjectPage.tsx', import.meta.url),
  'utf8',
);
const globalCssSource = readFileSync(
  new URL('../src/index.css', import.meta.url),
  'utf8',
);

test('proposal detail derives deterministic next-step actions from existing state', () => {
  assert.match(researchProjectSource, /type ProposalNextActionKind/);
  assert.match(researchProjectSource, /interface ProposalNextAction/);
  assert.match(researchProjectSource, /buildProposalNextActions/);
  assert.match(researchProjectSource, /proposalEvidenceCount\(idea\)/);
  assert.match(researchProjectSource, /validationMap\[idea\.id\]/);
  assert.match(researchProjectSource, /executionPackMap\[idea\.id\]/);
  assert.match(researchProjectSource, /writingBriefMap\[idea\.id\]/);
  assert.match(researchProjectSource, /experiments\.filter\(experiment => experiment\.idea_id === idea\.id\)/);
});

test('proposal next-step actions reuse existing proposal workflows', () => {
  assert.match(researchProjectSource, /renderProposalNextActions/);
  assert.match(researchProjectSource, /className="proposal-next-actions"/);
  assert.match(researchProjectSource, /补证据/);
  assert.match(researchProjectSource, /验证闭环/);
  assert.match(researchProjectSource, /实验推进包/);
  assert.match(researchProjectSource, /生成项目包/);
  assert.match(researchProjectSource, /写作准备/);
  assert.match(researchProjectSource, /和 AI 讨论/);
  assert.match(researchProjectSource, /openExperiment\(idea\)/);
  assert.match(researchProjectSource, /handleGenCode\(idea\.id\)/);
  assert.match(researchProjectSource, /loadWritingBrief\(idea\.id, true\)/);
  assert.match(researchProjectSource, /openCopilot\(idea\)/);
  assert.match(researchProjectSource, /openTimeline\(idea\)/);
});

test('proposal detail renders compact idea brief before secondary details', () => {
  assert.match(researchProjectSource, /interface ProposalOutline/);
  assert.match(researchProjectSource, /interface IdeaBriefMetadata/);
  assert.match(researchProjectSource, /interface ProposalDeepeningMetadata/);
  assert.match(researchProjectSource, /interface ProposalSelectionSelfCheck/);
  assert.match(researchProjectSource, /proposal_outline/);
  assert.match(researchProjectSource, /selection_self_check/);
  assert.match(researchProjectSource, /proposalBriefFromOutline/);
  assert.match(researchProjectSource, /proposalBriefForIdea/);
  assert.match(researchProjectSource, /renderIdeaBrief/);
  assert.match(researchProjectSource, /research_question/);
  assert.match(researchProjectSource, /key_insight/);
  assert.match(researchProjectSource, /failure_condition/);
  assert.match(researchProjectSource, /深入打磨/);
  assert.match(researchProjectSource, /自动自检/);
  assert.match(researchProjectSource, /入库前自检/);
  assert.match(researchProjectSource, /quality_gates/);
  assert.match(researchProjectSource, /\/research\/ideas\/\$\{idea\.id\}\/deepen/);
  assert.match(researchProjectSource, /proposal-secondary-collapse/);
  assert.match(researchProjectSource, /评审、证据与质量信号/);
  assert.match(researchProjectSource, /执行、写作与证据详情/);
});

test('proposal next-step actions are compact and responsive', () => {
  assert.match(globalCssSource, /\.proposal-idea-brief/);
  assert.match(globalCssSource, /\.proposal-brief-section/);
  assert.match(globalCssSource, /\.proposal-secondary-collapse/);
  assert.match(globalCssSource, /\.proposal-next-actions/);
  assert.match(globalCssSource, /\.proposal-next-action-grid/);
  assert.match(globalCssSource, /grid-template-columns: repeat\(3, minmax\(0, 1fr\)\)/);
  assert.match(globalCssSource, /\.proposal-next-action\.is-primary/);
  assert.match(globalCssSource, /overflow-wrap: anywhere/);
});
