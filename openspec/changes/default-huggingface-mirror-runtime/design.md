## Context

The chat request hung in retrieval because sentence-transformers attempted to reach `huggingface.co` while loading `all-MiniLM-L6-v2`. The repo already supports `HF_ENDPOINT`, but defaults leave it empty locally and `https://huggingface.co` in Docker Compose. The reranker CrossEncoder path also imports from `sentence_transformers` and can trigger the same network dependency.

## Decisions

- Set `Settings.HF_ENDPOINT` default to `https://hf-mirror.com`.
- Set Docker Compose defaults to `${HF_ENDPOINT:-https://hf-mirror.com}` for backend and worker.
- Make `_configure_runtime_environment()` assign configured values into `os.environ` instead of only `setdefault`.
  - Rationale: if a prior process env points to HuggingFace, application settings should still enforce the chosen runtime mirror.
- Reuse `_configure_runtime_environment()` from `hybrid_search.py` before loading `CrossEncoder`.
  - Rationale: all sentence-transformers model loads should share mirror/cache behavior.

## Risks

- [Risk] Operators outside China may prefer direct HuggingFace.
  -> Mitigation: `HF_ENDPOINT` remains overrideable in `.env` and Compose.
- [Risk] Existing process env may intentionally point elsewhere.
  -> Mitigation: explicit environment variables still flow into settings; the app only overwrites with the configured value.
