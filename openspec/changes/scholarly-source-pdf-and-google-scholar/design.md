## Context

The paper library already normalizes arXiv, Semantic Scholar, and OpenAlex results into a shared `PaperResult`. The configured arXiv export endpoint is intermittently throttled or slow, while the alternate `arxiv.org/api/query` endpoint remains responsive. OpenAlex normalization currently keeps only a landing page and drops the official `best_oa_location.pdf_url` field. Google Scholar does not provide a supported public API for direct application integration, so HTML scraping would create an unstable dependency.

## Goals / Non-Goals

**Goals:**

- Keep arXiv useful during endpoint throttling with request spacing and bounded endpoint fallback.
- Preserve and display provider-supplied open PDF links.
- Offer an explicit comprehensive mode that returns visibly mixed scholarly sources.
- Support Google Scholar through an optional configured SerpApi adapter without making it required.

**Non-Goals:**

- Scraping Google Scholar pages directly.
- Downloading paywalled PDFs or bypassing publisher access controls.
- Replacing existing local-library hybrid retrieval.

## Decisions

### Use arXiv endpoint fallback with serialized request spacing

The adapter will try the configured primary endpoint and a configurable fallback endpoint in order, spacing requests with an async lock. This keeps provider behavior bounded and avoids parallel bursts. The default primary endpoint becomes `https://arxiv.org/api/query`, while `https://export.arxiv.org/api/query` remains a fallback.

### Use OpenAlex `best_oa_location` for open PDF discovery

The adapter will select `best_oa_location` and read its `pdf_url`, with `primary_location.pdf_url` as a secondary candidate. The URL will be exposed in remote previews and preserved under `metadata_json.pdf_url` during ingestion. Missing URLs remain missing rather than implying that a PDF exists.

### Keep provider source labels after aggregation

The comprehensive search mode will gather arXiv, Semantic Scholar, OpenAlex, and configured Google Scholar results, then deduplicate by scholarly identifiers and normalized title while preserving provider order. Individual provider modes remain available so users can distinguish strict-provider searches from comprehensive discovery.

### Integrate Google Scholar through SerpApi only when configured

The service will call SerpApi's Google Scholar engine only when `SERPAPI_API_KEY` is present. No direct Scholar HTML fetching is introduced. A missing key returns an empty optional-provider result so comprehensive search continues to work.

## Risks / Trade-offs

- [Risk] arXiv endpoints can both throttle or time out. → Keep OpenAlex and Semantic Scholar as bounded fallbacks and expose source labels.
- [Risk] OpenAlex entries may genuinely have no open PDF. → Show PDF actions only when a provider supplies an open URL.
- [Risk] SerpApi is a third-party paid dependency. → Keep it optional and configuration-gated.
- [Risk] Comprehensive search can be slower than a strict-provider query. → Run providers concurrently and retain provider-specific selectors.
