## 1. Provider configuration

- [x] 1.1 Add optional SearXNG, Tavily, Exa and Brave Search environment settings.
- [x] 1.2 Add deployment template values and expose active provider names without secrets.

## 2. Provider adapters and orchestration

- [x] 2.1 Implement structured provider adapters using the shared web result contract.
- [x] 2.2 Prefer configured structured providers and use Bing/DDG HTML as bounded fallback.
- [x] 2.3 Preserve canonical URL deduplication and provider failure isolation.

## 3. Verification

- [x] 3.1 Add tests for structured parsing, primary provider preference and sparse-result fallback.
- [x] 3.2 Run backend targeted tests.
- [x] 3.3 Validate the OpenSpec change strictly.
