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
- **WHEN** the user opens README, introduction, user manual, or OpenSpec project overview
- **THEN** those current docs use `AstraLoom` as the product name

### Requirement: AstraLoom home page can retain the restored visual composition
The AstraLoom home page SHALL use the restored pre-star-map visual composition while presenting the current product name as `AstraLoom`.

#### Scenario: User views the restored home page
- **WHEN** the user opens the home page
- **THEN** the page presents the product name as `AstraLoom`
- **AND** it uses the restored particle hero, quick actions, stats, feature cards, and footer composition
- **AND** it does not present `Auto-Research-DS` as the current product name

