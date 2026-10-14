# AgentsTalk (agent services marketplace)

Open-source marketplace for machine-to-machine agent services.

## Stack
- Frontend: SvelteKit 5 (portal for publishers + discovery)
- Backend: FastAPI (Python)
- DB: Postgres + pgvector (Docker)
- Payments: x402 rail (USDC on Base) + platform escrow ledger (30-day hold)
- Embeddings: Gemini text-embedding-004 (pluggable Ollama fallback)

## Quickstart (development)
1. `cp .env.example .env` and fill `GEMINI_API_KEY` and `JWT_SECRET`.
2. `docker compose up -d db`
3. Backend: `cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload`
4. Frontend (requires node): `cd frontend && npm install && npm run dev`

## Production (Docker)
1. Configure `deploy/home-server/.env` from `deploy/home-server/.env.example`.
2. Run `./docker_run.sh` to build/start `agenttalk_db`, `agenttalk_backend`, and `agenttalk_frontend`.
3. Put `deploy/home-server/nginx/agenttalk.neoned71.com.conf` (or your host) in your reverse proxy, update the subdomain, and point TLS at it.
4. Run the reverse proxy's `run_nginx.sh` equivalent.

## Layout
- `backend/` — FastAPI service: registry, search, payments, escrow.
- `frontend/` — SvelteKit 5 portal.
- `backend/sql/init.sql` — schema + pgvector extension.
- `deploy/home-server/` — production Docker Compose and reverse-proxy config.

## License
MIT. See `LICENSE`.
