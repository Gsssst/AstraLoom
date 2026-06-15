## Context

The chat module already supports normal conversation, local RAG, web enhancement, image attachments, and thinking streams. The paper library already has resilient scholarly search across arXiv, Semantic Scholar, OpenAlex, and optional Google Scholar, plus personal paper ingestion. What is missing is a task-specific chat state that uses these capabilities as a deliberate research-discovery workflow instead of generic evidence injection.

Open-source references shape the approach:
- GPT Researcher: expose a visible research plan, gather sources, and report sourced findings.
- STORM: encourage multiple angles and knowledge curation instead of single-query retrieval.
- DocsGPT: treat chat as a tool/file/knowledge interface rather than a plain prompt box.

## Goals / Non-Goals

**Goals:**
- Add an explicit Research Scout mode to chat without disrupting ordinary chat.
- Use existing scholarly discovery providers through `search_scholarly_papers(source="scholarly")`.
- Stream a discovery status, structured candidate metadata, and a concise recommendation answer.
- Make candidates actionable in the UI with provider/source links and clear rationale.
- Keep the first phase implementable without migrations or new external dependencies.

**Non-Goals:**
- Full agent tool execution framework with user-approved side effects.
- Word/PPT/image-generation workflows.
- Skill installation or marketplace support.
- Automatic ingestion of all recommended papers.
- Long-running background deep-research reports.

## Decisions

1. **Assistant mode is request-scoped, not a new session type.**
   - Add `assistant_mode: "general" | "research_scout"` to chat requests.
   - Rationale: users can switch modes without creating separate session tables or migration work.
   - Alternative considered: create a separate Research Scout page. Rejected for first phase because the user asked to upgrade the existing chat experience.

2. **Research Scout uses structured scholarly candidates plus prose.**
   - Backend returns candidate metadata in a `research_scout` stream meta payload and also injects a compact source context into the model.
   - Rationale: the UI can render reliable cards even if the prose varies, while the model still explains trade-offs naturally.
   - Alternative considered: ask the model to output JSON. Rejected because stream parsing and model reliability would be weaker.

3. **Discovery breadth comes from existing paper search service.**
   - Use `search_scholarly_papers(..., source="scholarly", max_results=...)` for provider diversity and deduplication.
   - Rationale: this reuses existing arXiv/Semantic Scholar/OpenAlex/Google Scholar behavior and avoids new provider complexity.

4. **Recommendation rationale is deterministic-first.**
   - Backend computes lightweight rationale fields from title/abstract/year/source before model generation.
   - Rationale: the candidate cards remain useful and testable even when the LLM answer is short or interrupted.

5. **First-stage actions route to existing workflows.**
   - Candidate cards expose source/PDF links and copy/search affordances; ingestion can reuse existing paper-library remote preview flow in a later task.
   - Rationale: no new write API is needed for first useful discovery mode.

6. **Candidate cards can now become library assets.**
   - Research Scout cards reuse `/papers/ingest-personal` with server-issued preview tokens to add one candidate to the user's paper library.
   - Rationale: the discovery loop should not end at a chat answer; useful papers must become searchable, classifiable library items.
   - Alternative considered: bulk-ingest every recommendation. Rejected because Research Scout should keep user-approved side effects explicit.

7. **Chat layout moves toward a workbench reading stream.**
   - Messages are centered with a constrained reading width, lighter assistant blocks, darker user prompts, and a persistent composer.
   - Rationale: Codex/Claude Code style interfaces work because the answer is treated as a work artifact, not a decorative bubble feed.

## Risks / Trade-offs

- **Search quality depends on upstream provider availability** → Degrade with a clear status and still answer from any returned candidates.
- **Candidate cards may trigger side effects** → Use one-click, single-paper ingestion only; never bulk-ingest without a user action.
- **Assistant mode can add UI complexity** → Keep mode choices small and visually explain what each mode does.
- **Model may overclaim novelty** → Prompt requires distinguishing "interesting" from "useful" and grounding claims in candidate metadata.
