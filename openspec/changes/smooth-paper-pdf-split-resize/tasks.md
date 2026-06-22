## 1. Resize State Wiring

- [x] 1.1 Add PDF split resize active state in the paper detail page and pass it to the PDF viewer.
- [x] 1.2 Ensure resize active state is cleared on pointer end and cleanup paths.

## 2. PDF Width Stability

- [x] 2.1 Update the PDF viewer to freeze page width updates while split resizing is active.
- [x] 2.2 Trigger a final container measurement after split resizing ends.
- [x] 2.3 Debounce PDF page width measurements during outer layout resize transitions.

## 3. Verification

- [x] 3.1 Add focused regression coverage for the resize freeze behavior.
- [x] 3.2 Run OpenSpec validation and frontend checks.
