## 1. Remove Table Repair Runtime

- [x] 1.1 Remove Marker adapter script, Marker dependency file, Docker Marker install/config, and parser settings.
- [x] 1.2 Remove low-quality table repair API route, Celery task, maintenance job implementation, and frontend maintenance action handling.
- [x] 1.3 Remove table repair tests and contract assertions.

## 2. Remove Visual Asset Runtime

- [x] 2.1 Remove visual asset service, API routes, response fields, status builders, and maintenance recommendations.
- [x] 2.2 Remove frontend visual evidence cards, visual asset status display, and paper detail extraction actions.
- [x] 2.3 Remove visual asset tests and contract assertions.

## 3. Reset Active OpenSpec Surface

- [x] 3.1 Remove the in-progress table repair stabilization change because that direction is discarded.
- [x] 3.2 Validate OpenSpec after removing active visual/table repair requirements.

## 4. Verification

- [x] 4.1 Run targeted backend tests for paper maintenance and paper reader grounding.
- [x] 4.2 Run targeted frontend contract tests for paper library/detail flows.
- [x] 4.3 Commit the removal.
