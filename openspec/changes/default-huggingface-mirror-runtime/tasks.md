## 1. Runtime Defaults

- [x] 1.1 Set application `HF_ENDPOINT` default to `https://hf-mirror.com`.
- [x] 1.2 Set Docker Compose backend/worker `HF_ENDPOINT` defaults to `https://hf-mirror.com`.
- [x] 1.3 Apply HuggingFace runtime env before reranker model load.
- [x] 1.4 Ignore local `backend/model-cache/`.

## 2. Tests And Docs

- [x] 2.1 Update runtime env tests for mirror defaults and override behavior.
- [x] 2.2 Update docs to describe mirror as default.
- [x] 2.3 Validate OpenSpec and run targeted tests.
- [x] 2.4 Commit changes.
