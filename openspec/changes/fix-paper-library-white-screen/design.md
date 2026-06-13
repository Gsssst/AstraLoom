## Context

`PapersPage.tsx` defines `formatMaintenanceJobCompletion` after a `useEffect` that includes the function in its dependency array. JavaScript evaluates hook arguments during render, before later `const` initializers run, so this can throw and blank the page.

## Goals / Non-Goals

**Goals:**

- Remove the runtime initialization error.
- Keep the visual evidence job progress behavior unchanged.

**Non-Goals:**

- Redesign the maintenance page.
- Change backend job behavior.

## Decisions

1. Move `formatMaintenanceJobCompletion` and `isVisualEvidenceJob` above the polling `useEffect`.
   - This is the smallest safe fix and keeps the existing logic intact.

## Risks / Trade-offs

- [Risk] Contract tests may not catch every runtime hook-order issue. -> Also run the frontend build to exercise TypeScript/Vite compilation.
