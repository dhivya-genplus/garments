---
name: e2e-testing
description: End-to-end testing with the Antigravity browser subagent and permanent Playwright / API integration tests, scenario format and evidence. Use for Tester runs and any test-writing step.
---
# E2E testing

Scenario format (from each Given/When/Then):
```
S-<ticket>-<n>: <criterion>
  Login as: <role>   Company: <test company>   Data: <fixture>
  Steps: ...   Expect: ...   Evidence: screenshot/recording name
```
Always add negatives: wrong role (403 / hidden), other company's id (404), invalid date
`2026-03-31` (400), locked FY date (409), negative stock, duplicate code.

Browser subagent run: open staging/local URL, use test users seeded per role, run each scenario,
save screenshots named `S-<ticket>-<n>.png`; never use real client credentials.

Playwright (frontend/<app>/tests/e2e/<module>/<ticket>.spec.ts): page objects per screen,
fixtures per role, reset data via `/api/test/reset` (test env only). API integration tests
(backend/tests/integration/test_<module>.py) call endpoints with the contract payloads.
CI runs: pytest → npm test → playwright (against docker compose stack). A red run blocks merge.
Module smoke list: login, create master, create + post transaction, cancel it, open one report,
export it; then trial balance = 0 and stock identity.
