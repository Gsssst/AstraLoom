## 1. Reference Context

- [x] 1.1 Add body citation context extraction for requested bibliography numbers.
- [x] 1.2 Return citation context evidence together with the matched bibliography entry and update prompt guidance.

## 2. Top-Level Sections

- [x] 2.1 Detect Chinese and English top-level section-number requests such as `第四部分` and `section 4`.
- [x] 2.2 Recover embedded top-level headings from noisy PDF extraction without matching figure captions.

## 3. Verification

- [x] 3.1 Add regression tests for reference context and noisy Section 4 extraction.
- [x] 3.2 Run OpenSpec validation and targeted backend tests, then commit.
