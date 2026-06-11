## 1. Docling Backend

- [x] 1.1 Add `docling` to supported structured parser backends.
- [x] 1.2 Implement optional Docling conversion through dynamic import.
- [x] 1.3 Normalize Docling Markdown, dict exports, and common typed collections into structured blocks.

## 2. Fallback And Configuration

- [x] 2.1 Route `PDF_STRUCTURED_PARSER_BACKEND=docling` through the Docling backend.
- [x] 2.2 Preserve lightweight fallback when Docling is unavailable or conversion fails.
- [x] 2.3 Forward `docling` backend value through Docker Compose.

## 3. Verification

- [x] 3.1 Add tests for Docling object normalization.
- [x] 3.2 Add tests for Docling backend success and fallback behavior.
- [x] 3.3 Run OpenSpec validation and targeted backend tests.
- [x] 3.4 Commit the change.
