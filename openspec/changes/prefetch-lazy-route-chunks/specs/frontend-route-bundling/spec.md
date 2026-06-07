## MODIFIED Requirements

### Requirement: Route Pages Are Lazily Loaded
The frontend SHALL load page-level route modules through dynamic imports instead of statically importing every page into the initial application bundle, and SHALL support route chunk prefetch when a user signals navigation intent.

#### Scenario: App registers lazy route pages
- **WHEN** the application route tree is defined
- **THEN** each page route component is created through a dynamic import
- **AND** the existing route paths and layout nesting remain unchanged

#### Scenario: User opens a lazy route
- **WHEN** a user navigates to a route whose page chunk is not yet loaded
- **THEN** the app displays a lightweight route loading fallback until the page module resolves

#### Scenario: User signals route navigation intent
- **WHEN** a user hovers, focuses, or touches a known navigation control before activating it
- **THEN** the frontend starts loading the target route chunk without calling backend page data APIs

#### Scenario: Route prefetch is deduplicated
- **WHEN** multiple navigation controls prefetch the same route target
- **THEN** the frontend reuses the existing in-flight or completed chunk load instead of starting duplicate prefetch work
