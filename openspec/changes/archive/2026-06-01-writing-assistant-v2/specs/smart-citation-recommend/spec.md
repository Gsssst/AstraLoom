## ADDED Requirements

### Requirement: Context-aware citation position detection

The system SHALL analyze the user's writing text to identify positions where citations are needed, based on claim statements, methodology descriptions, and comparative assertions. Each identified position SHALL include the surrounding context sentence and a reason for the citation suggestion.

#### Scenario: Detect citation positions in a paragraph

- **WHEN** user submits text "Recent work has shown that transformer models can be effectively distilled into smaller architectures while preserving performance."
- **THEN** the system SHALL identify "transformer models can be effectively distilled" as a claim requiring citation
- **AND** SHALL provide the surrounding sentence as context

#### Scenario: No citation needed for original claims

- **WHEN** user submits text "We propose a novel approach to this problem."
- **THEN** the system SHALL NOT flag "We propose" statements as requiring citations
- **AND** SHALL only flag factual claims, comparisons, and methodology references

### Requirement: Multi-source paper retrieval for citation

The system SHALL search multiple sources for each citation position: local knowledge base (pgvector), Semantic Scholar API, and arXiv API. Results SHALL be merged and deduplicated, with local papers prioritized when similarity scores are comparable (within 0.05 difference).

#### Scenario: Local paper matches take priority

- **WHEN** both local knowledge base and Semantic Scholar return relevant papers for a citation position
- **AND** the local paper similarity score is within 0.05 of the remote result
- **THEN** the local paper SHALL be ranked higher in the recommendation list

#### Scenario: Fallback to remote sources when local has no match

- **WHEN** local knowledge base returns no results above similarity threshold 0.5
- **THEN** the system SHALL use Semantic Scholar and arXiv results
- **AND** SHALL mark these results as "remote" source

### Requirement: Citation suggestion includes positioning advice

The system SHALL return each citation recommendation with: the paper metadata (title, authors, year, abstract snippet), relevance score, source (local/remote), BibTeX entry, and a positioning hint indicating which sentence or claim the citation supports.

#### Scenario: Complete citation recommendation

- **WHEN** a citation position is identified at "transformer distillation techniques"
- **THEN** the response SHALL include at least one paper recommendation with positioning hint "Supports claim about transformer distillation effectiveness"
- **AND** each recommendation SHALL include title, authors, year, similarity score, and BibTeX entry
