## ADDED Requirements

### Requirement: Preserve LaTeX commands during text processing

The system SHALL detect and protect LaTeX commands, math environments, citations, cross-references, and floating environments during text polishing and translation. Protected blocks SHALL be passed through unchanged while surrounding text is processed.

#### Scenario: Polish text with inline math

- **WHEN** input text contains "The loss function $\mathcal{L}(x) = -\log p(x)$ is minimized"
- **THEN** the LaTeX block "$\mathcal{L}(x) = -\log p(x)$" SHALL appear unchanged in output
- **AND** surrounding English text SHALL be polished for grammar and style

#### Scenario: Translate text with citations

- **WHEN** input contains "As shown in \cite{vaswani2017attention}, the transformer architecture..."
- **THEN** the `\cite{vaswani2017attention}` command SHALL be preserved as-is
- **AND** the surrounding text SHALL be translated

### Requirement: LaTeX environment protection

The system SHALL recognize and protect these LaTeX environments during processing: `figure`, `table`, `equation`, `equation*`, `align`, `align*`, `algorithm`, `tabular`, `itemize`, `enumerate`. Content within these environments SHALL NOT be modified by text polishing.

#### Scenario: Polish text containing a table environment

- **WHEN** input text contains `\begin{table}...\end{table}` with tabular data
- **THEN** the entire table environment SHALL be preserved unchanged
- **AND** text before and after the table SHALL be polished normally

### Requirement: LaTeX project import

The system SHALL accept `.tex` file uploads and extract: the document structure (sections, subsections), text content separated from LaTeX markup, bibliography entries from `.bib` files, and figure/table references. Imported projects SHALL be stored as `WritingProject` with auto-detected sections.

#### Scenario: Import ACL-formatted paper

- **WHEN** user uploads a `.tex` file with `\section{Introduction}`, `\section{Related Work}`, `\section{Method}`
- **THEN** the system SHALL create a WritingProject with three sections matching the LaTeX structure
- **AND** extract bibliography from any linked `.bib` file

### Requirement: LaTeX compilation check

The system SHALL provide an optional LaTeX compilation check that runs `pdflatex` or `xelatex` in a sandboxed environment. The check SHALL report compilation errors with line numbers and suggest fixes. The system SHALL support up to 3 automatic retries with common fixes (missing packages, undefined references on first pass).

#### Scenario: Detect and report compilation error

- **WHEN** LaTeX compilation fails with "Undefined control sequence \xyz"
- **THEN** the system SHALL report the error with file name and line number
- **AND** SHALL suggest "Check if \xyz is defined or if a package is missing"

#### Scenario: Auto-fix common compilation issues

- **WHEN** first compilation fails with "undefined references" (common on first pass)
- **THEN** the system SHALL re-run pdflatex automatically
- **AND** SHALL succeed on the second pass
