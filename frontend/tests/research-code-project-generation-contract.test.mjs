import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

const researchProjectSource = readFileSync(
  new URL('../src/pages/ResearchProjectPage.tsx', import.meta.url),
  'utf8',
);

test('research project page models generated code project packages', () => {
  assert.match(researchProjectSource, /interface CodeProjectFile/);
  assert.match(researchProjectSource, /interface CodeProjectManifest/);
  assert.match(researchProjectSource, /generated_code_project\?: CodeProjectManifest/);
  assert.match(researchProjectSource, /codeProjectSelectedFile/);
});

test('research project page stores package generation response', () => {
  assert.match(researchProjectSource, /response\.data\.code_project as CodeProjectManifest/);
  assert.match(researchProjectSource, /generated_code_project: projectPackage/);
  assert.match(researchProjectSource, /实验项目包已生成/);
  assert.match(researchProjectSource, /README\.md/);
});

test('research project page renders package browser and download action', () => {
  assert.match(researchProjectSource, /renderCodeProject/);
  assert.match(researchProjectSource, /实验项目包/);
  assert.match(researchProjectSource, /下载 ZIP/);
  assert.match(researchProjectSource, /\/research\/ideas\/\$\{idea\.id\}\/code-project\/download/);
  assert.match(researchProjectSource, /responseType: 'blob'/);
  assert.match(researchProjectSource, /projectPackage\.files\.map/);
  assert.match(researchProjectSource, /projectPackage\.run_commands\.map/);
  assert.match(researchProjectSource, /projectPackage\.safety_notes\.map/);
});

test('research project page supports legacy single-code fallback', () => {
  assert.match(researchProjectSource, /旧版实验代码/);
  assert.match(researchProjectSource, /重新生成结构化实验项目包/);
  assert.match(researchProjectSource, /重新生成实验项目包/);
});
