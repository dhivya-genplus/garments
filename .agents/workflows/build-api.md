---
description: Builder-API — implement one backend ticket (models, services, API/views, unit + integration tests) (owner: Backend developer)
---
# /build-api <ticket id>
Allowed to edit: backend/ only (never migrations already applied, never .env, never deploy/).
Skills to read: service-layer, db-schema-design, format-service; then the stack skill from
GEMINI.md STACK (django-monolith | django-drf-api | nodejs-api) and django-channels-ws when
WEBSOCKETS: yes; plus ledger-posting / employee-roles-privileges / report-builder when the
ticket touches them.

1. Read the ticket row, its PRD section, docs/api-contract.md rows for it and docs/architecture.md.
2. Plan artifact: files to create/change, model fields, service functions with signatures,
   endpoints/views, tests (one per acceptance criterion + ledger invariants if applicable).
   STOP for approval.
3. Set the ticket to "In progress" with the owner's name (ask the owner's name if unknown).
4. Create branch `feature/<ticket>-<slug>` from develop inside backend/.
5. Implement in order, running tests after each step:
   a. models + migration (new migration file only)
   b. selectors (reads) and services (writes, inside transactions, privilege checks, company scope)
   c. API serializers/views or Django views+templates, exactly matching the contract
   d. unit tests for services, integration tests for endpoints, invariant tests for ledgers
   e. seed/fixture data if the ticket needs it
6. Run the full backend test suite and lint. Fix failures; never weaken tests.
7. Self-check: list each acceptance criterion with the test that proves it.
8. Commit per step (`<ticket>: ...`). Do not push until the owner says so.
9. Walkthrough + the exact tracker row update (status "In review", branch). The owner applies
   it with /update-tracker.
