## Context

The old implementation combined two experimental directions:

- High-fidelity table repair through a Marker adapter and async maintenance action.
- Visual asset extraction through PDF page rendering, asset metadata, image routes, visual evidence cards, and optional summaries.

Both paths added significant runtime and UI surface area. The table repair path is not viable in the current local environment because Marker is OOM-killed even on small runs. The visual asset path is being discarded by product direction so the next implementation can be redesigned cleanly.

## Goals / Non-Goals

**Goals:**

- Remove old feature code and UI affordances so users no longer see unusable actions.
- Remove Marker-specific runtime dependencies/configuration from the project.
- Remove visual asset runtime dependencies/configuration and response fields.
- Keep normal paper ingestion, PDF proxying, text extraction, structured parsing, table quality metadata, and paper chat intact.
- Leave archived OpenSpec history alone, but remove active/in-progress specs and changes for discarded capabilities.

**Non-Goals:**

- Do not rewrite the replacement table/visual strategy in this change.
- Do not purge existing database metadata or uploaded image files.
- Do not remove general PyMuPDF/fitz usage that predates or supports unrelated PDF text workflows unless it is exclusively visual-asset runtime.

## Decisions

1. **Remove user-facing actions first.**
   - Maintenance recommendations and paper detail quick actions will no longer advertise table repair or visual asset extraction.
   - This prevents users from triggering dead runtime paths during the removal.

2. **Delete discarded runtime modules and adapters.**
   - `parse_tables_marker.py`, `requirements-marker.txt`, Marker Docker installation/config, visual asset service, and dedicated visual routes are removed.

3. **Preserve neutral metadata handling where harmless.**
   - Existing papers may contain historical metadata keys. The removal will ignore those keys rather than migrating the database.

4. **Prune active OpenSpec contracts.**
   - Specs that require visual assets or table repair must be removed or modified so the active contract reflects the reset baseline.

## Risks / Trade-offs

- [Risk] Tests that assert visual/table repair behavior will fail after removal. -> Remove or rewrite those assertions to match the reset baseline.
- [Risk] Some historical UI references may remain in archived OpenSpec files. -> Leave archive unchanged because it is historical, not active product contract.
- [Risk] Existing metadata may still reference old visual assets. -> Do not surface those references in active APIs/UI.
