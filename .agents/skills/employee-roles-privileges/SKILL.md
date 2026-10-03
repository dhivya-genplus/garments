---
name: employee-roles-privileges
description: Employee master, user accounts, roles and the seeded privilege catalogue; how to check privileges in services, APIs and UI. Use for auth, user, role, employee and any privilege-gated feature.
---
# Employee, roles and privileges

Tables: tm_employee, tm_user (employee_id), tm_role, tc_privilege (seeded from code),
tm_role_privilege, tm_user_role (one role per company per user; branch scope list), ta_login.

Privilege codes: `<module>.<action>` with actions view/create/edit/cancel/delete_draft/print/
export, plus special codes (backdate_entry, edit_rate, discount_above_limit,
negative_stock_override, credit_limit_override, unlock_fy, reopen_fy, view_cost_price, pos_only, approve).
Seed file: `core/privileges.py` (Django) / `src/core/privileges.ts` (Node) is the single source;
a management command / script syncs it into tc_privilege.

Checks:
- Service: `require(actor, "sales_invoice.create")` first line of every write service.
- API: permission class / middleware mapping endpoint → privilege (from api-contract table).
- UI: `usePrivilege("sales_invoice.create")` hides buttons; routes guarded in layout.
- Branch scope: selectors filter by actor.branch_ids unless the user holds `<module>.all_branches`.

Employee screens: list, form (code auto from series), link/unlink user, role assignment,
deactivate (record_status I disables login). Password policy, lockout after 5 failures,
JWT access 15 min + refresh, logout everywhere on role change.
