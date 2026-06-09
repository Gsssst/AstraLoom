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
const writingPageSource = readFileSync(
  new URL('../src/pages/WritingPage.tsx', import.meta.url),
  'utf8',
);
const researchProjectSource = readFileSync(
  new URL('../src/pages/ResearchProjectPage.tsx', import.meta.url),
  'utf8',
);
const graphSource = readFileSync(
  new URL('../src/components/ResearchKnowledgeGraph.tsx', import.meta.url),
  'utf8',
);
const responsiveCssSource = readFileSync(
  new URL('../src/styles/responsive.css', import.meta.url),
  'utf8',
);
const algorithmSource = readFileSync(
  new URL('../src/services/researchAlgorithms.ts', import.meta.url),
  'utf8',
);

test('paper detail exposes PaperQA-style evidence confidence and citation readiness', () => {
  assert.match(paperDetailSource, /computeEvidenceConfidence/);
  assert.match(paperDetailSource, /computeMetadataQuality/);
  assert.match(paperDetailSource, /buildResearchCitationKey/);
  assert.match(paperDetailSource, /paper-answer-evidence-panel/);
  assert.match(paperDetailSource, /PaperQA 风格证据检查/);
  assert.match(paperDetailSource, /paper-citation-network-panel/);
  assert.match(paperDetailSource, /引用网络准备度/);
  assert.match(paperDetailSource, /参考文献抽取/);
});

test('paper library exposes JabRef-style citation keys and metadata quality', () => {
  assert.match(papersPageSource, /buildResearchCitationKey/);
  assert.match(papersPageSource, /computeMetadataQuality/);
  assert.match(papersPageSource, /computeDuplicateRiskMap/);
  assert.match(papersPageSource, /duplicateRiskForPaper/);
  assert.match(papersPageSource, /JabRef 质量/);
  assert.match(papersPageSource, /疑似重复/);
  assert.match(papersPageSource, /key:\{citationKey\}/);
});

test('writing workbench exposes an Overleaf-style project structure', () => {
  assert.match(writingPageSource, /buildWritingFileTree/);
  assert.match(writingPageSource, /overleaf-project-structure-panel/);
  assert.match(writingPageSource, /main\.tex/);
  assert.match(writingPageSource, /references\.bib/);
  assert.match(writingPageSource, /compile\.log/);
});

test('research page exposes a STORM-style process and graph', () => {
  assert.match(researchProjectSource, /stormFlowSteps/);
  assert.match(researchProjectSource, /STORM 研究流程/);
  assert.match(researchProjectSource, /storm-research-flow-panel/);
  assert.match(researchProjectSource, /researchGraphNodes/);
  assert.match(researchProjectSource, /researchGraphEdges/);
  assert.match(researchProjectSource, /scoreGraphEdgeStrength/);
});

test('shared research knowledge graph is reusable and styled', () => {
  assert.match(graphSource, /interface ResearchGraphNode/);
  assert.match(graphSource, /interface ResearchGraphEdge/);
  assert.match(graphSource, /research-knowledge-graph/);
  assert.match(graphSource, /research-graph-node-grid/);
  assert.match(responsiveCssSource, /\.research-knowledge-graph/);
  assert.match(responsiveCssSource, /\.research-graph-edge/);
  assert.match(responsiveCssSource, /\.writing-file-tree-row/);
  assert.match(responsiveCssSource, /\.storm-flow-step/);
});

test('research workbench algorithms are centralized', () => {
  assert.match(algorithmSource, /buildResearchCitationKey/);
  assert.match(algorithmSource, /computeMetadataQuality/);
  assert.match(algorithmSource, /computeDuplicateRiskMap/);
  assert.match(algorithmSource, /computeEvidenceConfidence/);
  assert.match(algorithmSource, /scoreGraphEdgeStrength/);
  assert.match(writingPageSource, /scoreGraphEdgeStrength/);
});
