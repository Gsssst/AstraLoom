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

test('research project page models proposal writing brief data', () => {
  assert.match(researchProjectSource, /interface ProposalWritingBrief/);
  assert.match(researchProjectSource, /claim_evidence_map/);
  assert.match(researchProjectSource, /unsafe_claims/);
  assert.match(researchProjectSource, /section_outline/);
  assert.match(researchProjectSource, /evidence_gaps/);
  assert.match(researchProjectSource, /writingBriefMap/);
});

test('research project page loads writing brief endpoint before draft creation', () => {
  assert.match(researchProjectSource, /loadWritingBrief/);
  assert.match(researchProjectSource, /\/research\/ideas\/\$\{ideaId\}\/writing-brief/);
  assert.match(researchProjectSource, /加载写作准备包失败/);
  assert.match(researchProjectSource, /response\.data as ProposalWritingBrief/);
});

test('proposal detail renders writing preparation panel', () => {
  assert.match(researchProjectSource, /renderWritingBriefPanel/);
  assert.match(researchProjectSource, /写作准备包/);
  assert.match(researchProjectSource, /标题候选/);
  assert.match(researchProjectSource, /章节骨架/);
  assert.match(researchProjectSource, /贡献链/);
  assert.match(researchProjectSource, /Claim-Evidence Map/);
  assert.match(researchProjectSource, /暂不应直接写成结论/);
  assert.match(researchProjectSource, /证据缺口/);
});

test('create writing draft preserves returned brief and evidence messaging', () => {
  assert.match(researchProjectSource, /response\.data\.writing_brief/);
  assert.match(researchProjectSource, /写作准备包已随项目保存/);
  assert.match(researchProjectSource, /证据不足，请先补强引用/);
  assert.match(researchProjectSource, /loadWritingBrief\(idea\.id, true\)/);
});

test('writing brief css keeps claim and outline text inside cards', () => {
  assert.match(globalCssSource, /\.proposal-writing-brief/);
  assert.match(globalCssSource, /\.proposal-writing-brief-section/);
  assert.match(globalCssSource, /overflow-wrap: anywhere/);
  assert.match(globalCssSource, /min-width: 0/);
});
