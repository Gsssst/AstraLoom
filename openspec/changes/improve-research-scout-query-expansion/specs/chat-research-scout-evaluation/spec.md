## MODIFIED Requirements

### Requirement: Research Scout handles multilingual paper discovery prompts
Research Scout SHALL use an LLM query planner to expand Chinese or mixed-language paper discovery prompts before building candidate cards, with deterministic fallback when planning fails.

#### Scenario: Chinese prompt uses English technical keyword
- **WHEN** the user asks "请帮我找10篇关于多模态大模型memory的论文"
- **THEN** Research Scout first asks the LLM to produce English scholarly query variants for multimodal large language model memory
- **AND** uses fallback query variants if the LLM planner fails
- **AND** returns candidate card metadata when providers return related papers
- **AND** does not answer only with suggested search keywords unless all planned scholarly searches return no candidates.
