import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

const researchProjectSource = readFileSync(
  new URL('../src/pages/ResearchProjectPage.tsx', import.meta.url),
  'utf8',
);

test('research project page exposes proposal iteration timeline state and endpoint', () => {
  assert.match(researchProjectSource, /interface TimelineEvent/);
  assert.match(researchProjectSource, /interface IdeaTimeline/);
  assert.match(researchProjectSource, /timelineOpen/);
  assert.match(researchProjectSource, /timelineLoading/);
  assert.match(researchProjectSource, /timelineData/);
  assert.match(researchProjectSource, /\/research\/ideas\/\$\{idea\.id\}\/timeline/);
});

test('research project page opens timeline from proposal and copilot actions', () => {
  assert.match(researchProjectSource, /const openTimeline = async \(idea: Idea\)/);
  assert.match(researchProjectSource, /openTimeline\(idea\)/);
  assert.match(researchProjectSource, /openTimeline\(copilotIdea\)/);
  assert.match(researchProjectSource, /迭代轨迹/);
  assert.match(researchProjectSource, /加载迭代轨迹失败/);
});

test('research project page renders categorized timeline drawer', () => {
  assert.match(researchProjectSource, /renderTimelineDrawer/);
  assert.match(researchProjectSource, /<Timeline/);
  assert.match(researchProjectSource, /timelineTypeLabels/);
  assert.match(researchProjectSource, /timelineSeverityColors/);
  assert.match(researchProjectSource, /timelineData\.events\.map/);
  assert.match(researchProjectSource, /event\.details\?\.next_actions/);
  assert.match(researchProjectSource, /event\.details\?\.risks/);
  assert.match(researchProjectSource, /event\.details\?\.evolution_focus/);
  assert.match(researchProjectSource, /event\.details\?\.results/);
});
