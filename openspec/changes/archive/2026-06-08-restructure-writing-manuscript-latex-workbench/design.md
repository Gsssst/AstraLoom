## Context

The project already has:
- Writing projects and sections stored in `WritingProject` / `WritingSection`.
- LaTeX import/export and `LatexProcessor.compile_check`.
- Section-level evidence cards, citation checks, claim safety checks, quality checks, and export readiness.
- A paper writing UI that still exposes one-off tools as top-level tabs and includes a survey draft creation card inside the paper project workbench.

The desired model is closer to a manuscript editor:

```text
Manuscript
├─ Section list
├─ Current section LaTeX source
├─ Preview / compile diagnostics
└─ AI section assistant
```

Survey/literature-review generation is still useful, but it is a different workflow from writing a paper section by section.

## Goals / Non-Goals

**Goals:**
- Make manuscript writing chapter-first.
- Store/edit each section as LaTeX body source.
- Add compile/preview diagnostics for a section and the assembled manuscript.
- Provide a section-scoped AI assistant panel that uses current section, proposal brief, evidence cards, and safety diagnostics as context.
- Move survey creation out of the manuscript workbench.
- Reduce template prominence in the main writing path.

**Non-Goals:**
- Do not replace the database schema in this change.
- Do not implement collaborative editing.
- Do not guarantee official conference formatting.
- Do not require a new LaTeX compiler dependency beyond the existing `pdflatex`-based check path.
- Do not remove existing APIs used by other pages.

## Decisions

1. **Use `WritingSection.content` as LaTeX body source.**
   - Rationale: the existing model already persists per-section content and export can assemble it into a document.
   - Alternative: add separate `latex_source` columns. That would require migration and is unnecessary for the first version.

2. **Compile checks wrap sections in a minimal article document.**
   - Rationale: section body source is not a complete `.tex` file. Wrapping allows section-level syntax checks without requiring a full manuscript.
   - Alternative: only compile the full document. That makes it harder to fix the section the user is editing.

3. **Preview means compile diagnostics first, rendered source preview second.**
   - Rationale: the current backend can check LaTeX compile status. Browser PDF rendering can be added later.
   - Alternative: build full PDF preview now. That is higher risk and depends on runtime compiler/PDF plumbing.

4. **AI assistant is a panel bound to current section.**
   - Rationale: AI actions need the section role, current LaTeX, evidence cards, proposal brief, and citation diagnostics.
   - Alternative: keep AI tools as top-level tabs. That is the current problem and loses context.

5. **Survey is a separate mode.**
   - Rationale: survey writing has different source material and output structure from manuscript chapters.

## Risks / Trade-offs

- Existing Markdown-like section content may be treated as LaTeX body source -> keep export tolerant and label it as source editing.
- `pdflatex` may not be installed in some deployments -> surface the existing “compiler not installed” error as a preview diagnostic.
- AI assistant actions may initially be prompt scaffolds rather than fully autonomous rewrites -> keep first version explicit and section-scoped.
