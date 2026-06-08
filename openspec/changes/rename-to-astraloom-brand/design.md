## Context

The existing home page uses a generic animated technology hero and the old `Auto-Research-DS` name. The new name `AstraLoom` suggests a clearer product metaphor: stars/constellations for discovery and loom/weaving for connecting papers, evidence, ideas, experiments, and manuscripts.

## Goals / Non-Goals

**Goals:**
- Replace active product naming with `AstraLoom`.
- Make the first viewport immediately communicate the new brand and core workflow.
- Keep the home page usable, not just decorative: search and module entry points remain available.
- Preserve route behavior, backend contracts, and existing user workflows.

**Non-Goals:**
- Rename repository folder, Docker service names, package names, or historical archived change text.
- Introduce new backend features or data migrations.
- Add new image-generation dependencies.

## Decisions

- Use a code-native front-end visual instead of external bitmap assets so the brand page stays self-contained and fast.
- Build the hero around a constellation/loom stage with nodes and connecting threads that map to the app modules.
- Use `AstraLoom` consistently in current user-facing copy and runtime metadata.
- Update current docs and project overview, while leaving archived OpenSpec historical records intact.

## Risks / Trade-offs

- Some archived references to the old name will remain because they document past changes. This avoids rewriting historical artifacts.
- A more branded home page can become too decorative if not restrained. The design keeps search and workflow entries in the first viewport.
