# Garments ERP & CRM — Antigravity workspace

STACK: django-drf-nextjs        # django-monolith | django-drf-nextjs | node-nextjs
DATABASE: postgresql            # mysql | postgresql (sqlite in local dev)
COUNTRY_PACK: IN                # IN | SG | AE  (sets currency INR, number/date format dd/mm/yyyy, GST, FY 01/04-31/03)
WEBSOCKETS: no                  # yes | no  (Channels / ws server only when PRD needs live updates)
REPOS:
  backend:  ./backend           (git: garments-backend)
  frontend: ./frontend          (git: garments)

## Read before any task
1. docs/PRD.md — the only source of requirements
2. docs/TRACKER.md — the ticket you are working on
3. docs/api-contract.md — fixed contract between backend and frontend
4. .agents/rules/* — always-on rules (loaded automatically)
5. The skill named in your workflow (.agents/skills/<name>/SKILL.md)

## Commands
- Backend run:  cd backend && python manage.py runserver
- Backend test: cd backend && python manage.py test
- Frontend run: cd frontend && npm run dev
- Frontend test: cd frontend && npm test && npx playwright test
- Lint: ruff check . / npm run lint
- Migrate: cd backend && python manage.py migrate

## How work happens
Plan first. Wait for approval. One ticket per conversation. Implement one task at a time
and run tests after each. Record progress in docs/TRACKER.md as the workflow says.
Never touch files outside the repo your workflow allows.
