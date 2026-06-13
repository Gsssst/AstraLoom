## 1. Backend Job Flow

- [x] 1.1 Add a single-paper visual evidence job runner that reuses the maintenance job registry and deduplicates queued/running jobs by paper id.
- [x] 1.2 Change `/papers/{paper_id}/extract-visual-evidence` to return quickly with current visual status and job metadata.
- [x] 1.3 Preserve visual evidence failure details in job status and paper metadata.

## 2. Frontend Feedback

- [x] 2.1 Update paper library repair action handling to treat visual evidence extraction as queued work instead of a blocking request.
- [x] 2.2 Poll the returned job until success/failure and refresh paper status when done.

## 3. Verification

- [x] 3.1 Add backend tests for queued single-paper extraction and duplicate click deduplication.
- [x] 3.2 Add frontend contract or unit coverage for queued visual evidence action handling.
- [x] 3.3 Run targeted backend/frontend tests, OpenSpec validation, and diff checks.
- [x] 3.4 Commit the completed change.
