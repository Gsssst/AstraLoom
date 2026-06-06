## Context

The frontend already has `getApiErrorMessage` and `getHttpErrorMessage`, which normalize common Axios, backend, validation, timeout, network, and HTTP status failures. That covers toast copy, but it does not give pages a stable way to render richer persistent feedback.

Settings model connection testing is a good first adopter because failures often require a concrete recovery step: check `.env`, restart the backend, verify API keys, wait for upstream recovery, or log in again.

## Goals / Non-Goals

**Goals:**
- Preserve existing string-only helper behavior.
- Add a structured error detail helper that pages can use for Alert-style feedback.
- Classify common errors into categories and severities.
- Show persistent API connection test failures in settings.

**Non-Goals:**
- Add a global notification bus or interceptor-side toast.
- Replace every existing `message.error` call in one pass.
- Change backend error schemas.
- Add automatic retry UI beyond reporting whether retry is reasonable.

## Decisions

- Add `getApiErrorDetails` and `getHttpErrorDetails` beside existing helpers.
  - Rationale: existing call sites remain stable while new UI can opt into richer details.
  - Alternative considered: change `getApiErrorMessage` return type; rejected as too risky and noisy.
- Derive category and severity from transport status/code first, then fallback to message parsing.
  - Rationale: status codes are stable enough for auth, permission, validation, timeout, and upstream cases.
  - Alternative considered: require backend to return explicit categories; deferred because current error shapes are inconsistent across endpoints.
- Start adoption in settings API test failure.
  - Rationale: high-value workflow, small UI surface, and easy to validate without altering broader page behavior.

## Risks / Trade-offs

- [Risk] Recovery suggestions can be too generic for some endpoints.
  -> Mitigation: keep suggestions category-level and allow pages to pass action/fallback context.
- [Risk] Duplicate feedback if a page shows both toast and Alert.
  -> Mitigation: settings keeps a short warning toast and uses the Alert for durable details.
- [Risk] Message parsing based on English network strings is brittle.
  -> Mitigation: retain existing checks and fall back to safe generic guidance.
