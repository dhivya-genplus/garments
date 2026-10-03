---
description: Scout — read client inputs and draft or extend the PRD with acceptance criteria and open questions (owner: Product Owner)
---
# /scout [module name or "all"]
Allowed to edit: docs/PRD.md only.

1. Read GEMINI.md and everything in docs/inputs/ (notes, transcripts, sample documents, screenshots).
   If docs/inputs/ is empty, ask for inputs and stop.
2. Extract and list: user roles, business processes, entities (masters/transactions), reports,
   integrations, country pack needs (currency, tax, FY, languages), non-functional needs.
3. For the requested module, draft the PRD section: goals, stories with Given/When/Then
   acceptance criteria, business rules, reports. Use the PRD template headings exactly.
4. Append to "8. Open questions": every assumption you made and every question the client has not
   answered, numbered, each with the PRD line it affects.
5. Do NOT invent requirements, numbers, tax rules or screens that the inputs do not support;
   mark unknowns as [TBC].
6. Present the draft as an artifact for the Product Owner to comment on. Apply comments.
7. Walkthrough: sections written, open questions count, suggested module order.
   Tracker: nothing to update unless the Product Owner marks the PRD version as approved.
