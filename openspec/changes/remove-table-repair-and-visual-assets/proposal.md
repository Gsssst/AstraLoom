## Why

The current low-quality table repair implementation depends on Marker `TableConverter`, which is too memory-heavy for the local Docker CPU environment and fails all candidates. The visual asset extraction path was added as a parallel experimental evidence lane, but the user wants to discard both implementations and rebuild from a clean baseline.

## What Changes

- Remove the low-quality table repair maintenance action, endpoint, Celery task, Marker adapter, Marker dependency file, and related Docker configuration.
- Remove the visual asset extraction/summarization runtime, endpoints, maintenance recommendations, paper response fields, frontend visual evidence cards, and tests tied to that feature.
- Remove the in-progress stabilization OpenSpec change that was created for the discarded table repair direction.
- Keep baseline PDF text parsing, structured extraction, table quality detection metadata, and normal paper Q&A behavior intact.

## Capabilities

### New Capabilities

### Modified Capabilities

- `paper-library-maintenance-center`: Remove old low-quality table repair and visual asset maintenance actions from the active contract.
- `paper-multimodal-visual-evidence`: Remove the active visual asset evidence capability from the current product contract.
- `paper-qa-evidence-grounding`: Remove active requirements that depend on visual assets as answer evidence.
- `knowledge-base-retrieval-maintenance`: Remove table repair maintenance behavior tied to the discarded implementation.

## Impact

- Backend API routes and Pydantic response models under paper APIs.
- Backend services, Celery tasks, Docker configuration, parser scripts, and dependency files.
- Frontend paper detail and maintenance UI contracts.
- OpenSpec active changes and specs related to the discarded implementations.
- Targeted backend/frontend tests.
