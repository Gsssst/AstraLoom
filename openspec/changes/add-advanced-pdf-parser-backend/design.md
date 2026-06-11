## Context

The previous iteration added lightweight structured extraction using installed PDF libraries. It improves table and caption grounding but does not perform OCR, chart understanding, formula recognition, or high-quality layout reconstruction. GitHub projects such as Docling, MinerU, Marker, and Unstructured commonly solve this by producing Markdown/JSON blocks from a parser pipeline before RAG.

The app should be able to consume those parser outputs when operators install one, while still working without heavyweight dependencies.

## Goals / Non-Goals

**Goals:**
- Add a backend abstraction for advanced structured PDF parsers.
- Support a generic command adapter so deployments can wire Docling, MinerU, Marker, or another parser without adding a required Python dependency.
- Normalize parser JSON into existing `StructuredPdfExtraction` and `StructuredPdfBlock` objects.
- Propagate HuggingFace mirror/cache environment variables to parser subprocesses.
- Keep lightweight parsing as the default and fallback.

**Non-Goals:**
- Bundle or install Docling, MinerU, Marker, or Unstructured.
- Add UI for parser configuration.
- Add pixel-level VLM analysis inside the application process.
- Replace the existing structured metadata cache format.

## Decisions

1. Introduce `PDF_STRUCTURED_PARSER_BACKEND` with `lightweight`, `command`, and `auto`.
   - Rationale: `lightweight` preserves current behavior; `command` lets operators opt into external tools; `auto` can try command first and fall back.
   - Alternative considered: hard-code Docling Python APIs. Rejected because dependencies and model assets are large and vary by deployment.

2. Use a JSON contract for external parser commands.
   - Rationale: JSON is stable across parser choices and easy to test. The command receives the PDF path and writes JSON to stdout or a configured output file.
   - Alternative considered: parse Markdown only. Rejected because page numbers, block types, and metadata need structured fields.

3. Keep command execution bounded.
   - Rationale: PDF parsing can be slow or memory-heavy. The backend must avoid hanging paper Q&A.
   - Implementation constraints: timeout, max JSON bytes, no shell interpolation, and fallback to lightweight parsing on failure.

4. Reuse HuggingFace runtime environment configuration.
   - Rationale: Docling/MinerU-style OCR/VLM backends may download models from HuggingFace; user policy requires mirror access.
   - Implementation constraints: parser subprocess env receives `HF_ENDPOINT`, `HF_HOME`, `TRANSFORMERS_CACHE`, and `SENTENCE_TRANSFORMERS_HOME`.

## Risks / Trade-offs

- [Risk] External parser command is misconfigured or missing. -> Fall back to lightweight parser and log a warning.
- [Risk] Parser JSON format varies. -> Accept a permissive normalized schema with common aliases for type, text, markdown, page, and metadata.
- [Risk] Large parser output bloats metadata. -> Enforce max output bytes and existing block/character caps.
- [Risk] Shell command injection. -> Parse commands with `shlex.split` and run without `shell=True`.
