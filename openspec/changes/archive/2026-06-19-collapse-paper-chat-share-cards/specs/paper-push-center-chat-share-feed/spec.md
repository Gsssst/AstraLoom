## ADDED Requirements

### Requirement: Paper chat share feed remains scannable with multiple shares
The paper push center SHALL keep multiple paper chat share items scannable by not expanding all shared content at once.

#### Scenario: Multiple shares exist
- **WHEN** the page renders multiple `paper_chat_share` notifications
- **THEN** each notification occupies a compact card until individually expanded
