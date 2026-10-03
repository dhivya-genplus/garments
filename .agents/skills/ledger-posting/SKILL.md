---
name: ledger-posting
description: Post, cancel and verify accounting vouchers (tl_voucher) and stock movements (tl_stock, FIFO layers) with invariant tests. Use for any ticket that touches money or stock.
---
# Ledger posting

## Voucher
`post_voucher(company_id, voucher)`: validate ΣDr == ΣCr (4 dp) and FY open; insert tl_voucher +
tl_voucher_line; update bill balances via tl_bill / tl_bill_allocation. Returns voucher id.
`reverse_voucher(company_id, voucher_id, reason)`: inserts a contra voucher with lines swapped,
links `reversed_by`; original is never deleted or edited.

Typical mappings (chart of accounts ids resolved from `tm_account` by code):
- Sales invoice: Dr Customer (party), Cr Sales, Cr Output tax components
- Purchase bill: Dr Purchases / Stock, Dr Input tax, Cr Supplier
- Receipt: Dr Bank/Cash, Cr Customer (+ allocation to bills)
- Stock adjustment: Dr/Cr Stock adjustment, Cr/Dr Inventory

## Stock
`stock.receive(company_id, lines, ref)`: tl_stock qty_in rows + new tl_stock_layer per line.
`stock.issue(company_id, lines, ref)`: consume FIFO layers; cost of goods from layers; block if
insufficient and actor lacks `negative_stock_override`. Serial/IMEI items: one layer per unit.
Cancel: re-create layers with original in_date.

## Invariant tests (copy into every ledger ticket)
```python
def test_voucher_balanced(): assert sum(dr) == sum(cr)
def test_trial_balance_zero(fy): assert selectors.trial_balance(company, fy).total == 0
def test_stock_identity(item): assert qty_in - qty_out == sum(layer.qty_remaining)
def test_bill_balance_non_negative(): ...
def test_cancel_restores_exactly(): post → snapshot → cancel → assert ledgers == before
def test_no_voucher_in_locked_fy(): ...
```
