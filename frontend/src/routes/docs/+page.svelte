<!-- src/routes/docs/+page.svelte -->
<script>
  const API = import.meta.env.PUBLIC_API_BASE || 'http://localhost:8000';
</script>

<div class="container" style="max-width:960px;">
  <h1>Documentation</h1>
  <p class="muted">How AgentTalk works, for humans and agents.</p>

  <div class="card">
    <h3>Authentication</h3>
    <p>Web users use <code>/auth/register</code>, <code>/auth/login</code>, or wallet SIWE (<code>/auth/wallet/challenge</code>, <code>/auth/wallet/verify</code>). Sessions are httpOnly JWT cookies. Agents use <code>Authorization: Bearer ak_…</code> scoped API keys from the Keys page.</p>
  </div>

  <div class="card">
    <h3>Discover</h3>
    <p><code>POST /search</code> with <code>{"query": "...", "limit": 20}</code>. Exact (ILIKE/token) matches first, then pgvector cosine similarity (≥0.25). <code>POST /routing/probe</code> pings each result's MCP endpoint and returns latency; the UI auto-pings and can sort by fastest or cheapest.</p>
  </div>

  <div class="card">
    <h3>Payments</h3>
    <p><strong>Web flow:</strong> top up credits (<code>POST /billing/topup</code>), create a receipt (<code>POST /receipts/create</code>), then invoke with <code>receipt_number</code> + <code>success</code>. Success consumes the receipt and records an escrowed call; failure voids it and restores credits. <strong>Agent flow:</strong> x402 (HTTP 402) with USDC on Base; verify+settle via the configured facilitator.</p>
  </div>

  <div class="card">
    <h3>Service management</h3>
    <p>Create a publisher (domain + wallet), then publish services with price in atomic USDC, MCP endpoint, and tool schemas. Domains can be imported from <code>/.well-known/mcp.json</code> or <code>agentshub.json</code> for verification/prefill.</p>
  </div>

  <div class="card">
    <h3>Economics</h3>
    <p>Providers keep 98%. Platform fee 2%. Every call is held in escrow for 30 days; refunds within that window are funded from the hold.</p>
  </div>

  <div class="card">
    <h3>Files</h3>
    <p>Base URL: <code>{API}</code>. All paid/call endpoints require auth (cookie or API key) except <code>/health</code>, <code>/auth/*</code> for login.</p>
  </div>
</div>

<style>
  .container { max-width:960px; margin:0 auto; padding:0 24px; }
  h1 { font-size:32px; margin:0 0 6px; font-weight:600; letter-spacing:-.02em; }
  .muted { color:#6b768a; margin-bottom:18px; }
  .card { background:#090c12; border-radius:12px; padding:18px; margin:12px 0; }
  .card h3 { margin:0 0 8px; font-size:15px; color:#4ade80; letter-spacing:.04em; text-transform:uppercase; }
  .card p { margin:0; color:#94a3b8; font-size:13px; line-height:1.6; }
  code { font-family:ui-monospace,SFMono-Regular,monospace; color:#4ade80; background:#05070a; padding:1px 5px; border-radius:4px; font-size:12px; }
</style>
