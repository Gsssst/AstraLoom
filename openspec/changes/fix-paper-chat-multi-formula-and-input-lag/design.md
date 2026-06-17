## Context

The current formula route uses `detect_requested_formula_number()` and therefore collapses a multi-number request to the first matched number. The evidence planner then budgets formula evidence around that single target.

On the frontend, `question` lives in `PaperDetailPage`. The page owns PDF rendering state, chat messages, evidence drawers, attachments, parse status, and graph/resource UI. Updating this state on every keypress is too expensive.

## Goals / Non-Goals

**Goals:**
- Return exact formula evidence for all explicit formula numbers in a single question.
- Preserve order and deduplicate formula evidence.
- Avoid reducing existing text/context evidence too aggressively.
- Make typing local to the composer until send/reset/retry needs to interact with the parent.

**Non-Goals:**
- Do not redesign the paper chat UI.
- Do not add frontend performance instrumentation in this fix.
- Do not change formula extraction/OCR beyond multi-number routing.

## Design

1. Add `detect_requested_formula_numbers(query)`:
   - extract all numbers attached to formula/equation terms;
   - support Chinese punctuation/list separators such as `8、9、10`;
   - keep `detect_requested_formula_number()` as a first-number wrapper for compatibility.
2. In formula-number retrieval:
   - retrieve text formula evidence for each requested number;
   - merge structured formula evidence only for remaining budget if present;
   - keep metadata per formula, including `requested_formula_number`.
3. Update plan formula budget to scale with the number of requested formulas.
4. Add a memoized `PaperChatComposer` with local `draft` state and a ref API:
   - `getValue()`
   - `clear()`
   - `restore(value)`
   - `setValue(value)`
5. Parent submit flow reads from the ref and no longer updates top-level state on each keystroke.

## Risks / Trade-offs

- Multi-formula questions can consume more context budget. The formula budget scales to the requested count, while document evidence fills the remaining top-k.
- Local composer state introduces an imperative ref, but it keeps the change contained and avoids reworking the full paper detail component.
