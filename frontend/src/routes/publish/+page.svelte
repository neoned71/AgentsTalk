<!-- src/routes/publish/+page.svelte -->
<script>
  const API = import.meta.env.PUBLIC_API_BASE || 'http://localhost:8000';
  let domain = $state(''); let wallet = $state(''); let name = $state('');
  let description = $state(''); let endpoint = $state('');
  let price = $state('1000');
  let publisherId = $state(null);
  let status = $state('');
  let error = $state(null);
  let drafts = $state([]);

  async function createPublisher() {
    status='creating publisher…'; error=null;
    const r = await fetch(`${API}/publishers`, { method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ domain, wallet_address: wallet, display_name: domain }) });
    const d = await r.json();
    if (!r.ok) { error=JSON.stringify(d); status=''; return; }
    publisherId = d.id; status = 'publisher created';
  }

  async function importDomain() {
    if (!domain || !wallet) { error='domain and wallet required'; return; }
    status='importing .well-known manifests…'; error=null;
    const r = await fetch(`${API}/publishers/import-domain`, { method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ domain, wallet_address: wallet }) });
    const d = await r.json();
    if (!r.ok) { error=JSON.stringify(d); status=''; return; }
    publisherId = d.publisher_id;
    drafts = d.service_drafts || [];
    if (drafts.length) {
      const s = drafts[0];
      name = s.name || name;
      description = s.description || description;
      endpoint = s.mcp_endpoint || endpoint;
      price = String(s.price_atomic || price);
    }
    status = `imported · verified: ${d.verified} · ${drafts.length} draft(s)`;
  }

  async function publish() {
    if (!publisherId) { error='create/import publisher first'; return; }
    status='publishing…'; error=null;
    const r = await fetch(`${API}/services`, { method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ publisher_id: publisherId, name, description, mcp_endpoint: endpoint,
        price_atomic: Number(price), tool_schemas: [] }) });
    const d = await r.json();
    if (!r.ok) { error=JSON.stringify(d); status=''; return; }
    status = 'published: ' + d.id;
  }
</script>

<div class="container">
  <h1>Publish a service</h1>
  <p class="muted">List an MCP service so agents can discover, pay, and call it.</p>
  <div class="note">
    <span class="note-id">HOW IT WORKS</span>
    <span>Step 1 creates a publisher bound to your account (domain + USDC wallet). Step 2 publishes the service manifest: name, description (used for vector search), MCP endpoint, price per call in USDC atomic units, and tool schemas. “Import from .well-known” fetches `/.well-known/mcp.json` / `agentshub.json` to verify domain ownership and prefill drafts. Prices are in the smallest USDC unit (6 decimals: 1,000,000 = 1 USDC).</span>
  </div>

  <div class="card">
    <h3>1. Provider identity</h3>
    <input class="input" bind:value={domain} placeholder="domain (e.g. example.com)" />
    <div style="height:8px"></div>
    <input class="input" bind:value={wallet} placeholder="wallet address (USDC on Base)" />
    <div style="height:12px"></div>
    <div class="row">
      <button class="btn" onclick={createPublisher}>Create publisher</button>
      <button class="btn" style="background:#1f2a44;color:#e6e9f0;" onclick={importDomain}>Import from .well-known</button>
    </div>
    {#if publisherId}<p class="muted">publisher id: {publisherId}</p>{/if}
    {#if drafts.length}
      <p class="muted" style="margin-top:8px;">Found {drafts.length} service draft(s) — fields prefilled below. Prices may need adjusting.</p>
    {/if}
  </div>

  <div class="card">
    <h3>2. Service</h3>
    <input class="input" bind:value={name} placeholder="service name" />
    <div style="height:8px"></div>
    <textarea class="input" rows="3" bind:value={description} placeholder="description (used for search)"></textarea>
    <div style="height:8px"></div>
    <input class="input" bind:value={endpoint} placeholder="mcp endpoint URL" />
    <div style="height:8px"></div>
    <input class="input" bind:value={price} placeholder="price in USDC atomic (6 decimals)" />
    <div style="height:12px"></div>
    <button class="btn" onclick={publish}>Publish service</button>
  </div>

  <p class="muted">{status}</p>
  {#if error}<p style="color:var(--warn)">{error}</p>{/if}
</div>
