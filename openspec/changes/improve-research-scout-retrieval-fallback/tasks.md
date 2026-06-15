## 1. Retrieval Strategy

- [x] 1.1 Add a Research Scout retrieval helper that runs arXiv-enriched search first and broad scholarly fallback when results are below target.
- [x] 1.2 Rank merged candidates with query-match, arXiv/PDF, citation, and recency signals before truncating to the final limit.
- [x] 1.3 Add retrieval strategy metadata to Research Scout response/tool trace without reintroducing generic web references.

## 2. Verification

- [x] 2.1 Add backend tests covering arXiv-empty broad fallback and strategy metadata.
- [x] 2.2 Update frontend contract tests if the tool trace metadata contract changes.
- [x] 2.3 Run OpenSpec validation, focused backend tests, frontend contract tests, and frontend build.
