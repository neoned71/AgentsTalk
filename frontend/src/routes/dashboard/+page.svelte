<script>
  import { page } from '$app/stores';
  const API = import.meta.env.PUBLIC_API_BASE || 'http://localhost:8000';
  let q = $derived($page.url.searchParams.get('q') || '');
  let searchQuery = $state('');
  let searchResults = $state([]);
  let searching = $state(false);
  let hasSearched = $state(false);
  let searchError = $state(null);
  let payouts = $state([]);
  let calls = $state([]);
  let loading = $state(true);
  let error = $state(null);
  let releasing = $state(false);
  let lastRefresh = $state(null);

  async function load() {
    loading = true; error = null;
    try {
      const [p, c] = await Promise.all([
        fetch(`${API}/payouts`).then(r => r.json()),
        fetch(`${API}/calls?limit=100`).then(r => r.json())
      ]);
      payouts = Array.isArray(p) ? p : [];
      calls = Array.isArray(c) ? c : [];
      lastRefresh = new Date();
    } catch (e) { error = e?.message || 'Failed to load'; }
    finally { loading = false; }
  }

  async function release() {
    releasing = true; error = null;
    try {
      await fetch(`${API}/payouts/release-due`, { method: 'POST' });
      await load();
    } catch (e) { error = e?.message || 'Release failed'; }
    finally { releasing = false; }
  }

  $effect(() => { load(); });

  let settledCalls = $derived(calls.filter(c => c.status === 'settled' || c.status === 'released'));
  let refundedCalls = $derived(calls.filter(c => c.status === 'refunded'));
  let totalRevenue = $derived(settledCalls.reduce((a, c) => a + (c.price_atomic || 0), 0));
  let pendingPayouts = $derived(payouts.filter(p => p.status === 'pending'));
  let releasedPayouts = $derived(payouts.filter(p => p.status !== 'pending'));
  let totalPending = $derived(pendingPayouts.reduce((a, p) => a + (p.amount_atomic || 0), 0));

  async function doSearch(term = searchQuery) {
    const t = (term || '').trim();
    if (!t) return;
    searching = true; searchError = null;
    hasSearched = true;
    try {
      const r = await fetch(`${API}/search`, {
        method:'POST', credentials:'include',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({ query: t, limit: 20 })
      });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail || JSON.stringify(d));
      searchResults = d.results;
    } catch (e) { searchError = e.message; }
    finally { searching = false; }
  }

  $effect(() => {
    if (q) { searchQuery = q; doSearch(q); }
    else { searchQuery = searchQuery || 'summarize'; doSearch(searchQuery); }
  });
</script>

<div class="page">
  <header class="head">
    <div class="head-main">
      <h1>Dashboard</h1>
      <p class="meta">Last refresh: {lastRefresh ? lastRefresh.toLocaleTimeString() : '—'}</p>
    </div>
    <div class="head-actions">
      <button class="ghost" onclick={load} disabled={loading}>{loading ? 'Loading' : 'Refresh'}</button>
      <button class="primary" onclick={release} disabled={releasing}>{releasing ? 'Releasing' : 'Release due payouts'}</button>
    </div>
  </header>

  {#if error}<div class="banner">{error}</div>{/if}

  {#if q || searchResults.length}
    <section class="block">
      <div class="block-head">
        <div>
          <h2>Search results</h2>
          <p class="meta">{searching ? 'searching…' : searchResults.length + ' results'}{q ? ` for “${q}”` : ''}</p>
        </div>
        <div class="search">
          <input bind:value={searchQuery} placeholder="refine query…" onkeydown={(e)=>e.key==='Enter' && doSearch()} />
          <button onclick={() => doSearch()} disabled={searching}>{searching ? '…' : 'Search'}</button>
        </div>
      </div>

      {#if searchError}<div class="banner">{searchError}</div>{/if}

      {#if searchResults.length}
        <div class="results">
          {#each searchResults as r}
            <a class="result" href={`/service/${r.id}`}>
              <div class="result-top">
                <span class="result-name">{r.name}</span>
                <span class="price">{r.currency} {(r.price_atomic/1e6).toFixed(6)}</span>
              </div>
              <p class="result-desc">{r.description}</p>
              <div class="result-foot">
                <span class="pill">{r.match}</span>
                <span class="score">score {r.score}</span>
              </div>
            </a>
          {/each}
        </div>
      {:else if !searching && !searchError}
        <div class="empty">No matches. Try another query.</div>
      {/if}
    </section>
  {/if}

  {#if hasSearched}
    <section class="metrics">
      <div class="metric">
        <span class="metric-label">Total calls</span>
        <span class="metric-value">{calls.length}</span>
      </div>
      <div class="metric">
        <span class="metric-label">Settled</span>
        <span class="metric-value">{settledCalls.length}</span>
      </div>
      <div class="metric">
        <span class="metric-label">Refunded</span>
        <span class="metric-value">{refundedCalls.length}</span>
      </div>
      <div class="metric">
        <span class="metric-label">Revenue</span>
        <span class="metric-value">{(totalRevenue/1e6).toFixed(4)}<span class="unit">USDC</span></span>
      </div>
      <div class="metric">
        <span class="metric-label">Pending payouts</span>
        <span class="metric-value">{pendingPayouts.length}</span>
      </div>
      <div class="metric">
        <span class="metric-label">Pending amount</span>
        <span class="metric-value">{(totalPending/1e6).toFixed(4)}<span class="unit">USDC</span></span>
      </div>
    </section>

    <section class="stack">
      <div class="block">
        <div class="block-head">
          <div><h2>Payouts</h2><p class="meta">{payouts.length} total</p></div>
        </div>
        {#if loading}
          <div class="loading">Loading payouts…</div>
        {:else if payouts.length === 0}
          <div class="empty">No payouts yet. After the 30-day escrow window closes, earnings release here.</div>
        {:else}
          <div class="table">
            <table>
              <thead>
                <tr><th>ID</th><th>Publisher</th><th>Amount</th><th>Status</th><th>Created</th><th>Tx</th></tr>
              </thead>
              <tbody>
                {#each payouts as p}
                  <tr>
                    <td class="mono">{p.id.slice(0,8)}…</td>
                    <td class="mono">{p.publisher_id.slice(0,8)}…</td>
                    <td class="amount">{(p.amount_atomic/1e6).toFixed(6)} <span class="unit">{p.currency}</span></td>
                    <td><span class="status {p.status}">{p.status}</span></td>
                    <td class="meta">{new Date(p.created_at).toLocaleString()}</td>
                    <td class="mono">{p.tx_hash ? p.tx_hash.slice(0,10)+'…' : '—'}</td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        {/if}
      </div>

      <div class="block">
        <div class="block-head">
          <div><h2>Recent calls</h2><p class="meta">Last {calls.length}</p></div>
        </div>
        {#if loading}
          <div class="loading">Loading calls…</div>
        {:else if calls.length === 0}
          <div class="empty">No calls yet. Invoke a service to see it here.</div>
        {:else}
          <div class="table">
            <table>
              <thead>
                <tr><th>ID</th><th>Service</th><th>Agent</th><th>Price</th><th>Status</th><th>Created</th></tr>
              </thead>
              <tbody>
                {#each calls as c}
                  <tr>
                    <td class="mono">{c.id.slice(0,8)}…</td>
                    <td class="mono">{c.service_id.slice(0,8)}…</td>
                    <td class="meta">{c.agent_id}</td>
                    <td class="amount">{(c.price_atomic/1e6).toFixed(6)}</td>
                    <td><span class="status {c.status}">{c.status}</span></td>
                    <td class="meta">{new Date(c.created_at).toLocaleString()}</td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        {/if}
      </div>
    </section>
  {/if}
</div>

<style>
  .page { max-width: 1180px; margin: 0 auto; padding: 48px 24px 80px; }

  .head { display:flex; justify-content:space-between; align-items:flex-end; gap:18px; flex-wrap:wrap; margin-bottom:44px; }
  h1 { margin:0; font-size:36px; line-height:1; font-weight:600; letter-spacing:-0.03em; }
  .meta { margin:6px 0 0; color:#7b8494; font-size:12px; letter-spacing:.02em; }
  .head-actions { display:flex; gap:10px; }
  button { font:inherit; cursor:pointer; border-radius:8px; padding:9px 14px; font-size:13px; font-weight:500; transition:background .15s ease,color .15s ease; }
  .ghost { background:#111725; color:#c8cfda; }
  .ghost:hover { background:#182232; }
  .ghost:disabled { opacity:.55; cursor:default; }
  .primary { background:#4ade80; color:#04120a; }
  .primary:hover { background:#63e79b; }
  .primary:disabled { opacity:.55; cursor:default; }

  .banner { background:rgba(248,113,113,.08); color:#fca5a5; padding:12px 14px; border-radius:8px; font-size:13px; margin-bottom:20px; }

  .block { padding: 8px 0 4px; }
  .block-head { display:flex; justify-content:space-between; align-items:flex-end; gap:16px; flex-wrap:wrap; margin-bottom:16px; }
  .block-head h2 { margin:0; font-size:17px; font-weight:600; letter-spacing:-0.01em; }
  .block-head .meta { margin-top:4px; }

  .search { display:flex; gap:8px; min-width:min(460px,100%); }
  .search input { flex:1; background:#0e1524; color:#e2e8f0; border-radius:8px; padding:10px 12px; font-family:ui-monospace,SFMono-Regular,monospace; font-size:13px; outline:none; }
  .search input::placeholder { color:#5b6472; }
  .search button { background:#1d283a; color:#dbe4f0; }
  .search button:hover { background:#263550; }
  .search button:disabled { opacity:.6; cursor:default; }

  .results { display:grid; grid-template-columns:repeat(auto-fill,minmax(280px,1fr)); gap:10px; }
  .result { display:block; background:#0f1624; border-radius:10px; padding:16px; text-decoration:none; color:inherit; transition:background .15s ease, transform .15s ease; }
  .result:hover { background:#141d2f; transform:translateY(-1px); }
  .result-top { display:flex; justify-content:space-between; align-items:baseline; gap:10px; }
  .result-name { font-weight:600; font-size:15px; letter-spacing:-0.01em; }
  .price { color:#4ade80; font-family:ui-monospace,SFMono-Regular,monospace; font-size:12px; }
  .result-desc { color:#94a3b8; font-size:13px; line-height:1.5; margin:8px 0 12px; }
  .result-foot { display:flex; align-items:center; justify-content:space-between; font-size:11px; color:#8b95a5; }
  .pill { background:#182234; color:#cbd5e1; padding:3px 8px; border-radius:999px; }
  .score { font-family:ui-monospace,SFMono-Regular,monospace; opacity:.75; }

  .metrics { display:grid; grid-template-columns:repeat(6,1fr); gap:10px; margin-top:44px; }
  .metric { padding:20px 4px 0; }
  .metric-label { display:block; color:#7b8494; font-size:10px; text-transform:uppercase; letter-spacing:.14em; }
  .metric-value { display:block; margin-top:12px; font-size:29px; font-weight:600; letter-spacing:-0.02em; font-family:ui-monospace,SFMono-Regular,monospace; color:#e7ecf3; }
  .unit { margin-left:6px; font-size:12px; color:#8b95a5; font-weight:400; }

  .stack { margin-top:48px; display:flex; flex-direction:column; gap:52px; }
  .loading, .empty { color:#8b95a5; font-size:13px; padding:22px 2px; }

  .table { overflow-x:auto; }
  table { width:100%; border-collapse:separate; border-spacing:0 10px; min-width:720px; }
  thead th { color:#7b8494; font-size:10px; text-transform:uppercase; letter-spacing:.14em; text-align:left; padding:0 14px 10px; font-weight:500; }
  tbody tr { background:#111827; }
  tbody td { padding:14px; font-size:13px; color:#e7ecf3; }
  tbody td:first-child { border-radius:8px 0 0 8px; }
  tbody td:last-child { border-radius:0 8px 8px 0; }
  tbody tr:hover td { background:#182234; }
  .mono { font-family:ui-monospace,SFMono-Regular,monospace; color:#b9c3d1; font-size:12px; }
  .amount { font-family:ui-monospace,SFMono-Regular,monospace; }
  .status { padding:4px 10px; border-radius:999px; font-size:11px; font-weight:600; text-transform:capitalize; }
  .status.pending { background:rgba(250,204,21,.12); color:#facc15; }
  .status.settled { background:rgba(74,222,128,.12); color:#4ade80; }
  .status.released { background:rgba(96,165,250,.12); color:#60a5fa; }
  .status.refunded { background:rgba(248,113,113,.12); color:#f87171; }

  @media (max-width: 900px) {
    .metrics { grid-template-columns:repeat(3,1fr); }
  }
  @media (max-width: 560px) {
    .metrics { grid-template-columns:repeat(2,1fr); }
    .head { align-items:flex-start; }
    .search { width:100%; }
  }
</style>
