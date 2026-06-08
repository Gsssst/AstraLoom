## ADDED Requirements

### Requirement: Configurable Debian apt mirror
The backend Docker image build SHALL allow Debian apt and Python package mirrors to be configured without editing source files.

#### Scenario: Build uses default regional mirror
- **GIVEN** the backend image is built without custom build arguments
- **WHEN** apt package metadata and packages are fetched
- **THEN** the build uses a regional Debian mirror instead of `deb.debian.org`

#### Scenario: Build can use caller-provided mirrors
- **GIVEN** a caller provides `APT_MIRROR` or `PIP_INDEX_URL` build arguments
- **WHEN** the backend image is built
- **THEN** Debian apt sources and pip package downloads use the provided mirrors

### Requirement: apt transient failure tolerance
The backend Docker image build SHALL retry transient apt and pip package fetch failures.

#### Scenario: apt fetch encounters transient server errors
- **GIVEN** the configured mirror intermittently returns server errors
- **WHEN** the backend system packages are installed
- **THEN** apt fetches use retry and timeout options before failing the build

#### Scenario: pip encounters a large package download timeout
- **GIVEN** Python package downloads are slow or unstable
- **WHEN** backend Python dependencies are installed
- **THEN** pip uses retry and timeout options before failing the build
