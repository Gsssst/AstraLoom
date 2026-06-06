## 1. Runtime State Handling

- [x] 1.1 Remove `backend/celerybeat-schedule` from Git tracking.
- [x] 1.2 Ignore Celery Beat schedule state files.
- [x] 1.3 Configure development and production Celery Beat services to write schedule state under `/tmp`.

## 2. Verification

- [x] 2.1 Validate the OpenSpec change.
- [x] 2.2 Confirm Git no longer reports `backend/celerybeat-schedule` as a tracked modification.
