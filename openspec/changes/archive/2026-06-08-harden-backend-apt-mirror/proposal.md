## Why

Backend image builds now install TeX packages for LaTeX preview, which substantially increases apt downloads. The default Debian CDN has repeatedly returned `502 Bad Gateway` for individual `.deb` files in the current network path, causing otherwise valid builds to fail.

## What Changes

- Make the backend Docker build use configurable Debian apt and Python package mirrors.
- Default the build to China-friendly Debian and PyPI mirrors to reduce CDN failures for local development.
- Add apt and pip retry/timeout options so transient package download failures are retried automatically.
- Preserve an escape hatch to build against the official Debian mirror when needed.

## Capabilities

### New Capabilities
- `backend-image-build-reliability`: Backend container builds can tolerate transient apt/pip mirror failures and support configurable package mirrors.

### Modified Capabilities
- None.

## Impact

- Affected file: `backend/Dockerfile`
- Affected system: Docker Compose backend image build
- No runtime API or database changes
