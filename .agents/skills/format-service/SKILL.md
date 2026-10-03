---
name: format-service
description: Number, date, currency and timezone formatting from the company's country pack; backend FormatService and frontend lib/format. Use whenever a value is parsed from or shown to a user.
---
# FormatService

Country pack rows (`tc_country`, `tc_number_format`, `tc_date_format`, `tc_timezone`,
`tc_currency`) are loaded once per company into `CompanyContext`.

Backend (`core/formats.py` or `src/core/format.ts`):
- `parse_date("31/03/2026") -> date` strict `dd/mm/yyyy`; raise ValidationError otherwise
- `format_date(d) -> "31/03/2026"`; `format_datetime(utc_dt) -> "31/03/2026 14:05"` in company tz
- `to_company_tz(utc_dt)`, `day_start_utc(date)`, `day_end_utc(date)` for range filters
- `format_number(Decimal, kind="money"|"qty"|"rate")` → grouping from pack (IN: 12,34,567.89)
- `format_money(Decimal, currency_id)` → symbol + number
- `fy_for(date)` → financial year row or None

Frontend (`lib/format/`): same functions on top of the pack fetched at login; use `Intl` only
with the pack's locale and explicit `minimumFractionDigits`; dates are always built/parsed with
the dd/mm/yyyy helpers, never `new Date(string)`.

Rules: inputs are parsed at the boundary once; internally use `Decimal`/`date`/UTC; format once
at the output boundary. Report/list endpoints return pre-formatted display strings plus raw values.
