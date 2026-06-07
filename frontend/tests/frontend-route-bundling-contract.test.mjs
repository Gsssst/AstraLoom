import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

const appSource = readFileSync(
  new URL('../src/App.tsx', import.meta.url),
  'utf8',
);
const viteConfigSource = readFileSync(
  new URL('../vite.config.ts', import.meta.url),
  'utf8',
);

const pageModules = [
  'HomePage',
  'ChatPage',
  'PapersPage',
  'ResearchPage',
  'ResearchProjectPage',
  'WritingPage',
  'SettingsPage',
  'LoginPage',
  'RegisterPage',
  'PaperDetailPage',
  'PaperDigestInboxPage',
  'WorkspacesPage',
  'WorkspaceDetailPage',
  'AdminPage',
  'ActionCenterPage',
];

test('app uses lazy route imports instead of static page imports', () => {
  assert.match(appSource, /import React, \{ Suspense, lazy, useEffect \} from 'react'/);
  assert.match(appSource, /const lazyRoute = \(element: React\.ReactNode\)/);
  assert.match(appSource, /<Suspense fallback=\{routeFallback\}>/);
  assert.match(appSource, /<WorkflowLoadingState/);

  for (const moduleName of pageModules) {
    assert.match(appSource, new RegExp(`const ${moduleName} = lazy\\(\\(\\) => import\\('\\./pages/${moduleName}'\\)\\)`));
    assert.doesNotMatch(appSource, new RegExp(`import ${moduleName} from '\\./pages/${moduleName}'`));
    assert.match(appSource, new RegExp(`element=\\{lazyRoute\\(<${moduleName} />\\)\\}`));
  }
});

test('existing route paths remain registered after lazy split', () => {
  for (const routePath of [
    '/',
    '/login',
    '/register',
    '/chat',
    '/actions',
    '/papers',
    '/papers/digests',
    '/papers/:paperId',
    '/research',
    '/research/:projectId',
    '/writing',
    '/workspaces',
    '/workspaces/:spaceId',
    '/admin',
    '/settings',
  ]) {
    assert.match(appSource, new RegExp(`path="${routePath.replace(/\//g, '\\/')}"`));
  }
  assert.match(appSource, /<Route element=\{<AppLayout \/>\}>/);
});

test('vite config defines stable manual vendor chunks', () => {
  assert.match(viteConfigSource, /const vendorChunk = \(id: string\)/);
  assert.match(viteConfigSource, /manualChunks: vendorChunk/);
  for (const chunkName of [
    'vendor-react',
    'vendor-antd',
    'vendor-markdown',
    'vendor-pdf',
    'vendor-state',
    'vendor-misc',
  ]) {
    assert.match(viteConfigSource, new RegExp(`return '${chunkName}'`));
  }
});
