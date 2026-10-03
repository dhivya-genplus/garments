---
trigger: always_on
---
# Git and security

- Branch from `develop`: `feature/<ticket>-<slug>`, `fix/<ticket>-<slug>`, `hotfix/<ticket>-<slug>` (from main).
- Commit format: `<ticket>: <imperative summary>` — small commits after each task.
- Never push to `main` or `develop` directly; never force-push; never rewrite shared history.
- Never read, print, commit or edit `.env`, keys, certificates or anything under `deploy/`.
- Never run: `DROP`, `TRUNCATE`, `rm -rf`, `git push --force`, `manage.py flush`, any command
  against a non-local host, or a migration against staging/production.
- Secrets come from environment variables only; configuration from `tc_*` tables.
- Security checklist on every ticket: company scope on every query, privilege check at service
  and API layer, parameterised queries only, CSRF on forms, file upload type/size limits, no
  debug flags, no stack traces to users, rate limit on auth endpoints.
- Dependencies: add a package only when the plan approved it; pin versions.
