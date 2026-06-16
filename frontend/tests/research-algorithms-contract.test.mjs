import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

const algorithmSource = readFileSync(
  new URL('../src/services/researchAlgorithms.ts', import.meta.url),
  'utf8',
);

const loadAlgorithms = async () => {
  const ts = await import('typescript');
  const source = ts.transpileModule(algorithmSource, {
    compilerOptions: {
      module: ts.ModuleKind.ES2022,
      target: ts.ScriptTarget.ES2022,
      verbatimModuleSyntax: true,
    },
  }).outputText;
  const encoded = Buffer.from(source, 'utf8').toString('base64');
  return import(`data:text/javascript;base64,${encoded}`);
};

test('citation keys use stable author, year, title, and identifier tokens', async () => {
  const { buildResearchCitationKey } = await loadAlgorithms();
  assert.equal(
    buildResearchCitationKey({
      title: 'Attention Is All You Need',
      authors: ['Ashish Vaswani'],
      year: 2017,
      arxiv_id: '1706.03762v7',
    }),
    'Vaswani2017attention3762',
  );
});

test('metadata quality uses weighted readiness tiers', async () => {
  const { computeMetadataQuality } = await loadAlgorithms();
  const weak = computeMetadataQuality({ title: 'Thin metadata' });
  const ready = computeMetadataQuality({
    title: 'Retrieval Augmented Generation',
    authors: ['Jane Doe'],
    year: 2025,
    abstract: 'A complete abstract.',
    doi: '10.1000/example',
    has_full_text: true,
    has_embedding: true,
    tags: ['rag'],
    citation_count: 12,
  });
  assert.equal(weak.tier, 'weak');
  assert.equal(ready.tier, 'ready');
  assert.ok(ready.percent > weak.percent);
  assert.ok(ready.checks.find((check) => check.key === 'identifier').weight > 1);
});

test('duplicate risk prioritizes DOI and arXiv before normalized titles', async () => {
  const { computeDuplicateRiskMap, duplicateRiskForPaper } = await loadAlgorithms();
  const papers = [
    { title: 'Same Title', doi: 'https://doi.org/10.1145/123' },
    { title: 'Different Title', doi: '10.1145/123' },
    { title: 'Normalized: Title!' },
    { title: 'normalized title' },
  ];
  const map = computeDuplicateRiskMap(papers);
  assert.equal(duplicateRiskForPaper(papers[0], map).risk, 'strong');
  assert.equal(duplicateRiskForPaper(papers[2], map).risk, 'possible');
});

test('evidence confidence penalizes insufficient evidence and rewards grounded references', async () => {
  const { computeEvidenceConfidence } = await loadAlgorithms();
  const grounded = computeEvidenceConfidence({
    references: [
      { type: 'paper_evidence', source: 'current_paper', score: 0.9 },
      { type: 'paper_evidence', source: 'current_paper', score: 0.85 },
      { source: 'web', score: 0.7 },
    ],
    evidence: { evidence_count: 3, evidence_coverage: 0.9, evidence_insufficient: false },
  });
  const insufficient = computeEvidenceConfidence({
    references: [{ source: 'web', score: 0.7 }],
    evidence: { evidence_count: 1, evidence_coverage: 0.2, evidence_insufficient: true },
  });
  assert.equal(grounded.status, 'strong');
  assert.equal(insufficient.status, 'weak');
  assert.ok(grounded.weightedScore > insufficient.weightedScore);
});

test('evidence confidence treats matched numbered sections as targeted support', async () => {
  const { computeEvidenceConfidence } = await loadAlgorithms();
  const sectionMatched = computeEvidenceConfidence({
    references: [{ type: 'paper_evidence', source: 'current_paper', score: 1 }],
    evidence: {
      evidence_count: 1,
      evidence_coverage: 1,
      evidence_insufficient: false,
      section_evidence_match: true,
      target_section_number: '3.2',
      matched_section_heading: '3.2 ALVTS Framework',
    },
  });
  const sectionMissing = computeEvidenceConfidence({
    references: [{ type: 'paper_evidence', source: 'current_paper', score: 0.7 }],
    evidence: {
      evidence_count: 1,
      evidence_coverage: 0.3333,
      evidence_insufficient: false,
      section_evidence_match: false,
      target_section_number: '3.2',
    },
  });

  assert.equal(sectionMatched.status, 'section');
  assert.equal(sectionMatched.coverage, 1);
  assert.equal(sectionMatched.targetSectionNumber, '3.2');
  assert.equal(sectionMatched.matchedSectionHeading, '3.2 ALVTS Framework');
  assert.equal(sectionMissing.status, 'partial');
  assert.ok(sectionMatched.weightedScore > sectionMissing.weightedScore);
});

test('graph edge strength uses relation metadata, scores, and counts', async () => {
  const { scoreGraphEdgeStrength } = await loadAlgorithms();
  assert.equal(scoreGraphEdgeStrength({ relation: 'evidence', score: 0.9 }), 'strong');
  assert.equal(scoreGraphEdgeStrength({ relation: 'supports', score: 0.5 }), 'medium');
  assert.equal(scoreGraphEdgeStrength({ relation: 'unknown', count: 0 }), 'weak');
  assert.equal(scoreGraphEdgeStrength({ relation: 'supports gap', count: 2 }), 'strong');
});
