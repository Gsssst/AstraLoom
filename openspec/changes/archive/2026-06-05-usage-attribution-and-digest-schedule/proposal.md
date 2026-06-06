# Change: Usage Attribution And Digest Schedule

## Why

Token usage is currently recorded as `system` because the LLM service does not know the authenticated request user. Daily paper digests are configured in Celery beat, but the worker can fail when async database connections are reused across event loops, and users cannot choose a fixed daily delivery hour.

## What Changes

- Track the current authenticated user in a request-local usage context.
- Record LLM token usage against the current user when available, falling back to `system` only for true background/system calls.
- Add a daily digest `send_hour` setting to user subscriptions.
- Run the digest scheduler hourly and deliver only subscriptions due for the current Beijing hour.
- Avoid duplicate same-day deliveries and dispose async DB pools after the Celery task run to prevent cross-event-loop failures.

## Non-Goals

- Reassign historical `system` usage records.
- Add email transport.
- Add arbitrary cron expressions per user.
