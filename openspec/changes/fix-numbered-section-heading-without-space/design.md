## Context

The ALVTS paper's parsed `full_text` contains the target heading as `3.2.ALVTSFramework Layer-wiseTokenSelectionandProcessing.`. This is a common PDF extraction artifact: the visible heading has a section number and title, but spaces around punctuation are lost.

The existing heading parser requires whitespace after the numbered heading separator, which correctly avoids many false positives but misses this real section heading.

## Design

Extend numbered heading parsing with a second compact-heading regex:

- Accepts `3.2.ALVTSFramework`, `3.2:ALVTS Framework`, and `Section 3.2.ALVTS`.
- Still requires a multi-part section number for compact matches.
- Requires title-like trailing text to prevent metric values from matching.
- Keeps the existing standard heading parser first.

The extraction range logic can remain unchanged once `_parse_numbered_heading()` can parse the compact heading line.

## Risks / Trade-offs

- Compact parsing could match unusual numeric prose. To limit this, only multi-level numbers are accepted and the title must contain alphabetic or CJK text.
- Headings with fully collapsed titles may still be visually hard for the model to read, but matching the range is better than falling back to unrelated sections.
