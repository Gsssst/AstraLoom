import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

const layoutSource = readFileSync(
  new URL('../src/components/AppLayout.tsx', import.meta.url),
  'utf8',
);
const homeStyles = readFileSync(
  new URL('../src/styles/home.css', import.meta.url),
  'utf8',
);

test('shared application shell retains responsive layout class hooks', () => {
  for (const className of [
    'app-layout-main',
    'app-layout-header',
    'app-layout-content',
    'app-header-account',
    'app-header-user-name',
  ]) {
    assert.match(layoutSource, new RegExp(`className="${className}"`));
  }
});

test('collapsed sidebar logo spans the sidebar width before centering its icon', () => {
  assert.match(
    layoutSource,
    /data-testid="sidebar-logo-link" style=\{\{ width: '100%', cursor: 'pointer' \}\}/,
  );
  assert.match(layoutSource, /width: '100%', boxSizing: 'border-box'/);
});

test('chat session active state does not add a second full-height left border', () => {
  assert.doesNotMatch(
    homeStyles,
    /\.chat-session-item\.is-active\s*\{[^}]*border-left:/,
  );
});
