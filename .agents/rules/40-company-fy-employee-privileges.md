---
trigger: always_on
---
# Company, financial year, employee, roles and privileges

- `tm_company`: name, legal name, country_id (country pack), timezone, locale, currency_id,
  number_format_id, date_format_id, decimal precision overrides, tax registration no, logo,
  address; `tm_branch` per location with its own doc series. Every user session is bound to one
  company and one default branch.
- Financial year `tm_financial_year`: start_date, end_date, status (O open, L locked, C closed).
  IN: fixed Apr–Mar; SG/AE: any 12 months starting the company's chosen month. No transaction may
  be dated outside an FY or inside a locked/closed FY unless the user holds `backdate_entry` /
  `unlock_fy`. Year-end carries closing balances to opening entries of the next FY, net P&L to
  retained earnings, open bills and stock layers forward with original dates.
- Employee `tm_employee` (code, name, branch_id, department, designation, contact, joining date,
  status) is separate from the login `tm_user` (email/mobile, password hash, employee_id,
  is_active, last_login). One employee may have zero or one user.
- Roles `tm_role` and privileges `tc_privilege` (code-defined, seeded) with `tm_role_privilege`.
  Per module the catalogue is: view, create, edit, cancel, delete_draft, print, export.
  Special privileges: backdate_entry, edit_rate, discount_above_limit, negative_stock_override,
  credit_limit_override, unlock_fy, reopen_fy, view_cost_price, pos_only, approve.
- Effective access = user active ∧ company module enabled ∧ role has privilege. Checked in the
  service layer AND at the API/view layer; the frontend only hides what the API would refuse.
- Approval flows (where the PRD asks): `tx_approval` with level, approver role, status; the
  document status moves to posted only after the last level approves.
