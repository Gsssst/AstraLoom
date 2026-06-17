## ADDED Requirements

### Requirement: Broad Visual Result Coverage
Paper-page AI Q&A SHALL use catalog-style visual evidence coverage for questions asking whether a paper has visual results, which figures exist, qualitative cases, or what visualizations support.

#### Scenario: User asks for visual results across the paper
- **WHEN** the user asks a broad visual question such as "论文中有没有可视化结果？这些结果支持了什么结论？"
- **THEN** retrieved current-paper evidence includes a compact page-aware catalog of available figure, image, chart, plot, diagram, and qualitative-case evidence before general text fallback
- **AND** the answer context instructs the model to distinguish between visual metadata/captions that were retrieved and image pixels that were attached for inspection.

#### Scenario: User asks about a specific figure
- **WHEN** the user asks about a specific figure number or a narrowly scoped chart/table
- **THEN** the system MAY use the targeted visual retrieval lane instead of the broad visual catalog lane.
