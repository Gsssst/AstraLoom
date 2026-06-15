## Context

The reported screenshots show a prompt asking for CVPR 2025/2026 video grounding papers, but the answer behaves like ordinary chat: it claims it cannot verify conference lists, shows generic Bing RSS pages about unrelated topics, and does not display Research Scout cards, import actions, or AI scoring. The exported chat file similarly contains a plain Markdown list rather than structured candidates.

Existing code confirms two root causes:

- The backend appends ordinary RAG/web context before Research Scout context, so generic web references can be emitted even for scout mode.
- The frontend only sends `assistant_mode: research_scout` when the visible mode selector is set, so paper-search prompts can stay in ordinary chat.

The stream-scroll hook already exists, but token updates still call the bottom-follow effect on every message change; the hook should more aggressively classify user wheel/touch/scroll-up intent and expose that behavior in tests.

## Goals / Non-Goals

**Goals:**
- Paper-finding prompts such as "找 10 篇 2025-2026 CVPR video grounding 论文" enter Research Scout automatically.
- Research Scout retrieves from scholarly sources (`arxiv_enriched`, Semantic Scholar/OpenAlex enrichment) and does not inject ordinary web search snippets.
- Research Scout metadata always reaches the frontend before/with the answer so candidate cards, import actions, classification actions, project actions, and evaluation scores are visible.
- Venue/year constraints appear in parsed intent and candidate constraint metadata even when provider venue evidence is incomplete.
- Generic web reference strips are not shown for scout-mode answers.
- User upward scrolling during streaming pauses bottom-following until the user returns near the bottom.

**Non-Goals:**
- Full CVF/OpenAccess scraping.
- Guaranteeing CVPR 2026 accepted-paper completeness before the official list is available.
- Claim-level citation verification.
- Replacing heuristic scroll handling with a virtualized message list.

## Decisions

1. **Auto-detect paper discovery intent on the frontend and backend.**
   - Frontend switches the outgoing request to Research Scout when the prompt clearly asks to find/list/recommend papers.
   - Backend repeats this detection for robustness, so API callers get the same behavior.

2. **Research Scout bypasses ordinary web retrieval.**
   - In scout mode, `_append_retrieval_context` is not called with `web_search_enabled=True`.
   - Optional local RAG may still be used for library relation, but displayed references are scout candidates only unless upload visual refs exist.

3. **Candidate cards are a required output surface, not a bonus.**
   - Stream metadata carries `research_scout.candidates` even if the answer text is terse.
   - Empty candidate state must explain that scholarly discovery returned no papers instead of falling back to generic sites.

4. **Venue and year constraints stay explicit.**
   - Intent parsing extracts years and venue aliases such as CVPR.
   - Constraint metadata shows matched/unknown state to help users understand evidence limitations.

5. **Source strip wording is mode-aware.**
   - Scout answers use "论文候选来源" and only list scout references.
   - Ordinary chat keeps "检索来源" for non-scout retrieval.

6. **Scroll intent wins over stream updates.**
   - The auto-scroll hook pauses on wheel-up, touch-up, PageUp/Home-like key navigation, and scroll position moving away from the bottom.
   - It resumes only when the user scrolls back within the bottom threshold or a new send starts.

## Risks / Trade-offs

- **False-positive auto-routing**: Some ordinary questions mention papers. Mitigate with trigger words requiring find/list/recommend/count-style paper discovery intent.
- **Scout returns fewer items than generic web**: Prefer fewer scholarly candidates over unrelated web pages.
- **Venue evidence unavailable**: Keep `unknown` constraints visible instead of inventing CVPR membership.
- **Scroll hook complexity**: Keep logic contained in `useChatAutoScroll` and cover with contract tests.
