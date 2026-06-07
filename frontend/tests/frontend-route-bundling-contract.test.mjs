import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

const appSource = readFileSync(
  new URL('../src/App.tsx', import.meta.url),
  'utf8',
);
const lazyRoutesSource = readFileSync(
  new URL('../src/routes/lazyRoutes.tsx', import.meta.url),
  'utf8',
);
const appLayoutSource = readFileSync(
  new URL('../src/components/AppLayout.tsx', import.meta.url),
  'utf8',
);
const workflowGuideSource = readFileSync(
  new URL('../src/components/WorkflowStepGuide.tsx', import.meta.url),
  'utf8',
);
const homeSource = readFileSync(
  new URL('../src/pages/HomePage.tsx', import.meta.url),
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
  assert.match(appSource, /import React, \{ Suspense, useEffect \} from 'react'/);
  assert.match(appSource, /import \{ lazyPages \} from '\.\/routes\/lazyRoutes'/);
  assert.doesNotMatch(appSource, /import React, \{ Suspense, lazy,/);
  assert.doesNotMatch(appSource, /lazy\(\(\) => import\('\.\/pages\//);
  assert.match(appSource, /const lazyRoute = \(element: React\.ReactNode\)/);
  assert.match(appSource, /<Suspense fallback=\{routeFallback\}>/);
  assert.match(appSource, /<WorkflowLoadingState/);

  for (const moduleName of pageModules) {
    assert.match(appSource, new RegExp(`\\b${moduleName},`));
    assert.doesNotMatch(appSource, new RegExp(`import ${moduleName} from '\\./pages/${moduleName}'`));
    assert.match(appSource, new RegExp(`element=\\{lazyRoute\\(<${moduleName} />\\)\\}`));
  }
});

test('lazy route registry owns page loaders and lazy page components', () => {
  assert.match(lazyRoutesSource, /import \{ lazy, type ComponentType \} from 'react'/);
  assert.match(lazyRoutesSource, /export const routeLoaders = \{/);
  assert.match(lazyRoutesSource, /export const lazyPages = \{/);

  for (const moduleName of pageModules) {
    assert.match(lazyRoutesSource, new RegExp(`${moduleName}: \\(\\) => import\\('\\.\\.\\/pages\\/${moduleName}'\\)`));
    assert.match(lazyRoutesSource, new RegExp(`${moduleName}: lazy\\(routeLoaders\\.${moduleName}\\)`));
  }
});

test('lazy route prefetch only warms route chunks and deduplicates route targets', () => {
  assert.match(lazyRoutesSource, /export const prefetchRouteChunk = \(path\?: string \| null\)/);
  assert.match(lazyRoutesSource, /export const prefetchRouteIntent = \(path\?: string \| null\)/);
  assert.match(lazyRoutesSource, /const prefetchedRoutes = new Map<string, Promise<PageModule>>\(\)/);
  assert.match(lazyRoutesSource, /new URL\(path, window\.location\.origin\)\.pathname/);
  assert.match(lazyRoutesSource, /path\.split\(\/\[\?#\]\/\)\[0\] \|\| '\/'/);
  assert.match(lazyRoutesSource, /prefetchedRoutes\.has\(entry\.key\)/);
  assert.match(lazyRoutesSource, /prefetchedRoutes\.set\(entry\.key, entry\.loader\(\)\.catch/);
  assert.match(lazyRoutesSource, /prefetchRouteChunk\(path\)\?\.catch\(\(\) => \{\}\)/);

  for (const routePattern of [
    'match: /^\\/$/',
    'match: /^\\/login\\/?$/',
    'match: /^\\/register\\/?$/',
    'match: /^\\/chat(?:\\/.*)?$/',
    'match: /^\\/actions(?:\\/.*)?$/',
    'match: /^\\/papers\\/digests\\/?$/',
    'match: /^\\/papers\\/[^/]+\\/?$/',
    'match: /^\\/papers(?:\\/.*)?$/',
    'match: /^\\/research\\/[^/]+\\/?$/',
    'match: /^\\/research(?:\\/.*)?$/',
    'match: /^\\/writing(?:\\/.*)?$/',
    'match: /^\\/workspaces\\/[^/]+\\/?$/',
    'match: /^\\/workspaces(?:\\/.*)?$/',
    'match: /^\\/admin(?:\\/.*)?$/',
    'match: /^\\/settings(?:\\/.*)?$/',
  ]) {
    assert.ok(lazyRoutesSource.includes(routePattern), `missing ${routePattern}`);
  }

  assert.doesNotMatch(lazyRoutesSource, /\bfetch\s*\(/);
  assert.doesNotMatch(lazyRoutesSource, /\bapi\./);
  assert.doesNotMatch(lazyRoutesSource, /\baxios\b/);
});

test('high intent navigation surfaces trigger route chunk prefetch', () => {
  for (const source of [appLayoutSource, workflowGuideSource, homeSource]) {
    assert.match(source, /import \{ prefetchRouteIntent \} from '\.\.\/routes\/lazyRoutes'/);
  }

  for (const source of [appLayoutSource, homeSource]) {
    assert.match(source, /onMouseEnter: \(\) => prefetchRouteIntent\(/);
    assert.match(source, /onFocus: \(\) => prefetchRouteIntent\(/);
    assert.match(source, /onTouchStart: \(\) => prefetchRouteIntent\(/);
  }

  assert.match(appLayoutSource, /\{\.\.\.routeIntentProps\('\/'\)\}/);
  assert.match(appLayoutSource, /onMouseEnter: \(\) => prefetchRouteIntent\(m\.key\)/);
  assert.match(appLayoutSource, /\{\.\.\.routeIntentProps\(m\.key\)\}/);
  assert.match(appLayoutSource, /\{\.\.\.routeIntentProps\('\/settings'\)\}/);
  assert.match(appLayoutSource, /\{\.\.\.routeIntentProps\('\/papers\/digests'\)\}/);
  assert.match(appLayoutSource, /\{\.\.\.routeIntentProps\('\/login'\)\}/);

  assert.match(workflowGuideSource, /onMouseEnter=\{\(\) => prefetchRouteIntent\(step\.path\)\}/);
  assert.match(workflowGuideSource, /onFocus=\{\(\) => prefetchRouteIntent\(step\.path\)\}/);
  assert.match(workflowGuideSource, /onTouchStart=\{\(\) => prefetchRouteIntent\(step\.path\)\}/);

  assert.match(homeSource, /\{\.\.\.routeIntentProps\(action\.path\)\}/);
  assert.match(homeSource, /\{\.\.\.routeIntentProps\(quickActions\[i\]\.path\)\}/);
  assert.match(homeSource, /\{\.\.\.routeIntentProps\(a\.path\)\}/);
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
