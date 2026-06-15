## Context

The current Research Scout uses provider-diverse scholarly search. This is useful for breadth, but it can return candidates without PDFs or with inconsistent identifiers. For a research workflow centered on reading and library ingestion, arXiv PDFs should be the primary surface. Similar systems such as PaperQA2 and GPT Researcher separate retrieval from metadata enrichment and evidence-grounded ranking; OpenAlex and Semantic Scholar are better used as enrichment sources instead of replacing arXiv when a PDF is needed.

## Goals / Non-Goals

**Goals:**
- Prefer arXiv results when building Research Scout candidates.
- Preserve arXiv PDF URLs whenever an equivalent Semantic Scholar/OpenAlex result exists.
- Enrich arXiv results with venue, citation count, DOI, source URL, and institutions when provider metadata can be matched.
- Expose metadata provenance in the candidate payload and UI.
- Keep provider failures non-fatal.

**Non-Goals:**
- Download and parse PDF first pages for affiliations in this change.
- Persist enrichment fields to database models.
- Build a long-running background enrichment job.
- Replace existing broad `source="scholarly"` behavior outside Research Scout.

## Decisions

1. **Add a new source mode instead of changing all scholarly search.**
   - Use `source="arxiv_enriched"` for Research Scout.
   - Rationale: other pages may depend on current round-robin provider diversity.

2. **Merge metadata into the arXiv candidate, not the reverse.**
   - Keep `source="arxiv"` and `pdf_url` from arXiv while adding `metadata.enrichment`.
   - Rationale: arXiv PDF availability remains the primary candidate identity.

3. **Match by strongest identifiers first.**
   - Prefer arXiv id, then DOI, then normalized title.
   - Rationale: title matching is useful but less reliable.

4. **Provenance is explicit.**
   - Candidate metadata records which provider supplied venue, institutions, citations, DOI, and PDF.
   - Rationale: the UI can communicate confidence without overclaiming.

## Risks / Trade-offs

- **Provider lookup latency** -> perform enrichment with bounded candidate count and concurrent provider searches.
- **Title matching false positives** -> only title-merge when normalized titles are strong exact matches.
- **Institutions remain incomplete** -> show provenance and unknown status rather than guessing.
