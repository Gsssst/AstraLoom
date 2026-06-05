## 1. Proposal Lineage

- [x] 1.1 Add parent proposal and evolution metadata fields to `ResearchIdea`
- [x] 1.2 Add Alembic migration `020` for proposal lineage fields

## 2. External Scholarly Evidence

- [x] 2.1 Extend workbench run configuration with optional external scholarly search
- [x] 2.2 Normalize, deduplicate, and merge arXiv and Semantic Scholar evidence with failure-tolerant source errors

## 3. Proposal Decision And Evolution API

- [x] 3.1 Add enriched proposal response fields and request schemas
- [x] 3.2 Add project-owned proposal decision and structured comparison endpoints
- [x] 3.3 Implement and expose traceable single-step proposal evolution

## 4. Workbench Interface

- [x] 4.1 Add external-search run control and visible evidence provenance
- [x] 4.2 Add proposal pin, reject, restore, and evolution actions
- [x] 4.3 Add two-to-four proposal selection and side-by-side comparison view

## 5. Verification

- [x] 5.1 Add backend regression coverage for external degradation, decisions, comparison, and evolution
- [x] 5.2 Apply migration, run targeted tests, build frontend assets, and validate OpenSpec
