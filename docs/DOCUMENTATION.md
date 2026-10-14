# AgentTalk — Complete Platform Documentation

This document is the canonical technical and operational reference for
AgentTalk, the centralized MCP service marketplace for machine-to-machine
agents. It covers architecture, setup, configuration, security, payments,
data models, APIs, frontend, operations, and integration patterns.

## 1. What AgentTalk does

AgentTalk lets providers publish machine services with a per-call price in
cryptocurrency (USDC on Base, 6 decimals). Consumers and agents:

1. Discover services through exact-first plus semantic (pgvector) search.
2. Invoke services through `/.well-known` MCP manifests.
3. Pay either per invocation via x402 (`402 Payment Required`) or with
   prefunded credits using server-side receipts.
4. Settle funds through a 98/2 split with a 30-day escrow for consumer
   protection (cashback / refund window).
5. Manage listings, calls, API keys, receipts, payouts, wallet linkage, and
   routing/probe results from a web UI.

## 2. Repository layout

```
agentsTalk/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app, CORS, lifespan startup
│   │   ├── config.py               # Settings (env-driven)
│   │   ├── auth.py                 # JWT, cookies, SIWE verification
│   │   ├── db.py                   # async SQLAlchemy engine/sessions
│   │   ├── models.py               # ORM models
│   │   ├── routers/                # auth, publishes, services, search, calls,
│   │   │                           # receipts, billing, keys, routing, payouts
│   │   └── services/               # x402, embeddings, wellknown, security
│   ├── sql/init.sql                # fresh-database DDL (extensions/indexes/fts)
│   └── requirements.txt
├── frontend/
│   └── src/                        # SvelteKit 5 UI, routes, components
├── docs/                           # audit, trace, and this canonical doc
├── frontend/static/demo-flow.json  # recorded fixture used by /demo replay page
├── docker-compose.yml
├── .env.example
└── README-related files
```

## 3. Backend architecture

- Framework: FastAPI (async), Pydantic settings, SQL Alchemy 2 async ORM.
- Database: PostgreSQL 17, pgvector, pg_trgm.
- Auth: email/password + JWT in `httponly` cookie; wallet link via SIWE-style
  EIP-191 signature; agent-facing API keys.
- Search: exact ILIKE/conditions, then pgvector cosine or an embedding provider.
- Pay: x402 around a facilitator / payment payload or credit receipts provider.
- Settlement: 98% developer share, 2% platform fee; calls held in escrow 30
  days and released to `payouts`.
- Startup:
  - imports required extensions
  - creates tables from SQL Alchemy metadata when missing
  - upgrades existing `services` table with `search_tsv`
  - installs the FTS trigger and GIN index
  - starts a periodic escrow release loop

## 4. Configuration (`backend/app/config.py` + `.env`)

All settings are read through `pydantic-settings` from environment and `.env`.
Secrets are never committed. `.env` is ignored; `.env.example` documents defaults.

Important settings:
- `ENVIRONMENT`: `dev`, `staging`, or `production`
- `DATABASE_URL`
- `JWT_SECRET`: required, 32+ chars; blank is rejected at startup
- `JWT_EXP_MINUTES`
- `SECURE_COOKIES`: required `true` in production TLS
- `CORS_ORIGINS`: explicit list, comma-separated
- `PLATFORM_WALLET_ADDRESS`: platform receiver for x402 payments
- `PLATFORM_FEE_BPS` (default 200 basis points)
- `ESCROW_HOLD_DAYS` (default 30)
- `ALLOW_DEMO_TOPUP`: only enable in non-production/local (default false)
- `X402_FACILITATOR_URL`
- `USDC_ADDRESS`
- `CHAIN`
- `embedding_provider`, `gemini_api_key`, `gemini_embedding_model`, etc.

## 5. Database and startup

Fresh local setup:
1. `docker compose up -d postgres` or use `backend/sql/init.sql`.
2. Start backend once so SQLAlchemy creates all tables.
3. `CREATE EXTENSION` and FTS trigger/index are applied automatically.
4. HNSW vector index may be added manually if size requires it.

Do not drop existing tables in production without migrations. SQLAlchemy
`create_all` adds missing tables but does not alter existing schema; manual
`ALTER TABLE` is included only for the `search_tsv` upgrade. For broader
changes, write migrations before deploy. A dedicated migration baseline should
be adopted before first external production install.

## 6. Authentication and authorization

### 6.1 Web sessions
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/logout`
- `GET /auth/me`

Uses bcrypt passwords and JWT stored in `access_token` cookie:
- `HttpOnly`, `SameSite=Lax`, `Secure` controlled by `SECURE_COOKIES`.

### 6.2 Wallet login (linked account)
- `POST /auth/wallet/challenge` returns a signed SIWE-style message with
  address/nonce/domain/issued/expires.
- `POST /auth/wallet/verify` verifies EIP-191 signature and links wallet.
- Nonces and expiry are stored in short-lived cookies.
- Challenge messages bind host/domain plus address.

### 6.3 API keys (agents)
- Format: `ak_<prefix>_<secret>`
- Stored as SHA-256 hash; prefix lookup then hash comparison.
- `spend_limit_atomic` and `spent_atomic` available; exceeded limit rejects requests.
- Keys are created/revoked through `/keys`.

### 6.4 Roles
- `consumer`, `provider`, `admin`
- Admin bypasses ownership checks on publishers/services/calls/payouts.
- Public publisher detail hides wallet address unless owner/admin.

### 6.5 Rate limiting
A basic in-memory IP limiter protects auth routes. In horizontally-scaled
deployments, replace with a shared limiter / Redis.

## 7. Credit, receipt, and x402 payment flow

### 7.1 Prefunded credits
- `POST /billing/topup` is disabled by default in non-demo environments.
- `GET /billing/balance`
- `POST /receipts/create` locks balance, deducts credits, creates `reserved`
  receipt with a unique receipt number, and records a balance debit.
- `POST /calls/invoke` with `receipt_number` consumes receipt and records the
  call. Calls `success:false` void the receipt and restore credits.

### 7.2 x402 (agents direct)
- Providers specify price/currency/chain.
- Calling `/calls/invoke` without payment returns `402` and payment requirements.
- Client submits wallet-signed payment payload.
- Backend calls facilitator verify + settle and records transaction hash.
- Platform wallet must be configured; unset platform wallet refuses the call.

### 7.3 Escrow and payouts
- 2% fee to platform, 98% developer share.
- Each settled call gets `escrow_release_at = now + 30 days`.
- `POST /payouts/release-due` (or periodic loop) releases settled calls and
  creates payout records for publisher shares.
- Refund endpoint sets status to refunded (only before release or via dispute).

## 8. Security architecture and hardening

- `JWT_SECRET` must be set; weak blank defaults are rejected on startup.
- CORS uses explicit allowed origins; credentials allowed only against list.
- Cookies: `HttpOnly`, `SameSite=Lax`, `Secure` optional.
- No publisher wallet leakage.
- Calls and payouts are scoped to caller ownership unless admin.
- SSRF guards block private and reserved hosts for `import-domain` and probes.
- Generic exception handler prevents stack traces from reaching clients.
- x402 settlement reports explicitly checked.
- Escrow/receipt operations are row-locked to reduce races.
- Secure `.env.example` included.
- Documentation and API endpoints proxy through expected auth.

Run behind TLS and a reverse proxy in production. Set a strong `JWT_SECRET`,
`SECURE_COOKIES=true`, `ENVIRONMENT=production`, and lawful CORS list.

## 9. REST API overview

- `POST /auth/*`
- `GET /auth/me`
- `/publishers` — create/mine/get/import-domain
- `/services` — publish/list/get
- `/search` — search
- `/calls` — invoke, list, refund
- `/receipts` — create/list/get
- `/billing` — balance/topup
- `/keys` — manage API keys
- `/routing` — probe and runtime sorting
- `/payouts` — release-due/list
- `/health` — service and database status

## 10. Deployment and operations

- Run Postgres with pgvector and pg_trgm.
- Backend from repository root with `--app-dir backend` so `.env` resolves.
- Run Uvicorn behind reverse proxy.
- Frontend: `npm run build` / preview, set `PUBLIC_API_BASE`.
- Use `docker compose` where available:
  - postgres service
  - backend build (runtime dependencies)
  - frontend preview server
- Plan backups, monitoring, structured logs, alerts on 5xx, DB health, payout jobs.

## 11. Production release checklist

- Configure production environment and TLS.
- Rotate JWT secret.
- Set platform wallet and facilitator account.
- Delete or disable demo topup.
- Run health and smoke tests.
- Verify all `docs`/legal fields are counsel-approved.
- Add monitoring and backups.
- Validate wallet flows and x402 with testnet/mainnet.
- Validate each search route returns only authorized data.
- Configure logs and audit trails.
- Ensure release-due job scheduled securely.
- Load test vector search and probe endpoints.

## 12. Frontend pages

Landing, login, discover, service detail, dashboard, publisher page, publish,
my services, my calls, credits, wallet, keys, demo replay,
documentation/license pages, persistent navbar/footer.

## 13. Integration with popular tools (quick starts)

### FastAPI
```python
import requests
BASE="https://api.your-agenttalk-host"
key="ak_..."
r=requests.post(f"{BASE}/search", headers={"Authorization": "Bearer "+key},
               json={"query":"translate text","limit":5})
match=r.json()["results"][0]
payload=requests.post(f"{BASE}/calls/invoke",
    headers={"Authorization":"Bearer "+key},
    json={"service_id":match["id"],"agent_id":"script","request_payload":{"text":"hello"}})
print(payload.status_code, payload.json())
```

### MCP JSON component
```json
{
  "mcpServers": {
    "agenttalk-summarize": {
      "command": "npx",
      "args": ["mcp-remote", "https://provider.example.com/mcp/summarize-url"]
    }
  }
}
```
Use `/discover` to resolve manifests; each service returns `mcp_endpoint`.

### LangChain-style
```python
from langchain.tools import tool
import requests, os
BASE=os.environ["AGENTTALK_API"]
KEY=os.environ["AGENTTALK_KEY"]

@tool
def summarize_url(url: str) -> str:
    services=requests.post(f"{BASE}/search", headers={"Authorization":f"Bearer {KEY}"},
        json={"query":"summarize url"}).json()["results"]
    svc=next(s for s in services if "summarize" in s["name"])
    r=requests.post(f"{BASE}/calls/invoke", headers={"Authorization":f"Bearer {KEY}"},
        json={"service_id":svc["id"],"agent_id":"langchain-agent","request_payload":{"url":url}})
    return r.json()["mcp_endpoint"]
```

### OpenAI Agents / functions
Wrap AgentTalk search + invoke actions as tool definitions. The invoker can select `service_id` and call `/calls/invoke`; lock API key spend to cap risk.

### AutoGen / CrewAI
Register tool functions mapped to common task classes. Search budget using `/routing/probe` to prefer lowest latency or cheapest services.

### x402 wallet client
For no-credit clients, handle 402 payment requirements with USDC on Base.
```
curl -i -X POST http://localhost:8000/calls/invoke -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{"service_id":"...","agent_id":"cli","request_payload":{"x":1}}'
```
Then sign and resend with `_payment_payload` or `payment_tx`.

## 14. Notes for developers

- Keep migrations explicit.
- Add Alembic baseline before external launch.
- Avoid relying on embeddings if unavailable; exact search still returns.
- Treat x402 as real-money: test on testnet first.
- Add unit/integration/E2E tests and CI before release.
