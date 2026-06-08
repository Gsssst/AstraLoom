## 1. OpenSpec

- [x] 1.1 Create proposal, design, delta specs, and task list.
- [x] 1.2 Validate the OpenSpec change strictly before implementation.

## 2. Paper Import Ownership

- [x] 2.1 Add paper importer metadata to the ORM model and Alembic migration with `gst` backfill.
- [x] 2.2 Thread current user metadata through paper ingestion and file-import endpoints.
- [x] 2.3 Return importer metadata in paper search/detail responses.
- [x] 2.4 Add backend search filtering for `owner=mine`.

## 3. Paper Library UI

- [x] 3.1 Add a "我的" filter to the paper-library source controls.
- [x] 3.2 Display importer account tags on local paper cards.
- [x] 3.3 Update frontend contract coverage for owner tags and report prompt UI.

## 4. Group Report

- [x] 4.1 Accept custom report instructions in report API requests.
- [x] 4.2 Use custom instructions in report generation while preserving default behavior.
- [x] 4.3 Set group-report Word fonts to SimSun for Chinese and Times New Roman for Latin text.
- [x] 4.4 Add/update backend tests for custom prompt and Word font helpers.

## 5. Verification

- [x] 5.1 Run targeted backend/frontend tests, frontend build, OpenSpec validation, and diff checks.
- [ ] 5.2 Commit implementation, archive the OpenSpec change, and commit the archive.
