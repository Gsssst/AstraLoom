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
