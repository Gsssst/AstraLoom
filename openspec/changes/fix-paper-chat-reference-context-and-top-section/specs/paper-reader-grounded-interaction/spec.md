## ADDED Requirements

### Requirement: Top-Level Numbered Section Lookup
The paper AI backend SHALL recognize explicit top-level numbered section requests in Chinese and English and retrieve the matching section text when it can be detected.

#### Scenario: User asks for section four in Chinese
- **WHEN** the user asks about `第四部分`, `第 4 部分`, or `第 4 节`
- **THEN** the backend detects section number `4` and attempts numbered-section retrieval before general document retrieval.

#### Scenario: Extracted PDF embeds a heading mid-line
- **WHEN** extracted paper text contains an embedded heading such as `4.Experiments` inside a noisy line
- **THEN** numbered-section retrieval can recover the heading and return the section range
- **AND** figure captions such as `Figure 4.` are not treated as section headings.
