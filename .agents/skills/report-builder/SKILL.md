---
name: report-builder
description: Data-driven report definitions (tc_report), selectors, filters, cursor pagination, async export to PDF/XLSX. Use for any report, dashboard or export ticket.
---
# Report builder

Definition (tc_report JSON): code, title, module, privilege, columns [{key, label_key, type
(text/date/money/qty/rate), align, total: sum|none}], filters [{key, type (date_range/select/
text/party/item/branch), required, default}], default_sort, group_by, drill_to (report code).

Engine: `run_report(company_id, actor, code, params, cursor)`:
1. scope → company + actor.branch_ids; 2. parse filters via FormatService; 3. date range to UTC
bounds; 4. call `selectors.report_<code>` returning an ordered queryset/query; 5. paginate by
cursor (keyset on sort key + id); 6. format display values; 7. totals from a separate aggregate
query over the same filters.

Export: `tx_report_session` row (params, user, created_at) → background job renders XLSX
(openpyxl / exceljs) or PDF (WeasyPrint / puppeteer) with header block (company, branch,
period, generated at dd/mm/yyyy HH:MM, user) → file stored → notification. Never render large
exports inline in the request.

Frontend: one generic `<ReportPage code="...">` reads the definition from `/api/v1/reports/<code>`
and renders filters, table, totals, export buttons; no per-report pages.

Standard reports to seed: day book, trial balance, P&L, balance sheet, outstanding receivables/
payables with ageing, stock summary, stock ledger, tax summary (country pack labels).
