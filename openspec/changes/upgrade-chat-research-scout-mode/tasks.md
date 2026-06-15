## 1. Backend Research Scout

- [x] 1.1 Add validated `assistant_mode` support to chat send/stream requests.
- [x] 1.2 Implement Research Scout discovery helpers that query comprehensive scholarly providers and build structured candidate metadata.
- [x] 1.3 Stream Research Scout status and candidate metadata while preserving normal chat/RAG/web behavior.

## 2. Frontend Research Scout

- [x] 2.1 Add chat assistant mode state and a visible Research Scout mode selector.
- [x] 2.2 Render Research Scout paper candidate cards from stream metadata.
- [x] 2.3 Submit assistant mode with normal and attachment chat sends without breaking existing controls.

## 3. Verification

- [x] 3.1 Add/update contract tests for Research Scout mode UI and backend request schema.
- [x] 3.2 Run focused frontend/backend verification and document any unrelated failures.

## 4. Research Scout Closed Loop

- [x] 4.1 Reuse personal paper ingestion so a Research Scout candidate can be added to the paper library from chat.
- [x] 4.2 Show per-card saving and saved states without leaving the conversation.
- [x] 4.3 Add follow-up search chips for baseline, survey, latest, and counterexample discovery.

## 5. Codex-Style Chat Workbench UI

- [x] 5.1 Constrain message reading width and make assistant answers feel like work artifacts.
- [x] 5.2 Restyle references, stream status, and candidate cards to sit inside the answer flow.
- [x] 5.3 Keep the existing session list, controls, uploads, thinking, and streaming behavior intact.
- [x] 5.4 Replace the legacy prompt shortcut row with a Codex-like single composer surface.

## 6. Follow-Up Iterations

- [x] 6.1 Add "加入分类" directly from Research Scout cards.
- [x] 6.2 Add "加入研究方向素材池" directly from Research Scout cards.
- [x] 6.3 Promote repeated Research Scout actions into a broader tool/agent mode.
