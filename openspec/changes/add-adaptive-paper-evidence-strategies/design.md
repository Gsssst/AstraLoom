## Context

The previous table-evidence iteration added complete selected table bodies and `table_pack` evidence. That solves many local table questions, but broad experiment questions still fail because the retriever answers "what are the experiments/results/ablations overall?" with a small set of BM25 hits. Those questions need breadth first: all table inventory, the most relevant complete tables, and experiment-section text.

External implementation patterns:

- RAGFlow exposes chunking/references and uses multiple recall plus reranking before answering.
- Docling and MinerU convert complex documents into structured Markdown/JSON outputs, including table structure and reading order.
- Marker exports markdown/JSON/chunks and uses an optional LLM correction mode for tables/forms/equations.
- LlamaIndex's recursive table example indexes table summaries, then expands into table-specific query engines when a table summary is retrieved.

## Goals / Non-Goals

**Goals:**

- Route current-paper questions to retrieval strategies that match the user's intent.
- Build a broad experiment dossier for experiment/evaluation/result questions.
- Use GPT-class 128k context more confidently for broad experiment questions.
- Preserve complete selected table bodies.
- Keep ordinary factual/section questions compact and fast.
- Keep evidence references traceable to page, parser source, evidence type, and metadata.

**Non-Goals:**

- Install a new parser or vector database.
- Do pixel-level figure/table visual understanding.
- Send every table body unconditionally when a paper has many large tables.
- Replace the existing BM25 retrieval path for normal questions.

## Decisions

1. Introduce explicit evidence strategy detection.
   - `compact`: default small evidence set.
   - `table`: local table/metric/baseline question, using existing table packs.
   - `experiment`: broad experiment/evaluation/results question, using a dossier.
   - Section detection remains orthogonal and can narrow text snippets.
   - Rationale: different questions need different evidence shapes, not a single global top-k.

2. Use an experiment dossier as the first evidence item.
   - The dossier includes a complete table catalog for all structured table blocks and grouped text snippets from experiment/results/evaluation sections.
   - Rationale: the model needs a global map before detailed reasoning; this is the same high-level-to-detail idea used by recursive table retrieval.

3. Preserve selected table bodies in full.
   - Prompt control comes from table-pack count and supplemental text limits, not truncating selected tables.
   - Rationale: truncating table bodies is exactly what causes missing metrics/rows.

4. Use a larger evidence budget only for broad experiment mode.
   - Broad experiment mode can return up to 18 evidence items: one dossier, several full table packs, and focused text snippets.
   - Rationale: a 128k context window can handle a richer evidence bundle, but global expansion on every question would slow normal Q&A and increase noise.

5. Keep all-table coverage through catalog plus selected full bodies.
   - If there are many tables, the catalog includes every table, while full bodies are selected by experiment relevance and quality.
   - Rationale: this gives the model awareness of omitted tables and supports follow-up retrieval without hiding the existence of evidence.

## Risks / Trade-offs

- [Risk] Large experiment dossiers may increase latency and prompt cost. -> Apply the wider budget only to broad experiment intent and cap full table pack count.
- [Risk] A catalog is not a substitute for a full table body. -> Mark catalog entries separately and include full bodies for the best experiment-related tables.
- [Risk] Poor parser output can still mislead. -> Preserve parser source, quality metadata, row/column counts, and same-page caption/context in evidence metadata.
