## Context

The app runs LaTeX checks by shelling out to `pdflatex`. In local/container setups without TeX installed, users see only a hard failure. Separately, `SectionEditor` calls `onUpdate` immediately from `onChange`, and `WritingPage` persists through the API and updates project sections on every character. That can retrigger derived summary effects and cause visible layout movement.

## Goals / Non-Goals

**Goals:**
- Make missing `pdflatex` a degraded preview state instead of a blocking compile failure.
- Detect obvious source issues without a compiler, such as unbalanced environments/braces.
- Stop per-keystroke API writes and parent rerenders.
- Ensure toolbar actions operate on the latest in-editor draft.

**Non-Goals:**
- Do not install TeX Live or system packages from the app.
- Do not implement a full LaTeX parser.
- Do not replace the existing section editor component.

## Decisions

1. **Return fallback diagnostics with a `compiler_available` flag.**
   - Rationale: the frontend can distinguish "source looks acceptable but compiler missing" from actual LaTeX errors.
   - Alternative: keep returning `success: false`. That makes the feature feel broken even when the source is not the problem.

2. **Use local draft state plus debounced save in `SectionEditor`.**
   - Rationale: typing should be immediate and should not force parent-level workbench refreshes for each character.
   - Alternative: debounce only the parent handler. Local draft state still gives the editor stable text during in-flight saves and section switching.

3. **Pass latest draft to section actions.**
   - Rationale: users expect preview/quality/AI actions to use the text currently visible in the editor, not the last persisted section.

## Risks / Trade-offs

- [Risk] Fallback diagnostics can miss errors that only a real compiler catches.
  -> Mitigation: clearly mark the compiler as unavailable and add a warning recommending installing `pdflatex` for full checks.
- [Risk] Debounced saves may leave unsaved text briefly after typing.
  -> Mitigation: flush save on blur and when section-scoped actions run.
