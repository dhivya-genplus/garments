---
description: Builder-UI — implement one frontend or template ticket against the API contract (owner: Frontend developer)
---
# /build-ui <ticket id> [app folder, default frontend/web]
Allowed to edit: frontend/<app>/ only (django-monolith: backend/templates/ and backend/static/ only).
Skills to read: nextjs-frontend (or django-monolith for templates), format-service, api-contract,
e2e-testing.

1. Read the ticket row, PRD section, docs/api-contract.md rows it consumes, and the design
   files/screens referenced in the ticket.
2. Plan artifact: routes/pages, components, API client functions (typed from the contract),
   state, form validation, i18n keys, empty/loading/error states, privilege-based visibility,
   tests. STOP for approval.
3. Set the ticket to "In progress"; create branch `feature/<ticket>-<slug>` inside the app repo.
4. Implement in order, running tests after each:
   a. API client + types from the contract (mock server if backend ticket not merged yet)
   b. page and components; all strings via i18n; dates/numbers via lib/format
   c. forms: client validation mirrors contract rules; server errors mapped to fields
   d. privilege checks: hide/disable per role from the session's privilege list
   e. component tests; Playwright e2e for the user story
5. Run lint, type check, unit and e2e tests.
6. If the API does not match the contract, stop and report the mismatch to the ticket owner;
   do not patch around it in the frontend.
7. Self-check against acceptance criteria; Walkthrough with screenshots; tracker row update
   (status "In review", branch) for the owner to apply.
