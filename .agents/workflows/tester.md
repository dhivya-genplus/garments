---
description: Tester — run the browser subagent through acceptance criteria and write permanent e2e/integration tests (owner: QA)
---
# /tester <ticket id or module number>
Allowed to edit: backend/tests/, frontend/<app>/tests/ only. Never edit application code or
existing tests except to add new ones.
Skills to read: e2e-testing, plus ledger-posting for ledger invariants.

1. Read the ticket(s), PRD acceptance criteria and api-contract rows. Confirm the app is running
   (local or staging URL given by the human).
2. Plan artifact: one scenario per acceptance criterion, plus negative cases (wrong role, wrong
   company, invalid date/number format, locked FY, negative stock) and ledger invariant checks.
   STOP for approval.
3. Browser run: use the browser subagent to execute each scenario on the running app; capture a
   screenshot per scenario and the recording. Record pass/fail per criterion.
4. Permanent tests: write Playwright tests (frontend/<app>/tests/e2e/) and/or API integration
   tests (backend/tests/integration/) for every passed scenario. Run them; they must pass.
5. For a module run: also execute the module smoke list (login, one master, one transaction,
   cancel it, one report) and the trial-balance / stock identity checks.
6. Report: table of criterion → result → evidence link; defects as revision rows (type bug,
   source QA) for the tracker; status "Testing" → "Merged" is applied by the owner only after
   review, so you propose "E2E: pass/fail" for the row.
