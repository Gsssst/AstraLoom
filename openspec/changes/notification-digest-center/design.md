## Context

The existing settings page persists digest keywords and two delivery booleans. In-app notification list APIs already exist, but the scheduled task is not imported by the Celery application and the Docker deployment does not run Celery Beat. The email switch persists state without any configured mail transport or delivery implementation. Users cannot trigger a digest immediately, so there is no practical way to verify that the subscription works.

## Goals / Non-Goals

**Goals:**
- Provide a reliable in-app arXiv digest path shared by manual tests and scheduled delivery.
- Let a signed-in user validate keywords and trigger an immediate test notification from settings.
- Load the daily Celery task and deploy Celery Beat so automatic scheduling is real.
- Expose delivery status and refresh the global unread count immediately after a test delivery.
- Present email delivery honestly as unavailable until a mail transport is implemented.

**Non-Goals:**
- Implement SMTP, third-party transactional email, mobile push, or browser Web Push.
- Add a database migration.
- Change scholarly provider ranking or paper ingestion behavior.

## Decisions

### Use one in-app dispatch service for scheduled and manual delivery

`DigestService.dispatch_in_app_digest` will fetch papers once, build a digest from those papers, optionally create a `Notification`, and return a structured result. The scheduled Celery task and the manual API will call the same method. This avoids the current duplicate arXiv fetch and prevents manual testing from drifting away from scheduled behavior.

Alternative considered: enqueue the Celery task from the test endpoint. Rejected because it makes first-use testing depend on Redis, a running worker, and polling. A synchronous bounded test is easier for users to understand and still exercises the same service logic.

### Deliver a test notification even when no matching paper is found

Manual tests will create an in-app notification with a clear no-results message. Scheduled runs will continue skipping empty digests to avoid daily noise. This gives immediate, visible confirmation that the notification channel works independently of arXiv result availability.

### Load the task in Celery and configure Beat centrally

The Celery application will include `app.tasks.daily_digest` and own the `beat_schedule`. Docker Compose will run a dedicated `celery-beat` service. Keeping schedule configuration in `celery_app.py` makes both worker and beat processes use the same task registration.

### Make email status explicit

The subscription response will expose `email_available: false`. The API will reject attempts to enable email delivery until transport support exists. The frontend will disable the email switch and explain the limitation.

### Use a lightweight browser event to refresh the header badge

After a successful manual test push, settings dispatches a `notifications:refresh` browser event. `AppLayout` listens for the event and reloads the unread count. This avoids introducing a global notification store for a narrow cross-component refresh.

## Risks / Trade-offs

- [Manual tests wait for arXiv and LLM responses] → Keep provider requests bounded by existing timeouts and return a visible loading state.
- [A test can create an empty-result notification] → Mark test notifications clearly and reserve empty notifications for explicit manual tests only.
- [Celery Beat duplicates schedules if multiple replicas run] → Deploy a single `celery-beat` service.
- [Email switch behavior changes] → Preserve the field in storage but reject new enable attempts and explain that the channel is not configured.
