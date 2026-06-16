## 1. Daya API alignment

- [x] 1.1 Add Daya-compatible image generation configuration defaults and documentation.
- [x] 1.2 Replace `/images/generations` payload construction with Vertex/Gemini `generateContent` payload construction.
- [x] 1.3 Parse Vertex/Gemini `candidates[].content.parts[].inlineData` image responses into existing generated image artifacts.
- [x] 1.4 Add a direct OpenAI-compatible Chat Completions helper that accepts `response_format`, `web_search_options`, and other Daya extension body fields.
- [x] 1.5 Route the default LLM tool planner through structured JSON output when OpenAI-compatible chat is active.

## 2. Verification

- [x] 2.1 Update backend unit tests for Daya image payloads, response parsing, and endpoint selection.
- [x] 2.2 Add LLM service tests for direct Chat Completions extension payloads and planner structured-output routing.
- [x] 2.3 Run focused backend tests.
- [x] 2.4 Run `openspec validate --specs --strict`.
- [x] 2.5 Commit the completed change.
