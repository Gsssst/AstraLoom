## ADDED Requirements

### Requirement: Local paper status strip shows local readiness
The paper library SHALL show local readiness status chips in local/library views and SHALL reserve remote importability chips for remote search-backed result views.

#### Scenario: User views local paper library
- **WHEN** the user views local, saved, collection, reading, or maintenance-backed paper lists
- **THEN** the status strip SHALL show counts for loaded papers, full text readiness, vector readiness, visual evidence readiness, and open PDF availability
- **AND** it SHALL NOT show import-only labels such as "可入库", "本次已加入", or "缺远程 ID".

#### Scenario: User views remote search results
- **WHEN** the user views scholarly, arXiv, Semantic Scholar, OpenAlex, or Google Scholar search results
- **THEN** the status strip SHALL continue to show importability labels including local match, importable, newly imported, open PDF, and missing remote ID.
