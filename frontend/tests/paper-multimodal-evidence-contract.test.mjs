import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

const paperDetailSource = readFileSync(
  new URL('../src/pages/PaperDetailPage.tsx', import.meta.url),
  'utf8',
);

test('paper chat references preserve visual evidence metadata', () => {
  assert.match(paperDetailSource, /evidence_type\?: string/);
  assert.match(paperDetailSource, /metadata\?: \{/);
  assert.match(paperDetailSource, /asset_id\?: string/);
  assert.match(paperDetailSource, /thumbnail_path\?: string/);
  assert.match(paperDetailSource, /crop_strategy\?: string/);
  assert.match(paperDetailSource, /bbox\?: number\[\]/);
  assert.match(paperDetailSource, /has_visual_summary\?: boolean/);
  assert.match(paperDetailSource, /visual_evidence\?: boolean/);
});

test('paper chat renders visual evidence references distinctly', () => {
  assert.match(paperDetailSource, /ref\.evidence_type\?\.startsWith\('visual'\)/);
  assert.match(paperDetailSource, /图像视觉证据/);
  assert.match(paperDetailSource, /表格视觉证据/);
  assert.match(paperDetailSource, /return 'purple'/);
  assert.match(paperDetailSource, /referenceTooltip\(ref\)/);
});

test('paper chat renders preview cards for visual evidence assets', () => {
  assert.match(paperDetailSource, /paper-chat-visual-reference-card/);
  assert.match(paperDetailSource, /visualReferenceImageUrl\(ref\)/);
  assert.match(paperDetailSource, /\/api\/papers\/\$\{paper\.id\}\/visual-assets\/\$\{encodeURIComponent\(ref\.metadata\.asset_id\)\}\/image/);
  assert.match(paperDetailSource, /visualReferenceKindLabel\(ref\)/);
  assert.match(paperDetailSource, /handleEvidenceReferenceClick\(ref\)/);
});

test('paper chat evidence meta includes visual evidence counts', () => {
  assert.match(paperDetailSource, /visual_evidence_count\?: number/);
  assert.match(paperDetailSource, /visual_evidence_available\?: boolean/);
  assert.match(paperDetailSource, /其中 \$\{msg\.evidence\.visual_evidence_count\} 条视觉证据/);
});
