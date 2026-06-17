## Context

The existing numbered formula retrieval requires an explicit marker such as `(2)` in extracted text. Some PDFs render equation labels far to the right, and text extraction may drop one label while preserving neighboring labels. This matches the observed behavior: other numbered formulas are found, but formula 2 is not.

## Goals / Non-Goals

**Goals:**
- Keep exact numbered-label matching as the first choice.
- Add a bounded fallback only for preferred/current page text.
- Avoid using global formula order, which caused earlier wrong answers.
- Preserve metadata showing that this is a page-local order inference, not an exact label match.

**Non-Goals:**
- Do not OCR rendered PDF images.
- Do not implement a full formula object index.
- Do not change frontend UI in this fix.

## Design

1. Existing flow tries explicit label matching on preferred pages, all pages, and full text.
2. If explicit label matching fails for preferred pages, scan only those preferred page texts for display-like math lines.
3. Split candidate formulas by math-heavy lines, excluding section headings and prose-only lines.
4. Return the Nth candidate on that page for "formula N", with nearby explanatory text but without crossing into neighboring labeled formulas.
5. Add metadata:
   - `formula_order_fallback: true`
   - `formula_number_match: false`
   - `preferred_page_match: true`
   - `fallback_reason: "missing_formula_label_on_preferred_page"`

## Risks / Trade-offs

- Page-local formula order can still be imperfect if PDF text order differs from visual order. The fallback is intentionally restricted to preferred pages and only runs after exact label matching fails.
- If the user asks globally while current-page context is stale, the answer may infer from that page. Existing explicit page parsing and global fallback reduce this risk, and future UI can expose/clear current page context.
