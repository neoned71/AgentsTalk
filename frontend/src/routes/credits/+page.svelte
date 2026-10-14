<!-- src/routes/credits/+page.svelte -->
<script>
  const API = import.meta.env.PUBLIC_API_BASE || 'http://localhost:8000';
  let balance = $state(0);
  let currency = $state('USDC');
  let amount = $state('1000000'); // 1 USDC
  let loading = $state(true);
  let error = $state(null);
  let status = $state('');

  async function load() {
    loading = true; error = null;
    try {
      const r = await fetch(`${API}/billing/balance`, { credentials:'include' });
      const d = await r.json();
      if (!r.ok) throw new Error(JSON.stringify(d));
      balance = d.balance_atomic; currency = d.currency;
    } catch (e) { error = e.message; }
    finally { loading = false; }
  }
  async function topup() {
    status = ''; error = null;
    try {
      const r = await fetch(`${API}/billing/topup`, {
        method:'POST', credentials:'include',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({ amount_atomic: Number(amount), reference:'demo' })
      });
      const d = await r.json();
      if (!r.ok) throw new Error(JSON.stringify(d));
      balance = d.balance_atomic; currency = d.currency; status = 'Top up successful (demo).';
    } catch (e) { error = e.message; }
  }
  $effect(() => { load(); });
</script>

<div class="container">
  <h1>Credits</h1>
  <p class="muted">Pre-fund your account to use the web UI flow (receipts). Top-up is a demo action in this build.</p>
  <div class="note">
    <span class="note-id">HOW IT WORKS</span>
    <span>Credits are held in your account balance. “Pay with credits” on a service reserves a receipt: the price is deducted and locked. If the call succeeds, the receipt is consumed and 98% accrues to the provider (held 30 days in escrow). If it fails, the receipt is voided and credits returned. This keeps funds safe without wallet signatures for every call.</span>
  </div>
  {#if loading}<div class="skel"></div>
  {:else if error}<p class="warn">{error}</p>
  {:else}
    <div class="card">
      <div class="bal">{(balance/1e6).toFixed(6)}</div>
      <div class="muted">{currency} balance</div>
    </div>
    <div class="card">
      <h3>Top up (demo)</h3>
      <input class="input" bind:value={amount} placeholder="amount in USDC atomic (6 decimals)" />
      <div style="height:10px"></div>
      <button class="btn" onclick={topup}>Add credits</button>
      {#if status}<p class="ok">{status}</p>{/if}
    </div>
  {/if}
</div>

<style>
  .muted { color:#8b93a7; } .warn { color:#fca5a5; } .ok { color:#6ee7b7; }
  h1 { font-size:clamp(26px,4vw,40px); margin:0 0 4px; font-weight:800; }
  .card { background:rgba(18,24,38,.6); border:1px solid #1f2a44; border-radius:12px; padding:18px; margin:14px 0; }
  .bal { font-size:40px; font-weight:800; background:linear-gradient(90deg,#6ee7b7,#60a5fa); -webkit-background-clip:text; background-clip:text; color:transparent; }
  .input { background:#0e1320; color:#e6e9f0; border:1px solid #1f2a44; padding:10px 12px; border-radius:8px; width:100%; box-sizing:border-box; }
  .btn { background:#6ee7b7; color:#0b0f19; border:none; padding:10px 16px; border-radius:8px; font-weight:700; cursor:pointer; }
  .skel { height:34px; background:linear-gradient(90deg,#121826,#1f2a44,#121826); background-size:200%; animation:shim 1.2s linear infinite; border-radius:8px; margin:10px 0; }
  @keyframes shim { 0%{background-position:200% 0} 100%{background-position:-200% 0} }
  .container { max-width:720px; margin:0 auto; padding:0 24px; }
</style>
