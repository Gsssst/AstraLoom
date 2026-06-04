## Why

The digest inbox is now readable and actionable, but recommendations are still generated from static arXiv keyword searches with coarse year-level freshness checks. To become a useful daily research radar, the digest must learn from the user's research projects and recommendation feedback while keeping its ranking explainable.

## What Changes

- Search multiple scholarly providers for digest candidates instead of relying on arXiv alone.
- Preserve provider publication timestamps and apply exact freshness windows when providers expose them.
- Canonically deduplicate candidates across keywords and providers before ranking.
- Rank digest candidates with an explainable heuristic using subscription keywords, active research-project keywords, saved or read papers, freshness, and prior digest feedback.
- Store recommendation score, reasons, provider identity, and trusted remote-ingestion token in digest metadata.
- Add per-paper digest actions for “稍后阅读”, “感兴趣”, and “不感兴趣”.
- Use “不感兴趣” feedback to suppress the same paper from later digests.
- Keep historical digest records compatible when they do not contain the new ranking fields.

## Capabilities

### New Capabilities
- `personalized-paper-digest-ranking-and-feedback`: Multi-source, explainable digest ranking with user preference signals and recommendation feedback.

### Modified Capabilities

## Impact

- Scholarly normalization: `app/services/paper_search.py`
- Digest recommendation service: `app/services/digest_service.py`
- Notification API: `app/api/notifications.py`
- Digest inbox UI: `src/pages/PaperDigestInboxPage.tsx`
- Tests: digest ranking, freshness, metadata, and feedback regression coverage
