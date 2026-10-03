---
name: service-layer
description: Service/selector layer pattern — all writes in services inside transactions with privilege and company checks; all reads in selectors. Use for every backend ticket.
---
# Service layer

- `selectors.py` / `repositories/`: read functions returning plain data; always take `company_id`.
- `services.py`: write functions. Signature: `create_x(*, actor, company_id, data) -> X`.
  `actor` carries user_id, branch_id, privileges.
- Every service: check privilege → validate (dates in FY, formats, business rules) → open
  transaction → write document → post ledgers (via ledger-posting) → generate doc_no → audit
  row → return. Any failure raises a `DomainError(code, message, fields)`; nothing partial.
- Views/controllers are thin: parse → call service → serialise. No business logic in views,
  serializers, templates or React components.

```python
@transaction.atomic
def post_sales_invoice(*, actor, company_id, invoice_id):
    require(actor, "sales_invoice.create")
    inv = selectors.get_invoice_for_update(company_id, invoice_id)   # SELECT ... FOR UPDATE
    fy = fy_service.assert_open_fy(company_id, inv.doc_date, actor)
    tax = TaxEngine.compute(inv.lines, company_id, inv.party_state_id)
    inv.doc_no = numbering.next(company_id, inv.branch_id, fy.id, "SI")
    ledger.post_voucher(company_id, build_voucher(inv, tax))
    stock.issue(company_id, inv.lines, ref=inv)
    inv.status, inv.posted_at, inv.posted_by = "P", now_utc(), actor.user_id
    inv.save()
    audit.log(actor, "sales_invoice.post", inv.id)
    return inv
```
Node equivalent: `prisma.$transaction(async (tx) => { ... })` with the same order.

Tests: one unit test per rule in the service; integration test per endpoint; use factories with
`company_id` set; always include a cross-company negative test.
