import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

const appSource = readFileSync(
  new URL('../src/App.tsx', import.meta.url),
  'utf8',
);
const layoutSource = readFileSync(
  new URL('../src/components/AppLayout.tsx', import.meta.url),
  'utf8',
);
const paletteSource = readFileSync(
  new URL('../src/components/GlobalCommandPalette.tsx', import.meta.url),
  'utf8',
);
const responsiveStyles = readFileSync(
  new URL('../src/styles/responsive.css', import.meta.url),
  'utf8',
);
const packageSource = readFileSync(
  new URL('../package.json', import.meta.url),
  'utf8',
);

test('app opens global command palette from keyboard and custom header event', () => {
  assert.match(appSource, /import GlobalCommandPalette from '\.\/components\/GlobalCommandPalette'/);
  assert.match(appSource, /const \[commandPaletteOpen, setCommandPaletteOpen\] = React\.useState\(false\)/);
  assert.match(appSource, /e\.preventDefault\(\); setCommandPaletteOpen\(true\);/);
  assert.match(appSource, /window\.addEventListener\('command-palette:open', openCommandPalette\)/);
  assert.match(appSource, /window\.removeEventListener\('command-palette:open', openCommandPalette\)/);
  assert.match(appSource, /<GlobalCommandPalette open=\{commandPaletteOpen\} onOpenChange=\{setCommandPaletteOpen\} \/>/);
  assert.doesNotMatch(appSource, /window\.location\.href = '\/papers'/);
});

test('header exposes visible command palette trigger and updated shortcut copy', () => {
  assert.match(layoutSource, /SearchOutlined/);
  assert.match(layoutSource, /className="command-palette-trigger"/);
  assert.match(layoutSource, /window\.dispatchEvent\(new Event\('command-palette:open'\)\)/);
  assert.match(layoutSource, /搜索 \/ 命令/);
  assert.match(layoutSource, /⌘K/);
  assert.match(layoutSource, /\['Ctrl\+K', '打开命令面板'\]/);
});

test('palette defines grouped static workflow commands and resource adapters', () => {
  for (const routePath of [
    '/',
    '/chat',
    '/actions',
    '/workspaces',
    '/papers',
    '/papers/digests',
    '/research',
    '/writing',
    '/settings',
  ]) {
    assert.match(paletteSource, new RegExp(`path: '${routePath.replace(/\//g, '\\/')}'`));
  }

  for (const group of ['导航', '行动', '论文', '研究方向', '项目空间', '反馈 Issue', '写作项目']) {
    assert.match(paletteSource, new RegExp(`group: '${group}'|${group}`));
  }

  assert.match(paletteSource, /export const searchResources = async/);
  assert.match(paletteSource, /Promise\.allSettled/);
  assert.match(paletteSource, /api\.get\('\/papers\/search'/);
  assert.match(paletteSource, /api\.get\('\/research\/projects'\)/);
  assert.match(paletteSource, /api\.get\('\/workspaces'\)/);
  assert.match(paletteSource, /api\.get\('\/writing\/projects'\)/);
  assert.match(paletteSource, /source: 'local'/);
  assert.match(paletteSource, /page_size: 5/);
  assert.match(paletteSource, /部分资源搜索暂不可用/);
});

test('palette searches workspace issue summaries and opens issue deep links', () => {
  assert.match(paletteSource, /BugOutlined/);
  assert.match(paletteSource, /type CommandKind = 'route' \| 'action' \| 'paper' \| 'research' \| 'workspace' \| 'issue' \| 'writing'/);
  assert.match(paletteSource, /space\.issue_summary/);
  assert.match(paletteSource, /id: `workspace-issue-\$\{space\.id\}-\$\{issue\.id\}`/);
  assert.match(paletteSource, /group: '反馈 Issue'/);
  assert.match(paletteSource, /path: issue\.path \|\| `\/workspaces\/\$\{space\.id\}\?issue=\$\{issue\.id\}`/);
  assert.match(paletteSource, /kind: 'issue'/);
  assert.match(paletteSource, /搜索页面、论文、研究方向、项目空间、Issue 或写作项目/);
});

test('palette supports keyboard-first selection and route prefetch', () => {
  assert.match(paletteSource, /inputRef\.current\?\.focus\?\.\(\)/);
  assert.match(paletteSource, /event\.key === 'ArrowDown'/);
  assert.match(paletteSource, /event\.key === 'ArrowUp'/);
  assert.match(paletteSource, /event\.key === 'Enter'/);
  assert.match(paletteSource, /activate\(commands\[activeIndex\]\)/);
  assert.match(paletteSource, /navigate\(item\.path\)/);
  assert.match(paletteSource, /prefetchRouteIntent\(item\.path\)/);
  assert.match(paletteSource, /onCancel=\{closePalette\}/);
});

test('palette styling is responsive and adds no command palette dependency', () => {
  for (const className of [
    'global-command-palette',
    'command-palette-trigger',
    'command-palette-shell',
    'command-palette-input',
    'command-palette-results',
    'command-palette-item',
    'command-palette-resource-state',
  ]) {
    assert.match(paletteSource + responsiveStyles, new RegExp(className));
  }
  assert.match(responsiveStyles, /@media \(max-width: 767px\)[\s\S]*\.global-command-palette/);

  const packageJson = JSON.parse(packageSource);
  assert.equal(packageJson.dependencies?.cmdk, undefined);
  assert.equal(packageJson.dependencies?.kbar, undefined);
  assert.equal(packageJson.dependencies?.['react-cmdk'], undefined);
});
