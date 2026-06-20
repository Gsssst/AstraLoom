## Context

The current implementation stores paper chat share metadata in `Notification.metadata_json` and discussion state in `paper_chat_share_threads`, participants, comments, and statuses. Personal paper notes already exist as `UserPaper.personal_notes` and are edited from the paper detail page.

The reference pattern from mature tools is consistent:
- Hypothesis keeps discussion/annotation anchored to a source resource and limits access by group or participant.
- Zotero turns PDF annotations into reusable note content rather than leaving them only as transient highlights.
- Logseq-style block notes preserve context in Markdown so excerpts can be linked, searched, and reused.

This change applies that pattern locally: discussion remains in the push center, while a participant can append a structured Markdown snapshot to their own paper note.

## Goals / Non-Goals

**Goals:**
- Add a one-click "settle to paper note" action for expanded paper chat share cards.
- Reuse the existing personal paper note field and preserve any existing note content.
- Produce a readable Markdown block that includes shared Q&A, comments, statuses, and source metadata.
- Keep authorization tied to share-thread participants.

**Non-Goals:**
- Creating project-space resources, shared team notes, or a new knowledge-base entity.
- Editing or deleting previously settled blocks.
- Deduplicating semantically similar discussions across users.
- Saving discussions for notifications that do not resolve to a local paper.

## Decisions

1. **Append to `UserPaper.personal_notes` instead of adding a new table.**
   - Rationale: the first useful workflow is "I am reading this paper; put this discussion where my paper notes already live."
   - Alternative considered: a dedicated settlement table. That would support richer history later, but adds migration and UI complexity before the workflow is validated.

2. **Snapshot Markdown at save time.**
   - Rationale: comments and statuses may continue changing; the saved note should represent what the user chose to preserve at that moment.
   - Alternative considered: dynamic links back to the thread only. That keeps content live but makes notes less portable and less useful when reading offline or exporting.

3. **Use the paper chat share notification id as the frontend action target.**
   - Rationale: the push center already owns share-card access by notification id; the backend resolves or creates the stable thread id from that notification.
   - Alternative considered: call by `share_thread_id`. That would need extra access checks and sender/recipient notification lookup logic in the UI.

4. **Require a local paper id before saving.**
   - Rationale: personal notes are keyed by local `papers.id`. Remote digest recommendations must be ingested before they can have notes.
   - Alternative considered: save a standalone note without a paper. That belongs to a later project-resource or knowledge-base feature.

## Risks / Trade-offs

- Existing notes can become long -> cap individual shared fields and return a preview so users know the save completed.
- Duplicate saves can append the same discussion multiple times -> include timestamp and source thread id in the block; semantic dedupe can be added later if users need it.
- Legacy notifications may lack selected messages -> still save sender note, comments, statuses, and source metadata, with a clear empty-message line.
- Formatting from AI answers can contain Markdown/LaTeX -> preserve message content as Markdown and isolate each message under headings.
