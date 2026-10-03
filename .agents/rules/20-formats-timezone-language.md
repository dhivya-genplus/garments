---
trigger: always_on
---
# Number, date, timezone and language handling

- Storage: all timestamps in UTC. All dates (`doc_date`, due dates) are calendar dates in the
  company's timezone, stored as DATE.
- The company timezone (`tm_company.timezone`) is the single temporal authority. No user-level
  timezone override. Day boundaries, "today", FY boundaries and overdue arithmetic are computed in
  the company timezone.
- Date input/output format is `dd/mm/yyyy`; datetime is `dd/mm/yyyy HH:MM` (24-hour). The
  backend rejects any other format with a structured validation error. Country pack may change
  the separator (IN: `dd-mm-yyyy` allowed on display only); ISO 8601 is used ONLY inside the API
  contract when the contract says so, never shown to users.
- Numbers: formatting is data, not code. `FormatService` (backend) / `lib/format` (frontend) read
  `tc_number_format` from the country pack: IN uses Indian grouping (12,34,567.89); SG/AE use
  1,234,567.89. Decimal places: money 2, qty 3, rate 4, unless the company overrides precision.
- Currency symbol and code come from `tc_currency`; multi-currency transactions store
  `currency_id`, `fx_rate` (18,4) and base-currency amounts alongside document-currency amounts.
- Never hard-code a date pattern, number pattern, currency symbol, tax label or FY start month.
- Language: all user-facing strings go through i18n (Django `gettext` / Next.js `next-intl`
  message files under `messages/<locale>.json`). Default locale `en`; the company sets its
  locale; RTL locales (ar) set `dir="rtl"` on `<html>`. Database content is not translated.
- Frontend displays what the API returns already formatted for lists/reports; it formats only
  on-screen inputs, using the same country pack rules fetched once at login.
