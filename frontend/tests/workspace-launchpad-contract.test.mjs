import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

const listSource = readFileSync(
  new URL('../src/pages/WorkspacesPage.tsx', import.meta.url),
  'utf8',
);
const detailSource = readFileSync(
  new URL('../src/pages/WorkspaceDetailPage.tsx', import.meta.url),
  'utf8',
);

test('workspace list cards expose launchpad summaries', () => {
  assert.match(listSource, /launchpadResourceMeta/);
  assert.match(listSource, /space\.dashboard\?\.stage_label/);
  assert.match(listSource, /space\.dashboard\?\.progress_score/);
  assert.match(listSource, /space\.summary\?\.counts\?\.\[item\.key\]/);
  assert.match(listSource, /打开后可绑定论文、方向和写作项目/);
});

test('workspace detail exposes role-aware quick-start launchpad', () => {
  assert.match(detailSource, /项目空间启动台/);
  assert.match(detailSource, /canEditResources \? '绑定核心论文' : '查看核心论文'/);
  assert.match(detailSource, /openResourceBinder\('papers'\)/);
  assert.match(detailSource, /创建或绑定方向/);
  assert.match(detailSource, /推进写作项目/);
  assert.match(detailSource, /workspace-resource-binder/);
});

test('workspace detail exposes research cockpit loop', () => {
  assert.match(detailSource, /科研驾驶舱/);
  assert.match(detailSource, /空间级闭环/);
  assert.match(detailSource, /证据语料/);
  assert.match(detailSource, /Idea 推进/);
  assert.match(detailSource, /写作落地/);
  assert.match(detailSource, /开放问题/);
  assert.match(detailSource, /诊断证据缺口/);
  assert.match(detailSource, /规划下一步 Idea/);
  assert.match(detailSource, /检查写作落地风险/);
});

test('workspace detail keeps existing operations reachable', () => {
  assert.match(detailSource, /绑定空间资源/);
  assert.match(detailSource, /手动输入 ID/);
  assert.match(detailSource, /添加空间成员/);
  assert.match(detailSource, /最近活动/);
  assert.match(detailSource, /handleBindCandidate/);
  assert.match(detailSource, /handleUnlinkResource/);
});
