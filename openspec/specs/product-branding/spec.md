# product-branding Specification

## Purpose
TBD - created by archiving change rename-to-astraloom-brand. Update Purpose after archive.
## Requirements
### Requirement: Product identity is AstraLoom
The application SHALL use `AstraLoom` as the current user-facing product name.

#### Scenario: User views core brand surfaces
- **WHEN** a user opens the home, login, register, or command-palette entry surfaces
- **THEN** those surfaces present the product as `AstraLoom`
- **AND** they do not present `Auto-Research-DS` as the current product name

#### Scenario: Runtime metadata is requested
- **WHEN** backend app metadata, generated LaTeX author metadata, or scholarly HTTP user agents identify the product
- **THEN** they use `AstraLoom`

### Requirement: Home page reflects the AstraLoom research workflow
The home page SHALL provide a brand-adapted first screen that combines the AstraLoom identity with direct research workflow entry points.

#### Scenario: User opens the home page
- **WHEN** the home page loads
- **THEN** the first viewport prominently displays `AstraLoom`
- **AND** it explains the paper-to-idea-to-writing workflow
- **AND** it provides direct navigation to chat, papers, research directions, and writing

#### Scenario: User searches from the home page
- **WHEN** the user enters a paper query and submits from the home page
- **THEN** the app navigates to the paper library search route with that query

### Requirement: Current documentation uses the active brand
Current project documentation SHALL refer to the active product as `AstraLoom`.

#### Scenario: User reads current docs
- **WHEN** the user opens README, introduction, user manual, frontend README, or OpenSpec project overview
- **THEN** those current docs use `AstraLoom` as the product name
- **AND** they do not present default framework template text as the project description

#### Scenario: README presents bilingual lab self-hosting positioning
- **WHEN** a prospective lab maintainer opens the README from GitHub
- **THEN** the README describes AstraLoom in Chinese and English as a self-hosted research workspace for individual labs and research groups
- **AND** it avoids implying that the project is intended as a centrally hosted public SaaS product
- **AND** it includes concise guidance about files that should and should not be uploaded to GitHub

#### Scenario: README uses GitHub-style project presentation
- **WHEN** a prospective maintainer opens the README on GitHub
- **THEN** the README presents AstraLoom with a concise tagline, badges or quick metadata, table of contents, feature overview, quick start, and deployment guidance
- **AND** it includes GitHub-renderable diagrams for the research workflow and deployment architecture
- **AND** it preserves bilingual lab self-hosting positioning and upload safety guidance

#### Scenario: README title is centered
- **WHEN** a prospective maintainer opens the README on GitHub
- **THEN** the top product title is centered with the README hero block
- **AND** it presents the product name as `AstraLoom`

#### Scenario: README identifies repository license
- **WHEN** a prospective lab maintainer opens the README
- **THEN** the License section identifies the repository as MIT licensed
- **AND** it points readers to the root `LICENSE` file

#### Scenario: README Quick Start distinguishes local and server URLs
- **WHEN** a prospective lab maintainer reads the README Quick Start
- **THEN** the README explains that `localhost` is for local-machine runs
- **AND** it shows that lab-server deployments should be accessed through the server IP or domain

#### Scenario: README keeps security guidance concise
- **WHEN** a reader scans the README project homepage
- **THEN** the README includes concise warnings not to commit secrets, private papers, uploads, or backups
- **AND** it does not include a long one-time GitHub upload checklist in the main presentation flow

#### Scenario: Deeper docs expand the README positioning
- **WHEN** a prospective lab maintainer opens the introduction or user manual
- **THEN** the docs explain that each lab deploys its own instance
- **AND** they describe paper library, toolbox, research direction, proposal review, LaTeX writing, project space, and AI assistant workflows using the current product model
- **AND** they include practical data-boundary guidance for API keys, private papers, uploads, notes, logs, and database backups

#### Scenario: Frontend README is project-specific
- **WHEN** a frontend contributor opens `frontend/README.md`
- **THEN** it describes the AstraLoom frontend stack, local commands, and development notes
- **AND** it does not present the app as a generic React/Vite starter template

### Requirement: AstraLoom home page can retain the restored visual composition
The AstraLoom home page SHALL use the restored pre-star-map visual composition while presenting the current product name as `AstraLoom`.

#### Scenario: User views the restored home page
- **WHEN** the user opens the home page
- **THEN** the page presents the product name as `AstraLoom`
- **AND** it uses the restored particle hero, quick actions, stats, feature cards, and footer composition
- **AND** it does not present `Auto-Research-DS` as the current product name
