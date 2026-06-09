## Context

Docker-based projects commonly document `localhost` as the access URL for local runs. AstraLoom's README should keep that convention while also making server deployment obvious for lab maintainers.

## Decision

Keep the existing endpoint list and add a one-line note before it:

- Local machine: `http://localhost`
- Lab server: `http://<server-ip-or-domain>`

Mirror the same clarification in the Chinese section.

## Non-Goals

- No deployment guide rewrite.
- No reverse proxy or HTTPS configuration changes.
- No changes to Docker Compose ports.

## Validation

- Run OpenSpec validation.
- Run `git diff --check`.
