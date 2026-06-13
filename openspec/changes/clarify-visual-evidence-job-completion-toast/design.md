## Context

The backend now queues single-paper visual evidence extraction and the frontend polls the existing maintenance job endpoint. The current UI already renders an `activeMaintenanceJob` alert near the maintenance center header, but that can be missed when the user is focused on the paper processing list. The success toast also always formats counters, which is misleading for jobs whose result is better described by `job.message`.

There is a second issue: batch visual evidence backfill currently only selects papers whose visual evidence is missing or failed. Papers with old ready visual evidence but missing table OCR are skipped, so the user sees "没有需要提取视觉证据的论文" even though OCR refresh is still needed.

## Goals / Non-Goals

**Goals:**

- Make active visual evidence job progress visible in the processing-status area.
- Use job messages such as "视觉证据提取完成" or "没有需要提取视觉证据的论文" in success toasts.
- Make missing OCR / low-confidence visual table states actionable in maintenance candidate selection.
- Preserve existing polling behavior.

**Non-Goals:**

- Add per-table OCR progress percentages.
- Add persistent server-side job storage.

## Decisions

1. Add a small inline job progress alert above the processing-status list.
   - This keeps progress near the action buttons without duplicating a full job dashboard.

2. Add a formatter for maintenance completion messages.
   - If all counters are zero and the backend has a message, show the message instead of a meaningless `0/0/0` summary.
   - Otherwise keep the count summary for batch jobs.

3. Add one backend helper for visual evidence refresh need.
   - A paper needs visual extraction when status is missing, failed, has missing OCR, has missing visual summaries, or has low-confidence visual tables.
   - Use the helper in maintenance recommendations, health samples, and backfill candidate selection.

## Risks / Trade-offs

- [Risk] The job still has coarse progress for OCR internals. -> The alert shows current paper and job message; deeper per-table progress can be added later if needed.
- [Risk] Some low-confidence tables may already be usable. -> The action is a refresh opportunity; it remains explicit and admin-triggered.
