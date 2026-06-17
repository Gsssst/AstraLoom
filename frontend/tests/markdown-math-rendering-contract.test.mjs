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

test('shared markdown renderer normalizes trailing display equation labels into katex tags', () => {
  assert.match(markdownSource, /export const normalizeDisplayEquationTags = \(value: string\)/);
  assert.match(markdownSource, /DISPLAY_MATH_BLOCK_RE = \/\\\$\\\$\(\[\\s\\S\]\*\?\)\\\$\\\$\/g/);
  assert.match(markdownSource, /STANDALONE_INLINE_MATH_LINE_RE/);
  assert.match(markdownSource, /TRAILING_NUMERIC_EQUATION_LABEL_RE/);
  assert.match(markdownSource, /normalizeTrailingDisplayEquationLabel\(expression\)/);
  assert.match(markdownSource, /KATEX_TAG_RE\.test\(trimmed\)/);
  assert.match(markdownSource, /const body = trimmed\.replace\(TRAILING_NUMERIC_EQUATION_LABEL_RE, ''\)\.trimEnd\(\)/);
  assert.match(markdownSource, /\\tag\{\$\{label\}\}/);
  assert.match(markdownSource, /normalizeDisplayEquationTags\(normalizedBracketLines\)/);
});

test('shared markdown renderer preserves non-math contexts', () => {
  assert.match(markdownSource, /FENCED_CODE_BLOCK_RE/);
  assert.match(markdownSource, /segment\.startsWith\('```'\) \|\| segment\.startsWith\('~~~'\)/);
  assert.match(markdownSource, /\^E\\d\+\(\?:\[,;\\s\]\+E\\d\+\)\*\$/);
  assert.doesNotMatch(markdownSource, /normalizeDisplayEquationTags\(value\)/);
});

test('shared markdown renderer keeps long display equations scrollable', () => {
  assert.match(markdownSource, /className="markdown-body app-markdown"/);
  assert.match(indexCssSource, /\.app-markdown \.katex-display \{[\s\S]*max-width: 100%;/);
  assert.match(indexCssSource, /\.app-markdown \.katex-display \{[\s\S]*overflow-x: auto;/);
  assert.match(indexCssSource, /\.app-markdown \.katex-display > \.katex \{[\s\S]*white-space: nowrap;/);
  assert.match(indexCssSource, /\.app-markdown \.katex-display > \.katex > \.katex-html:has\(> \.tag\) \{[\s\S]*padding-right: 3\.4em;/);
  assert.match(indexCssSource, /\.app-markdown \.katex-display > \.katex > \.katex-html > \.tag \{[\s\S]*right: 0\.2em;/);
  assert.doesNotMatch(indexCssSource, /\.app-markdown \.katex-display > \.katex \{[\s\S]*width: max-content;/);
  assert.doesNotMatch(indexCssSource, /\.app-markdown \.katex-display > \.katex \{[\s\S]*min-width: max-content;/);
  assert.match(indexCssSource, /\.app-markdown \.katex,[\s\S]*\.app-markdown \.katex \* \{[\s\S]*word-break: normal;/);
});

test('shared markdown renderer can link paper evidence markers', () => {
  assert.match(markdownSource, /export interface MarkdownEvidenceLink/);
  assert.match(markdownSource, /evidenceLinks\?: Record<string, MarkdownEvidenceLink>/);
  assert.match(markdownSource, /EVIDENCE_MARKER_RE = \/\\\[\(E\\d\+\)\\\]\/g/);
  assert.match(markdownSource, /EVIDENCE_LINK_PREFIX = '#paper-evidence-'/);
  assert.match(markdownSource, /export const linkMarkdownEvidenceMarkers/);
  assert.match(markdownSource, /linkMarkdownEvidenceMarkers\(normalizeMarkdownMath\(content\), evidenceLinks\)/);
  assert.match(markdownSource, /\^#paper-evidence-\(E\\d\+\)\$/i);
  assert.match(markdownSource, /renderEvidenceLinkedText\(children, evidenceLinks\)/);
  assert.match(markdownSource, /className=\{`markdown-evidence-link/);
  assert.match(indexCssSource, /\.markdown-evidence-link \{/);
});
