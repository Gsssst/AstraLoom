## MODIFIED Requirements

### Requirement: Caption-Linked Visual Region Crops
The system SHALL generate focused region crop assets for parser-detected figure, chart, table, and caption regions when a PDF can be rendered.

#### Scenario: Figure caption crop is generated
- **WHEN** visual extraction finds a figure caption or figure region on a rendered PDF page
- **THEN** the system stores a figure visual evidence asset with its own crop image path, page number, bbox, caption, crop strategy metadata, parser source, and confidence
- **AND** the asset remains linked to the page-level render as fallback.

#### Scenario: Table crop is generated
- **WHEN** visual extraction finds a table region or table caption on a rendered PDF page
- **THEN** the system stores a table visual evidence asset with crop image path, page number, bbox, caption, parser source, and any OCR/table markdown generated for that crop.

#### Scenario: Crop cannot be generated
- **WHEN** a caption-linked visual asset cannot be cropped
- **THEN** the system SHALL keep the page-level render reference usable
- **AND** expose metadata explaining that the visual asset is using the page fallback.

### Requirement: Preview-Ready Visual References
The frontend SHALL display visual evidence references as compact preview cards when an image asset is available.

#### Scenario: Paper Q&A answer includes visual evidence
- **WHEN** a paper Q&A answer includes a visual evidence reference with an asset id
- **THEN** the UI shows a preview card containing the thumbnail/image, visual kind, page number, confidence, and caption or snippet
- **AND** clicking the card navigates to the referenced PDF page when available.

#### Scenario: Evidence has no image preview
- **WHEN** a visual evidence reference has page and caption metadata but no image asset
- **THEN** the UI still shows a compact textual evidence reference and allows PDF page navigation when a page number is available.
