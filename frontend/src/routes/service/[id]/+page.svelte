<!-- src/routes/service/[id]/+page.svelte (polished invoke flow) -->
<script>
  import AnimatedNote from '$lib/AnimatedNote.svelte';
  const API = import.meta.env.PUBLIC_API_BASE || 'http://localhost:8000';
  let { data } = $props();

  let service = $state(null);
  let loading = $state(true);
  let error = $state(null);

  let payTx = $state('');
  let invoking = $state(false);
  let status = $state('');
  let challenge = $state(null);
  let receipt = $state(null);
  let copied = $state(false);

  async function loadService() {
    loading = true; error = null;
    try {
      const r = await fetch(`${API}/services/${data.id}`, { credentials:'include' });
      if (!r.ok) throw new Error(await r.text());
      service = await r.json();
    } catch (e) { error = e.message; }
    finally { loading = false; }
  }
  $effect(() => { loadService(); });

  function reset() { challenge = null; receipt = null; status = ''; error = null; }

  async function invoke() {
    invoking = true; error = null; status = 'requesting…';
    try {
      const r = await fetch(`${API}/calls/invoke`, {
        method: 'POST', credentials:'include', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          service_id: data.id,
          agent_id: 'demo-agent',
          request_payload: payTx ? { _payment_payload: { txHash: payTx } } : {},
          payment_tx: payTx || null
        })
      });
      const d = await r.json();
      if (r.status === 402) {
        challenge = d; status = 'payment required — sign & settle, then retry'; return;
      }
      if (!r.ok) throw new Error(typeof d === 'string' ? d : (d.detail || JSON.stringify(d)));
      receipt = d; status = 'settled';
    } catch (e) { error = e.message; status = ''; }
    finally { invoking = false; }
  }

  let creditStatus = $state('');

  async function invokeWithCredits(success) {
    invoking = true; error = null; creditStatus = success ? 'reserving receipt…' : 'reserving receipt (will fail)…';
    try {
      const rr = await fetch(`${API}/receipts/create`, {
        method:'POST', credentials:'include',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({ service_id: data.id })
      });
      const rd = await rr.json();
      if (!rr.ok) throw new Error(rd.detail || JSON.stringify(rd));
      creditStatus = 'invoking…';
      const ir = await fetch(`${API}/calls/invoke`, {
        method:'POST', credentials:'include',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({
          service_id: data.id,
          agent_id: 'web-user',
          request_payload: {},
          receipt_number: rd.receipt_number,
          success
        })
      });
      const idd = await ir.json();
      if (!ir.ok) throw new Error(idd.detail || JSON.stringify(idd));
      receipt = idd; challenge = null;
      status = idd.receipt_consumed ? 'receipt consumed' : 'receipt voided (credits restored)';
      creditStatus = '';
    } catch (e) { error = e.message; status = ''; creditStatus = ''; }
    finally { invoking = false; }
  }

  let walletAvailable = $derived(typeof window !== 'undefined' && !!window.ethereum);

  async function payWithWallet() {
    if (!window.ethereum) { error = 'No wallet detected (window.ethereum).'; return; }
    invoking = true; error = null; status = 'connecting wallet…';
    try {
      const { createWalletClient, custom, http } = await import('viem');
      const { wrapFetchWithPayment } = await import('x402-fetch');
      const { base } = await import('viem/chains');

      const [account] = await window.ethereum.request({ method: 'eth_requestAccounts' });
      const walletClient = createWalletClient({ account, chain: base, transport: custom(window.ethereum) });
      const paidFetch = wrapFetchWithPayment(fetch, walletClient);

      status = 'signing payment…';
      const r = await paidFetch(`${API}/calls/invoke`, {
        method: 'POST', credentials:'include', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ service_id: data.id, agent_id: account, request_payload: {} })
      });
      const d = await r.json();
      if (!r.ok) throw new Error(typeof d === 'string' ? d : (d.detail || JSON.stringify(d)));
      receipt = d; challenge = null; status = 'settled via wallet';
    } catch (e) {
      error = e?.message || String(e);
      status = '';
    } finally { invoking = false; }
  }

  async function copyEndpoint() {
    if (!service) return;
    await navigator.clipboard.writeText(service.mcp_endpoint);
    copied = true; setTimeout(() => (copied = false), 1400);
  }
</script>

<div class="container" style="max-width:900px;">
  {#if loading}
    <div class="skel"></div>
    <div class="skel short"></div>
  {:else if error}
    <p class="warn">{error}</p>
    <button class="btn" onclick={loadService}>Retry</button>
  {:else}
    <!-- header -->
    <div class="head">
      <div>
        <div class="crumbs"><a href="/">← Back</a></div>
        <h1>{service.name}</h1>
        <p class="muted">{service.description}</p>
        <AnimatedNote variant="receipt" title="HOW INVOCATION WORKS" note="Endpoint is what your agent calls; price is atomic USDC per call. “Get 402 challenge” returns exact payment requirements; a settled tx hash lets you invoke. “Pay with credits” reserves a receipt, then consumes only on success and restores credits on failure. Wallet mode uses x402." />
      </div>
      <div class="pricecard">
        <div class="price">{service.currency} {(service.price_atomic/1e6).toFixed(6)}</div>
        <div class="pricelbl">per call · {service.chain}</div>
      </div>
    </div>

    <!-- meta grid -->
    <div class="metagrid">
      <div class="meta">
        <div class="metak">Network</div>
        <div class="metav">{service.chain}</div>
      </div>
      <div class="meta">
        <div class="metak">Currency</div>
        <div class="metav">{service.currency}</div>
      </div>
      <div class="meta">
        <div class="metak">Version</div>
        <div class="metav">{service.version || '1.0.0'}</div>
      </div>
      <div class="meta">
        <div class="metak">Publisher</div>
        <div class="metav mono">{service.publisher_id?.slice(0,8)}…</div>
      </div>
    </div>

    <!-- endpoint -->
    <div class="card">
      <div class="cardhead">
        <h3>MCP endpoint</h3>
        <button class="ghostbtn" onclick={copyEndpoint}>{copied ? 'Copied ✓' : 'Copy'}</button>
      </div>
      <code class="endpoint">{service.mcp_endpoint}</code>
      <p class="muted small">Point your MCP client at this URL. AgentsHub collects payment at invoke time.</p>
    </div>

    <!-- tool schemas -->
    {#if service.tool_schemas?.length}
      <div class="card">
        <h3>Tools exposed ({service.tool_schemas.length})</h3>
        <ul class="tools">
          {#each service.tool_schemas as t}
            <li>
              <div class="toolname">{t.name}</div>
              <div class="tooldesc">{t.description || '—'}</div>
            </li>
          {/each}
        </ul>
      </div>
    {/if}

    <!-- invoke -->
    <div class="card invokecard">
      <h3>Invoke</h3>
      <p class="muted small">Dry-run: request without payment returns a 402 challenge with exact requirements. Paste a settled tx hash to invoke.</p>
      <div class="payrow">
        <input class="input" bind:value={payTx} placeholder="0x… payment tx hash (optional)" />
        <button class="btn" onclick={invoke} disabled={invoking}>
          {invoking ? 'Working…' : (payTx ? 'Invoke (settled)' : 'Get 402 challenge')}
        </button>
      </div>
      <div class="creditrow">
        <button class="btn credit" onclick={() => invokeWithCredits(true)} disabled={invoking}>Pay with credits</button>
        <button class="ghostbtn" onclick={() => invokeWithCredits(false)} disabled={invoking}>Simulate failed call (void)</button>
        {#if creditStatus}<span class="muted small">{creditStatus}</span>{/if}
      </div>
      {#if status}<div class="status">{status}</div>{/if}
      {#if error}<div class="warn">{error}</div>{/if}

      {#if challenge}
        <div class="box">
          <div class="boxtitle">402 payment required</div>
          <pre>{JSON.stringify(challenge.paymentRequirements, null, 2)}</pre>
          <p class="muted small">
            Pay <strong>{(challenge.price_atomic/1e6).toFixed(6)} {challenge.currency}</strong> to the
            platform wallet on {challenge.chain}, then retry with the tx hash.
          </p>
        </div>
      {/if}

      {#if receipt}
        <div class="box ok">
          <div class="boxtitle">Settled ✓</div>
          <div class="receiptgrid">
            <div><span>Call ID</span><code>{receipt.call_id}</code></div>
            <div><span>Tx hash</span><code>{receipt.tx_hash}</code></div>
            <div><span>Escrow release</span><code>{receipt.escrow_release_at}</code></div>
            <div><span>Platform fee</span><code>{(receipt.platform_fee_atomic/1e6).toFixed(6)}</code></div>
            <div><span>Developer share</span><code>{(receipt.developer_share_atomic/1e6).toFixed(6)}</code></div>
          </div>
          <p class="muted small">{receipt.note}</p>
          <button class="ghostbtn" onclick={reset}>Try again</button>
        </div>
      {/if}
    </div>

    <!-- economics breakdown -->
    <div class="card">
      <h3>Economics of one call</h3>
      <div class="econrow">
        <div><span>Price</span><b>{(service.price_atomic/1e6).toFixed(6)} {service.currency}</b></div>
        <div><span>Provider (98%)</span><b>{((service.price_atomic*9800/10000)/1e6).toFixed(6)}</b></div>
        <div><span>Platform (2%)</span><b>{((service.price_atomic*200/10000)/1e6).toFixed(6)}</b></div>
        <div><span>Hold window</span><b>30 days</b></div>
      </div>
    </div>
  {/if}
</div>

<style>
  .warn { color:#fca5a5; }
  .muted { color:#8b93a7; }
  .small { font-size:12px; }
  .mono { font-family:ui-monospace,SFMono-Regular,monospace; }

  .skel { height:36px; background:linear-gradient(90deg,#121826,#1f2a44,#121826); background-size:200%; animation:shim 1.2s linear infinite; border-radius:8px; margin:12px 0; }
  .skel.short { width:60%; }
  @keyframes shim { 0%{background-position:200% 0} 100%{background-position:-200% 0} }

  .head { display:flex; justify-content:space-between; align-items:flex-start; gap:24px; flex-wrap:wrap; margin-bottom:20px; }
  .crumbs a { color:#6ee7b7; text-decoration:none; font-size:13px; }
  h1 { margin:6px 0 6px; font-size:clamp(26px,4vw,40px); font-weight:800; letter-spacing:-0.02em; }
  .pricecard { background:rgba(18,24,38,.7); border:1px solid #1f2a44; border-radius:12px; padding:16px 20px; text-align:right; }
  .price { font-size:26px; font-weight:800; background:linear-gradient(90deg,#6ee7b7,#60a5fa); -webkit-background-clip:text; background-clip:text; color:transparent; }
  .pricelbl { font-size:12px; color:#8b93a7; }

  .metagrid { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin:16px 0; }
  .meta { background:rgba(18,24,38,.5); border:1px solid #1f2a44; border-radius:10px; padding:12px; }
  .metak { font-size:11px; text-transform:uppercase; letter-spacing:.1em; color:#8b93a7; }
  .metav { font-size:15px; font-weight:600; margin-top:4px; }

  .card { background:rgba(18,24,38,.6); border:1px solid #1f2a44; border-radius:12px; padding:18px; margin:14px 0; }
  .cardhead { display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; }
  .card h3 { margin:0; font-size:16px; }
  .endpoint { display:block; background:#0e1320; padding:10px 12px; border-radius:8px; word-break:break-all; font-size:13px; color:#6ee7b7; }
  .tools { list-style:none; padding:0; margin:0; display:grid; gap:10px; }
  .tools li { background:#0e1320; border-radius:8px; padding:10px 12px; }
  .toolname { font-weight:700; font-size:14px; }
  .tooldesc { color:#8b93a7; font-size:12px; margin-top:2px; }

  .invokecard { border-color:rgba(110,231,183,.25); }
  .payrow { display:flex; gap:10px; margin-top:8px; }
  .creditrow { display:flex; gap:10px; margin-top:10px; align-items:center; flex-wrap:wrap; }
  .credit { background:#a78bfa; color:#0b0f19; }
  .input { background:#0e1320; color:#e6e9f0; border:1px solid #1f2a44; padding:10px 12px; border-radius:8px; flex:1; }
  .btn { background:#6ee7b7; color:#0b0f19; border:none; padding:10px 16px; border-radius:8px; font-weight:700; cursor:pointer; white-space:nowrap; }
  .btn:disabled { opacity:.6; cursor:default; }
  .ghostbtn { background:transparent; color:#b4bcd0; border:1px solid #1f2a44; padding:5px 10px; border-radius:7px; cursor:pointer; font-size:12px; }
  .status { margin-top:10px; color:#6ee7b7; font-size:13px; }

  .box { background:#0e1320; border:1px solid #1f2a44; border-radius:10px; padding:12px; margin-top:12px; }
  .box.ok { border-color:rgba(110,231,183,.4); }
  .boxtitle { font-weight:700; margin-bottom:6px; }
  .box pre { font-size:11px; color:#b4bcd0; white-space:pre-wrap; margin:6px 0; }
  .receiptgrid { display:grid; grid-template-columns:1fr 1fr; gap:8px; margin:8px 0; }
  .receiptgrid div { display:flex; flex-direction:column; gap:2px; }
  .receiptgrid span { font-size:11px; color:#8b93a7; text-transform:uppercase; }
  .receiptgrid code { font-size:12px; color:#e6e9f0; word-break:break-all; }

  .econrow { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; }
  .econrow div { display:flex; flex-direction:column; gap:4px; }
  .econrow span { font-size:11px; color:#8b93a7; text-transform:uppercase; }
  .econrow b { font-size:15px; }

  .note { margin:14px 0; padding:12px 14px; background:#0e1320; border:1px solid #1f2a44; font-size:12px; color:#94a3b8; line-height:1.5; }
  .note-id { display:block; font-family:ui-monospace,SFMono-Regular,monospace; font-size:10px; color:#4ade80; letter-spacing:.12em; margin-bottom:4px; }
  @media (max-width:720px) {
    .metagrid, .econrow, .receiptgrid { grid-template-columns:1fr 1fr; }
    .payrow { flex-direction:column; }
  }
</style>
