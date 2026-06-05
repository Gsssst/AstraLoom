## ADDED Requirements

### Requirement: Authenticated account entry remains visually aligned
The application SHALL render the authenticated account avatar and visible user name as one horizontally aligned header control on desktop layouts.

#### Scenario: Desktop account control is aligned
- **WHEN** an authenticated user views the application on a desktop-width screen
- **THEN** the avatar and visible user name are vertically centered within a single horizontal account control

#### Scenario: Long account name remains contained
- **WHEN** the authenticated user's visible name exceeds the available account control width
- **THEN** the name is truncated without wrapping or displacing neighboring header actions

### Requirement: Authenticated account entry remains compact on mobile
The application SHALL preserve an avatar-only account entry on narrow screens.

#### Scenario: Mobile account control hides the name
- **WHEN** an authenticated user views the application below the mobile breakpoint
- **THEN** the account control displays the avatar and hides the visible user name
