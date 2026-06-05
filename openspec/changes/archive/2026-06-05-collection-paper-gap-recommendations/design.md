## Overview

This change turns a user paper collection from a passive folder into a lightweight research-maintenance surface. The backend derives topic hints from the collection name and the papers already inside it, then exposes coverage diagnostics and recommendation queries. The frontend shows those diagnostics in the collection view and lets the user ingest recommended remote papers into the selected collection.

## Backend

### Topic Extraction

The folder API will derive topic terms from:

- folder name
- paper titles
- paper abstracts
- paper tags when available

The extraction is intentionally deterministic and dependency-free: normalize text, remove broad stopwords, score frequent academic phrases/terms, and keep a bounded list. This avoids making the quality-maintenance feature depend on an LLM call.

### Coverage Analysis

Coverage topics are built from:

- detected collection topic terms
- curated research-maintenance facets such as survey, benchmark, method, evaluation, dataset, and recent work
- domain hints for common terms such as video grounding and multimodal learning

Each topic reports:

- label
- query
- matched_count
- sample matched paper titles
- status: covered, thin, or missing

### Recommendations

The recommendations endpoint accepts a kind:

- classic: seminal/survey/benchmark-oriented query
- recent: recent-year query
- gap: first missing or thin coverage topic
- related: general collection terms

It calls the existing scholarly provider search pipeline and filters out papers already present in the selected collection using arXiv ID, DOI, remote ID, and normalized title keys. Returned items include a signed remote-ingest token so the frontend can reuse `/papers/ingest-personal`.

## Frontend

The Papers page collection view will:

- fetch coverage whenever the selected collection changes
- show coverage tags and suggested query chips
- let the user request recommendation batches by kind
- display recommendation cards with reason, source metadata, abstract, and an ingest button
- ingest directly into the currently selected collection

## Tradeoffs

- This is not a full citation graph recommender. It is a pragmatic first pass built on the existing search providers.
- Topic extraction is heuristic. The UI presents it as “覆盖分析/补充建议” rather than authoritative taxonomy.
- Stronger recommendations can later use citations, embeddings, and user reading feedback once more data is available.
