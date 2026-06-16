## 1. Planner Core

- [ ] 1.1 Add planner data models for planner decisions, planner observations, loop result, parse errors, and stop reasons.
- [ ] 1.2 Add strict JSON extraction/parsing for planner responses, including fenced JSON and malformed-output diagnostics.
- [ ] 1.3 Add planner prompt construction that includes registered tool schemas, current user query, bounded conversation context, and compact prior observations.
- [ ] 1.4 Add a bounded planner loop that calls the LLM, validates planned actions through the tool registry, executes actions through the existing runtime, and feeds observations into follow-up rounds.
- [ ] 1.5 Add deterministic fallback integration when the planner fails, returns no useful actions, or only produces rejected calls.

## 2. Runtime And Chat Integration

- [ ] 2.1 Extend the existing chat tool trace payload to include planner round events, fallback usage, planner stop reason, and tool observations.
- [ ] 2.2 Integrate the planner loop into the non-stream chat send path for general mode only.
- [ ] 2.3 Integrate the planner loop into the stream chat send path and include planner trace metadata in stream meta/saved messages.
- [ ] 2.4 Preserve Research Scout routing and existing candidate cards, source strip collapse, tool trace collapse, and manual scroll behavior.
- [ ] 2.5 Ensure side-effect observations such as `waiting_confirmation` stop the planner loop and keep the existing confirmation endpoint behavior.

## 3. Frontend Trace Compatibility

- [ ] 3.1 Verify the existing collapsed trace UI renders planner steps without new layout regressions.
- [ ] 3.2 Add small frontend status/label handling only if planner introduces statuses not already supported.
- [ ] 3.3 Ensure planner trace metadata remains hidden from visible reference strips while still reconstructing from saved messages.

## 4. Verification

- [ ] 4.1 Add backend tests for planner JSON parsing, malformed output fallback, unknown tool rejection, invalid argument rejection, and bounded round stops.
- [ ] 4.2 Add backend tests for planner-driven `search_papers`, `search_library`, and `import_paper` waiting-confirmation behavior using mocks.
- [ ] 4.3 Add chat integration tests confirming generic planner metadata appears in stream/non-stream paths and Research Scout remains isolated.
- [ ] 4.4 Add or update frontend contract tests for planner trace display and hidden internal trace references.
- [ ] 4.5 Run OpenSpec validation, focused backend tests, frontend contract tests, and frontend build.
