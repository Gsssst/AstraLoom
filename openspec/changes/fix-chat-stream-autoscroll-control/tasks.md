## 1. Shared Scroll Control

- [x] 1.1 Add a reusable hook that tracks whether the chat scroll container is near the bottom.
- [x] 1.2 Expose conditional bottom-following refs for scroll containers and end sentinels.

## 2. Page Integration

- [x] 2.1 Replace main chat unconditional streaming auto-scroll with conditional bottom-following.
- [x] 2.2 Replace paper-detail chat unconditional streaming auto-scroll with conditional bottom-following.

## 3. Verification and Commit

- [x] 3.1 Add frontend contract coverage for manual-scroll-aware streaming behavior.
- [x] 3.2 Run OpenSpec validation and targeted frontend tests.
- [x] 3.3 Commit the implementation.
- [x] 3.4 Harden manual scroll detection with captured wheel/touch intent and disabled browser scroll anchoring.
