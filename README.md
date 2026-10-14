# AgentTalk (agent services marketplace)

## Stack
- Frontend: SvelteKit 5 (portal for publishers + discovery)
- Backend: FastAPI (Python)
- DB: Postgres + pgvector (docker)
- Payments: x402 rail (USDC on Base) + platform escrow ledger (30-day hold)
- Embeddings: Gemini text-embedding-004 (pluggable Ollama fallback)

## Quickstart
1. `cp .env.example .env` and fill `GEMINI_API_KEY`.
2. `docker compose up -d db`
3. Backend: `cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload`
4. Frontend (requires node): `cd frontend && npm install && npm run dev`

## Layout
- `backend/` — FastAPI service: registry, search, payments, escrow.
- `frontend/` — SvelteKit 5 portal.
- `backend/sql/init.sql` — schema + pgvector extension.
