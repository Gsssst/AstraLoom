## Overview

This is a UX transparency layer over existing paper search and ingestion APIs. The backend already returns provider/source metadata for search results, and the frontend already supports target collections and remote ingestion.

## Frontend

Enhance `PapersPage.tsx`:

- Add provider guidance text for each external source mode.
- Add a compact external-search status banner when source is remote.
- Make result cards show whether the paper has open PDF, source URL, remote ID, and target collection.
- Improve empty states for remote search with concrete retry suggestions.
- After one-click ingest, refresh collections and selected collection diagnostics when relevant.

## Testing

Extend paper library frontend contract tests to assert:

- provider transparency labels are present;
- remote cards expose open PDF/source/target collection status;
- empty-result guidance exists for external search.
