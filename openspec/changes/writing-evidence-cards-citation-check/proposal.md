# writing-evidence-cards-citation-check

## Why

The writing assistant can already create survey drafts from research topics and research ideas, but the evidence carried into those drafts is still hidden in project metadata or plain reference text. Users cannot quickly see which papers support a draft, insert a citation marker, or check whether a paragraph's citation is actually grounded by the cited paper. This makes the writing loop feel unfinished and makes weak citations easy to miss.

## What Changes

- Add writing project evidence cards built from project metadata, local papers, arXiv IDs, and research idea evidence.
- Add a project section citation check that maps inline citations such as `[1]`, `arXiv:...`, and `Paper ID:...` to evidence cards and scores local-paper support.
- Surface evidence cards and section citation diagnostics in the writing project UI.
- Make weak/unchecked evidence explicit so users know when they need to import papers, supplement full text, or rewrite unsupported claims.

## Non-Goals

- Full automatic manuscript fact checking across every generated sentence.
- Replacing the existing citation recommendation and BibTeX export flows.
- External paid academic search integration.

## Open-Source Reference Patterns

- PaperQA-style evidence-first answering: keep source snippets close to the generated text instead of treating citations as decorative labels.
- RefChecker/TexGuardian-style citation verification: classify claim-citation pairs by support level and expose weak or unverifiable cases.

## Success Criteria

- A writing project generated from a research idea exposes evidence cards with roles, source identifiers, and local/import status.
- A user can run citation checks for a section and see strong, partial, weak, missing, or unchecked results.
- Weak or external-only evidence is called out clearly in the UI.
- Existing writing exports and project editing continue to work.
