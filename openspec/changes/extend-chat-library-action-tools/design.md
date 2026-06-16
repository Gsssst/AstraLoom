## Context

General chat already has a shared `ChatToolRegistry`, typed Pydantic tool schemas, bounded runtime execution, a planner loop, and a confirmation token path for `import_paper`. The next Stage 2 step is not to add a new agent framework, but to make the existing runtime useful for concrete library actions.

Mature projects point in the same direction: LangChain/LangGraph model tools as validated callable components inside controlled workflows, while LibreChat and Open WebUI expose tool/function availability as chat capabilities. This project already has the right local primitive, so this change extends the registered tools rather than introducing a parallel tool system.

## Goals / Non-Goals

**Goals:**

- Register `read_pdf`, `add_to_folder`, and `create_research_project` in the generic chat tool registry.
- Keep `read_pdf` read-only and bounded to local papers the current user can access through the existing paper library.
- Keep `add_to_folder` and `create_research_project` behind exact confirmation tokens.
- Return structured references/context so final chat answers can cite what the tool observed.
- Let deterministic fallback route obvious prompts for these tools when force mode is enabled or planner output is invalid.
- Extend frontend confirmation handling for multiple side-effect tools.

**Non-Goals:**

- A tool marketplace or per-tool permission UI.
- New database tables or migrations.
- Arbitrary file-system PDF parsing from chat uploads.
- Automatic unconfirmed mutation of folders or research projects.
- Replacing Research Scout card actions.

## Decisions

### Decision: Reuse `ChatToolRegistry`

The new tools will be registered next to `search_papers`, `search_library`, and `import_paper`.

Rationale: the registry already provides typed schemas, trace events, bounded execution, side-effect gating, and frontend-visible tool metadata.

### Decision: Implement `read_pdf` from local stored paper evidence

`read_pdf` accepts a local `paper_id`, optional `query`, and small `top_k`. It loads the paper through SQLAlchemy, prefers `PaperChunkService.retrieve_chunks` when full text exists, and falls back to abstract/title metadata.

Rationale: this avoids new PDF extraction dependencies and respects the current ingestion/full-text pipeline.

### Decision: Treat organization tools as side effects

`add_to_folder` and `create_research_project` are registered with `side_effect=True`, so the first planner pass returns `waiting_confirmation` with normalized arguments and a confirmation token.

Rationale: adding papers to folders or projects mutates user state and must not happen from autonomous model planning alone.

### Decision: Keep arguments local and explicit

Organization tools operate on existing local `paper_id` values. If the model only has a remote paper candidate, it must first use `import_paper` and receive confirmation before adding it elsewhere.

Rationale: this prevents ambiguity around remote IDs and avoids creating hidden imports as a side effect of organization requests.

### Decision: Frontend confirmation is generic by tool

The existing trace UI will render confirmation buttons for supported side-effect tools with tool-specific labels rather than hard-coding only `import_paper`.

Rationale: this preserves the same user workflow while allowing new confirmed tools.

## Risks / Trade-offs

- **Planner may not know exact local IDs** -> Encourage `search_library` before organization actions and reject invalid IDs with clear observations.
- **`read_pdf` may only have abstract-level evidence** -> Return an explicit coverage label and avoid pretending full text was read.
- **Confirmation UI could become crowded** -> Only render action buttons on waiting-confirmation steps and keep labels concise.
- **Creating projects from vague prompts could produce poor names** -> Require a non-empty project title and allow optional description/keywords, with confirmation before creation.
