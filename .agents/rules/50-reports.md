---
trigger: always_on
---
# Reports and report builder

- Reports read from selectors/read-models, never from services, and contain no business logic.
- Order of evaluation: scope by company (and branch privilege) → apply additive filters → anchor
  to a date range in the company timezone → deterministic ordering → cursor pagination.
- Report definitions are data in `tc_report` (code, title, module, columns, filters, default
  sort, group-by, totals, privilege). The report builder renders any definition; adding a report
  means adding a definition plus a selector, not a new screen.
- Large reports run async: a report session (`tx_report_session`) stores parameters; export
  (PDF/XLSX) re-runs the same session and streams the file with metadata headers (company,
  branch, period, generated at, user).
- Summary tables (`ts_*`) may be pre-computed for dashboards with an integrity check against the
  ledgers; they are never the source of truth.
- Every figure shown must be reproducible from ledgers; a report that disagrees with the trial
  balance or stock identity is a defect in the report, not the ledger.
