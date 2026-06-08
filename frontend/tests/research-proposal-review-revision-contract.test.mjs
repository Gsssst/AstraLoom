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

test('research project page models proposal review packages and version comparisons', () => {
  assert.match(researchProjectSource, /interface ProposalReviewPackage/);
  assert.match(researchProjectSource, /proposal_review\?: ProposalReviewPackage/);
  assert.match(researchProjectSource, /interface ProposalVersionComparison/);
  assert.match(researchProjectSource, /proposal_review_readiness\?: string/);
  assert.match(researchProjectSource, /review_objection_count\?: number/);
  assert.match(researchProjectSource, /has_child_versions\?: boolean/);
});

test('proposal review package panel exposes review fields and refresh action', () => {
  assert.match(researchProjectSource, /renderProposalReviewPanel/);
  assert.match(researchProjectSource, /结构化审稿包/);
  assert.match(researchProjectSource, /审稿异议/);
  assert.match(researchProjectSource, /必要实验/);
  assert.match(researchProjectSource, /修订计划/);
  assert.match(researchProjectSource, /下一版修订焦点/);
  assert.match(researchProjectSource, /refreshProposalReviewPackage/);
  assert.match(researchProjectSource, /\/research\/ideas\/\$\{idea\.id\}\/review-package/);
});

test('review-guided revision uses dedicated endpoint and modal focus input', () => {
  assert.match(researchProjectSource, /openReviewRevision/);
  assert.match(researchProjectSource, /reviseFromReview/);
  assert.match(researchProjectSource, /reviewRevisionIdea/);
  assert.match(researchProjectSource, /reviewRevisionFocus/);
  assert.match(researchProjectSource, /按审稿意见修订 Proposal/);
  assert.match(researchProjectSource, /生成修订版/);
  assert.match(researchProjectSource, /\/research\/ideas\/\$\{reviewRevisionIdea\.id\}\/revise-from-review/);
  assert.match(researchProjectSource, /setIdeas\(previous => \[child, \.\.\.previous\.filter/);
});

test('proposal version comparison drawer renders parent child changes', () => {
  assert.match(researchProjectSource, /openVersionComparison/);
  assert.match(researchProjectSource, /renderVersionComparisonDrawer/);
  assert.match(researchProjectSource, /\/research\/ideas\/\$\{idea\.id\}\/version-comparison/);
  assert.match(researchProjectSource, /Proposal 版本对比/);
  assert.match(researchProjectSource, /父版本/);
  assert.match(researchProjectSource, /当前版本/);
  assert.match(researchProjectSource, /字段级变化/);
  assert.match(researchProjectSource, /审稿修订来源/);
});

test('proposal board actions route review revision and version compare workflows', () => {
  assert.match(researchProjectSource, /actionType === 'review_revision'/);
  assert.match(researchProjectSource, /openReviewRevision\(idea\)/);
  assert.match(researchProjectSource, /actionType === 'version_compare'/);
  assert.match(researchProjectSource, /latestChild \|\| idea/);
  assert.match(researchProjectSource, /openVersionComparison\(latestChild \|\| idea\)/);
  assert.match(researchProjectSource, /审稿 \{proposalReviewReadinessLabels/);
  assert.match(researchProjectSource, /异议 \{item\.signals\.review_objection_count\}/);
  assert.match(researchProjectSource, /已有修订版/);
});

test('proposal review revision css keeps dense review content responsive', () => {
  assert.match(globalCssSource, /\.proposal-review-package/);
  assert.match(globalCssSource, /\.proposal-review-section/);
  assert.match(globalCssSource, /\.proposal-version-change/);
  assert.match(globalCssSource, /\.proposal-version-side/);
  assert.match(globalCssSource, /overflow-wrap: anywhere/);
  assert.match(globalCssSource, /min-width: 0/);
});
