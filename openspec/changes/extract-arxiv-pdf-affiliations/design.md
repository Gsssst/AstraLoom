## Context

GROBID, Science Parse, and CERMINE all treat paper header parsing as the reliable place to extract title, authors, and affiliations from PDFs. This project already has PDF parsing dependencies in other workflows, but Research Scout needs a lightweight, bounded version that does not require a separate service.

## Goals / Non-Goals

**Goals:**
- For arXiv-enriched Research Scout candidates, attempt first-page text extraction from arXiv PDFs.
- Extract institution-like lines using conservative keyword and email-domain heuristics.
- Limit network and parsing cost by only processing a small number of top arXiv candidates.
- Preserve evidence and provenance so users can see that affiliations came from the PDF first page.
- Fail open: if PDF download or parsing fails, keep existing metadata.

**Non-Goals:**
- Full author-affiliation mapping.
- Full-document PDF parsing.
- GROBID service integration.
- LLM-based affiliation guessing.
- Database persistence of extracted affiliation evidence.

## Decisions

1. **Use first-page text only.**
   - Rationale: affiliation evidence is usually in the paper header, and first-page-only parsing bounds latency.

2. **Use heuristics rather than LLM guessing.**
   - Rationale: institutions must be evidence-backed. LLMs can be added later for normalization, not unsupported inference.

3. **Process only top arXiv candidates.**
   - Rationale: PDF download/parsing is more expensive than metadata merging. A bounded top-k pass improves common cases without slowing every result.

4. **Merge as provenance-rich metadata.**
   - Store extracted institutions under normal `institutions` and keep `pdf_first_page_affiliations` evidence in metadata.
   - Rationale: existing Research Scout cards and constraint matching can reuse the same institution field.

## Risks / Trade-offs

- **False positives from first-page text** -> require institution keywords or academic/company email domains and keep snippets visible.
- **Latency from PDF downloads** -> cap processed candidates and bytes.
- **Parser availability differences** -> try PyMuPDF first, then pdfplumber; failure is non-fatal.
