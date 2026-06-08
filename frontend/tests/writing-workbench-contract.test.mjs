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
const authenticatedPdfPreviewSource = readFileSync(
  new URL('../src/components/writing/AuthenticatedPdfPreview.tsx', import.meta.url),
  'utf8',
);

test('writing assistant exposes paper and grant workbench modes', () => {
  assert.match(writingPageSource, /写论文助手/);
  assert.match(writingPageSource, /写本子助手/);
  assert.match(writingPageSource, /论文章节工作台/);
});

test('writing page defaults to manuscript-first paper workflow', () => {
  assert.match(writingPageSource, /useState(?:<[^>]+>)?\('paper'\)/);
  assert.match(writingPageSource, /useState<[^>]+>\('manuscript'\)/);
  assert.doesNotMatch(writingPageSource, /key: 'grant', label:/);
});

test('paper workflow separates manuscript, survey, and auxiliary tools', () => {
  assert.match(writingPageSource, /paperWorkflow/);
  assert.match(writingPageSource, /manuscriptWorkbench/);
  assert.match(writingPageSource, /surveyWorkflowPanel/);
  assert.match(writingPageSource, /auxiliaryToolsPanel/);
  assert.match(writingPageSource, /正文写作按章节推进/);
  assert.match(writingPageSource, /综述、Related Work 对比表、研究空白和参考文献作为独立 workflow/);
});

test('manuscript workbench is active-section focused', () => {
  assert.match(writingPageSource, /activeSectionId/);
  assert.match(writingPageSource, /activeSection = selectedProject/);
  assert.match(writingPageSource, /章节导航/);
  assert.match(writingPageSource, /当前章节 LaTeX 源码/);
  assert.doesNotMatch(writingPageSource, /projectSections\.map\(s => \(\s*<SectionEditor/s);
});

test('manuscript workbench exposes create-section entry in navigation and empty state', () => {
  assert.match(writingPageSource, /handleCreateSection/);
  assert.match(writingPageSource, /projects\/\$\{selectedProject\.id\}\/sections/);
  assert.match(writingPageSource, /新增章节/);
  assert.match(writingPageSource, /创建第一个章节/);
  assert.match(writingPageSource, /setActiveSectionId\(section\.id\)/);
});

test('manuscript workbench groups project and evidence in compact support rail', () => {
  assert.match(writingPageSource, /manuscript-workbench-grid/);
  assert.match(writingPageSource, /manuscript-support-rail/);
  assert.match(writingPageSource, /manuscript-editor-main/);
  assert.match(writingPageSource, /supportRailCollapsed/);
  assert.match(writingPageSource, /gridTemplateColumns: supportRailCollapsed \? '64px minmax\(0, 1fr\)' : '320px minmax\(0, 1fr\)'/);
  assert.match(writingPageSource, /<WritingProjectPanel[\s\S]*\{evidencePanel\}/);
  assert.match(writingPageSource, /gridTemplateColumns: '240px minmax\(0, 1fr\)'/);
});

test('manuscript workbench support rail can collapse to widen editor', () => {
  assert.match(writingPageSource, /data-support-rail-state=\{supportRailCollapsed \? 'collapsed' : 'expanded'\}/);
  assert.match(writingPageSource, /manuscript-support-rail-collapsed/);
  assert.match(writingPageSource, /MenuFoldOutlined/);
  assert.match(writingPageSource, /MenuUnfoldOutlined/);
  assert.match(writingPageSource, /收起项目与证据栏/);
  assert.match(writingPageSource, /展开项目与证据栏/);
  assert.match(writingPageSource, /maxWidth=\{assistantMode === 'paper' && paperWorkflow === 'manuscript' \? 1600 : 1100\}/);
});

test('manuscript workbench exposes latex preview diagnostics', () => {
  assert.match(writingPageSource, /preview-section/);
  assert.match(writingPageSource, /preview-manuscript/);
  assert.match(writingPageSource, /latexPreviewChecks/);
  assert.match(writingPageSource, /manuscriptPreview/);
  assert.match(writingPageSource, /compiler_available === false/);
  assert.match(sectionEditorSource, /LaTeX 源码/);
  assert.match(sectionEditorSource, /LaTeX 预览检查/);
  assert.match(sectionEditorSource, /源码级检查/);
  assert.match(sectionEditorSource, /未安装 pdflatex/);
  assert.match(sectionEditorSource, /查看编译日志/);
  assert.match(sectionEditorSource, /pdf_preview_url/);
  assert.match(sectionEditorSource, /pdf_scope === 'manuscript'/);
  assert.match(sectionEditorSource, /整篇 PDF 预览/);
  assert.match(sectionEditorSource, /AuthenticatedPdfPreview/);
  assert.match(authenticatedPdfPreviewSource, /responseType: 'blob'/);
  assert.match(authenticatedPdfPreviewSource, /URL\.createObjectURL/);
  assert.match(authenticatedPdfPreviewSource, /URL\.revokeObjectURL/);
  assert.match(authenticatedPdfPreviewSource, /<iframe/);
  assert.match(writingPageSource, /pdf_preview_url/);
  assert.match(writingPageSource, /pdf_scope === 'manuscript'/);
});

test('section editor exposes latex command suggestions', () => {
  assert.match(sectionEditorSource, /LATEX_SNIPPETS/);
  assert.match(sectionEditorSource, /\\\\cite\{\}/);
  assert.match(sectionEditorSource, /LaTeX 命令补全/);
  assert.match(sectionEditorSource, /applyLatexSuggestion/);
  assert.match(sectionEditorSource, /ArrowDown/);
  assert.match(sectionEditorSource, /Enter/);
  assert.match(sectionEditorSource, /Tab/);
});

test('writing workbench exposes latex compile layout controls', () => {
  assert.match(writingPageSource, /latexCompileLayout/);
  assert.match(writingPageSource, /compile-settings/);
  assert.match(writingPageSource, /当前编译版式/);
  assert.match(writingPageSource, /单栏/);
  assert.match(writingPageSource, /双栏/);
  assert.match(writingPageSource, /模板/);
});

test('section editor keeps local drafts and debounces persistence', () => {
  assert.match(sectionEditorSource, /draftContent/);
  assert.match(sectionEditorSource, /saveTimerRef/);
  assert.match(sectionEditorSource, /setTimeout\(\(\) => \{/);
  assert.match(sectionEditorSource, /}, 800\)/);
  assert.match(sectionEditorSource, /flushDraft/);
  assert.match(sectionEditorSource, /onBlur=\{\(\) => flushDraft\(\)\}/);
  assert.match(sectionEditorSource, /onPreviewLatex\(flushDraft\(\)\)/);
  assert.match(sectionEditorSource, /onSectionAiAction\(flushDraft\(\), action\.key\)/);
  assert.match(writingPageSource, /\[selectedProject\?\.id, projectRefreshSignal\]/);
  assert.doesNotMatch(writingPageSource, /\[selectedProject\?\.id, projectSections\]/);
});

test('section editor exposes section-scoped AI assistant actions', () => {
  assert.match(sectionEditorSource, /当前章节 AI 助手/);
  assert.match(sectionEditorSource, /起草本节/);
  assert.match(sectionEditorSource, /改进论证/);
  assert.match(sectionEditorSource, /补证据引用/);
  assert.match(sectionEditorSource, /Claim 安全/);
  assert.match(sectionEditorSource, /润色源码/);
  assert.match(sectionEditorSource, /修复 LaTeX/);
  assert.match(writingPageSource, /section_action/);
  assert.match(writingPageSource, /section_source/);
  assert.match(writingPageSource, /phases: \['writer'\]/);
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
  assert.match(writingPageSource, /写作推进栏/);
  assert.match(writingPageSource, /建议下一步/);
  assert.match(writingPageSource, /章节进度/);
  assert.match(writingPageSource, /证据覆盖/);
  assert.match(writingPageSource, /引用风险/);
  assert.match(writingPageSource, /投稿模板/);
  assert.match(writingPageSource, /去处理/);
});

test('paper workbench exposes action-first stage strip and blockers', () => {
  assert.match(writingPageSource, /workbenchStageSteps/);
  assert.match(writingPageSource, /stageStepState/);
  assert.match(writingPageSource, /workbenchTargetLabels/);
  assert.match(writingPageSource, /workbenchPriorityLabels/);
  assert.match(writingPageSource, /buildWorkbenchBlockers/);
  assert.match(writingPageSource, /阶段路径/);
  assert.match(writingPageSource, /阻塞项/);
  assert.match(writingPageSource, /空章节/);
  assert.match(writingPageSource, /偏短章节/);
  assert.match(writingPageSource, /缺少证据卡/);
  assert.match(writingPageSource, /未匹配引用/);
  assert.match(writingPageSource, /未绑定官方模板/);
  assert.match(writingPageSource, /快速跳转/);
});

test('paper workbench surfaces preserved proposal writing brief', () => {
  assert.match(writingPageSource, /type ProposalWritingBrief/);
  assert.match(writingPageSource, /getProjectWritingBrief/);
  assert.match(writingPageSource, /metadata_json\?\.writing_brief/);
  assert.match(writingPageSource, /renderWritingBriefWorkbenchPanel/);
  assert.match(writingPageSource, /Proposal 写作准备包/);
  assert.match(writingPageSource, /标题候选/);
  assert.match(writingPageSource, /章节骨架/);
  assert.match(writingPageSource, /贡献链/);
  assert.match(writingPageSource, /Claim-Evidence Map/);
  assert.match(writingPageSource, /暂不应直接写成结论/);
  assert.match(writingPageSource, /证据缺口/);
  assert.match(writingPageSource, /实验写作计划/);
});

test('paper workbench folds writing brief risks into guidance', () => {
  assert.match(writingPageSource, /hasWritingBriefRisk/);
  assert.match(writingPageSource, /getBriefClaimStatusCounts/);
  assert.match(writingPageSource, /buildWorkbenchBlockers\(workbenchSummary, selectedWritingBrief\)/);
  assert.match(writingPageSource, /unsupported-brief-claims/);
  assert.match(writingPageSource, /unsafe-brief-claims/);
  assert.match(writingPageSource, /brief-evidence-gaps/);
  assert.match(writingPageSource, /处理 Proposal 写作风险/);
  assert.match(writingPageSource, /scrollToWorkbenchTarget\('brief'\)/);
  assert.match(writingPageSource, /handleResolveBriefClaim/);
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

test('section citation diagnostics expose claim safety checks', () => {
  assert.match(sectionEditorSource, /Claim 安全检查/);
  assert.match(sectionEditorSource, /claim_safety_summary/);
  assert.match(sectionEditorSource, /claim_diagnostics/);
  assert.match(sectionEditorSource, /缺引用/);
  assert.match(sectionEditorSource, /弱支撑/);
  assert.match(sectionEditorSource, /外部未校验/);
  assert.match(sectionEditorSource, /未发现高风险 claim/);
  assert.match(sectionEditorSource, /safetyAlertType/);
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
