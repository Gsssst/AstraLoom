## Context

The frontend Dockerfile runs `npm ci` and then `COPY . .`. Without a `.dockerignore`, any existing `frontend/node_modules` in the build context is copied into the image after `npm ci`. If those files came from another OS, filesystem, or upload method, executable bits may be wrong and commands such as `tsc` can fail with permission errors.

The backend build context also lacks filtering, so uploads, caches, and local environments can be accidentally included in image builds.

## Decision

Add scoped `.dockerignore` files inside `frontend/` and `backend/` because the compose build contexts are `./frontend` and `./backend`.

## Non-Goals

- No Dockerfile rewrite.
- No dependency version changes.
- No deployment topology changes.

## Validation

- Run OpenSpec validation.
- Run `git diff --check`.
