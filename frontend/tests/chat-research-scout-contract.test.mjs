import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

const chatPageSource = readFileSync(
  new URL('../src/pages/ChatPage.tsx', import.meta.url),
  'utf8',
);

const responsiveSource = readFileSync(
  new URL('../src/styles/responsive.css', import.meta.url),
  'utf8',
);

const backendChatSource = readFileSync(
  new URL('../../backend/app/api/chat_sessions.py', import.meta.url),
  'utf8',
);

const backendResearchSource = readFileSync(
  new URL('../../backend/app/api/research.py', import.meta.url),
  'utf8',
);

const backendPaperSearchSource = readFileSync(
  new URL('../../backend/app/services/paper_search.py', import.meta.url),
  'utf8',
);

test('chat page exposes Research Scout mode and sends assistant_mode', () => {
  assert.match(chatPageSource, /type ChatAssistantMode = 'general' \| 'research_scout'/);
  assert.match(chatPageSource, /chat-composer-mode-select/);
  assert.match(chatPageSource, /论文猎手/);
  assert.match(chatPageSource, /handleAssistantModeChange/);
  assert.match(chatPageSource, /isPaperDiscoveryPrompt/);
  assert.match(chatPageSource, /effectiveAssistantMode: ChatAssistantMode/);
  assert.match(chatPageSource, /assistant_mode: effectiveAssistantMode/);
  assert.match(chatPageSource, /effectiveWebSearch = effectiveAssistantMode === 'research_scout' \|\| webSearch/);
  assert.match(chatPageSource, /effectiveSearchDepth = effectiveAssistantMode === 'research_scout' \? 'deep' : searchDepth/);
  assert.match(chatPageSource, /已识别为找论文请求，正在启动论文猎手/);
  assert.match(chatPageSource, /论文猎手正在联网检索学术来源/);
  assert.match(chatPageSource, /已切换到论文猎手，并自动开启联网深度学术检索/);
});

test('chat page renders Research Scout candidate cards', () => {
  assert.match(chatPageSource, /interface ResearchScoutCandidate/);
  assert.match(chatPageSource, /research_scout/);
  assert.match(chatPageSource, /renderResearchScoutCards/);
  assert.match(chatPageSource, /research-scout-cards/);
  assert.match(chatPageSource, /论文猎手候选/);
  assert.match(chatPageSource, /继续分析/);
});

test('Research Scout cards support ingestion and follow-up search loops', () => {
  assert.match(chatPageSource, /handleResearchScoutIngest/);
  assert.match(chatPageSource, /ensureResearchScoutIngested/);
  assert.match(chatPageSource, /\/papers\/ingest-personal/);
  assert.match(chatPageSource, /remote_ingest_token: paper\.ingest_token/);
  assert.match(chatPageSource, /加入论文库/);
  assert.match(chatPageSource, /\['baseline', 'survey', 'latest', 'counterexample'\]/);
  assert.match(chatPageSource, /continueScoutSearch/);
});

test('Research Scout cards display returned candidates progressively without six-card hard cap', () => {
  assert.match(chatPageSource, /RESEARCH_SCOUT_INITIAL_CARD_LIMIT = 10/);
  assert.match(chatPageSource, /expandedScoutMessages/);
  assert.match(chatPageSource, /visibleCandidates = expanded \? candidates : candidates\.slice\(0, RESEARCH_SCOUT_INITIAL_CARD_LIMIT\)/);
  assert.doesNotMatch(chatPageSource, /candidates\.slice\(0, 6\)/);
  assert.match(chatPageSource, /展开全部/);
  assert.match(chatPageSource, /收起候选/);
});

test('Research Scout metadata tags are bounded inside candidate cards', () => {
  assert.match(chatPageSource, /className="research-scout-meta-tag"/);
  assert.match(chatPageSource, /<Tooltip title=\{paper\.venue\}>/);
  assert.match(responsiveSource, /\.research-scout-meta \.ant-space-item/);
  assert.match(responsiveSource, /\.research-scout-meta \.ant-tag,\s*\.research-scout-meta-tag,\s*\.research-scout-provenance \.ant-tag,\s*\.research-scout-constraints \.ant-tag/);
  assert.match(responsiveSource, /max-width: min\(100%, 260px\);/);
  assert.match(responsiveSource, /white-space: nowrap;/);
  assert.match(responsiveSource, /\.research-scout-expand-row/);
});

test('chat renders tool execution trace metadata', () => {
  assert.match(chatPageSource, /interface ToolTracePayload/);
  assert.match(chatPageSource, /tool_trace\?: ToolTracePayload/);
  assert.match(chatPageSource, /toolTrace = event\.content\.tool_trace/);
  assert.match(chatPageSource, /renderToolTrace/);
  assert.match(chatPageSource, /工具执行轨迹/);
  assert.match(chatPageSource, /chat-tool-trace/);
  assert.match(chatPageSource, /toolTraceStatusLabel/);
  assert.match(responsiveSource, /\.chat-tool-trace/);
  assert.match(responsiveSource, /\.chat-tool-trace-step/);
});

test('chat tool execution traces are collapsed by default', () => {
  assert.match(chatPageSource, /expandedToolTraces/);
  assert.match(chatPageSource, /setExpandedToolTraces/);
  assert.match(chatPageSource, /chat-tool-trace-compact/);
  assert.match(chatPageSource, /chat-tool-trace-toggle/);
  assert.match(chatPageSource, /expanded && <div className="chat-tool-trace-steps">/);
  assert.match(chatPageSource, /展开/);
  assert.match(chatPageSource, /收起/);
  assert.match(responsiveSource, /\.chat-tool-trace-compact/);
  assert.match(responsiveSource, /\.chat-tool-trace-toggle/);
});

test('Research Scout cards can route candidates into collections and research projects', () => {
  assert.match(chatPageSource, /ResearchScoutIntent/);
  assert.match(chatPageSource, /renderResearchScoutIntent/);
  assert.match(chatPageSource, /检索意图拆解/);
  assert.match(chatPageSource, /paper\.caveat/);
  assert.match(chatPageSource, /paper\.library_relation/);
  assert.match(chatPageSource, /handleAddScoutToCollection/);
  assert.match(chatPageSource, /\/folders\/\$\{selectedCollectionId\}\/papers/);
  assert.match(chatPageSource, /handleAddScoutToProject/);
  assert.match(chatPageSource, /\/research\/projects\/\$\{selectedProjectId\}\/papers/);
  assert.match(chatPageSource, /加入研究方向素材池/);
});

test('Research Scout supports constraint-aware evaluation metadata', () => {
  assert.match(chatPageSource, /venues\?: string\[\]/);
  assert.match(chatPageSource, /institutions\?: string\[\]/);
  assert.match(chatPageSource, /authors\?: string\[\]/);
  assert.match(chatPageSource, /constraint_mode\?: 'hard' \| 'soft'/);
  assert.match(chatPageSource, /metadata_provenance\?: Record<string, string>/);
  assert.match(chatPageSource, /enrichment\?: \{/);
  assert.match(chatPageSource, /pdf_first_page_affiliations\?:/);
  assert.match(chatPageSource, /ResearchScoutEvaluationDimension/);
  assert.match(chatPageSource, /ResearchScoutConstraintMatch/);
  assert.match(chatPageSource, /renderResearchScoutEvaluation/);
  assert.match(chatPageSource, /renderResearchScoutConstraintMatches/);
  assert.match(chatPageSource, /renderResearchScoutProvenance/);
  assert.match(chatPageSource, /结构化评估/);
  assert.match(chatPageSource, /arXiv PDF 优先/);
  assert.match(chatPageSource, /机构证据: PDF 首页/);
  assert.match(chatPageSource, /research-scout-provenance/);
  assert.match(chatPageSource, /LLM 评估/);
  assert.match(chatPageSource, /规则初筛/);
  assert.match(chatPageSource, /发表单位/);
  assert.match(chatPageSource, /当前元数据无法确认/);
  assert.match(responsiveSource, /\.research-scout-evaluation/);
  assert.match(responsiveSource, /\.research-scout-score-chip/);
  assert.match(responsiveSource, /\.research-scout-constraints/);
  assert.match(responsiveSource, /\.research-scout-provenance/);
});

test('chat sidebar collapses to a hover rail and send button uses a compact arrow control', () => {
  assert.match(chatPageSource, /sidebarHoverOpen/);
  assert.match(chatPageSource, /chat-session-rail/);
  assert.match(chatPageSource, /desktopSidebarOpen \? 272 : 52/);
  assert.match(chatPageSource, /ArrowUpOutlined/);
  assert.match(responsiveSource, /\.chat-session-rail/);
  assert.match(responsiveSource, /\.chat-session-sidebar\.is-open \.chat-session-panel/);
});

test('chat composer uses a Codex-like single input surface without legacy shortcut chips', () => {
  assert.doesNotMatch(chatPageSource, /promptShortcuts/);
  assert.doesNotMatch(chatPageSource, /chat-prompt-shortcuts/);
  assert.doesNotMatch(chatPageSource, /润色文本/);
  assert.match(chatPageSource, /chat-editor-footer/);
  assert.match(chatPageSource, /chat-composer-mode/);
  assert.match(chatPageSource, /assistantModeOptions/);
  assert.match(chatPageSource, /chat-plus-button/);
});

test('assistant mode selector lives in the composer instead of the toolbar', () => {
  assert.doesNotMatch(chatPageSource, /<div className="chat-toolbar-actions">[\s\S]*chat-assistant-mode-select/);
  assert.match(chatPageSource, /<div className="chat-editor-tools">[\s\S]*chat-composer-mode-select/);
  assert.match(chatPageSource, /optionLabelProp="label"/);
  assert.match(responsiveSource, /\.chat-composer-mode-select/);
  assert.doesNotMatch(responsiveSource, /\.chat-assistant-mode-select/);
});

test('chat workbench visual polish avoids glossy plastic treatment', () => {
  assert.match(responsiveSource, /\.chat-message-list\s*\{[\s\S]*background: #f6f7f9 !important;/);
  assert.match(responsiveSource, /\.chat-toolbar\s*\{[\s\S]*background: rgba\(248, 250, 252, 0\.96\) !important;/);
  assert.match(responsiveSource, /\.chat-composer-panel\s*\{[\s\S]*border-radius: 14px;/);
  assert.match(responsiveSource, /\.chat-message-bubble\.is-assistant\s*\{[\s\S]*box-shadow: 0 1px 2px/);
  assert.match(responsiveSource, /\.chat-control-pill:hover,[\s\S]*color: #1d4ed8 !important;/);
  assert.doesNotMatch(responsiveSource, /\.chat-message-list\s*\{[\s\S]*radial-gradient/);
  assert.doesNotMatch(responsiveSource, /\.chat-composer-panel\s*\{[\s\S]*border-radius: 28px/);
  assert.doesNotMatch(responsiveSource, /\.chat-send-button\s*\{[\s\S]*linear-gradient/);
});

test('chat viewport layout keeps composer low and expands reading rail', () => {
  assert.match(responsiveSource, /--chat-content-rail: min\(1320px, calc\(100vw - 160px\)\)/);
  assert.match(responsiveSource, /\.chat-workspace\s*\{[\s\S]*height: calc\(100vh - 72px\);/);
  assert.match(responsiveSource, /\.chat-toolbar\s*\{[\s\S]*min-height: 44px;[\s\S]*padding: 6px 16px;/);
  assert.match(responsiveSource, /\.chat-message-list\s*\{[\s\S]*padding: 16px 20px 10px;/);
  assert.match(responsiveSource, /\.chat-message-row\s*\{[\s\S]*max-width: var\(--chat-content-rail\);/);
  assert.match(responsiveSource, /\.chat-composer\s*\{[\s\S]*padding: 8px 20px 8px;/);
  assert.match(responsiveSource, /\.chat-composer-panel\s*\{[\s\S]*max-width: var\(--chat-content-rail\);/);
  assert.match(responsiveSource, /\.chat-editor\s*\{[\s\S]*min-height: 96px;/);
});

test('Research Scout styles are scoped', () => {
  assert.match(responsiveSource, /\.chat-composer-mode-select/);
  assert.match(responsiveSource, /\.research-scout-cards/);
  assert.match(responsiveSource, /\.research-scout-grid/);
  assert.match(responsiveSource, /\.research-scout-card/);
  assert.match(responsiveSource, /\.research-scout-intent/);
  assert.match(responsiveSource, /\.research-scout-risk/);
  assert.match(responsiveSource, /\.research-scout-refine-button/);
  assert.match(responsiveSource, /\.chat-message-row/);
  assert.match(responsiveSource, /\.chat-message-bubble/);
  assert.match(responsiveSource, /\.chat-reference-strip/);
});

test('backend streams Research Scout metadata from scholarly discovery', () => {
  assert.match(backendChatSource, /assistant_mode: Literal\["general", "research_scout"\]/);
  assert.match(backendChatSource, /PAPER_DISCOVERY_TRIGGER_RE/);
  assert.match(backendChatSource, /_is_paper_discovery_request/);
  assert.match(backendChatSource, /_effective_assistant_mode/);
  assert.match(backendChatSource, /_web_search_enabled_for_mode/);
  assert.match(backendChatSource, /_plan_research_scout_queries/);
  assert.match(backendChatSource, /_fallback_research_scout_queries/);
  assert.match(backendChatSource, /只规划检索 query/);
  assert.match(backendChatSource, /planned_queries/);
  assert.match(backendChatSource, /scout_enabled = effective_mode == "research_scout"/);
  assert.match(backendChatSource, /web_search_enabled=_web_search_enabled_for_mode\(req, effective_mode\)/);
  assert.match(backendChatSource, /"auto_routed": req\.assistant_mode != "research_scout"/);
  assert.match(backendChatSource, /RESEARCH_SCOUT_LIMITS/);
  assert.match(backendChatSource, /search_scholarly_papers\(/);
  assert.match(backendChatSource, /source="arxiv_enriched"/);
  assert.match(backendChatSource, /source="scholarly"/);
  assert.match(backendChatSource, /_retrieve_research_scout_papers/);
  assert.match(backendChatSource, /_research_scout_requested_count/);
  assert.match(backendChatSource, /_research_scout_final_limit/);
  assert.match(backendChatSource, /RESEARCH_SCOUT_MAX_FINAL_RESULTS/);
  assert.match(backendChatSource, /RESEARCH_SCOUT_POOL_MULTIPLIER/);
  assert.match(backendChatSource, /_rank_research_scout_papers/);
  assert.match(backendChatSource, /arxiv_first_then_scholarly_fallback/);
  assert.match(backendChatSource, /natural language video localization/);
  assert.match(backendChatSource, /text-to-video moment retrieval/);
  assert.match(backendChatSource, /pool_target/);
  assert.match(backendChatSource, /underfilled_by/);
  assert.match(backendChatSource, /_build_research_scout_context/);
  assert.match(backendChatSource, /_research_scout_intent/);
  assert.match(backendChatSource, /library_relation/);
  assert.match(backendChatSource, /优先阅读 Top 3/);
  assert.match(backendChatSource, /"intent": scout_intent/);
  assert.match(backendChatSource, /"research_scout": \{/);
  assert.match(backendChatSource, /"retrieval": scout_retrieval/);
  assert.match(backendChatSource, /论文猎手已整理/);
  assert.match(chatPageSource, /planned_queries\?: string\[\]/);
  assert.match(chatPageSource, /retrieval\?: \{/);
});

test('Research Scout source strip excludes generic web references', () => {
  assert.match(chatPageSource, /visibleReferencesForMessage/);
  assert.match(chatPageSource, /msg\.research_scout\?\.enabled/);
  assert.match(chatPageSource, /ref\.source === 'research_scout'/);
  assert.match(chatPageSource, /论文候选来源：/);
  assert.match(chatPageSource, /检索来源：/);
});

test('backend streams Research Scout tool execution trace', () => {
  assert.match(backendChatSource, /_tool_trace_step/);
  assert.match(backendChatSource, /_research_scout_tool_trace/);
  assert.match(backendChatSource, /"tool_trace": tool_trace/);
  assert.match(backendChatSource, /"search_papers"/);
  assert.match(backendChatSource, /"evaluate_papers"/);
  assert.match(backendChatSource, /"rank_recommendations"/);
  assert.match(backendChatSource, /"import_paper"/);
  assert.match(backendChatSource, /arXiv PDF/);
  assert.match(backendChatSource, /arxiv_first_enriched/);
  assert.match(backendChatSource, /fallback_used/);
  assert.match(backendChatSource, /stage_counts/);
  assert.match(backendChatSource, /不会自动执行副作用操作/);
});

test('backend builds evidence-bound Research Scout evaluations and constraints', () => {
  assert.match(backendChatSource, /RESEARCH_SCOUT_INSTITUTION_ALIASES/);
  assert.match(backendChatSource, /RESEARCH_SCOUT_VENUE_ALIASES/);
  assert.match(backendChatSource, /RESEARCH_SCOUT_EVALUATION_FOCUS/);
  assert.match(backendChatSource, /_research_scout_constraint_matches/);
  assert.match(backendChatSource, /_research_scout_candidate_evaluation/);
  assert.match(backendChatSource, /_apply_llm_research_scout_evaluations/);
  assert.match(backendChatSource, /只返回可解析 JSON/);
  assert.match(backendChatSource, /using heuristic evaluation/);
  assert.match(backendChatSource, /"evaluation": evaluation/);
  assert.match(backendChatSource, /"constraint_matches": constraint_matches/);
  assert.match(backendChatSource, /当前元数据无法确认/);
  assert.match(backendChatSource, /不要编造 affiliation/);
  assert.match(backendChatSource, /"constraint_mode": constraint_mode/);
  assert.match(backendChatSource, /"evaluation_focus": evaluation_focus/);
});

test('scholarly search preserves OpenAlex venue and institution metadata for scout cards', () => {
  assert.match(backendPaperSearchSource, /"institutions": institutions/);
  assert.match(backendPaperSearchSource, /"venue": best_source\.get\("display_name"\) or primary_source\.get\("display_name"\)/);
});

test('scholarly search supports arXiv-first enriched discovery', () => {
  assert.match(backendPaperSearchSource, /journal_ref = entry\.findtext\("arxiv:journal_ref"/);
  assert.match(backendPaperSearchSource, /comment = entry\.findtext\("arxiv:comment"/);
  assert.match(backendPaperSearchSource, /merge_arxiv_enriched_results/);
  assert.match(backendPaperSearchSource, /_merge_arxiv_with_enrichment/);
  assert.match(backendPaperSearchSource, /source == "arxiv_enriched"/);
  assert.match(backendPaperSearchSource, /"strategy": "arxiv_first"/);
  assert.match(backendPaperSearchSource, /"metadata_provenance"/);
});

test('scholarly search extracts PDF first-page affiliation evidence for arXiv candidates', () => {
  assert.match(backendPaperSearchSource, /ensure_cached_arxiv_pdf/);
  assert.match(backendPaperSearchSource, /ARXIV_ENRICHED_PDF_AFFILIATION_LIMIT/);
  assert.match(backendPaperSearchSource, /extract_affiliations_from_first_page_text/);
  assert.match(backendPaperSearchSource, /_extract_first_page_text_sync/);
  assert.match(backendPaperSearchSource, /enrich_arxiv_pdf_first_page_affiliations/);
  assert.match(backendPaperSearchSource, /"pdf_first_page_affiliations"/);
  assert.match(backendPaperSearchSource, /"pdf_first_page"/);
  assert.match(backendChatSource, /"pdf_first_page_affiliations": metadata\.get\("pdf_first_page_affiliations"\) or \[\]/);
});

test('backend exposes research project paper append endpoint for scout actions', () => {
  assert.match(backendResearchSource, /class ProjectPaperAddRequest/);
  assert.match(backendResearchSource, /@router\.post\("\/projects\/\{project_id\}\/papers"\)/);
  assert.match(backendResearchSource, /project\.paper_ids = current_ids/);
});
