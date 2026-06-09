## Why

AstraLoom can mark important papers and generate research ideas from evidence, but it does not preserve reusable method knowledge from papers. When a paper uses an algorithm, model, dataset, metric, or experimental tool, users need a dedicated place to capture that tool and later use it as inspiration or a constraint during idea generation.

## What Changes

- Add an independent research Toolbox space for reusable tools, algorithms, datasets, metrics, and experimental methods.
- Let users associate toolbox entries with source papers and concise evidence notes.
- Add toolbox selection to the research idea workbench so selected tools can guide candidate generation.
- Keep the first version manual and inspectable; AI extraction can be added later without changing the core data model.

## Capabilities

### New Capabilities
- `research-toolbox`: Users can create, browse, edit, and reuse structured research tools.

### Modified Capabilities
- `paper-api`: Papers can be linked to toolbox entries as source evidence.
- `research-idea-workbench`: Idea generation can use selected toolbox entries as generation context.

## Impact

- Backend database models and Alembic migration.
- Backend toolbox CRUD/link APIs.
- Frontend navigation and Toolbox page.
- Paper detail/library integration points for linking tools.
- Research project idea generation request payload and prompt/context assembly.
- Focused backend/frontend contract tests.
