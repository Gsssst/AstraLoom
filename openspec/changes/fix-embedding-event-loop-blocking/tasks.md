## 1. Embedding Runtime

- [x] 1.1 Move synchronous model initialization behind a thread-safe lazy loader.
- [x] 1.2 Run model loading and text encoding outside the asyncio event loop.

## 2. Regression Coverage

- [x] 2.1 Add backend coverage showing embedding generation yields to other asyncio tasks while model work runs.
- [x] 2.2 Add backend coverage showing concurrent embedding calls share one model initialization.

## 3. Verification

- [x] 3.1 Validate the OpenSpec change.
- [x] 3.2 Run targeted backend tests for embedding behavior.
- [x] 3.3 Verify health/login endpoints respond after backend restart.
