## 1. Split State And Drag Behavior

- [x] 1.1 Add mutually exclusive PDF and AI collapsed states with left/right snap thresholds.
- [x] 1.2 Restore either collapsed panel when dragging back into the normal split range.
- [x] 1.3 Reset both collapsed states when returning to the default split or leaving desktop PDF mode.

## 2. Collapsed Rail Layout

- [x] 2.1 Render a restorable PDF rail symmetric with the existing AI rail.
- [x] 2.2 Let PDF or AI flex into all remaining width when the opposite panel is collapsed.
- [x] 2.3 Add accessible rail styling and preserve the draggable divider.

## 3. Verification

- [x] 3.1 Add focused contract tests for both collapse directions, restoration, and fill behavior.
- [x] 3.2 Run focused tests and the frontend production build.
