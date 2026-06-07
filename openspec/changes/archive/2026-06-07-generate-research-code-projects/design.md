## Context

Research Ideas currently store generated implementation output in `research_ideas.generated_code`, a single text field produced by one prompt and rendered in a single code block. That does not match how experimental research code is normally structured: a Proposal needs reproducible setup, baseline/proposed/ablation entrypoints, evaluation scripts, result analysis, and notes that connect code back to the hypothesis and evidence.

Similar projects provide a useful direction. AI-Scientist uses template folders and run directories around experiment scripts, plotting, notes, and LaTeX/report assets. AI-Scientist v2 and CodeScientist also treat code as an experiment workspace with generated files, logs, reports, and iteration artifacts. This change applies the same shape without adding automatic execution.

## Goals / Non-Goals

**Goals:**
- Generate a structured experiment project package for each Proposal.
- Persist the package as a validated manifest with multiple files and metadata.
- Provide a zip download endpoint without writing generated files into the repository.
- Replace the frontend's single-code-block display with file browsing, preview, run commands, and download.
- Preserve backward compatibility for existing `generated_code` values.

**Non-Goals:**
- Automatically execute generated code.
- Provision containers, GPUs, datasets, or dependency installs.
- Guarantee scientific correctness of generated experiments.
- Replace the existing experiment feedback and execution-pack flows.
- Store generated package files on disk as source-controlled project files.

## Decisions

- **Store a JSON manifest on `ResearchIdea`.** Add `generated_code_project` JSON alongside legacy `generated_code`. This avoids a new table for a per-Idea artifact while keeping the manifest structured and migratable.
- **Use a deterministic project schema.** The backend expects `name`, `framework`, `summary`, `setup`, `run_commands`, `entrypoints`, `safety_notes`, and `files`. Each file has `path`, `language`, `purpose`, and `content`.
- **Ask the LLM for JSON, then repair/fallback.** The generator requests strict JSON. If parsing fails or required files are missing, the backend builds a conservative fallback project from the Proposal's experiment plan so the endpoint remains useful.
- **Keep legacy code populated.** The primary Python entrypoint is copied into `generated_code` for old UI/API compatibility, but the new UI consumes `generated_code_project`.
- **Generate zip in memory.** The download endpoint authorizes the Idea, sanitizes manifest file paths, creates a zip archive in memory, and streams it to the browser.
- **Do not execute artifacts.** The UI and API label generated projects as reviewable artifacts and provide commands for the user to run locally.

## Risks / Trade-offs

- Generated manifests can become large -> cap file count and per-file content size during normalization.
- LLM output may be malformed -> parse strict JSON first, extract JSON from fenced blocks, then fallback to deterministic templates.
- Zip path traversal risk -> reject absolute paths, parent traversal, empty paths, and control characters before archiving.
- Existing Ideas have only `generated_code` -> show legacy code when no project manifest exists, and let users regenerate a project package.
- A JSON column is less queryable than a normalized artifact table -> acceptable because packages are displayed by Idea and downloaded whole.

## Migration Plan

- Add nullable `generated_code_project` JSON column to `research_ideas`.
- Deploy backend code that can read both legacy code and new project manifests.
- Update frontend to prefer `generated_code_project` and fall back to `generated_code`.
- Rollback can drop the new column after ensuring no generated package data needs to be preserved.
