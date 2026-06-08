## 1. Backend Fix

- [x] 1.1 Change writing section and polish version foreign key ORM columns to UUID types matching migration 018.
- [x] 1.2 Ensure string IDs entering polish version manager are parsed to UUID before querying or inserting.

## 2. Regression Coverage

- [x] 2.1 Add tests that writing ORM foreign key columns use UUID types.
- [x] 2.2 Add PostgreSQL SQL compilation regression coverage showing section creation filters no longer use `VARCHAR` binds.

## 3. Verification

- [x] 3.1 Run focused backend tests and OpenSpec validation.
- [x] 3.2 Commit implementation, archive the OpenSpec change, validate specs, and commit the archive.
