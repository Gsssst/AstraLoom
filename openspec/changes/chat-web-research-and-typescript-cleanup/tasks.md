## 1. Structured Web Research Service

- [x] 1.1 Add structured web result parsing, canonical URL normalization, deduplication, and bounded ranking
- [x] 1.2 Add depth-aware query planning and concurrent Bing plus DuckDuckGo aggregation
- [x] 1.3 Preserve the formatted-context compatibility wrapper for existing callers

## 2. Shared Chat Retrieval Integration

- [x] 2.1 Extend shared retrieval limits with bounded web query breadth
- [x] 2.2 Inject structured web context and append clickable web references alongside local paper references
- [x] 2.3 Update chat and paper Q&A reference rendering to open web URLs when available

## 3. TypeScript Quality Cleanup

- [x] 3.1 Remove unused frontend imports, state, and destructured props reported by TypeScript
- [x] 3.2 Fix missing Ant Design imports and writing pipeline status typing

## 4. Verification

- [x] 4.1 Add backend regression tests for multi-provider aggregation, deduplication, degraded operation, and web citations
- [x] 4.2 Run targeted backend tests, full TypeScript build, Vite production build, and strict OpenSpec validation
