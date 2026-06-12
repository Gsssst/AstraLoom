## ADDED Requirements

### Requirement: Caption-Linked Visual Region Crops
The system SHALL generate focused region crop assets for detected figure and table captions when a PDF can be rendered.

#### Scenario: Figure caption crop is generated
- **WHEN** visual extraction finds a figure caption on a rendered PDF page
- **THEN** the system stores a figure visual asset with its own crop image path, page number, bbox, caption, and crop strategy metadata
- **AND** the asset remains linked to the page-level render as fallback.

#### Scenario: Crop cannot be generated
- **WHEN** a caption-linked visual asset cannot be cropped
- **THEN** the system SHALL keep the page-level render reference usable
- **AND** expose metadata explaining that the visual asset is using the page fallback.

### Requirement: Preview-Ready Visual References
The frontend SHALL display visual evidence references as compact preview cards when an image asset is available.

#### Scenario: Paper Q&A answer includes visual evidence
- **WHEN** a paper Q&A answer includes a visual evidence reference with an asset id
- **THEN** the UI shows a preview card containing the thumbnail/image, visual kind, page number, and caption or snippet
- **AND** clicking the card navigates to the referenced PDF page when available.
