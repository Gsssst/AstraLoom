## Why

The settings page still presents the original arXiv digest form, but the daily task is not loaded by the Celery application and no beat scheduler is deployed. Users also cannot verify a subscription immediately, inspect the latest delivery state, or distinguish the working in-app channel from the not-yet-configured email channel.

## What Changes

- Turn the existing subscription form into a usable digest center with keyword validation, delivery state, and an immediate test action.
- Reuse one backend dispatch path for scheduled and manual in-app digest delivery.
- Load the digest task in Celery and deploy a beat scheduler for the daily schedule.
- Return a clear manual-test result, including whether papers were found and whether an in-app notification was created.
- Mark email delivery as unavailable until a mail transport is implemented, instead of displaying a switch that only persists a value.
- Refresh the header notification count after a successful manual test push.

## Capabilities

### New Capabilities
- `notification-digest-center`: User-configurable arXiv digest subscriptions with reliable in-app delivery, manual test delivery, scheduling, and visible delivery status.

### Modified Capabilities

## Impact

- Backend API: `app/api/notifications.py`
- Backend services and tasks: `app/services/digest_service.py`, `app/tasks/daily_digest.py`, `app/tasks/celery_app.py`
- Deployment: `docker-compose.yml`
- Frontend: `src/pages/SettingsPage.tsx`, `src/components/AppLayout.tsx`
- Tests: backend notification digest regression coverage and frontend build verification
