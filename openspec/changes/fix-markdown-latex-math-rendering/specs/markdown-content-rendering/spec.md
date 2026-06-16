## ADDED Requirements

### Requirement: Shared Markdown renders LaTeX math
The shared Markdown renderer SHALL parse and render standard LaTeX inline and display math in AI-facing content using the existing KaTeX presentation layer.

#### Scenario: Display math in an AI answer
- **WHEN** an assistant message contains display math delimited as `$$...$$` or `\[...\]`
- **THEN** the Markdown renderer displays it as formatted math instead of raw delimiter text

#### Scenario: Inline math in an AI answer
- **WHEN** an assistant message contains inline math delimited as `$...$`
- **THEN** the Markdown renderer displays the expression inline without turning it into a code span or plain text

### Requirement: Shared Markdown tolerates bracketed LaTeX blocks
The shared Markdown renderer SHALL normalize obvious whole-line bracketed LaTeX formula blocks into display math before rendering, while preserving citations and ordinary bracketed text.

#### Scenario: Model emits bracketed formula text
- **WHEN** an assistant message contains a standalone line like `[ \tilde{W}_Q = U_Q V_Q ]`
- **THEN** the Markdown renderer treats that line as display math

#### Scenario: Message contains citations
- **WHEN** an assistant message contains citations such as `[E1]` or ordinary Markdown links
- **THEN** the Markdown renderer preserves them as ordinary Markdown content
