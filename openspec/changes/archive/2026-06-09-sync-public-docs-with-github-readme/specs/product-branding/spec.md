## MODIFIED Requirements

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

#### Scenario: Deeper docs expand the README positioning
- **WHEN** a prospective lab maintainer opens the introduction or user manual
- **THEN** the docs explain that each lab deploys its own instance
- **AND** they describe paper library, toolbox, research direction, proposal review, LaTeX writing, project space, and AI assistant workflows using the current product model
- **AND** they include practical data-boundary guidance for API keys, private papers, uploads, notes, logs, and database backups

#### Scenario: Frontend README is project-specific
- **WHEN** a frontend contributor opens `frontend/README.md`
- **THEN** it describes the AstraLoom frontend stack, local commands, and development notes
- **AND** it does not present the app as a generic React/Vite starter template
