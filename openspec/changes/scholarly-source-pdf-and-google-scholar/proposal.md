## Why

Remote paper discovery currently hides arXiv upstream failures by silently returning OpenAlex-only fallback results, and OpenAlex open-access PDF links are discarded during normalization. Users need a reliable multi-provider discovery flow with transparent source diversity and usable open PDFs, plus an optional compliant way to include Google Scholar results.

## What Changes

- Make arXiv retrieval resilient to endpoint throttling and transient timeouts by trying configured API endpoints with bounded retries and request spacing.
- Extract OpenAlex open-access PDF links, expose them in remote previews, and preserve them when a paper is added to the library.
- Add an explicit comprehensive scholarly-search mode that aggregates arXiv, Semantic Scholar, OpenAlex, and an optional Google Scholar provider while preserving visible source labels.
- Add an optional SerpApi Google Scholar adapter controlled by configuration. Do not scrape Google Scholar HTML directly.
- Extend the paper-library interface with provider selectors and open-PDF links when a remote provider supplies one.

## Capabilities

### New Capabilities

- `scholarly-source-pdf-and-google-scholar`: Reliable multi-provider scholarly discovery, open-PDF handling, and optional Google Scholar integration.

### Modified Capabilities

None.

## Impact

- Scholarly-search configuration and provider adapters.
- Remote paper-search API response and personal-ingestion metadata.
- Paper-library provider selector, cards, and abstract dialog.
- Focused backend regression tests and frontend build verification.
