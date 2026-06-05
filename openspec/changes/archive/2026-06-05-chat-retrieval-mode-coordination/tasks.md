## 1. Backend Retrieval Strategy

- [x] 1.1 Add validated chat retrieval depth and bounded retrieval limits
- [x] 1.2 Centralize knowledge-base and web context assembly for chat endpoints
- [x] 1.3 Reuse the bounded web-search service and preserve graceful fallback

## 2. Frontend Coordination

- [x] 2.1 Submit retrieval depth in streaming chat requests
- [x] 2.2 Auto-select deep retrieval when web enhancement is enabled
- [x] 2.3 Display the active retrieval strategy in the chat toolbar

## 3. Verification

- [x] 3.1 Add backend regression tests for retrieval limits, validation, and mixed context
- [x] 3.2 Run backend tests, frontend build, and strict OpenSpec validation
