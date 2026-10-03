---
trigger: always_on
---
# Ledgers: accounting (currency) and stock

- Every posted financial document creates one voucher in `tl_voucher` with lines in
  `tl_voucher_line` (account_id, dr_amount, cr_amount, base_dr, base_cr, currency_id, fx_rate,
  party_id, branch_id, fy_id, doc ref). For every voucher ΣDr = ΣCr to 4 dp, else the service
  raises and nothing is written.
- Posting, cancelling and re-posting are single ACID transactions (`transaction.atomic()` /
  Prisma `$transaction` / knex transaction). Document rows, voucher rows, stock rows and bill
  allocations commit together or not at all.
- Cancelling a posted document reverses its ledger and stock effect exactly (contra lines or
  reversal entries, never DELETE) and restores bill balances.
- Stock ledger `tl_stock` records qty_in / qty_out per item, warehouse, batch/serial (IMEI when
  the product needs it) with cost; valuation uses FIFO layers in `tl_stock_layer`
  (qty_remaining, in_date, cost). Stock on hand = Σ(qty_in − qty_out) = Σ layer.qty_remaining.
  Negative stock is blocked unless the user holds `negative_stock_override`.
- Bills: `tl_bill` balance = amount − Σ allocations, never negative; allocations live in
  `tl_bill_allocation`.
- Invariants checked by tests on every ledger-touching ticket: voucher balance, trial balance
  per FY = 0, stock identity, bill balance ≥ 0, cancel-restores-exactly, no voucher outside an
  open FY.
- Tax computation goes through `TaxEngine.compute(lines, company, party_state)`; India returns
  CGST+SGST or IGST by place of supply, SG/AE return one component. Tax labels (GST/VAT,
  GSTIN/TRN) come from `tc_tax_terminology`.
