## Why

The Writing workbench can check bracket citations, but users still need sentence-level guidance about claims that are not cited, are weakly supported, or rely on external-only evidence. After surfacing Proposal writing briefs, the next risk is letting unsupported draft claims move into polishing/export without a clear safety signal.

## What Changes

- Extend section citation checks with claim-level diagnostics derived from the section text.
- Detect substantive claim sentences that lack citation markers.
- Label cited claim sentences as strong, partial, weak, unchecked external, or missing based on existing evidence-card matching.
- Return a safety summary with counts, status, and recommended next actions.
- Show claim/citation safety diagnostics in the section editor alongside existing citation checks.
- No breaking API changes; existing citation `checks` remain.

## Capabilities

### New Capabilities

### Modified Capabilities
- `writing-evidence-cards-citation-check`: section citation checks must include claim-level safety diagnostics and the Writing UI must surface them.

## Impact

- Backend: `WritingProjectService.check_section_citations` and focused backend tests.
- Frontend: `SectionEditor` diagnostic display and writing workbench contract tests.
- No database migration or new dependency.
- External learning: RefChecker-style claim verification and Valsci/RAG-style evidence scoring informed the decision to separate claim detection, citation presence, and support strength.
