## 1. Scroll Lock

- [x] 1.1 Harden `useChatAutoScroll` so scroll events pause follow-output whenever the user is away from bottom.
- [x] 1.2 Expose and attach a defensive scroll pause handler on main chat and paper-detail chat containers.

## 2. Verification

- [x] 2.1 Update chat auto-scroll contract tests for the stronger manual-scroll lock.
- [x] 2.2 Run OpenSpec validation, frontend contract tests, and frontend build.
