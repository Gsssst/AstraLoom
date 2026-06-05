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

test('workspace detail keeps existing operations reachable', () => {
  assert.match(detailSource, /绑定空间资源/);
  assert.match(detailSource, /手动输入 ID/);
  assert.match(detailSource, /添加空间成员/);
  assert.match(detailSource, /最近活动/);
  assert.match(detailSource, /handleBindCandidate/);
  assert.match(detailSource, /handleUnlinkResource/);
});
