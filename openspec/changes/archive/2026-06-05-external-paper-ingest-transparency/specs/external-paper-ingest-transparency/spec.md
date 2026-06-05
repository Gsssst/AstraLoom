## ADDED Requirements

### Requirement: External Search Shows Provider Transparency
The paper library SHALL explain which scholarly provider strategy is active during external search.

#### Scenario: User selects a remote source
- **WHEN** the user selects arXiv, Semantic Scholar, OpenAlex, Google Scholar, or comprehensive scholarly search
- **THEN** the page shows a concise provider explanation and retry guidance.

### Requirement: Remote Paper Cards Show Ingest Readiness
Remote paper result cards SHALL clearly show whether a result can be ingested and what supporting links are available.

#### Scenario: Remote result has PDF or source URL
- **WHEN** a remote paper result includes `pdf_url` or `source_url`
- **THEN** the card exposes open PDF/source actions before the user ingests it.

#### Scenario: Target collection is selected
- **WHEN** a user has selected an ingest target collection
- **THEN** the card action makes clear that the paper will be added to the library and that collection.

### Requirement: Empty External Results Give Next Steps
External search empty states SHALL explain likely causes and actionable next steps.

#### Scenario: Remote search returns no items
- **WHEN** an external search returns no papers
- **THEN** the page suggests changing provider, relaxing year filters, retrying another batch, or checking maintenance/search diagnostics.
