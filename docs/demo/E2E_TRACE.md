# AgentTalk — End-to-End Demo Trace

A real local simulation against the FastAPI backend (`http://localhost:8000`), database Postgres 17 + pgvector, and frontend SvelteKit 5 (`http://localhost:5173`). No external LLM calls were made during the sim (discovery used token-based exact matching; embeddings are optional).

## Environment
- Backend: FastAPI / Uvicorn, auth via httpOnly JWT cookie (`access_token`, 7-day)
- Frontend: SvelteKit 5, layout guard re-checks `/auth/me` on every navigation
- DB: Postgres 17 (pgvector, pg_trgm), 10 tables (users, publishers, services, calls, payouts, api_keys, user_balances, credit_transactions, receipts, + relations)
- Payments: dual rail — account credits (receipts) + x402 USDC on Base; 98/2 split, 30-day escrow
- Routing: `POST /routing/probe` pings each MCP endpoint (5s timeout)

## Actors
- **Provider (admin)**: `admin@agentshub.local` — owns `demo.agentshub.local`, publishes 3 services.
- **Consumer (sim)**: `sim@test.local` — tops up, invokes, receives receipts.

## Seeded services
| Service | Price (USDC) | Description |
|---|---|---|
| summarize-url | 0.002000 | Summarize any web page URL into concise bullet points. |
| translate-text | 0.000800 | Translate text between 50+ languages. |
| image-analyze | 0.005000 | Extract labels/descriptions from images (vision). |

---

## Steps

### 1. Register + login (consumer)
```
POST /auth/register  → 201  { id, email, display_name, role: "consumer" }
POST /auth/login      → 200  Set-Cookie: access_token (HttpOnly, SameSite=Lax)
GET  /auth/me         → 200  { id, email, role, wallet_address }
```
Notes: layout re-checks `/auth/me` on every route change so a freshly logged-in user is recognized and is not bounced back to `/login`.

### 2. Discover (unauthenticated → login → dashboard auto-search)
```
POST /search {"query":"summarize url","limit":5}
→ 200 { "results": [ { "name":"summarize-url", "match":"exact", "score":1.0, "price_atomic":2000, "currency":"USDC" } ], "count":1 }
```
Unauthenticated visitors are redirected to `/login?q=...&next=/dashboard`; after auth the dashboard runs the search automatically and shows the result grid (header metric tiles unlock after first search).

### 3. Ping / routing proof
```
POST /routing/probe {"service_ids":["<summarize-url id>"]}
→ 200 { "results":[{"service_id":"...","ok":false,"latency_ms":null,"endpoint":"https://demo.agentshub.local/mcp"}], "best":null }
```
Demo endpoints are synthetic, so they report `down`; production endpoints return ms and the UI highlights `BEST: lowest ping`.

### 4. Prefund account (credits)
```
POST /billing/topup {"amount_atomic":5000,"reference":"sim2"}   → 200
GET  /billing/balance  → { "balance_atomic": 100045200, "currency":"USDC" }
```

### 5. Reserve a receipt (web credits flow)
```
POST /receipts/create {"service_id":"<id>"}
→ 200 { "receipt_number":"rcpt_TzbV7VdnZMfeJxgI", "amount_atomic":2000, "status":"reserved" }
GET  /receipts  → list shows status "reserved"
```

### 6. Invoke — success (consume)
```
POST /calls/invoke
  {"service_id":"<id>","agent_id":"sim2","request_payload":{},"receipt_number":"rcpt_TzbV7VdnZMfeJxgI","success":true}
→ 200 { "call_id":"d254b08e-...","status":"settled","receipt_consumed":true,
        "escrow_release_at":"2026-11-13T09:14:43Z","platform_fee_atomic":40,"developer_share_atomic":1960 }
GET /receipts → status "consumed"
```

### 7. Invoke — failure (void + refund)
```
POST /receipts/create → rcpt_qw4yhtJufMdxwLw7 (reserved)
POST /calls/invoke ... "success":false
→ 200 { "call_id":null,"status":"voided","receipt_consumed":false,
        "note":"receipt voided; credits restored." }
```

### 8. Scoped API key (agent rail)
```
POST /keys {"name":"sim-key","spend_limit_atomic":10000}
→ 201 { "id":"...","key":"ak_…","spend_limit_atomic":10000 }  (shown ONCE)
GET  /keys  → prefix, spent, revoked flag
```

### 9. Provider flow (admin)
```
POST /publishers {"domain":"demo.agentshub.local","wallet_address":"0x…"} → 201
POST /services {"publisher_id":"…","name":"summarize-url","price_atomic":2000,"..."} → 201 { "embedding_set":false }
GET  /my/services  → list under publisher
GET  /dashboard    → KPIs + payouts + recent calls
```

### 10. Footer / docs
- `/docs`, `/privacy`, `/terms`, `/license`, `/security` are public (auth-exempt) and rendered with the global layout (navbar + footer).

---

## Outcome
- ✅ Login no longer bounces (session re-check on navigation)
- ✅ Search returns results; propagated phrase auto-searches on dashboard
- ✅ Credit receipt reserve → consume (success) / void (failure) works; calls recorded; escrow math 98/2
- ✅ Keys issued with spend caps
- ✅ Probe returns per-service reachability + latency
- ✅ Animated explanatory step lists on every logged-in page
- ✅ Darker global theme, taller navbar, persistent footer, legal/docs pages

## Reproduce
```bash
# backend
cd backend && uvicorn app.main:app --reload
# frontend
cd frontend && npm run dev
# then open http://localhost:5173
```
EOF
echo "md written"