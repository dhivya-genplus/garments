---
name: nodejs-api
description: Stack skill for STACK=node-nextjs backend — Node.js 20 + TypeScript + Fastify + Prisma on MySQL or PostgreSQL, applying the same Genplus conventions as Django. Use for Builder-API on Node products.
---
# Node.js API (Fastify + Prisma)

Repo: backend/. `src/{server.ts,modules/<module>/{routes.ts,controller.ts,service.ts,repository.ts,schemas.ts,tests/},core/{context.ts,format.ts,privileges.ts,errors.ts,ledger/,numbering.ts},db/{schema.prisma,migrations/,seed.ts}}`.
- Prisma models map to tm_/tx_/tl_/tc_ tables (`@@map`), NO `@relation`; `Decimal` columns;
  `DateTime` stored UTC; business dates as `@db.Date`.
- Context plugin: verifies JWT, reads X-Company-Id, loads company pack + privileges into
  `request.ctx`; every repository function takes `companyId` first.
- Schemas: zod (or TypeBox) for request/response matching the contract; dd/mm/yyyy parsed via
  `core/format`; errors → `{code,message,fields}` through a global error handler.
- Services: `prisma.$transaction` wrapping document write + ledger post + numbering; `require(ctx, "x.y")` first.
- Cursor pagination helper in `core/pagination.ts`.
- Jobs: BullMQ + Redis for exports/year-end; WebSockets (if needed) via `@fastify/websocket`
  with company-scoped rooms, same rules as django-channels-ws.
- Tests: Vitest + supertest; integration tests run against docker compose DB; invariant tests
  from ledger-posting.
Commands: `npm run dev`, `npm test`, `npm run lint`, `npx prisma migrate dev --name <ticket>`, `npx prisma db seed`.
