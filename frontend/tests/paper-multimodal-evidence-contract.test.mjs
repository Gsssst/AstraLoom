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
  assert.match(paperDetailSource, /String\(ref\.evidence_type \|\| ''\)\.startsWith\('visual'\)/);
  assert.match(paperDetailSource, /return 'purple'/);
  assert.match(paperDetailSource, /referenceTooltip\(ref\)/);
  assert.match(paperDetailSource, /setTargetPdfPage\(page\)/);
  assert.match(paperDetailSource, /message\.info\(`已跳转到 PDF 第 \$\{page\} 页`\)/);
});

test('paper chat renders preview cards for visual evidence assets', () => {
  assert.match(paperDetailSource, /visualPreviewReferences/);
  assert.match(paperDetailSource, /paper-chat-visual-preview-list/);
  assert.match(paperDetailSource, /paper-chat-visual-preview/);
  assert.match(paperDetailSource, /ref\.metadata\?\.thumbnail_path \|\| ref\.metadata\?\.asset_path/);
  assert.match(paperDetailSource, /<img src=\{asset\}/);
  assert.match(paperDetailSource, /PDF \$\{page\}/);
  assert.match(paperDetailSource, /handleEvidenceReferenceClick\(ref\)/);
});

test('paper chat evidence meta includes visual evidence counts from backend contract', () => {
  assert.match(paperDetailSource, /visual_evidence_count\?: number/);
  assert.match(paperDetailSource, /visual_evidence_available\?: boolean/);
});

test('paper maintenance center exposes visual evidence jobs without table-repair wording', () => {
  assert.match(papersPageSource, /\/papers\/maintenance\/backfill-visual-evidence\?limit=5/);
  assert.match(papersPageSource, /\/papers\/maintenance\/jobs\/\$\{jobId\}/);
  assert.match(papersPageSource, /activeMaintenanceJob/);
  assert.match(papersPageSource, /维护任务已进入后台/);
  assert.match(papersPageSource, /维护任务状态读取失败/);
  assert.doesNotMatch(papersPageSource, /表格修复/);
});

test('non-admin maintenance view hides privileged repair actions', () => {
  assert.match(papersPageSource, /const maintenanceView = !isAdmin \?/);
  assert.match(papersPageSource, /知识库维护需要管理员权限/);
  assert.match(papersPageSource, /修复动作只对管理员开放/);
  assert.match(papersPageSource, /actions=\{isAdmin \?/);
});
