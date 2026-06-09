import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { join } from 'node:path';

const root = new URL('..', import.meta.url).pathname;
const read = (path) => readFileSync(join(root, path), 'utf8');

test('toolbox route is registered in lazy routes app and navigation', () => {
  const lazyRoutes = read('src/routes/lazyRoutes.tsx');
  const app = read('src/App.tsx');
  const layout = read('src/components/AppLayout.tsx');
  const palette = read('src/components/GlobalCommandPalette.tsx');

  assert.match(lazyRoutes, /ToolboxPage/);
  assert.match(lazyRoutes, /\/toolbox/);
  assert.match(app, /path="\/toolbox"/);
  assert.match(layout, /nav\.toolbox/);
  assert.match(palette, /route-toolbox/);
});

test('toolbox page exposes filters and create edit workflow', () => {
  const page = read('src/pages/ToolboxPage.tsx');

  assert.match(page, /\/toolbox\/tools/);
  assert.match(page, /添加工具/);
  assert.match(page, /工具名称/);
  assert.match(page, /适用场景/);
  assert.match(page, /局限性/);
  assert.match(page, /来源论文/);
  assert.match(page, /kindOptions/);
  assert.match(page, /maturityOptions/);
});

test('paper detail can link papers to toolbox entries', () => {
  const detail = read('src/pages/PaperDetailPage.tsx');

  assert.match(detail, /\/toolbox\/papers\/\$\{paperId\}\/tools/);
  assert.match(detail, /\/toolbox\/tools\/\$\{selectedToolId\}\/papers/);
  assert.match(detail, /工具箱关联/);
  assert.match(detail, /选择已有工具/);
  assert.match(detail, /证据说明/);
});

test('research idea generation can include toolbox context', () => {
  const page = read('src/pages/ResearchProjectPage.tsx');

  assert.match(page, /\/toolbox\/tools/);
  assert.match(page, /工具箱引导/);
  assert.match(page, /selectedToolIds/);
  assert.match(page, /tool_ids/);
  assert.match(page, /tool_mode/);
  assert.match(page, /toolModeOptions/);
});
