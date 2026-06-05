## 1. Backend Stream Protection

- [x] 1.1 Retry reasoning-only and empty LLM streams once
- [x] 1.2 Encode chat-session stream payloads as JSON SSE events
- [x] 1.3 Persist a visible fallback instead of an empty assistant message

## 2. Frontend Stream Consumption

- [x] 2.1 Add a buffered JSON SSE consumer shared by text and attachment sends
- [x] 2.2 Display retrieval and generation progress text while sending

## 3. Verification

- [x] 3.1 Add backend regression tests for stream retry, SSE encoding, and blank fallback
- [x] 3.2 Run backend tests, frontend build, and strict OpenSpec validation
