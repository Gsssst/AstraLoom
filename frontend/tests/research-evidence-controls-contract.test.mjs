import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

const researchProjectSource = readFileSync(
  new URL('../src/pages/ResearchProjectPage.tsx', import.meta.url),
  'utf8',
);

test('research workbench keeps evidence control state and payload wiring', () => {
  assert.match(researchProjectSource, /interface EvidenceControls/);
  assert.match(researchProjectSource, /const \[evidenceMaxItems, setEvidenceMaxItems\] = useState\(12\)/);
  assert.match(researchProjectSource, /const \[pinnedEvidenceIds, setPinnedEvidenceIds\] = useState<string\[\]>\(\[\]\)/);
  assert.match(researchProjectSource, /const \[excludedEvidenceIds, setExcludedEvidenceIds\] = useState<string\[\]>\(\[\]\)/);
  assert.match(researchProjectSource, /evidenceControlsPayload/);
  assert.match(researchProjectSource, /evidence_controls: evidenceControlsPayload\(\)/);
  assert.match(researchProjectSource, /run\?\.config_json\?\.evidence_controls/);
});

test('evidence map tab exposes count, pin, exclude, and clear controls', () => {
  assert.match(researchProjectSource, /生成证据控制/);
  assert.match(researchProjectSource, /evidenceCountOptions/);
  assert.match(researchProjectSource, /togglePinnedEvidence/);
  assert.match(researchProjectSource, /toggleExcludedEvidence/);
  assert.match(researchProjectSource, /清空固定/);
  assert.match(researchProjectSource, /清空排除/);
  assert.match(researchProjectSource, /已固定/);
  assert.match(researchProjectSource, /将排除/);
  assert.match(researchProjectSource, /control_summary/);
});
