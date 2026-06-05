# paper-collections-to-research-seeds

## Why

Users need a manual way to organize papers around a topic before generating research ideas. The current library has saved papers, reading status, tags, and an old folder shell, but there is no practical user-named collection that can be reused as a seed set when creating a research direction.

## What Changes

- Add user-owned paper collections with custom names and optional descriptions.
- Allow users to add/remove saved papers from collections and list papers in a collection.
- Add collection filtering to the paper library.
- Add a research-direction creation shortcut that imports all papers from selected collections as seed papers.

## Non-Goals

- Shared team collections.
- Nested collection trees.
- Automatic LLM clustering of collections.
- Replacing AI-generated tags.

## Reference Patterns

- Reference managers such as Zotero organize papers through user-defined collections and allow one paper to appear in multiple collections.
- Research assistants that support project-level grounding usually let users define an explicit paper set before running idea generation.

## Success Criteria

- Authenticated users can create/delete collections and add/remove their own saved papers.
- The paper library can show a selected collection and add selected papers to a collection.
- The research direction creation modal can select collections and automatically include their paper IDs.
- Backend and frontend contract tests cover the collection-to-research seed flow.
