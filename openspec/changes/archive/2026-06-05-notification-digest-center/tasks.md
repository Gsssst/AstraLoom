## 1. Backend Digest Delivery

- [x] 1.1 Refactor the digest service to fetch papers once and dispatch reusable in-app digest notifications.
- [x] 1.2 Validate subscription updates and expose explicit email-channel availability.
- [x] 1.3 Add an authenticated immediate test-push endpoint with structured delivery feedback.

## 2. Scheduling

- [x] 2.1 Register the daily digest task and centralize the Celery Beat schedule.
- [x] 2.2 Add a single Celery Beat service to Docker Compose.

## 3. Settings Experience

- [x] 3.1 Upgrade the settings push tab with delivery status, disabled email explanation, and immediate test action.
- [x] 3.2 Refresh the global unread notification badge after successful test delivery.

## 4. Verification

- [x] 4.1 Add regression tests for subscription validation, manual delivery, scheduled delivery, and task registration.
- [x] 4.2 Run backend tests, frontend build, and strict OpenSpec validation.
