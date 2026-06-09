## 1. Runtime Configuration

- [x] 1.1 Add embedding model and HuggingFace cache settings to backend configuration.
- [x] 1.2 Wire HuggingFace mirror/cache environment variables and persistent model cache volume into backend and celery worker containers.
- [x] 1.3 Load the embedding model from configurable settings while preserving the current default.

## 2. Operator Documentation

- [x] 2.1 Update environment examples with HuggingFace mirror/cache variables.
- [x] 2.2 Document server-side diagnosis and remediation for embedding model download failures.

## 3. Validation

- [x] 3.1 Add or update regression tests for configurable embedding model loading.
- [x] 3.2 Run OpenSpec validation and targeted backend tests/static checks.
