## Context

Daya's reviewed documentation confirms that ordinary OpenAI-compatible chat still uses `https://api.dayaai.com/v1/chat/completions`, including `tools`, `response_format`, `web_search_options`, and multimodal `image_url`/`file` content parts. However, Daya image generation is documented through the Google Vertex/Gemini-compatible API at `/v1beta/models/{model}:generateContent` with `generationConfig.responseModalities` containing `["TEXT", "IMAGE"]`.

The current project already has a bounded chat `generate_image` tool and a model-driven chat tool planner. The image tool currently calls `/images/generations`, and the planner asks for JSON via prompting instead of requesting structured output from the provider.

## Goals / Non-Goals

**Goals:**

- Make `generate_image` use the Daya-compatible Vertex/Gemini request and response shape.
- Reuse `OPENAI_COMPATIBLE_API_KEY` for Daya image generation so the user does not configure a second API key.
- Add direct Chat Completions support for provider extension bodies used by Daya, especially structured output.
- Apply structured JSON output to the planner when the active provider is OpenAI-compatible.

**Non-Goals:**

- Replace all LiteLLM chat calls.
- Implement full Daya-hosted web search answer generation in this change.
- Persist generated images or add a media library.
- Add the Google GenAI SDK dependency.

## Decisions

1. Use direct `httpx` for Daya Vertex/Gemini image generation.
   - Rationale: The project already depends on `httpx`, and Daya exposes a documented REST endpoint. This avoids introducing `google-genai` only for one bounded tool.
   - Alternative considered: add `google-genai`; rejected because it adds dependency surface and version churn without a clear benefit for this narrow adapter.

2. Add a separate image base setting instead of reusing `/v1`.
   - Rationale: Daya Chat Completions uses `/v1`, while Vertex/Gemini-compatible generation uses the host-level `/v1beta/...` path. A separate `IMAGE_GENERATION_API_BASE` avoids brittle string rewriting.
   - Alternative considered: derive the host from `OPENAI_COMPATIBLE_API_BASE`; rejected as the only behavior because users may point chat at another OpenAI-compatible host while image generation still needs a different endpoint.

3. Keep the existing generated artifact model.
   - Rationale: The frontend and tool runtime already understand image artifacts as data URLs with provider/model metadata.
   - Alternative considered: persist files under uploads; rejected because the current spec requires storage-free generation.

4. Add a direct Chat Completions helper to `LLMService`.
   - Rationale: LiteLLM is useful for normal chat but can drop or reject provider extension fields. A direct helper lets planner and future Daya web-search/citation work use `response_format` and `web_search_options` explicitly.
   - Alternative considered: pass all extension fields through LiteLLM; rejected because the existing code already notes some OpenAI provider extra bodies cause errors.

## Risks / Trade-offs

- Daya model availability differs by account → keep configuration errors explicit and surface provider status text.
- Vertex/Gemini responses may use either `inlineData` or `inline_data` casing → parse both.
- Some OpenAI-compatible providers may not support `response_format=json_schema` → use the direct structured helper only for the configured OpenAI-compatible provider and let existing planner fallback handle failures.
