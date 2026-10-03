---
description: Architect — turn one PRD module into data model, API contract and sprint tickets in the tracker (owner: Team lead)
---
# /architect <module number or name>
Allowed to edit: docs/architecture.md, docs/api-contract.md, docs/TRACKER.md.
Skills to read: db-schema-design, api-contract, service-layer, plus ledger-posting /
company-fy-setup / employee-roles-privileges / report-builder when the module touches them.

1. Read GEMINI.md (STACK, DATABASE, COUNTRY_PACK, WEBSOCKETS), the module's PRD section and all
   rules. Confirm the previous module's gate is marked passed in the tracker; if not, stop and say so.
2. Plan artifact: list every tm_/tx_/tl_/tc_ table the module needs with columns, references
   (as *_id), indexes, and which existing tables it touches. Wait for approval.
3. Write docs/architecture.md additions: tables, services, selectors, background jobs, ADRs.
4. Write the API contract rows for the module in docs/api-contract.md (django-drf-nextjs and
   node-nextjs) or the URL/view/template list (django-monolith). Mark each with the privilege it
   requires.
5. Split the module into tickets of 2–6 hours of agent work, ordered masters → transactions →
   ledger postings → reports → integrations. Each ticket: ID `T<module>-<nnn>`, title, PRD ref,
   agent (Builder-API / Builder-UI / Tester), files in scope, acceptance criteria copied from the
   PRD, tests required, out of scope, parallel-safe (yes/no and with which ticket).
6. Add the rows to docs/TRACKER.md with status Ready and add the module row with status Not started.
7. Walkthrough: table count, endpoint count, ticket list, which pairs run in parallel, risks.
