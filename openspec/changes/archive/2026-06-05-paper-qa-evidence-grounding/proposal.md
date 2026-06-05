## Why

Paper-page AI Q&A should behave like a reading assistant, not a generic summarizer. When users ask about Introduction, Method, or Experiments, the answer should be grounded in the corresponding paper section, cite evidence snippets, and admit when the paper text does not provide enough support. The current flow retrieves chunks but does not expose page-aware evidence to the user.

## What Changes

- Add structured evidence chunks for paper Q&A with section, score, page, and original snippet metadata.
- Prefer requested sections such as Introduction, Method, and Experiments when building paper Q&A context.
- Attach paper evidence references to streamed metadata so frontend references can show page/snippet/source.
- Make paper Q&A prompts require evidence-backed claims and explicit evidence-insufficient wording.
- Add frontend reference chips that show evidence coverage and can jump the PDF viewer to the referenced page.
- Add regression tests for section-first evidence retrieval, evidence metadata, and insufficient-evidence prompting.

## Capabilities

### New Capabilities
- `paper-qa-evidence-grounding`: Defines page/snippet-grounded paper AI Q&A with evidence coverage and PDF navigation.

## Impact

- Affected backend modules: paper chunk service, memory service, paper API, report service.
- Affected frontend modules: PDF viewer and paper detail Q&A panel.
- No database migration is required.
