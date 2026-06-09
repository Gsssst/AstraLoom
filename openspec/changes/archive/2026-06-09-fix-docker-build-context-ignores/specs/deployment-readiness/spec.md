## ADDED Requirements

### Requirement: Docker build contexts exclude local artifacts
Docker image build contexts SHALL exclude local dependency directories, build outputs, caches, uploads, and local environment files that can make server builds non-reproducible.

#### Scenario: Frontend image is built on a server with existing node_modules
- **WHEN** the frontend Docker image build context contains a local `node_modules` directory
- **THEN** Docker excludes it from the build context
- **AND** dependencies installed by `npm ci` inside the image are not overwritten by local artifacts

#### Scenario: Backend image is built on a server with runtime data
- **WHEN** the backend Docker image build context contains uploads, cache directories, virtual environments, or local env files
- **THEN** Docker excludes those artifacts from the build context
- **AND** runtime data is not baked into the backend image
