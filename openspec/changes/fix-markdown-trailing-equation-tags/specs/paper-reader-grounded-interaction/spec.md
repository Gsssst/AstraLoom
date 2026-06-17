## ADDED Requirements

### Requirement: Plain trailing display equation numbers render as separated tags
Markdown-rendered paper-chat display formulas SHALL convert a plain numeric label at the end of a display equation into a KaTeX equation tag before rendering. Tagged display equations SHALL reserve visible space for the equation number so it remains separated from the formula body. The renderer SHALL preserve inline math, fenced code blocks, and display equations that already use KaTeX tag syntax.

#### Scenario: Assistant output ends display math with a plain number label
- **WHEN** an assistant answer contains a display equation whose final non-whitespace token is `(3)`
- **THEN** the rendered formula uses KaTeX tag semantics for equation number `3`
- **AND** the equation number remains visually separated from the formula body.

#### Scenario: Existing KaTeX tag is preserved
- **WHEN** an assistant answer contains a display equation with `\tag{3}`
- **THEN** the renderer does not add another tag or alter the existing tag.

#### Scenario: Non-display contexts are preserved
- **WHEN** prose, inline math, or a fenced code block contains text ending in `(3)`
- **THEN** the renderer leaves that content unchanged.
