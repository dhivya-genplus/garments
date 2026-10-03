---
name: django-monolith
description: Stack skill for STACK=django-monolith — Django 5 with server-rendered templates, MySQL/MariaDB, HTMX for interactivity, single repo. Use for both Builder-API and Builder-UI on monolith products.
---
# Django monolith + MySQL

Repo: backend/ only (no frontend repo). `config/settings/{base,local,staging,prod}.py`,
`apps/<module>/{models.py,selectors.py,services.py,forms.py,views.py,urls.py,tests/}`,
`core/{base_models.py,formats.py,permissions.py,ledger/,numbering.py,middleware.py}`,
`templates/<module>/`, `static/`.
- DB: mysqlclient, `OPTIONS: {"charset": "utf8mb4", "init_command": "SET sql_mode='STRICT_TRANS_TABLES'"}`,
  `USE_TZ=True`, `TIME_ZONE="UTC"`; company tz applied by FormatService.
- Views: class-based, thin; forms do parsing via FormatService fields (`DMYDateField`,
  `MoneyField`); list pages use the shared `ListView` with cursor pagination and DataTable template;
  modals/partials via HTMX. Template tags `{% fmt_money %} {% fmt_date %} {% has_priv "x.y" %}`.
- Auth: Django auth with custom user → tm_user; company/branch/FY in session; middleware builds
  `request.ctx`.
- i18n: `gettext_lazy` everywhere; `locale/<lang>/LC_MESSAGES`.
- Background jobs: Celery + Redis (exports, year-end) or `django-q`; decide in architecture.md.
- Tests: pytest-django, factory_boy; `tests/integration` hits views with the test client.
- Admin template design follows the Genplus admin theme (see admin-template-design skill if present).
Commands: `pytest -q`, `ruff check .`, `python manage.py makemigrations <app>`, `compilemessages`.
