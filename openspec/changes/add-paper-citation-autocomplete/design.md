## Overview

Implement citation autocomplete as a frontend enhancement using the evidence cards already loaded for the selected writing project. This avoids a new backend endpoint and keeps suggestions in sync with the visible evidence rail.

## Frontend

- Map evidence cards to citation suggestions:
  - `key`: current `citation_marker` such as `[1]`;
  - `title`;
  - `authors`;
  - `year`;
  - `local_status_label`.
- Detect citation context with a regex ending at the cursor, e.g. `\\cite...{partial`.
- Show a compact suggestion list labeled "论文库引用".
- Filter by marker, title, authors, year, and arXiv id.
- Replace only the text inside the current cite braces from the opening brace to the cursor.
- Keep generic command suggestions for command prefixes outside citation braces.

## Limits

- This version inserts the existing project citation marker because the current citation checker resolves markers like `[1]`.
- A later BibTeX-focused change can introduce stable BibTeX keys and export `.bib` entries.
