---
name: django-drf-api
description: Stack skill for STACK=django-drf-nextjs backend — Django 5 + DRF REST API with JWT, company scoping, cursor pagination, MySQL or PostgreSQL. Use for Builder-API on API products.
---
# Django + DRF API

Repo: backend/. Layout as django-monolith but `api/` instead of `views.py`/templates:
`apps/<module>/api/{serializers.py,views.py,urls.py}`; `config/urls.py` mounts `/api/v1/`.
- DB: mysqlclient or psycopg; identical models; `DATABASE` from GEMINI.md decides settings only.
- Auth: `djangorestframework-simplejwt`; `CompanyContextMiddleware` reads X-Company-Id, verifies
  the user belongs to it, builds `request.ctx`; `/api/v1/me/` returns context + privileges.
- Permissions: `HasPrivilege("customer.view")` per view, mapped from the contract table.
- Serializers: parse dd/mm/yyyy and money strings with FormatService fields; output both raw and
  display values for lists/reports (`amount`, `amount_display`).
- Pagination: custom `CursorPagination` keyset on (sort key, id); page size max 100.
- Errors: exception handler maps DomainError → {code, message, fields}; 404 for foreign ids.
- OpenAPI: drf-spectacular; the generated schema must match docs/api-contract.md (Reviewer checks).
- CORS: only the frontend origin per environment; rate limit on `/auth/*`.
- Background: Celery + Redis for exports, notifications, year-end.
Commands: `pytest -q`, `ruff check .`, `python manage.py spectacular --file schema.yml`.
