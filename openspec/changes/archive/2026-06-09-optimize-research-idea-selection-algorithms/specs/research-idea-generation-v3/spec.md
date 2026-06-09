## ADDED Requirements

### Requirement: Evidence-aware candidate selection algorithms
The system SHALL rank and select generated research candidates using deterministic post-processing signals for duplicate quality, evidence coverage, novelty risk, experiment completeness, and diversity before persisting final proposals.

#### Scenario: Stronger duplicate is retained
- **WHEN** two generated candidates substantially overlap in title, hypothesis, gap, approach, experiment facets, or evidence references
- **THEN** the workbench merges them as duplicates and retains the candidate with stronger pre-review quality signals rather than blindly keeping the first generated item.

#### Scenario: Evidence coverage adjusts quality
- **WHEN** a reviewed candidate has linked evidence from multiple evidence categories or sources
- **THEN** its adjusted review metadata includes an evidence coverage profile and its quality score reflects that coverage within bounded scoring limits.

#### Scenario: Weak evidence and weak experiment are penalized
- **WHEN** a reviewed candidate has thin evidence, no strong baseline, no metrics, or too few experiment steps
- **THEN** its adjusted score is penalized before final selection even if the raw LLM review score is high.

#### Scenario: Final proposals cover distinct research angles
- **WHEN** final proposals are selected from reviewed candidates
- **THEN** the selection algorithm prefers candidates that add new gap, operator, evidence, dataset, metric, or risk facets and records selection rationale and suppressed near-duplicates.
