import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

const researchProjectSource = readFileSync(
  new URL('../src/pages/ResearchProjectPage.tsx', import.meta.url),
  'utf8',
);

test('research project page exposes focused idea copilot panel', () => {
  assert.match(researchProjectSource, /import Markdown from '..\/components\/Markdown'/);
  assert.match(researchProjectSource, /Drawer/);
  assert.match(researchProjectSource, /renderCopilotPanel/);
  assert.match(researchProjectSource, /Idea Copilot/);
  assert.match(researchProjectSource, /openCopilot\(idea\)/);
  assert.match(researchProjectSource, /进入迭代面板/);
});

test('idea copilot supports explicit modes and quick prompts', () => {
  assert.match(researchProjectSource, /type CopilotMode = 'mentor' \| 'skeptic' \| 'experiment_designer' \| 'writer'/);
  assert.match(researchProjectSource, /copilotModeOptions/);
  assert.match(researchProjectSource, /copilotQuickPrompts/);
  assert.match(researchProjectSource, /value=\{discussion\.mode\}/);
  assert.match(researchProjectSource, /onChange=\{mode => setDiscuss\(copilotIdea\.id, \{ mode \}\)\}/);
});

test('idea copilot sends mode and renders markdown replies', () => {
  assert.match(researchProjectSource, /\/research\/ideas\/\$\{ideaId\}\/discuss/);
  assert.match(researchProjectSource, /message: current\.msg, mode: current\.mode/);
  assert.match(researchProjectSource, /<Markdown content=\{entry\.content\} \/>/);
  assert.match(researchProjectSource, /response\.data\.risks/);
  assert.match(researchProjectSource, /response\.data\.next_actions/);
  assert.match(researchProjectSource, /response\.data\.suggested_questions/);
  assert.match(researchProjectSource, /response\.data\.evolution_focus/);
  assert.match(researchProjectSource, /context_summary/);
});

test('idea copilot can convert discussion into proposal evolution', () => {
  assert.match(researchProjectSource, /evolveFromCopilot/);
  assert.match(researchProjectSource, /\/research\/ideas\/\$\{ideaId\}\/discuss\/evolve/);
  assert.match(researchProjectSource, /创建下一版 Proposal/);
  assert.match(researchProjectSource, /setIdeas\(previous => \[response\.data, \.\.\.previous\]\)/);
  assert.match(researchProjectSource, /copilotIdea\.status !== 'draft' && copilotIdea\.status !== 'pinned'/);
});

test('idea response keeps discussion log available to copilot state', () => {
  assert.match(researchProjectSource, /discussion_log\?: CopilotLogEntry\[\]/);
  assert.match(researchProjectSource, /idea\?\.discussion_log \|\| \[\]/);
  assert.match(researchProjectSource, /setIdeas\(previous => previous\.map\(idea => idea\.id === ideaId \? \{ \.\.\.idea, discussion_log:/);
});
