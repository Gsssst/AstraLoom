## 1. Implementation

- [x] 1.1 Add request-local usage identity helpers and set them in auth dependencies.
- [x] 1.2 Update LLM usage logging to use the current usage identity.
- [x] 1.3 Add `send_hour` to digest subscription API/model and frontend settings.
- [x] 1.4 Change Celery digest scheduling to hourly due checks with same-day duplicate protection.
- [x] 1.5 Dispose async DB pools after digest task execution to avoid cross-loop asyncpg failures.

## 2. Verification

- [x] 2.1 Add tests for authenticated token attribution and system fallback.
- [x] 2.2 Add tests for digest send-hour filtering and duplicate protection.
- [x] 2.3 Run OpenSpec validation, focused backend tests, frontend contracts, and build.
