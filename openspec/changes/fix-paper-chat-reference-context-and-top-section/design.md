## Context

Current reference lookup intentionally avoids confusing body citations with bibliography entries, so `Reference [1]` returns the References item only. That fixed a previous failure, but it leaves the model without nearby body sentences that explain why `[1]` was cited. Current numbered section detection is also conservative: it accepts decimal section numbers like `3.2` but misses top-level numeric and Chinese ordinal requests.

## Goals / Non-Goals

**Goals:**
- Preserve bibliography-first reference lookup while adding body citation context as supplemental evidence.
- Detect top-level explicit section requests without mistaking metric values for sections.
- Split or recover noisy extracted lines that contain embedded top-level headings such as `4.Experiments`.

**Non-Goals:**
- Rebuild full citation graph analysis or citation intent classification.
- Guarantee perfect section recovery for every two-column extraction artifact.
- Change frontend PDF navigation behavior.

## Decisions

- Add citation-context evidence as a second item after the bibliography entry.
  - Rationale: the bibliography item answers "what is [1]", while citation context answers "why/how it relates".
  - Alternative: append context into the bibliography text. Separate evidence keeps metadata and page references clearer.
- Keep bare numeric top-level sections gated by section words or Chinese ordinal markers.
  - Rationale: avoids treating metrics like `63.2` or `4.0` as sections.
- Normalize embedded heading text before range extraction instead of changing chunk splitting globally.
  - Rationale: this confines risk to numbered-section lookup.

## Risks / Trade-offs

- [Risk] Body citation snippets may include unrelated nearby citations. -> Mitigation: keep snippets short and label them as citation context rather than bibliography facts.
- [Risk] Embedded heading recovery may split a noisy line incorrectly. -> Mitigation: require heading-like words after the number and reject figure/table/reference lines.
