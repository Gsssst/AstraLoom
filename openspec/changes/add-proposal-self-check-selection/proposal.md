## Why

Even after compact Idea Briefs, the generated Top Proposals can still be too loose because the final selected candidates are persisted before a focused critique-and-rewrite pass. Adding an automatic self-check before persistence moves quality control earlier, so users see clearer ideas immediately instead of needing to manually deepen every proposal.

## What Changes

- Add an automatic pre-persistence self-check for selected Top Proposals.
- For each selected candidate, critique novelty collision risk, scope boundary, mechanism clarity, experiment minimality, and failure condition.
- Rewrite the candidate's `idea_brief` using the critique while preserving legacy proposal fields and review metadata.
- Store self-check metadata in `review_json.selection_self_check` for transparency.
- Keep generation robust: if model self-check output is unavailable or invalid, persist deterministic fallback metadata instead of failing the run.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `research-idea-workbench`: selected Top Proposals shall be automatically self-checked and tightened before they are persisted.

## Impact

- Backend service: `backend/app/services/research_idea_workbench.py`
- Frontend proposal detail: `frontend/src/pages/ResearchProjectPage.tsx`
- Tests: `backend/tests/test_research_idea_workbench.py`, `frontend/tests/research-proposal-next-actions-contract.test.mjs`
- OpenSpec: adds requirements for pre-persistence proposal self-check.
