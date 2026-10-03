---
name: company-fy-setup
description: Company, branch, country pack and financial-year setup, FY validation and year-end carry-forward. Use for Module 0/1 tickets and anything that reads company settings.
---
# Company and financial year

Setup order (Module 0 seed): tc_country/tc_* packs → tm_company → tm_branch (main) →
tm_financial_year (current) → tc_doc_series per branch per doc type → tm_account (chart of
accounts from country template) → admin role + privileges → admin user.

Company wizard screens: 1 Company details, 2 Country & formats (inherit pack, override
precision/date/number), 3 Branches, 4 Financial year, 5 Document numbering, 6 Admin user.

FY service:
- `assert_open_fy(company_id, doc_date, actor)` → FY row or DomainError("FY_LOCKED"/"NO_FY")
- `lock_fy`, `unlock_fy` (privilege unlock_fy), `close_fy` → runs year-end
- Year-end: compute closing balances per balance-sheet account → opening voucher in next FY;
  net P&L → retained earnings/capital; carry open bills and stock layers with original dates;
  idempotent (re-run replaces the carry-forward voucher).
- IN pack: FY = 1 Apr – 31 Mar; SG/AE: start month from company; FY name "2026-27".

Session context: company_id, branch_id, fy_id (default current), locale, timezone, privilege set
— built once at login, refreshed on company/branch switch, sent to frontend as `/me`.
