## ADDED Requirements

### Requirement: Pipeline engine orchestrates multi-agent writing tasks

The system SHALL provide a `WritingPipeline` engine that coordinates multiple AI agents to complete writing tasks through sequential phases. Each phase SHALL emit progress events via SSE to the frontend.

#### Scenario: Execute full pipeline for Related Work generation

- **WHEN** user requests Related Work generation with topic "Transformer architecture variants"
- **THEN** the Pipeline SHALL execute Selector → Reader → Writer → Citation phases in sequence
- **AND** each phase transition SHALL emit an SSE progress event with phase name and status

#### Scenario: Execute lightweight pipeline for text polishing

- **WHEN** user requests text polishing
- **THEN** the Pipeline SHALL execute only Writer → Reviewer phases
- **AND** skip Selector, Reader, and Citation phases

#### Scenario: User cancels running pipeline

- **WHEN** user sends a cancellation request during pipeline execution
- **THEN** the Pipeline SHALL stop all in-progress agent calls
- **AND** emit a "cancelled" SSE event
- **AND** preserve any completed phase outputs

### Requirement: Pipeline supports configurable phase selection

The system SHALL allow callers to specify which phases to execute based on task type: lightweight tasks (polish, abstract) use Writer + Reviewer, standard tasks (Related Work, literature review) use Selector + Reader + Writer + Citation, and heavy tasks (full chapter) use all five phases.

#### Scenario: Auto-select phases by task type

- **WHEN** task type is "polish"
- **THEN** Pipeline SHALL auto-configure phases as [Writer, Reviewer]
- **AND** skip Selector, Reader, and Citation phases

#### Scenario: Manual phase override

- **WHEN** caller explicitly specifies phases ["Selector", "Writer"]
- **THEN** Pipeline SHALL execute only those phases regardless of task type

### Requirement: Pipeline emits real-time progress events

The system SHALL emit SSE events at each phase transition and at token-level granularity during Writer phase. Events SHALL include: phase start, phase progress (token streaming), phase complete, and pipeline error.

#### Scenario: Streaming tokens during Writer phase

- **WHEN** Writer agent generates content
- **THEN** each token SHALL be emitted as SSE event type "content"
- **AND** the frontend SHALL render tokens incrementally

#### Scenario: Error event on agent failure

- **WHEN** any agent fails (exception or timeout)
- **THEN** Pipeline SHALL emit SSE event type "error" with phase name and error message
- **AND** SHALL attempt retry once before failing the pipeline
