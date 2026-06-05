## 1. Backend Service Reliability

- [x] 1.1 Fix non-streaming LLM response processing so successful calls return content and record usage.
- [x] 1.2 Fix research Idea generation tuple handling while preserving paper source metadata and stored references.

## 2. API Route Reliability

- [x] 2.1 Move the Markdown paper export endpoint before the dynamic paper-detail route and remove the shadowed declaration.
- [x] 2.2 Remove the duplicate profile update route while preserving email and display-name updates.

## 3. Frontend Action Reliability

- [x] 3.1 Remove the invalid paper-detail share action that calls the research-project sharing endpoint.

## 4. Regression Verification

- [x] 4.1 Add focused backend regression tests for LLM return behavior, Idea prompt construction, route reachability, and unique profile route registration.
- [x] 4.2 Run backend regression tests, compile checks, frontend production build, and local endpoint smoke checks.
