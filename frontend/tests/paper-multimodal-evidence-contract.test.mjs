import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

const paperDetailSource = readFileSync(
  new URL('../src/pages/PaperDetailPage.tsx', import.meta.url),
  'utf8',
);

test('paper chat references preserve text and structured evidence metadata only', () => {
  assert.match(paperDetailSource, /evidence_type\?: string/);
  assert.match(paperDetailSource, /metadata\?: \{/);
  assert.match(paperDetailSource, /bbox\?: number\[\]/);
  assert.doesNotMatch(paperDetailSource, /asset_id\?: string/);
  assert.doesNotMatch(paperDetailSource, /thumbnail_path\?: string/);
  assert.doesNotMatch(paperDetailSource, /crop_strategy\?: string/);
  assert.doesNotMatch(paperDetailSource, /has_visual_summary\?: boolean/);
  assert.doesNotMatch(paperDetailSource, /visual_evidence\?: boolean/);
});

test('paper chat no longer renders visual evidence references distinctly', () => {
  assert.doesNotMatch(paperDetailSource, /ref\.evidence_type\?\.startsWith\('visual'\)/);
  assert.doesNotMatch(paperDetailSource, /图像视觉证据/);
  assert.doesNotMatch(paperDetailSource, /表格视觉证据/);
  assert.doesNotMatch(paperDetailSource, /return 'purple'/);
  assert.match(paperDetailSource, /referenceTooltip\(ref\)/);
});

test('paper chat no longer renders preview cards for visual evidence assets', () => {
  assert.doesNotMatch(paperDetailSource, /paper-chat-visual-reference-card/);
  assert.doesNotMatch(paperDetailSource, /visualReferenceImageUrl\(ref\)/);
  assert.doesNotMatch(paperDetailSource, /\/api\/papers\/\$\{paper\.id\}\/visual-assets\/\$\{encodeURIComponent\(ref\.metadata\.asset_id\)\}\/image/);
  assert.doesNotMatch(paperDetailSource, /visualReferenceKindLabel\(ref\)/);
  assert.match(paperDetailSource, /handleEvidenceReferenceClick\(ref\)/);
});

test('paper chat evidence meta no longer includes visual evidence counts', () => {
  assert.doesNotMatch(paperDetailSource, /visual_evidence_count\?: number/);
  assert.doesNotMatch(paperDetailSource, /visual_evidence_available\?: boolean/);
  assert.doesNotMatch(paperDetailSource, /其中 \$\{msg\.evidence\.visual_evidence_count\} 条视觉证据/);
});
