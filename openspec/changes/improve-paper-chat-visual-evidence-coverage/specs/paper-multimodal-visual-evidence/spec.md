## ADDED Requirements

### Requirement: Visual Catalog References
Paper Q&A SHALL expose broad visual catalog references when answering visual survey questions, while keeping attached image assets bounded.

#### Scenario: Visual catalog exceeds attachment budget
- **WHEN** a paper has more visual evidence items than can be attached to the model in one answer
- **THEN** the response metadata and prompt context include catalog entries for the available visual items up to the configured catalog limit
- **AND** image attachments remain bounded by the configured attachment limit
- **AND** the model context identifies which evidence is metadata-only versus image-attached.

#### Scenario: Catalog entry has a related asset
- **WHEN** a catalog entry has an image, thumbnail, crop, or same-page visual asset
- **THEN** the visual reference metadata includes the page, optional bbox, caption or summary, parser/source, confidence, and asset identifier when available.
