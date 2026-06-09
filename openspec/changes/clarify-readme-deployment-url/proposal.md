## Why

The README Quick Start currently only shows `localhost` URLs. That is fine for local Docker Compose, but AstraLoom is positioned for lab self-hosting, so maintainers also need to know what URL to use when running on a lab server.

## What Changes

- Clarify that `http://localhost` is for local machine deployment.
- Add the lab server form `http://<server-ip-or-domain>` for remote/self-hosted deployments.
- Apply the clarification to both English and Chinese Quick Start sections.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `product-branding`: README Quick Start shall distinguish local and lab-server access URLs.

## Impact

- Affected docs: `README.md`.
- Affected spec: `product-branding`.
- No runtime, API, dependency, or data changes.
