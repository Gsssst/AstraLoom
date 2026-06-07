## ADDED Requirements

### Requirement: Route Pages Are Lazily Loaded
The frontend SHALL load page-level route modules through dynamic imports instead of statically importing every page into the initial application bundle.

#### Scenario: App registers lazy route pages
- **WHEN** the application route tree is defined
- **THEN** each page route component is created through a dynamic import
- **AND** the existing route paths and layout nesting remain unchanged

#### Scenario: User opens a lazy route
- **WHEN** a user navigates to a route whose page chunk is not yet loaded
- **THEN** the app displays a lightweight route loading fallback until the page module resolves

### Requirement: Production Bundles Have Stable Boundaries
The frontend production build SHALL define stable bundle boundaries for page chunks and high-volume vendor code without changing runtime behavior.

#### Scenario: Vite build emits split chunks
- **WHEN** the frontend production build runs
- **THEN** Vite emits multiple JavaScript chunks for route and vendor boundaries
- **AND** the build exits successfully

#### Scenario: Vendor groups remain cacheable
- **WHEN** shared framework, UI, Markdown, or PDF dependencies are included in production output
- **THEN** they are assigned to stable named chunks where configured
