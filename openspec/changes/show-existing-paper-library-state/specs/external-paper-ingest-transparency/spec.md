## ADDED Requirements

### Requirement: Remote Previews Show Existing Library State
Remote paper previews SHALL indicate when the paper already exists in the local paper library.

#### Scenario: Search result matches local paper
- **WHEN** a remote search result matches a local paper by arXiv ID, DOI, provider metadata, or normalized title
- **THEN** the response includes an existing-library marker and the local paper identifier.

#### Scenario: Search result is already in library
- **WHEN** the paper library renders a remote result marked as already in the local library
- **THEN** the add-to-library action is disabled and displayed as "已在论文库".

#### Scenario: Digest or push result is already in library
- **WHEN** a paper recommendation or push card is marked as already in the local library
- **THEN** the card disables its add-to-library action and displays "已在论文库".

#### Scenario: Existing paper still has useful links
- **WHEN** a remote preview is already in the local library and includes a PDF or source URL
- **THEN** the card still allows opening the PDF or source link.
