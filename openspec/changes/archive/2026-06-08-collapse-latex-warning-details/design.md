## Overview

Update only the frontend diagnostic presentation. The backend response shape stays unchanged.

## Frontend

- Preserve top-level warning count tags.
- Render errors directly because they block or degrade compilation.
- Render warning lists inside a collapsed `Collapse` item labeled with the warning count.
- Keep compile logs collapsed separately.

## Risks

- Users may miss warnings if they do not expand the panel. The count remains visible in the header, so the existence of warnings is still clear.
