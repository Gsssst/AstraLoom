import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

const researchProjectSource = readFileSync(
  new URL('../src/pages/ResearchProjectPage.tsx', import.meta.url),
  'utf8',
);

test('research project page loads proposal progress board endpoint', () => {
  assert.match(researchProjectSource, /interface ProposalBoardItem/);
  assert.match(researchProjectSource, /interface ProposalBoard/);
  assert.match(researchProjectSource, /proposalBoardLoading/);
  assert.match(researchProjectSource, /loadProposalBoard/);
  assert.match(researchProjectSource, /\/research\/projects\/\$\{id\}\/proposal-board/);
  assert.match(researchProjectSource, /加载 Proposal 推进看板失败/);
});

test('research project page renders progress board tab and grouped cards', () => {
  assert.match(researchProjectSource, /proposalBoardTab/);
  assert.match(researchProjectSource, /key: 'proposal-board'/);
  assert.match(researchProjectSource, /推进看板/);
  assert.match(researchProjectSource, /proposalBoard\.groups\.filter/);
  assert.match(researchProjectSource, /proposalBoardStatusColors/);
  assert.match(researchProjectSource, /优先级 \{item\.priority\}/);
  assert.match(researchProjectSource, /item\.blockers\.length/);
});

test('progress board cards constrain long dynamic text inside card boundaries', () => {
  assert.match(researchProjectSource, /overflowWrap: 'anywhere'/);
  assert.match(researchProjectSource, /minWidth: 0/);
  assert.match(researchProjectSource, /maxWidth: '100%'/);
  assert.match(researchProjectSource, /background: '#fff7e6'/);
  assert.doesNotMatch(researchProjectSource, /item\.blockers\.slice\(0, 3\)\.map\(blocker => <Tag/);
});

test('proposal board recommended actions reuse existing workflows', () => {
  assert.match(researchProjectSource, /handleBoardAction/);
  assert.match(researchProjectSource, /setActiveWorkbenchTab\('evidence'\)/);
  assert.match(researchProjectSource, /loadExecutionPack\(idea\.id\)/);
  assert.match(researchProjectSource, /openExperiment\(idea\)/);
  assert.match(researchProjectSource, /createWritingDraft\(idea\)/);
  assert.match(researchProjectSource, /openCopilot\(idea\)/);
  assert.match(researchProjectSource, /updateDecision\(idea\.id, 'draft'\)/);
  assert.match(researchProjectSource, /openTimeline\(idea\)/);
});
