## Context

The paper-detail chat path builds a bounded evidence pack before calling the LLM. `PaperChunkService.detect_requested_sections()` currently maps only semantic aliases such as `method` or `experiments` to canonical sections. Questions like "请帮忙拆解第 3.2 节" become ordinary top-k queries, which can retrieve adjacent captions or overview text instead of the exact subsection.

Mature paper-QA systems such as PaperQA emphasize answer grounding through document chunks and citations, while structured PDF tools such as GROBID preserve section hierarchy where possible. The practical pattern for this codebase is to keep the existing chunked evidence model, but add a deterministic numbered-section lane before semantic/top-k retrieval.

## Goals / Non-Goals

**Goals:**
- Detect numbered section references such as `3.2`, `第 3.2 节`, `section 3.2`, and `sec. 3.2`.
- Locate a matching section heading in `full_text`, page text, or structured block text.
- Extract the content range from that heading to the next same-or-higher-level numbered heading.
- Return this range as high-priority `paper_evidence` with metadata that explains the match.
- When no exact match is found, expose a precise warning in the evidence plan so the model can say the parsed paper text does not contain the requested section.

**Non-Goals:**
- Replace the PDF parser or introduce GROBID as a dependency.
- Guarantee perfect section reconstruction for badly parsed two-column PDFs.
- Change frontend chat UX beyond existing evidence display.
- Alter ordinary chat or Research Scout.

## Design

### Detection

Add a detector that returns normalized numbered section requests:

- Chinese: `第 3.2 节`, `第3.2小节`, `3.2 节`
- English: `section 3.2`, `sec. 3.2`, `subsection 3.2`
- Bare numeric references are accepted only when accompanied by section-like words in the query to avoid confusing metric values with sections.

The first detected number becomes `target_section_number` in `PaperQuestionEvidencePlan`.

### Extraction

The extractor scans candidate text line-by-line for numbered headings. A heading match accepts common forms:

- `3.2 Title`
- `3.2. Title`
- `3.2: Title`
- `Section 3.2 Title`

Once a target heading is found, collect lines until the next numbered heading whose hierarchy level is same or higher than the target, for example `3.3` or `4`, but not `3.2.1`.

### Retrieval Order

`retrieve_evidence()` will run the numbered-section lane before method/table/visual/top-k lanes. If exact section evidence is found, it returns that evidence with scope `numbered_section`.

If no exact section is found, ordinary retrieval still runs, but the evidence plan includes a warning like `numbered_section_not_found:3.2`. The system prompt already tells the model to avoid overgeneralizing local evidence gaps; this warning lets the model phrase the failure precisely.

### Metadata

Numbered-section evidence includes:

- `source_type: "numbered_section"`
- `metadata.requested_section_number`
- `metadata.matched_heading`
- `metadata.extraction_strategy: "numbered_section_range"`

## Risks / Trade-offs

- PDF extraction may split headings across lines; exact matching can still fail. The fallback warning should make this visible.
- Bare `3.2` can mean a metric value; detection is intentionally conservative unless the query contains section-like markers.
- Extracted sections can be long; cap section text length and chunk long section ranges into a bounded evidence pack.
