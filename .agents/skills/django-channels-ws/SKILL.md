---
name: django-channels-ws
description: Add Django Channels WebSockets (live dashboards, notifications, POS sync) when GEMINI.md WEBSOCKETS=yes. Use only for tickets that the PRD marks as real-time.
---
# Django Channels (WebSockets)

Only when WEBSOCKETS: yes. Daphne/uvicorn ASGI, Redis channel layer.
- Consumers under `apps/<module>/consumers.py`; routing in `config/asgi.py`; groups named
  `company_<id>_<topic>` — every message is company-scoped; auth via JWT in the first message.
- Services publish events after commit (`transaction.on_commit`) through `events.publish(company_id, topic, payload)`;
  consumers never read the DB directly for business data.
- Payload shapes are listed in docs/api-contract.md under "WebSocket topics".
- Frontend: `lib/ws/useTopic(topic)` with reconnect/backoff; UI must stay correct without WS
  (polling fallback) — WS is an enhancement, never the only path.
- Tests: `channels.testing.WebsocketCommunicator` per topic; cross-company subscription must be refused.
Deploy: separate systemd service for the ASGI worker; Nginx `location /ws/` upgrade.
