## Why

After visual evidence extraction moved to background jobs, the user can no longer tell progress from the paper row, and the completion toast may say "成功 0，失败 0，跳过 0" even when the meaningful state is "no work needed" or "visual evidence complete". This makes the OCR workflow look broken or opaque.

## What Changes

- Treat ready-but-incomplete visual evidence, such as missing table OCR or low-confidence visual tables, as needing extraction/backfill.
- Show active visual evidence job progress near the paper processing list, including current paper and job message.
- Make completion toasts prefer the backend job message and only show count summaries when counts are meaningful.
- Keep the existing maintenance-center poller and job API; no new backend dependency.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `paper-library-maintenance-center`: Long-running visual evidence jobs must provide clear progress and completion feedback where users start or monitor the action, and ready-but-incomplete visual evidence must remain actionable.

## Impact

- Frontend: paper library maintenance UI and completion toast wording.
- Tests: frontend contract coverage for visible progress and non-misleading completion messages.
