## Why

The product already has strong module-level capabilities, but papers, research directions, writing, action center, and project spaces still feel like separate islands. Users need a consistent, lightweight guide that explains the next useful step and routes them across the research workflow without hunting through menus.

## What Changes

- Add a reusable frontend workflow step guide for major research workflow pages.
- Surface contextual next steps on the paper library, research direction, and writing workbench pages.
- Keep each guide actionable: users can jump to another module or trigger a local page action such as opening maintenance or creating a direction.
- Add a small contract test so future UI changes do not silently remove the cross-module guide.

## Capabilities

### New Capabilities
- `workflow-step-guide`: Contextual frontend guidance that presents consistent next-step actions across core workflow modules.

### Modified Capabilities
- None.

## Impact

- Frontend only: adds a shared component and wires it into paper, research, and writing pages.
- No API changes and no new dependencies.
- Adds frontend contract coverage for the new cross-module workflow guide.
