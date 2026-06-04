## ADDED Requirements

### Requirement: Selector agent chooses reading strategy

The Selector agent SHALL analyze the research topic and available papers to determine a reading strategy. The strategy SHALL specify: which papers to read in depth (full text) vs. skim (abstract only), reading order (by year, by relevance, or by citation graph), and which paper sections are most relevant (method, results, discussion).

#### Scenario: Reading strategy for a broad topic

- **WHEN** topic is "Transformer architectures for NLP" and 10 papers are available
- **THEN** Selector SHALL categorize papers into 2-3 thematic groups
- **AND** SHALL designate the most cited 3 papers for full-text reading
- **AND** SHALL designate remaining 7 papers for abstract-only skimming

### Requirement: Reader agent extracts structured information

The Reader agent SHALL read assigned papers and extract structured information into a shared working memory. For each paper, the Reader SHALL extract: core problem addressed, proposed method (2-3 sentence summary), key results/claims, relationship to other papers in the set, and direct quotes suitable for citation.

#### Scenario: Reader extracts from full-text paper

- **WHEN** Reader processes a paper with full text available
- **THEN** it SHALL extract information from abstract, method section, and results section
- **AND** SHALL store extracted information in structured JSON format in working memory
- **AND** SHALL note any contradictions or complementary approaches with other papers in the set

#### Scenario: Reader falls back to abstract-only

- **WHEN** a paper has no full text available
- **THEN** Reader SHALL extract information from abstract and title only
- **AND** SHALL mark the extracted information with "abstract_only" flag

### Requirement: Writer agent generates Related Work with paper relationships

The Writer agent SHALL generate Related Work text based on the Reader's working memory. The generated text SHALL: group papers by technical approach (2-3 groups), describe each paper's method and its relationship to the research topic, explicitly note limitations/gaps in each group, use numeric citations [1][2] consistently, and end with a summary of open problems.

#### Scenario: Generate Related Work with method-based grouping

- **WHEN** working memory contains 5 papers on model compression (2 on distillation, 2 on pruning, 1 on quantization)
- **THEN** Writer SHALL group them into "Distillation Methods", "Pruning Methods", and "Other Approaches"
- **AND** each group SHALL be one paragraph with 2-3 sentences per paper
- **AND** the last paragraph SHALL summarize gaps across all groups

### Requirement: Citation consistency and verification in output

The Writer SHALL use only papers from the Reader's working memory for citations (no hallucinated references). All citations SHALL use the [N] format matching the paper index. After generation, the Citation agent SHALL verify every [N] reference maps to an actual paper in the working memory.

#### Scenario: All citations map to real papers

- **WHEN** Writer generates text with citations [1], [2], [3]
- **THEN** Citation agent SHALL confirm that papers at indices 1, 2, and 3 exist in working memory
- **AND** SHALL flag any citation with no matching paper as an error

### Requirement: Graph-aware paper relationship mapping

The system SHALL build a relationship graph between papers in the working set. Relationships SHALL include: "cites" (paper A cites paper B), "extends" (paper A builds on paper B), "contrasts" (paper A proposes alternative to paper B), and "contemporary" (same year, similar venue). The relationship graph SHALL be used by both Selector (for reading order) and Writer (for narrative structure).

#### Scenario: Build paper relationship graph

- **WHEN** 5 papers are in the working set
- **AND** paper B cites paper A, paper C extends paper B
- **THEN** the graph SHALL include edges: B→A (cites), C→B (extends)
- **AND** Writer SHALL present them in chronological/narrative order: A, then B, then C
