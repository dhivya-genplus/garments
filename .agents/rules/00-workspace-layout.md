---
trigger: always_on
---
# Workspace layout and repo boundaries

- This workspace folder holds GEMINI.md, .agents/, docs/. `backend/` and each `frontend/<app>/`
  are SEPARATE git repositories. Never run git commands at the workspace root for code changes;
  run them inside the repo you are editing.
- Builder-API edits only `backend/`. Builder-UI edits only `frontend/<app>/`. Architect edits
  only `docs/`. Tester adds files only under `backend/tests/` and `frontend/<app>/tests/`.
  Releaser edits only `CHANGELOG.md` files and `docs/TRACKER.md`.
- STACK in GEMINI.md decides which stack skill applies:
  - django-monolith  → skills/django-monolith (templates rendered by Django, no frontend repo)
  - django-drf-nextjs → skills/django-drf-api + skills/nextjs-frontend (+ django-channels-ws if WEBSOCKETS: yes)
  - node-nextjs      → skills/nodejs-api + skills/nextjs-frontend
- Backend repo layout (Django): `config/`, `apps/<module>/{models,services,selectors,api|views,serializers,tests}/`,
  `core/` (formats, auth, permissions, ledger), `tests/`.
- Backend repo layout (Node): `src/{modules/<module>/{routes,controllers,services,repositories,schemas,tests},core/,db/}`.
- Frontend repo layout (Next.js App Router): `app/(auth)/`, `app/(app)/<module>/`, `components/`,
  `lib/{api,format,i18n,auth}/`, `tests/e2e/`.
- docs/api-contract.md is the only interface between backend and frontend. Neither builder may
  change it; a mismatch is reported to the ticket owner, not patched around.
