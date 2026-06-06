# usage-attribution-and-digest-schedule Specification

## ADDED Requirements

### Requirement: Token usage belongs to the authenticated user

The system SHALL record LLM token usage with the authenticated user identity when an LLM call is made during an authenticated request.

#### Scenario: Authenticated request calls LLM

- **WHEN** an authenticated user triggers an LLM call
- **THEN** token usage records include that user's ID and visible username
- **AND** usage is not attributed to `system`.

#### Scenario: Background call has no user

- **WHEN** an LLM call occurs without an authenticated user context
- **THEN** the usage record may be attributed to `system`.

### Requirement: Daily paper digest scheduling is user-configurable and reliable

The system SHALL deliver enabled daily paper digests at the user's configured Beijing hour.

#### Scenario: Subscription is due

- **WHEN** the hourly digest task runs during a subscription's configured Beijing hour
- **THEN** it dispatches that user's digest if it has not already been sent for that Beijing day.

#### Scenario: Subscription is not due

- **WHEN** the hourly digest task runs outside a subscription's configured Beijing hour
- **THEN** it skips that subscription without changing its last delivery time.

#### Scenario: Celery worker runs digest repeatedly

- **WHEN** the digest task runs on a worker that previously executed async database work
- **THEN** the task does not fail because of async database connections attached to a different event loop.
