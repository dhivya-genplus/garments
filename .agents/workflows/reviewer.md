---
description: Reviewer — check a ticket's diff against rules, PRD criteria and the security list; write findings (owner: second developer, never the ticket owner)
---
# /reviewer <ticket id>
Allowed to edit: nothing. Output is a review note artifact only.
Skills to read: service-layer, db-schema-design, format-service, and the stack skill.

1. Read the ticket, PRD criteria, api-contract rows, and the diff on the ticket branch
   (`git diff develop...feature/<ticket>-*` inside the repo).
2. Check, in this order, and list findings with file:line:
   a. Scope — files outside the ticket, unrelated changes, new packages not in the plan
   b. Rules — tm_/tx_ naming, no FK, record_status filter, company_id on every query, decimals,
      numbering service, UTC storage, format service used, i18n used, privilege checks at
      service AND API layer
   c. Ledgers — balanced vouchers, single transaction, cancel reversal, invariant tests present
   d. Contract — request/response exactly as docs/api-contract.md
   e. Tests — one per acceptance criterion, none weakened; negative cases present
   f. Security — parameterised queries, no secrets, no debug, upload limits, rate limits on auth
   g. Migrations — reversible, no edits to applied migrations
3. Severity: BLOCKER (must fix before merge), MAJOR (fix in this ticket), MINOR (note).
4. Verdict: "Ready for human review" only when there are no BLOCKERs. Never approve or merge;
   a human does both.
5. Suggest rule-file changes if the same finding appears for the second time across tickets.
