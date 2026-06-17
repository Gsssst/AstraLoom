import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

const paperDetailSource = readFileSync(
  new URL('../src/pages/PaperDetailPage.tsx', import.meta.url),
  'utf8',
);
const papersPageSource = readFileSync(
  new URL('../src/pages/PapersPage.tsx', import.meta.url),
  'utf8',
);

test('paper chat references preserve preview-ready visual evidence metadata', () => {
  assert.match(paperDetailSource, /evidence_type\?: string/);
  assert.match(paperDetailSource, /metadata\?: \{/);
  assert.match(paperDetailSource, /bbox\?: number\[\]/);
  assert.match(paperDetailSource, /asset_path\?: string/);
  assert.match(paperDetailSource, /thumbnail_path\?: string/);
  assert.match(paperDetailSource, /asset_token\?: string/);
  assert.match(paperDetailSource, /thumbnail_token\?: string/);
  assert.match(paperDetailSource, /visual_evidence\?: boolean/);
  assert.match(paperDetailSource, /summary\?: string/);
});

test('paper chat renders and routes visual evidence references distinctly', () => {
  assert.match(paperDetailSource, /metadata\?\.visual_evidence/);
  assert.match(paperDetailSource, /String\(ref\.evidence_type \|\| ''\)\.toLowerCase\(\)\.startsWith\('visual'\)/);
  assert.match(paperDetailSource, /visual: \{ label: '视觉\/OCR', color: 'purple' \}/);
  assert.match(paperDetailSource, /referenceTooltip\(ref\)/);
  assert.match(paperDetailSource, /setTargetPdfPage\(page\)/);
  assert.match(paperDetailSource, /message\.info\(`已跳转到 PDF 第 \$\{page\} 页`\)/);
});

test('paper chat renders preview cards only for non-table visual evidence assets', () => {
  assert.match(paperDetailSource, /visualPreviewReferences/);
  assert.match(paperDetailSource, /isTableLikeEvidenceReference/);
  assert.match(paperDetailSource, /paper-chat-visual-preview-list/);
  assert.match(paperDetailSource, /paper-chat-visual-preview/);
  assert.match(paperDetailSource, /ref\.metadata\?\.thumbnail_path \|\| ref\.metadata\?\.asset_path/);
  assert.match(paperDetailSource, /!isTableLikeEvidenceReference\(ref\)/);
  assert.match(paperDetailSource, /<img src=\{asset\}/);
  assert.match(paperDetailSource, /PDF 第 \$\{page\} 页/);
  assert.match(paperDetailSource, /handleEvidenceReferenceClick\(ref\)/);
});

test('paper chat keeps table evidence as chip-only references', () => {
  assert.match(paperDetailSource, /evidenceType === 'visual_table'/);
  assert.match(paperDetailSource, /evidenceType === 'table_pack'/);
  assert.match(paperDetailSource, /evidenceType === 'table_catalog'/);
  assert.match(paperDetailSource, /kind === 'table'/);
  assert.match(paperDetailSource, /category === 'visual' && asset && !isTableLikeEvidenceReference\(ref\)/);
});

test('paper chat collapses evidence references by default', () => {
  assert.match(paperDetailSource, /expandedReferencePanels/);
  assert.match(paperDetailSource, /referencePanelKey/);
  assert.match(paperDetailSource, /paper-chat-reference-summary/);
  assert.match(paperDetailSource, /paper-chat-reference-toggle/);
  assert.match(paperDetailSource, /查看引用/);
  assert.match(paperDetailSource, /收起引用/);
  assert.match(paperDetailSource, /referencesExpanded &&/);
  assert.match(paperDetailSource, /msg\.evidence &&/);
  assert.match(paperDetailSource, /visualRefs = visualPreviewReferences\(msg\.references\)/);
});

test('paper chat evidence drawer groups references by source type', () => {
  assert.match(paperDetailSource, /type PaperEvidenceCategory = 'paper_text' \| 'table' \| 'visual' \| 'web' \| 'related' \| 'other'/);
  assert.match(paperDetailSource, /paperEvidenceCategoryMeta/);
  assert.match(paperDetailSource, /evidenceCategoryForReference/);
  assert.match(paperDetailSource, /groupedEvidenceReferences/);
  assert.match(paperDetailSource, /paper_text: \{ label: '正文证据'/);
  assert.match(paperDetailSource, /table: \{ label: '表格证据'/);
  assert.match(paperDetailSource, /visual: \{ label: '视觉\/OCR'/);
  assert.match(paperDetailSource, /web: \{ label: '网页来源'/);
  assert.match(paperDetailSource, /related: \{ label: '相关论文'/);
  assert.match(paperDetailSource, /isVisualLikeEvidenceReference/);
});

test('paper chat evidence drawer renders grouped details with existing navigation', () => {
  assert.match(paperDetailSource, /evidenceDrawer/);
  assert.match(paperDetailSource, /openEvidenceDrawer\(msg, idx, referenceKey\)/);
  assert.match(paperDetailSource, /<Drawer[\s\S]*回答证据/);
  assert.match(paperDetailSource, /paper-evidence-drawer-section/);
  assert.match(paperDetailSource, /paper-evidence-drawer-item/);
  assert.match(paperDetailSource, /handleEvidenceReferenceClick\(ref\)/);
  assert.match(paperDetailSource, /category === 'visual' && asset && !isTableLikeEvidenceReference\(ref\)/);
  assert.match(paperDetailSource, /computeEvidenceConfidence\(drawerMessage\)/);
});

test('paper chat answer evidence markers navigate from inline citations', () => {
  assert.match(paperDetailSource, /evidenceLinksForMessage/);
  assert.match(paperDetailSource, /\^E\\d\+\$/i);
  assert.match(paperDetailSource, /handleEvidenceReferenceClick\(ref\)/);
  assert.match(paperDetailSource, /openEvidenceDrawer\(messageItem, index, referencePanelKey\(messageItem, index\)\)/);
  assert.match(paperDetailSource, /<Markdown content=\{msg\.content\} evidenceLinks=\{evidenceLinksForMessage\(msg, idx\)\}/);
  assert.match(paperDetailSource, /点击跳转到 PDF 第 \$\{page\} 页/);
});

test('paper chat evidence meta includes visual evidence counts from backend contract', () => {
  assert.match(paperDetailSource, /visual_evidence_count\?: number/);
  assert.match(paperDetailSource, /visual_evidence_available\?: boolean/);
});

test('paper detail chat can resize against content when PDF is hidden', () => {
  assert.match(paperDetailSource, /CONTENT_PANEL_DEFAULT_PERCENT/);
  assert.match(paperDetailSource, /contentPanelWidth/);
  assert.match(paperDetailSource, /handleContentChatResizePointerDown/);
  assert.match(paperDetailSource, /paper-detail-content-chat-resize-handle/);
  assert.match(paperDetailSource, /调整正文和 AI 问答宽度/);
  assert.match(paperDetailSource, /100 - contentPanelWidth/);
  assert.match(paperDetailSource, /showPdf\)\s*return/);
});

test('paper maintenance center exposes visual evidence jobs without table-repair wording', () => {
  assert.match(papersPageSource, /\/papers\/maintenance\/backfill-visual-evidence\?limit=5/);
  assert.match(papersPageSource, /兜底提取视觉证据/);
  assert.match(papersPageSource, /\/papers\/maintenance\/jobs\/\$\{jobId\}/);
  assert.match(papersPageSource, /activeMaintenanceJob/);
  assert.match(papersPageSource, /维护任务已进入后台/);
  assert.match(papersPageSource, /维护任务状态读取失败/);
  assert.doesNotMatch(papersPageSource, /表格修复/);
  assert.doesNotMatch(papersPageSource, /解析 5 篇 PDF/);
  assert.doesNotMatch(papersPageSource, /backfill-structured-pdf\?limit=5/);
});

test('single paper visual evidence action is queued and pollable', () => {
  assert.match(papersPageSource, /action\.key === 'visual_evidence'/);
  assert.match(papersPageSource, /response\.data\?\.job_id && response\.data\?\.job/);
  assert.match(papersPageSource, /setActiveMaintenanceJob\(response\.data\.job\)/);
  assert.match(papersPageSource, /已进入后台：/);
  assert.match(papersPageSource, /formatMaintenanceJobCompletion/);
  assert.match(papersPageSource, /job\.message && total === 0/);
  assert.match(papersPageSource, /视觉证据正在后台提取/);
  assert.match(papersPageSource, /待提取视觉证据/);
});

test('paper maintenance job helpers are initialized before polling effect', () => {
  const helperIndex = papersPageSource.indexOf('const formatMaintenanceJobCompletion = useCallback');
  const pollingIndex = papersPageSource.indexOf("const jobId = activeMaintenanceJob?.id");

  assert.ok(helperIndex > 0);
  assert.ok(pollingIndex > 0);
  assert.ok(helperIndex < pollingIndex);
});

test('non-admin maintenance view hides privileged repair actions', () => {
  assert.match(papersPageSource, /const maintenanceView = !isAdmin \?/);
  assert.match(papersPageSource, /知识库维护需要管理员权限/);
  assert.match(papersPageSource, /修复动作只对管理员开放/);
  assert.match(papersPageSource, /actions=\{isAdmin && item\.status === 'failed' \?/);
});
