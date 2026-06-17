import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

const markdownSource = readFileSync(
  new URL('../src/components/Markdown.tsx', import.meta.url),
  'utf8',
);
const packageSource = readFileSync(
  new URL('../package.json', import.meta.url),
  'utf8',
);
const indexCssSource = readFileSync(
  new URL('../src/index.css', import.meta.url),
  'utf8',
);

test('shared markdown renderer parses math before katex rendering', () => {
  assert.match(packageSource, /"remark-math":/);
  assert.match(markdownSource, /import remarkMath from 'remark-math'/);
  assert.match(markdownSource, /remarkPlugins=\{\[remarkGfm, remarkMath\]\}/);
  assert.match(markdownSource, /rehypePlugins=\{\[rehypeKatex\]\}/);
});

test('shared markdown renderer normalizes common model latex delimiters', () => {
  assert.match(markdownSource, /export const normalizeMarkdownMath = \(value: string\)/);
  assert.match(markdownSource, /replace\(\/\\\\\\\[\\s\*\(\[\\s\\S\]\*\?\)\\s\*\\\\\\\]\/g/);
  assert.match(markdownSource, /replace\(\/\\\\\\\(\(\[\\s\\S\]\*\?\)\\\\\\\)\/g/);
  assert.match(markdownSource, /line\.match\(\/\^\(\\s\*\)\\\[\\s\*\(\.\+\?\)\\s\*\\\]\(\\s\*\)\$\/\)/);
  assert.match(markdownSource, /looksLikeLatexMath\(expression\)/);
});

test('shared markdown renderer preserves non-math contexts', () => {
  assert.match(markdownSource, /FENCED_CODE_BLOCK_RE/);
  assert.match(markdownSource, /segment\.startsWith\('```'\) \|\| segment\.startsWith\('~~~'\)/);
  assert.match(markdownSource, /\^E\\d\+\(\?:\[,;\\s\]\+E\\d\+\)\*\$/);
});

test('shared markdown renderer keeps long display equations scrollable', () => {
  assert.match(markdownSource, /className="markdown-body app-markdown"/);
  assert.match(indexCssSource, /\.app-markdown \.katex-display \{[\s\S]*max-width: 100%;/);
  assert.match(indexCssSource, /\.app-markdown \.katex-display \{[\s\S]*overflow-x: auto;/);
  assert.match(indexCssSource, /\.app-markdown \.katex-display > \.katex \{[\s\S]*width: max-content;/);
  assert.match(indexCssSource, /\.app-markdown \.katex-display > \.katex \{[\s\S]*min-width: max-content;/);
  assert.match(indexCssSource, /\.app-markdown \.katex-display > \.katex \{[\s\S]*white-space: nowrap;/);
  assert.match(indexCssSource, /\.app-markdown \.katex,[\s\S]*\.app-markdown \.katex \* \{[\s\S]*word-break: normal;/);
});
