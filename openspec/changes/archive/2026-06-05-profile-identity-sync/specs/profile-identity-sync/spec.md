## ADDED Requirements

### Requirement: Current user recovery includes visible profile identity
The authenticated current-user API SHALL return the persisted display name and avatar together with the core account fields.

#### Scenario: Restore profile identity after login or refresh
- **WHEN** a user with a saved display name and avatar loads their current-user profile
- **THEN** the response includes the persisted display name and avatar

### Requirement: Profile saves update the active application identity
The settings page SHALL synchronize successful profile changes into the active authentication state used by the header account control.

#### Scenario: Display name updates immediately
- **WHEN** an authenticated user successfully saves a new display name
- **THEN** the header account control displays the new name without requiring a page reload

#### Scenario: Avatar updates immediately
- **WHEN** an authenticated user successfully uploads a new avatar
- **THEN** the header account control displays the new avatar without requiring a page reload

#### Scenario: Profile identity survives a new login
- **WHEN** a user signs out and signs in again after saving profile identity changes
- **THEN** the header account control restores the saved display name and avatar

