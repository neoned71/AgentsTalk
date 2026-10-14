<!-- src/routes/wallet/+page.svelte -->
<script>
  const API = import.meta.env.PUBLIC_API_BASE || 'http://localhost:8000';
  let address = $state('');
  let chain = $state('');
  let connected = $state(false);
  let loading = $state(false);
  let status = $state('');
  let error = $state(null);
  let linked = $state('');

  async function loadMe() {
    try {
      const r = await fetch(`${API}/auth/me`, { credentials:'include' });
      if (r.ok) { const d = await r.json(); linked = d.wallet_address || ''; }
    } catch (e) {}
  }
  $effect(() => { loadMe(); });

  async function connect() {
    if (!window.ethereum) { error = 'No wallet detected (window.ethereum).'; return; }
    loading = true; error = null; status = 'connecting…';
    try {
      const [addr] = await window.ethereum.request({ method:'eth_requestAccounts' });
      address = addr;
      const chainId = await window.ethereum.request({ method:'eth_chainId' });
      chain = chainId;
      connected = true;
      status = 'linking to account…';
      const cr = await fetch(`${API}/auth/wallet/challenge`, {
        method:'POST', credentials:'include',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({ address })
      });
      const cd = await cr.json();
      if (!cr.ok) throw new Error(cd.detail || JSON.stringify(cd));
      const signature = await window.ethereum.request({ method:'personal_sign', params:[cd.message, address] });
      const vr = await fetch(`${API}/auth/wallet/verify`, {
        method:'POST', credentials:'include',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({ address, signature, message: cd.message })
      });
      const vd = await vr.json();
      if (!vr.ok) throw new Error(vd.detail || JSON.stringify(vd));
      linked = address;
      status = 'Wallet linked to your account.';
    } catch (e) { error = e.message; status = ''; }
    finally { loading = false; }
  }

  async function disconnect() {
    if (!window.ethereum) return;
    try { await window.ethereum.request({ method:'wallet_revokePermissions', params:[{ eth_accounts: {} }] }); } catch (e) {}
    connected = false; address = ''; chain = ''; status = 'Disconnected.';
  }
</script>

<div class="container" style="max-width:960px;">
  <h1>Wallet</h1>
  <p class="muted">Connect and link a wallet for x402 per-call payments and identity.</p>
  <div class="card">
    <h3>Status</h3>
    <div class="row"><span class="lbl">Linked account wallet:</span><span class="val">{linked || '—'}</span></div>
    <div class="row"><span class="lbl">Connected browser wallet:</span><span class="val">{address || '—'}</span></div>
    <div class="row"><span class="lbl">Chain ID:</span><span class="val">{chain || '—'}</span></div>
    <div style="height:12px"></div>
    <div class="row">
      <button class="btn" onclick={connect} disabled={loading}>{loading ? 'Working…' : (connected ? 'Re-link wallet' : 'Connect wallet')}</button>
      {#if connected}<button class="ghost" onclick={disconnect}>Disconnect</button>{/if}
    </div>
    {#if status}<p class="ok">{status}</p>{/if}
    {#if error}<p class="warn">{error}</p>{/if}
  </div>
  <div class="note">
    <span class="note-id">HOW WALLET WORKS</span>
    <span>Connecting asks your wallet (window.ethereum) for an account and signature. The hub verifies the SIWE-style message and links the address to your account. Services can be invoked via x402 by paying USDC on Base; the linked wallet is used for identity and direct per-call payments.</span>
  </div>
</div>

<style>
  .container { max-width:960px; margin:0 auto; padding:0 24px; }
  h1 { font-size:32px; margin:0 0 6px; font-weight:600; letter-spacing:-.02em; }
  .muted { color:#6b768a; margin-bottom:18px; }
  .card { background:#090c12; border-radius:12px; padding:18px; margin:12px 0; }
  .card h3 { margin:0 0 10px; font-size:15px; color:#4ade80; letter-spacing:.04em; text-transform:uppercase; }
  .row { display:flex; gap:10px; align-items:center; margin:6px 0; font-size:13px; }
  .lbl { color:#7b8494; min-width:180px; }
  .val { color:#e7ecf3; font-family:ui-monospace,SFMono-Regular,monospace; word-break:break-all; }
  .btn { background:#4ade80; color:#04120a; border-radius:8px; padding:10px 16px; font-weight:700; cursor:pointer; }
  .btn:disabled { opacity:.6; cursor:default; }
  .ghost { background:transparent; color:#b9c3d1; padding:10px 14px; border-radius:8px; cursor:pointer; }
  .ok { color:#4ade80; font-size:13px; margin-top:8px; }
  .warn { color:#fca5a5; font-size:13px; margin-top:8px; }
</style>
