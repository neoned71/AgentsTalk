<!-- src/routes/docs/+page.svelte -->
<script>
  const API = import.meta.env.PUBLIC_API_BASE || 'http://localhost:8000';

  const methodColor = (method) =>
    method === 'GET' ? '#22d3ee' : method === 'POST' ? '#4ade80' : method === 'DELETE' ? '#f87171' : '#fbbf24';

  const groups = [
    {
      title: 'Health',
      id: 'health',
      items: [
        {
          method: 'GET',
          path: '/health',
          title: 'Service health',
          auth: 'Public',
          summary: 'Checks database connectivity and reports environment.',
          request: null,
          response: '{ "status": "ok", "environment": "production" }',
          notes: 'Use for readiness/load-balancer checks.'
        }
      ]
    },
    {
      title: 'Authentication',
      id: 'auth',
      items: [
        {
          method: 'POST',
          path: '/auth/register',
          title: 'Register with email and password',
          auth: 'Public',
          summary: 'Creates a user and sets an httpOnly JWT session cookie.',
          request: '{ "email": "user@example.com", "password": "secret", "display_name": "Optional" }',
          response: '{ "id": "...", "email": "...", "display_name": "...", "role": "user" }',
          notes: 'Rate limited by IP. Password required; display name defaults to email.'
        },
        {
          method: 'POST',
          path: '/auth/login',
          title: 'Log in',
          auth: 'Public',
          summary: 'Validates credentials and sets the session cookie.',
          request: '{ "email": "user@example.com", "password": "secret" }',
          response: '{ "id": "...", "email": "...", "display_name": "...", "role": "user", "wallet_address": null }',
          notes: 'Supports browser sessions only; API agents use scoped API keys.'
        },
        {
          method: 'POST',
          path: '/auth/logout',
          title: 'Log out',
          auth: 'Session',
          summary: 'Clears the auth cookie.',
          request: null,
          response: '{ "ok": true }',
          notes: 'No request body.'
        },
        {
          method: 'GET',
          path: '/auth/me',
          title: 'Current user',
          auth: 'Session or API key',
          summary: 'Returns the authenticated user profile.',
          request: null,
          response: '{ "id": "...", "email": "...", "display_name": "...", "role": "user", "wallet_address": null }',
          notes: 'Requires a valid cookie or bearer token.'
        },
        {
          method: 'POST',
          path: '/auth/wallet/challenge',
          title: 'Wallet sign-in challenge',
          auth: 'Public',
          summary: 'Creates a SIWE-style message and nonce for wallet authentication.',
          request: '{ "address": "0x..." }',
          response: '{ "message": "AgentsTalk wants you to sign in...", "nonce": "..." }',
          notes: 'Nonce and expiry are stored in short-lived cookies.'
        },
        {
          method: 'POST',
          path: '/auth/wallet/verify',
          title: 'Verify wallet signature',
          auth: 'Challenge cookies',
          summary: 'Verifies the SIWE signature and creates or updates the user session.',
          request: '{ "address": "0x...", "signature": "0x...", "message": "..." }',
          response: '{ "id": "...", "email": "...", "role": "user", "wallet_address": "0x..." }',
          notes: 'Message must match the previously issued challenge.'
        },
        {
          method: 'POST',
          path: '/auth/pairing/redeem',
          title: 'Redeem pairing code',
          auth: 'Public',
          summary: 'Exchanges a pairing code for a scoped session or key.',
          request: '{ "code": "pairing-code" }',
          response: '{ "ok": true }',
          notes: 'Useful for editor/CLI onboarding flows.'
        }
      ]
    },
    {
      title: 'Discovery and routing',
      id: 'discovery',
      items: [
        {
          method: 'POST',
          path: '/search',
          title: 'Search services',
          auth: 'Public',
          summary: 'Matches exact tokens first, then pgvector cosine similarity.',
          request: '{ "query": "summarize text", "limit": 20, "min_similarity": 0.25 }',
          response: '[{ "id": "...", "name": "...", "price_atomic": 1000, "score": 0.82, "active": true }]',
          notes: 'Exact matches are prioritized. Similarity threshold can be tuned per request.'
        },
        {
          method: 'POST',
          path: '/routing/probe',
          title: 'Probe endpoint latency',
          auth: 'Public',
          summary: 'Pings each result MCP endpoint and returns measured latency.',
          request: '{ "services": [{ "id": "...", "mcp_endpoint": "https://..." }] }',
          response: '[{ "id": "...", "latency_ms": 128, "error": null }]',
          notes: 'The UI auto-pings results and can sort by fastest or cheapest provider.'
        }
      ]
    },
    {
      title: 'Publishers and services',
      id: 'publishing',
      items: [
        {
          method: 'POST',
          path: '/publishers',
          title: 'Create publisher',
          auth: 'Session',
          summary: 'Registers a domain and payout wallet.',
          request: '{ "domain": "example.com", "wallet_address": "0x...", "display_name": "My org" }',
          response: '{ "id": "...", "domain": "example.com", "verified": false }',
          notes: 'Domains can be verified via .well-known files.'
        },
        {
          method: 'GET',
          path: '/publishers/mine',
          title: 'My publishers',
          auth: 'Session',
          summary: 'Lists publishers owned by the current user.',
          request: null,
          response: '[{ "id": "...", "domain": "example.com", "verified": false }]',
          notes: 'Used to populate publisher selectors.'
        },
        {
          method: 'GET',
          path: '/publishers/{publisher_id}',
          title: 'Publisher details',
          auth: 'Public',
          summary: 'Returns a publisher profile and services.',
          request: null,
          response: '{ "id": "...", "domain": "example.com", "display_name": "...", "verified": true }',
          notes: 'Public-facing publisher page data.'
        },
        {
          method: 'POST',
          path: '/publishers/import-domain',
          title: 'Import publisher domain',
          auth: 'Session',
          summary: 'Imports and verifies a publisher from a hosted .well-known file.',
          request: '{ "domain": "example.com" }',
          response: '{ "id": "...", "domain": "example.com", "verified": true }',
          notes: 'Supports agentshub.json and mcp.json metadata.'
        },
        {
          method: 'POST',
          path: '/services',
          title: 'Publish service',
          auth: 'Session',
          summary: 'Creates a priced MCP service manifest.',
          request: '{ "publisher_id": "...", "name": "...", "description": "...", "mcp_endpoint": "https://...", "price_atomic": 1000, "tool_schemas": [] }',
          response: '{ "id": "...", "name": "...", "active": true, "score": null }',
          notes: 'Price is integer USDC atomic units (6 decimals).'
        },
        {
          method: 'GET',
          path: '/services',
          title: 'List services',
          auth: 'Public',
          summary: 'Returns active services for discovery and dashboards.',
          request: null,
          response: '[{ "id": "...", "name": "...", "price_atomic": 1000, "active": true }]',
          notes: 'Admin and provider views may include inactive services.'
        },
        {
          method: 'GET',
          path: '/services/{service_id}',
          title: 'Service details',
          auth: 'Public',
          summary: 'Returns one service including manifest and schemas.',
          request: null,
          response: '{ "id": "...", "name": "...", "tool_schemas": [], "mcp_endpoint": "https://..." }',
          notes: 'Use before invoke to inspect pricing and tools.'
        }
      ]
    },
    {
      title: 'Calls, receipts, and refunds',
      id: 'calls',
      items: [
        {
          method: 'POST',
          path: '/receipts/create',
          title: 'Create payment receipt',
          auth: 'Session or API key',
          summary: 'Creates a receipt and reserves credits for a call.',
          request: '{ "service_id": "...", "amount_atomic": 1000 }',
          response: '{ "receipt_number": "...", "amount_atomic": 1000, "status": "pending" }',
          notes: 'Credits are held until invoke finalization.'
        },
        {
          method: 'GET',
          path: '/receipts',
          title: 'List receipts',
          auth: 'Session or API key',
          summary: 'Returns receipts for the authenticated account.',
          request: null,
          response: '[{ "receipt_number": "...", "status": "consumed", "amount_atomic": 1000 }]',
          notes: 'Includes pending, consumed, and voided states.'
        },
        {
          method: 'GET',
          path: '/receipts/{receipt_number}',
          title: 'Receipt details',
          auth: 'Session or API key',
          summary: 'Looks up a receipt by public number.',
          request: null,
          response: '{ "receipt_number": "...", "status": "pending", "amount_atomic": 1000 }',
          notes: 'Use for audit and reconciliation.'
        },
        {
          method: 'POST',
          path: '/calls/invoke',
          title: 'Invoke service',
          auth: 'Session, API key, or x402',
          summary: 'Executes a paid service call and finalizes credit consumption.',
          request: '{ "service_id": "...", "agent_id": "anonymous", "request_payload": {}, "receipt_number": "..." }',
          response: '{ "call_id": "...", "result": {}, "receipt_number": "..." }',
          notes: 'Use payment_tx for x402 agent flows and receipt_number for credit flows.'
        },
        {
          method: 'GET',
          path: '/calls',
          title: 'Call history',
          auth: 'Session or API key',
          summary: 'Returns paginated call records and status.',
          request: null,
          response: '[{ "id": "...", "service_id": "...", "status": "success", "amount_atomic": 1000 }]',
          notes: 'Supports dashboard and reconciliation workflows.'
        },
        {
          method: 'POST',
          path: '/calls/{call_id}/refund',
          title: 'Refund call',
          auth: 'Session or API key',
          summary: 'Refunds a failed call within the escrow window.',
          request: '{ "reason": "provider error" }',
          response: '{ "call_id": "...", "refunded": true }',
          notes: 'Failure must be client-reported or verifiable.'
        }
      ]
    },
    {
      title: 'Billing, keys, payouts',
      id: 'billing',
      items: [
        {
          method: 'GET',
          path: '/billing/balance',
          title: 'Credit balance',
          auth: 'Session or API key',
          summary: 'Returns the current credit balance.',
          request: null,
          response: '{ "balance_atomic": 1000000, "currency": "USDC" }',
          notes: 'Top-ups and refunds update this balance.'
        },
        {
          method: 'POST',
          path: '/billing/topup',
          title: 'Top up credits',
          auth: 'Session',
          summary: 'Adds credits to the account.',
          request: '{ "amount_atomic": 1000000 }',
          response: '{ "balance_atomic": 2000000 }',
          notes: 'Payment processing depends on platform configuration.'
        },
        {
          method: 'GET',
          path: '/keys',
          title: 'List API keys',
          auth: 'Session',
          summary: 'Lists metadata for scoped agent keys.',
          request: null,
          response: '[{ "id": "...", "name": "...", "prefix": "ak_...", "spend_limit_atomic": 100000 }]',
          notes: 'Full keys are only shown once at creation.'
        },
        {
          method: 'POST',
          path: '/keys',
          title: 'Create API key',
          auth: 'Session',
          summary: 'Creates a scoped key with spend caps.',
          request: '{ "name": "agent", "spend_limit_atomic": 100000 }',
          response: '{ "id": "...", "key": "ak_...", "prefix": "ak_..." }',
          notes: 'Store the returned key immediately.'
        },
        {
          method: 'POST',
          path: '/keys/{key_id}/revoke',
          title: 'Revoke key',
          auth: 'Session',
          summary: 'Deactivates an API key.',
          request: null,
          response: '{ "revoked": true }',
          notes: 'Revoked keys cannot invoke services.'
        },
        {
          method: 'GET',
          path: '/payouts',
          title: 'Payouts',
          auth: 'Session',
          summary: 'Lists provider payout and escrow records.',
          request: null,
          response: '[{ "id": "...", "amount_atomic": 9800, "status": "held" }]',
          notes: 'Funds are released after the escrow hold.'
        },
        {
          method: 'POST',
          path: '/payouts/release-due',
          title: 'Release due payouts',
          auth: 'Admin/cron',
          summary: 'Releases escrowed payouts that are due.',
          request: null,
          response: '{ "released": 3 }',
          notes: 'Usually called by a scheduler.'
        }
      ]
    }
  ];
</script>

<div class="container" style="max-width:1120px;">
  <h1>Documentation</h1>
  <p class="muted">How AgentsTalk works, for humans and agents.</p>

  <div class="docs-summary card">
    <h3>Base URL</h3>
    <p><code>{API}</code>. All paid call endpoints require authentication with a session cookie or API key, except <code>/health</code> and <code>/auth/*</code> login endpoints.</p>
    <p class="doc-note">Authentication uses <code>Authorization: Bearer ak_...</code> for agents and httpOnly session cookies for browsers. Base URL for local development defaults to <code>http://localhost:8000</code>.</p>
  </div>

  {#each groups as group}
    <section class="docs-group">
      <div class="docs-group-header">
        <h2>{group.title}</h2>
        <span class="group-count">{group.items.length} endpoint{group.items.length === 1 ? '' : 's'}</span>
      </div>
      <div class="docs-grid">
        {#each group.items as endpoint}
          <article class="api-card">
            <div class="api-card-top">
              <span class="method-pill" style={`color:${methodColor(endpoint.method)}; border-color:${methodColor(endpoint.method)}40; background:${methodColor(endpoint.method)}14;`}>{endpoint.method}</span>
              <code class="api-path">{endpoint.path}</code>
              <span class="auth-pill">{endpoint.auth}</span>
            </div>
            <h3>{endpoint.title}</h3>
            <p class="api-summary">{endpoint.summary}</p>
            {#if endpoint.request || endpoint.response}
              <details class="api-details">
                <summary>Examples</summary>
                {#if endpoint.request}
                  <div class="example-block">
                    <div class="example-label">Request</div>
                    <pre><code>{endpoint.request}</code></pre>
                  </div>
                {/if}
                {#if endpoint.response}
                  <div class="example-block">
                    <div class="example-label">Response</div>
                    <pre><code>{endpoint.response}</code></pre>
                  </div>
                {/if}
              </details>
            {/if}
            {#if endpoint.notes}
              <p class="api-note">{endpoint.notes}</p>
            {/if}
          </article>
        {/each}
      </div>
    </section>
  {/each}
</div>

<style>
  .docs-summary {
    margin-bottom: 24px;
  }
  .doc-note {
    color: #8b95a5;
    font-size: 13px;
    line-height: 1.6;
  }
  .docs-group {
    margin: 28px 0;
  }
  .docs-group-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 14px;
  }
  .docs-group-header h2 {
    margin: 0;
    font-size: 20px;
    letter-spacing: 0.02em;
  }
  .group-count {
    color: #64748b;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .08em;
  }
  .docs-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 16px;
  }
  .api-card {
    background: var(--panel);
    border: 1px solid #162033;
    border-radius: 14px;
    padding: 18px;
    min-height: 0;
    display: flex;
    flex-direction: column;
    gap: 10px;
    transition: border-color .16s, transform .16s;
  }
  .api-card:hover {
    border-color: #22d3ee55;
    transform: translateY(-2px);
  }
  .api-card-top {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
  }
  .method-pill {
    display: inline-flex;
    align-items: center;
    border: 1px solid;
    border-radius: 999px;
    padding: 4px 9px;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: .08em;
    text-transform: uppercase;
  }
  .api-path {
    background: #050a13;
    border: 1px solid #1f2937;
    border-radius: 8px;
    padding: 5px 8px;
    font-size: 12px;
    color: #c7d2fe;
    overflow-wrap: anywhere;
  }
  .auth-pill {
    margin-left: auto;
    background: #0f1624;
    border: 1px solid #1f2937;
    border-radius: 999px;
    padding: 4px 9px;
    font-size: 10px;
    color: #9aa4b2;
    text-transform: uppercase;
    letter-spacing: .06em;
    white-space: nowrap;
  }
  .api-card h3 {
    margin: 0;
    font-size: 16px;
  }
  .api-summary {
    margin: 0;
    color: #c7d2fe;
    line-height: 1.6;
  }
  .api-details {
    background: #050a13;
    border: 1px solid #162033;
    border-radius: 10px;
    padding: 10px 12px;
  }
  .api-details summary {
    cursor: pointer;
    color: #9aa4b2;
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .06em;
  }
  .example-block + .example-block {
    margin-top: 10px;
  }
  .example-label {
    color: #64748b;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .08em;
    margin-bottom: 6px;
  }
  .api-details pre {
    margin: 0;
    overflow-x: auto;
    white-space: pre-wrap;
    word-break: break-word;
  }
  .api-details code {
    font-size: 12px;
    line-height: 1.5;
  }
  .api-note {
    margin: 0;
    color: #64748b;
    font-size: 12px;
    line-height: 1.5;
  }
  @media (max-width: 860px) {
    .docs-grid {
      grid-template-columns: 1fr;
    }
    .auth-pill {
      margin-left: 0;
    }
  }
</style>
