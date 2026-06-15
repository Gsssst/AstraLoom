## ADDED Requirements

### Requirement: Research Scout parses scholarly constraints
Research Scout SHALL extract user constraints for venues, institutions, authors, constraint mode, and evaluation focus when such hints appear in the prompt.

#### Scenario: User asks for institutional constraints
- **WHEN** the user asks for papers from organizations such as universities, labs, or companies
- **THEN** the Research Scout intent metadata includes normalized `institutions`
- **AND** the request is still handled as a scholarly discovery request.

#### Scenario: User asks for venue or author constraints
- **WHEN** the user names conferences, journals, workshops, or authors
- **THEN** the Research Scout intent metadata includes `venues` and/or `authors` where detected.

#### Scenario: User marks constraints as strict
- **WHEN** the prompt uses strict terms such as "必须", "限定", "only", or "must"
- **THEN** the intent metadata marks `constraint_mode` as `hard`
- **AND** otherwise defaults to `soft`.

### Requirement: Research Scout evaluates paper candidates
Research Scout SHALL attach a structured evaluation object to each candidate paper.

#### Scenario: Candidate has enough metadata
- **WHEN** a candidate includes title, abstract, year, source, authors, citations, or PDF status
- **THEN** its evaluation includes novelty, relevance, reproducibility, impact, experiment quality, and risk dimensions
- **AND** each dimension includes a score, reason, evidence list, and confidence.

#### Scenario: Evidence is missing
- **WHEN** a dimension cannot be supported by available candidate metadata
- **THEN** the evaluation states the limitation through low confidence or conservative scoring
- **AND** does not claim unavailable facts as confirmed.

### Requirement: Research Scout displays constraint and evaluation signals
The chat interface SHALL display parsed constraints and compact evaluation scores on Research Scout candidate cards.

#### Scenario: User reviews Research Scout results
- **WHEN** candidate cards are rendered
- **THEN** venue, institution, author constraints, constraint mode, and evaluation focus are visible in the intent summary when present
- **AND** each card shows evaluation score chips plus concise reasons and confidence/evidence cues.
