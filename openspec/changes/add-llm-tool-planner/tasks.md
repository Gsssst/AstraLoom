## 1. Planner Core

- [x] 1.1 Add planner data models for planner decisions, planner observations, loop result, parse errors, and stop reasons.
- [x] 1.2 Add strict JSON extraction/parsing for planner responses, including fenced JSON and malformed-output diagnostics.
- [x] 1.3 Add planner prompt construction that includes registered tool schemas, current user query, bounded conversation context, and compact prior observations.
- [x] 1.4 Add a bounded planner loop that calls the LLM, validates planned actions through the tool registry, executes actions through the existing runtime, and feeds observations into follow-up rounds.
- [x] 1.5 Add deterministic fallback integration when the planner fails, returns no useful actions, or only produces rejected calls.

## 2. Runtime And Chat Integration

- [x] 2.1 Extend the existing chat tool trace payload to include planner round events, fallback usage, planner stop reason, and tool observations.
- [x] 2.2 Integrate the planner loop into the non-stream chat send path for general mode only.
- [x] 2.3 Integrate the planner loop into the stream chat send path and include planner trace metadata in stream meta/saved messages.
- [x] 2.4 Preserve Research Scout routing and existing candidate cards, source strip collapse, tool trace collapse, and manual scroll behavior.
- [x] 2.5 Ensure side-effect observations such as `waiting_confirmation` stop the planner loop and keep the existing confirmation endpoint behavior.

## 3. Frontend Trace Compatibility

- [x] 3.1 Verify the existing collapsed trace UI renders planner steps without new layout regressions.
- [x] 3.2 Add small frontend status/label handling only if planner introduces statuses not already supported.
- [x] 3.3 Ensure planner trace metadata remains hidden from visible reference strips while still reconstructing from saved messages.

## 4. Verification

- [x] 4.1 Add backend tests for planner JSON parsing, malformed output fallback, unknown tool rejection, invalid argument rejection, and bounded round stops.
- [x] 4.2 Add backend tests for planner-driven `search_papers`, `search_library`, and `import_paper` waiting-confirmation behavior using mocks.
- [x] 4.3 Add chat integration tests confirming generic planner metadata appears in stream/non-stream paths and Research Scout remains isolated.
- [x] 4.4 Add or update frontend contract tests for planner trace display and hidden internal trace references.
- [x] 4.5 Run OpenSpec validation, focused backend tests, frontend contract tests, and frontend build.
