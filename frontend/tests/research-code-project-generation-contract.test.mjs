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

test('research project page models generated code project packages', () => {
  assert.match(researchProjectSource, /interface CodeProjectFile/);
  assert.match(researchProjectSource, /interface CodeProjectManifest/);
  assert.match(researchProjectSource, /interface CodeProjectFolderGroup/);
  assert.match(researchProjectSource, /interface CodeProjectVersionSummary/);
  assert.match(researchProjectSource, /interface CodeProjectVersionCompare/);
  assert.match(researchProjectSource, /generated_code_project\?: CodeProjectManifest/);
  assert.match(researchProjectSource, /codeProjectSelectedFile/);
  assert.match(researchProjectSource, /codeProjectHistoryMap/);
});

test('research project page stores package generation response', () => {
  assert.match(researchProjectSource, /response\.data\.code_project as CodeProjectManifest/);
  assert.match(researchProjectSource, /generated_code_project: projectPackage/);
  assert.match(researchProjectSource, /实验项目包已生成/);
  assert.match(researchProjectSource, /readme\.md/);
  assert.match(researchProjectSource, /codeProjectDefaultFilePath/);
});

test('research project page renders package browser and download action', () => {
  assert.match(researchProjectSource, /renderCodeProject/);
  assert.match(researchProjectSource, /实验项目包/);
  assert.match(researchProjectSource, /下载 ZIP/);
  assert.match(researchProjectSource, /\/research\/ideas\/\$\{idea\.id\}\/code-project\/download/);
  assert.match(researchProjectSource, /responseType: 'blob'/);
  assert.match(researchProjectSource, /codeProjectFolderGroups/);
  assert.match(researchProjectSource, /code-project-file-tree/);
  assert.match(researchProjectSource, /code-project-preview-panel/);
});

test('research project page surfaces commands, entrypoints, file metadata, and copy actions', () => {
  assert.match(researchProjectSource, /visibleProjectPackage\.run_commands/);
  assert.match(researchProjectSource, /visibleProjectPackage\.entrypoints/);
  assert.match(researchProjectSource, /codeProjectLineCount/);
  assert.match(researchProjectSource, /copyCodeProjectText/);
  assert.match(researchProjectSource, /文件内容已复制/);
  assert.match(researchProjectSource, /运行命令已复制/);
  assert.match(researchProjectSource, /安装命令已复制/);
});

test('research project page supports legacy single-code fallback', () => {
  assert.match(researchProjectSource, /旧版实验代码/);
  assert.match(researchProjectSource, /重新生成结构化实验项目包/);
  assert.match(researchProjectSource, /重新生成实验项目包/);
  assert.match(researchProjectSource, /旧版实验代码已复制/);
});

test('research project page supports code project version history and comparison', () => {
  assert.match(researchProjectSource, /loadCodeProjectVersions/);
  assert.match(researchProjectSource, /selectCodeProjectVersion/);
  assert.match(researchProjectSource, /compareCodeProjectVersions/);
  assert.match(researchProjectSource, /\/research\/ideas\/\$\{ideaId\}\/code-project\/versions/);
  assert.match(researchProjectSource, /\/research\/ideas\/\$\{idea\.id\}\/code-project\/versions\/\$\{version\}/);
  assert.match(researchProjectSource, /\/research\/ideas\/\$\{ideaId\}\/code-project\/versions\/compare/);
  assert.match(researchProjectSource, /项目版本历史/);
  assert.match(researchProjectSource, /比较版本/);
  assert.match(researchProjectSource, /版本差异/);
  assert.match(researchProjectSource, /版本历史会从下一次生成实验项目包开始保存/);
});

test('research project browser css keeps file tree and preview responsive', () => {
  assert.match(globalCssSource, /\.code-project-browser/);
  assert.match(globalCssSource, /grid-template-columns: minmax\(220px, 0\.36fr\) minmax\(0, 1fr\)/);
  assert.match(globalCssSource, /\.code-project-file-row\.is-selected/);
  assert.match(globalCssSource, /\.code-project-version-panel/);
  assert.match(globalCssSource, /\.code-project-diff-panel/);
  assert.match(globalCssSource, /\.code-project-diff-row\.is-selected/);
  assert.match(globalCssSource, /\.code-project-preview pre/);
  assert.match(globalCssSource, /overflow-wrap: anywhere/);
  assert.match(globalCssSource, /@media \(max-width: 760px\)/);
});
