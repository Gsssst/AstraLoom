## 1. OpenSpec Hygiene

- [x] 1.1 Create proposal, design, and spec deltas for global PDF gesture zoom.
- [x] 1.2 Remove the superseded local magnifier change artifacts so it cannot be archived as the product contract.

## 2. Frontend Implementation

- [x] 2.1 Replace local magnifier state, DOM cloning, and floating loupe UI with a bounded global `zoomScale`.
- [x] 2.2 Render `react-pdf` pages at the effective zoomed width while preserving text and annotation layers.
- [x] 2.3 Add toolbar zoom controls and current zoom percentage.
- [x] 2.4 Add non-passive Ctrl/Cmd wheel gesture handling with scroll-anchor preservation.
- [x] 2.5 Update responsive PDF layout styles for horizontally scrollable zoomed pages.

## 3. Verification

- [x] 3.1 Replace local magnifier contract tests with global gesture zoom tests.
- [x] 3.2 Run frontend build, targeted contract tests, OpenSpec validation, and diff checks.
