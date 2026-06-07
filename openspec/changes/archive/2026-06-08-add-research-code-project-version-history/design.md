## Context

`research_ideas.generated_code_project` stores the latest structured project manifest, and `generated_code` stores a representative legacy string. Re-generation updates those fields in place. The current frontend can browse the latest package, but it cannot show previous versions or compare file changes.

Version history needs a durable backend representation because the UI should not rely on the latest manifest containing embedded history. A separate version table keeps the latest-field compatibility while enabling list/detail/compare endpoints.

## Goals / Non-Goals

**Goals:**
- Store a version snapshot every time structured code generation succeeds.
- Assign monotonically increasing version numbers per Idea.
- Keep `generated_code_project` as the latest manifest.
- Provide list, detail, and compare APIs for authorized Idea owners.
- Show version history and file-level diff summaries in the existing project browser.
- Keep comparison lightweight and dependency-free.

**Non-Goals:**
- Add Git integration or real repository commits.
- Execute generated code or run tests in containers.
- Add full syntax-aware diff editing.
- Migrate legacy `generated_code` strings into synthetic versions automatically.

## Decisions

### 1. Store versions in a dedicated table

Create `research_code_project_versions` with `idea_id`, `version`, `project_manifest`, `representative_code`, `summary`, and timestamps. This avoids bloating `research_ideas` and gives the API direct version queries.

Alternative considered: append a `versions` array into `generated_code_project`. Rejected because it would grow a hot JSON field and make version list/detail queries awkward.

### 2. Snapshot after normalization

Versions will persist the normalized and validated manifest, not raw LLM output. That keeps history safe, bounded, and aligned with downloadable ZIP contents.

Alternative considered: persist raw provider output for audit. Rejected for this change because raw output may include malformed or unsafe files and creates privacy/storage concerns.

### 3. Compare by safe file path

The compare API will map each version's files by `path` and return file statuses: `added`, `removed`, `modified`, or `unchanged`. Modified files include line counts and a compact unified diff string generated with Python standard library `difflib`.

Alternative considered: use an external diff library. Rejected because `difflib` is sufficient and avoids adding dependencies.

### 4. Version switching is read-only

Selecting an older version in the UI changes the browser preview, but does not mutate `generated_code_project`. The latest package remains the active/current generated project for downloads unless a version-specific download endpoint is added later.

Alternative considered: let users restore an old version as current. Rejected for this first slice because restore semantics should be explicit and may affect downstream experiment records.

## Risks / Trade-offs

- [Risk] Version snapshots increase storage. -> Mitigation: generated packages are already bounded; store only normalized manifests.
- [Risk] Large diffs can be noisy. -> Mitigation: provide file-level summary first and a compact diff preview only for selected/modified files.
- [Risk] Existing Ideas may have a latest package but no version rows. -> Mitigation: API returns an empty history; future regeneration creates version 1 without breaking latest display.
