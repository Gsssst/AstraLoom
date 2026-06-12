## Why

The low-quality table repair action is wired to the Marker adapter, but the backend image currently lacks the `marker_single` CLI that the adapter invokes. Administrators can start the repair action, yet every candidate fails before any high-fidelity table extraction can run.

## What Changes

- Add a deployable Marker runtime dependency path for the backend and worker images.
- Keep the existing `PDF_TABLE_PARSER_COMMAND` adapter contract unchanged.
- Verify the runtime exposes `marker_single` before treating table repair as operational.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `deployment-readiness`: Docker deployments that enable Marker table repair must install the Marker CLI runtime used by the project adapter.

## Impact

- Affects backend Python dependencies and Docker rebuild/runtime verification.
- Increases backend image size when Marker is installed.
- Does not change paper metadata schema, table repair API contracts, or frontend routes.
