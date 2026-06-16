## Context

Chat already has a generic tool runtime, planner trace, attachment extraction, and built-in research skills. The remaining Stage 2 tool list includes `generate_image`, which should help create research visuals such as paper figure sketches, method flow diagrams, and presentation illustrations.

Mature chat products usually expose image generation as a tool or provider integration rather than hard-coding it into the chat answer path. LibreChat exposes image generation through configurable endpoints/tools, Open WebUI supports multiple image backends, and ComfyUI/Automatic1111 provide workflow-style local generation APIs. This project should start with a small provider abstraction and keep the tool result observable.

## Goals / Non-Goals

**Goals:**

- Add a configurable OpenAI-compatible image generation service.
- Register `generate_image` as a read-only tool in the chat tool registry.
- Return bounded image artifacts as `data:image/...;base64,...` plus metadata.
- Surface missing-provider configuration as a rejected observation, not a server crash.
- Add deterministic fallback for explicit user prompts such as "生成一张方法流程图".

**Non-Goals:**

- Persisting generated images to disk or database.
- Image editing, inpainting, or reference-image input.
- Frontend gallery/editor for generated images.
- ComfyUI/Stable Diffusion provider implementation in this slice.
- Bypassing normal tool validation or side-effect policy.

## Decisions

### Decision: OpenAI-compatible provider first

Use the configured OpenAI-compatible API base/key with an image model setting and call `/images/generations`.

Rationale: the project already supports an OpenAI-compatible provider for chat and vision, and this keeps deployment simple. The service module will still isolate payload construction so a later ComfyUI provider can be added.

### Decision: Return artifacts in observations

The tool will return image artifacts with data URLs and metadata in `ChatToolObservation.artifacts`; the final answer can summarize them and the tool trace can expose details.

Rationale: existing tool traces already carry artifacts/references without requiring a new persistence model.

### Decision: No persistence in first slice

The tool is read-only from the project data perspective. It may call an external generation API, but it will not create local files, papers, folders, or projects.

Rationale: persistence needs product decisions about asset libraries, permissions, and cleanup. Returning data URLs is sufficient for the initial chat workflow.

## Risks / Trade-offs

- **Large base64 payloads can bloat messages** -> Limit count and supported sizes, and cap returned metadata.
- **Provider compatibility varies** -> Keep payload small and add focused tests for payload shape and response parsing.
- **Generated images may be unsuitable for scientific claims** -> Include purpose/style metadata and require final answers to frame images as drafts/concepts.
- **No persistence means results can be lost after the chat turn** -> Accept for this slice; asset persistence can be a later OpenSpec change.
