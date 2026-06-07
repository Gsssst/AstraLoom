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

test('research project page models gap selection and generation constraints', () => {
  assert.match(researchProjectSource, /interface GapSelection/);
  assert.match(researchProjectSource, /selected_gap_titles\?: string\[\]/);
  assert.match(researchProjectSource, /blocked_gap_titles\?: string\[\]/);
  assert.match(researchProjectSource, /interface GenerationConstraints/);
  assert.match(researchProjectSource, /researchModeOptions/);
  assert.match(researchProjectSource, /riskAppetiteOptions/);
  assert.match(researchProjectSource, /resourceBudgetOptions/);
  assert.match(researchProjectSource, /\['gap_review', '选择 Gap'\]/);
});

test('research project page calls gap preview and continuation endpoints', () => {
  assert.match(researchProjectSource, /handleGapPreview/);
  assert.match(researchProjectSource, /\/research\/projects\/\$\{projectId\}\/idea-runs\/gap-preview/);
  assert.match(researchProjectSource, /handleContinueFromGaps/);
  assert.match(researchProjectSource, /\/research\/projects\/\$\{projectId\}\/idea-runs\/\$\{run\.id\}\/continue-from-gaps/);
  assert.match(researchProjectSource, /gap_selection: \{/);
  assert.match(researchProjectSource, /generation_constraints: \{/);
});

test('gap map tab renders user selection controls and status feedback', () => {
  assert.match(researchProjectSource, /gap-selection-panel/);
  assert.match(researchProjectSource, /预览 Gap Map/);
  assert.match(researchProjectSource, /按选择继续生成 Proposal/);
  assert.match(researchProjectSource, /重新提取 Gap Map/);
  assert.match(researchProjectSource, /研究模式/);
  assert.match(researchProjectSource, /风险偏好/);
  assert.match(researchProjectSource, /资源预算/);
  assert.match(researchProjectSource, /推进/);
  assert.match(researchProjectSource, /暂不考虑/);
  assert.match(researchProjectSource, /已选择 \{selectedGapTitles\.length\} 个，屏蔽 \{blockedGapTitles\.length\} 个/);
});

test('gap map tab supports feedback editing and single-gap refinement', () => {
  assert.match(researchProjectSource, /interface GapUserFeedback/);
  assert.match(researchProjectSource, /interface GapFeedbackDraft/);
  assert.match(researchProjectSource, /gapRatingOptions/);
  assert.match(researchProjectSource, /gapLabelOptions/);
  assert.match(researchProjectSource, /handleSaveGapFeedback/);
  assert.match(researchProjectSource, /\/research\/projects\/\$\{projectId\}\/idea-runs\/\$\{run\.id\}\/gaps\/\$\{index\}\/feedback/);
  assert.match(researchProjectSource, /handleRefineGap/);
  assert.match(researchProjectSource, /\/research\/projects\/\$\{projectId\}\/idea-runs\/\$\{run\.id\}\/gaps\/\$\{index\}\/refine/);
  assert.match(researchProjectSource, /保存 Gap 反馈/);
  assert.match(researchProjectSource, /细化这个 Gap/);
  assert.match(researchProjectSource, /编辑与反馈/);
});

test('gap map tab renders linked evidence context', () => {
  assert.match(researchProjectSource, /evidenceById/);
  assert.match(researchProjectSource, /evidenceOptions/);
  assert.match(researchProjectSource, /关联证据/);
  assert.match(researchProjectSource, /证据解释/);
  assert.match(researchProjectSource, /gap-evidence-item/);
});

test('proposal detail renders applied gap selection metadata', () => {
  assert.match(researchProjectSource, /appliedGapSelection/);
  assert.match(researchProjectSource, /gap-selection-signal/);
  assert.match(researchProjectSource, /Gap 约束/);
  assert.match(researchProjectSource, /selected_gap_titles/);
  assert.match(researchProjectSource, /关注点：\{appliedGapSelection\.focus_note\}/);
});

test('gap selection css keeps long gap titles readable', () => {
  assert.match(globalCssSource, /\.gap-selection-panel/);
  assert.match(globalCssSource, /\.gap-selection-signal/);
  assert.match(globalCssSource, /\.gap-review-card/);
  assert.match(globalCssSource, /\.gap-feedback-collapse/);
  assert.match(globalCssSource, /\.gap-evidence-item/);
  assert.match(globalCssSource, /border-radius: 8px/);
  assert.match(globalCssSource, /background: #fbfaff/);
  assert.match(globalCssSource, /overflow-wrap: anywhere/);
});
