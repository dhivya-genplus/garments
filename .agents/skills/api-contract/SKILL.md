---
name: api-contract
description: How Architect writes and builders consume docs/api-contract.md — endpoint rows, DTO shapes, errors, pagination, auth, versioning. Use when defining or implementing any endpoint.
---
# API contract

Row format: `| GET | /api/v1/customers/ | customer.view | ?q,&state_id,&cursor | CustomerList |`
DTOs defined once below the table in JSON with example values and field rules
(`doc_date: "31/03/2026" (dd/mm/yyyy, within open FY)`).

Conventions: nouns plural, kebab-case paths, ids as integers; list → cursor pagination; detail
`/{id}/`; actions as sub-resources `POST /sales-invoices/{id}/post/`, `/cancel/`.
Standard responses: 200/201 with DTO; 400 `{code:"VALIDATION", fields}`; 403 `{code:"FORBIDDEN",
privilege}`; 409 `{code:"STATE", message}` for FY locked / already posted; 404 never leaks
other-company ids (return 404 for both missing and foreign).
Headers: Authorization Bearer; X-Company-Id; X-Branch-Id optional; Accept-Language.
Versioning: path `/v1/`; breaking change = new version, never an edit to v1 rows.
Frontend generates types from the DTO section (`lib/api/types.ts`); builders must not add
fields the contract does not list.
For django-monolith: the same table lists URL name, view, template and privilege instead of DTOs.
