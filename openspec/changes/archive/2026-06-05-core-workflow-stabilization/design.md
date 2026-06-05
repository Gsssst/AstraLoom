## Context

The application exposes several advanced workflows, but a small set of implementation defects breaks their normal execution paths. The failures cross service, API routing, and frontend action boundaries. This change repairs the existing behavior without expanding product scope or changing data models.

## Goals / Non-Goals

**Goals:**
- Return content reliably from successful non-streaming LLM calls and retain retry and usage-tracking behavior.
- Keep the research paper-selection tuple shape consistent throughout Idea generation.
- Ensure fixed paper utility routes are registered before the dynamic `/{paper_id}` detail route.
- Remove the incorrect paper-detail share action until a paper-sharing contract exists.
- Keep exactly one profile update route with email and display-name support.
- Add focused regression tests for the repaired backend paths.

**Non-Goals:**
- Add authorization boundaries or role policy changes.
- Redesign the UI or introduce responsive layout behavior.
- Change retrieval ranking quality, embedding models, or citation verification depth.
- Add a new paper-sharing API.

## Decisions

### 1. Keep retry handling inside the non-streaming LLM loop

Successful completion processing, reasoning fallback, usage logging, and return will occur inside the loop after the provider call succeeds. This keeps retries local and avoids an implicit `None` return.

Alternative considered: move response processing after the loop. Rejected because successful loop state would need to be carried across control flow and the current retry structure is simpler to repair in place.

### 2. Normalize research candidates only at reference boundaries

`PaperSelectionService.select_papers()` intentionally returns `(paper, score, source)`. Prompt generation will continue to preserve the source, while the parser reference input will explicitly project candidates to `(paper, score)`.

Alternative considered: change the selector return shape. Rejected because source metadata is useful to ranking diagnostics and prompt context.

### 3. Register fixed paper utility routes before `/{paper_id}`

The Markdown export handler will be moved into the fixed-route section. FastAPI matches routes in registration order, so fixed endpoints must be declared before the dynamic detail handler.

Alternative considered: constrain `paper_id` at the router path layer. Rejected as a broader API refactor that does not address other future fixed routes.

### 4. Remove the invalid paper share button

The current paper-detail action calls a research-project endpoint with a paper ID and cannot succeed. The action will be removed until a dedicated paper-share requirement is proposed.

Alternative considered: copy the arXiv URL. Rejected because it changes product semantics from application sharing to external-source linking without an agreed requirement.

### 5. Add lightweight tests using dependency stubs

Tests will cover service and router behavior without provider network calls or a live database. This creates a small regression floor while the broader test strategy remains future work.

## Risks / Trade-offs

- [Risk] Removing the paper share button temporarily reduces visible actions. → Mitigation: preserve the correct external arXiv link and propose paper sharing separately if needed.
- [Risk] Focused tests do not cover full Docker integration. → Mitigation: also run frontend build and local endpoint smoke checks.
- [Risk] Route ordering can regress as new paper endpoints are added. → Mitigation: add a route-order regression assertion.
