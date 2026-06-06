## 1. Responses Streaming

- [x] 1.1 Add an OpenAI Responses API stream parser for output text and reasoning summary deltas.
- [x] 1.2 Route OpenAI-compatible `show_thinking` requests to the Responses stream.
- [x] 1.3 Keep normal GPT and DeepSeek stream paths unchanged.

## 2. Metadata And Tests

- [x] 2.1 Mark OpenAI-compatible provider thinking support as available.
- [x] 2.2 Add backend tests for Responses event parsing and provider routing.

## 3. Verification

- [x] 3.1 Validate the OpenSpec change.
- [x] 3.2 Run targeted backend tests and frontend build.
- [x] 3.3 Commit the focused implementation.
