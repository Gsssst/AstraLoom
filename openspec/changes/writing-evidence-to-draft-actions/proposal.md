# writing-evidence-to-draft-actions

## Why

The writing project UI now exposes evidence cards and citation diagnostics, but users still have to manually copy markers, decide where to paste them, and build a Related Work comparison table by hand. The next step is to turn evidence cards into direct writing actions while keeping the process transparent and evidence-grounded.

## What Changes

- Allow users to insert an evidence citation marker into the currently edited section.
- Generate a deterministic evidence-backed Related Work comparison table from project evidence cards.
- Let users write the generated table into the appropriate project section.
- Surface low-evidence and external-only warnings before users rely on incomplete evidence.

## Non-Goals

- Fully automatic manuscript generation.
- Replacing manual editing or citation verification.
- External scholarly search integration.

## Reference Patterns

- PaperQA-style evidence-first writing: keep citations and snippets attached to generated text actions.
- Citation verification tools: distinguish checked local evidence from unchecked external evidence.

## Success Criteria

- Evidence cards support "copy" and "insert into current section" actions.
- The writing project can generate a Related Work comparison table from its evidence cards.
- The UI shows whether the generated table is based on local verified evidence or external/weak evidence.
- Existing writing project editing, evidence cards, and citation checks continue to work.
