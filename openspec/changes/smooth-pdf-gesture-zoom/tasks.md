## 1. Specification

- [x] 1.1 Create OpenSpec proposal, design, spec delta, and task list for smooth PDF gesture zoom.

## 2. Frontend Implementation

- [x] 2.1 Keep `react-pdf` page render width stable during zoom and apply visual scale with CSS transforms.
- [x] 2.2 Reserve scaled page dimensions using per-page aspect ratios so pages do not overlap.
- [x] 2.3 Update evidence hit scrolling to use transformed client rectangles.
- [x] 2.4 Update PDF zoom styles for transformed page shells.

## 3. Verification

- [x] 3.1 Update zoom contract tests to assert transform-based smooth zoom and stable page rendering.
- [x] 3.2 Run frontend build, targeted tests, OpenSpec validation, and diff checks.
