<!-- src/routes/discover/+page.svelte -->
<script>
  import { page } from '$app/stores';
  const API = import.meta.env.PUBLIC_API_BASE || 'http://localhost:8000';
  let q = $derived($page.url.searchParams.get('q') || '');
  let query = $state('');
  let results = $state([]);
  let loading = $state(false);
  let error = $state(null);
  let invoked = $state(false);
  let probing = $state(false);
  let sortMode = $state('best'); // best (latency) | cheapest
  let latencies = $state({});

  async function search() {
    if (!query.trim()) return;
    loading = true; error = null; invoked = true;
    latencies = {};
    try {
      const r = await fetch(`${API}/search`, {
        method:'POST', credentials:'include',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({ query, limit: 20 })
      });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail || JSON.stringify(d));
      results = d.results;
      await probe(results.map(x => x.id));
    } catch (e) { error = e.message; }
    finally { loading = false; }
  }

  async function probe(ids) {
    if (!ids.length) return;
    probing = true;
    try {
      const r = await fetch(`${API}/routing/probe`, {
        method:'POST', credentials:'include',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({ service_ids: ids })
      });
      const d = await r.json();
      if (!r.ok) throw new Error(JSON.stringify(d));
      const m = {};
      for (const x of d.results) m[x.service_id] = x;
      latencies = m;
    } catch (e) { /* probe optional */ }
    finally { probing = false; }
  }

  let sortedResults = $derived(() => {
    const arr = [...results];
    if (sortMode === 'cheapest') {
      return arr.sort((a,b) => a.price_atomic - b.price_atomic);
    }
    // best: reachable lowest latency first, then cheap
    return arr.sort((a,b) => {
      const la = latencies[a.id]; const lb = latencies[b.id];
      const ra = la && la.ok ? la.latency_ms : 999999;
      const rb = lb && lb.ok ? lb.latency_ms : 999999;
      if (ra !== rb) return ra - rb;
      return a.price_atomic - b.price_atomic;
    });
  });

  $effect(() => { if (q && !loading) { query = q; search(); } });

  let bestId = $derived(() => {
    if (sortMode !== 'best') return null;
    const reach = results.filter(r => latencies[r.id]?.ok);
    if (!reach.length) return null;
    return reach.sort((a,b) => latencies[a.id].latency_ms - latencies[b.id].latency_ms)[0].id;
  });
</script>

<div class="container">
  <h1>Discover services</h1>
  <p class="muted">Exact matches first, then semantically similar. Auto-pinged for latency. Choose fastest or cheapest.</p>
  <div class="note">
    <span class="note-id">HOW IT WORKS</span>
    <span>The hub embeds your query (Gemini/Ollama) and ranks exact name/ID hits first, then cosine-similar services above 0.25. Each result is pinged in parallel to measure reachability and latency; FASTEST sorts by ping then price, CHEAPEST by price only. Logged-out visitors are redirected to login before any result is shown.</span>
  </div>

  <div class="searchbar">
    <input class="sinput" bind:value={query} placeholder="Try: summarize url, translate text..." onkeydown={(e)=>e.key==='Enter' && search()} />
    <button class="btn" onclick={search} disabled={loading}>{loading ? 'Searching…' : 'SEARCH'}</button>
  </div>

  {#if error}<p class="warn">{error}</p>{/if}

  {#if results.length}
    <div class="toolbar">
      <span class="muted small">{results.length} results · {probing ? 'pinging…' : 'pinged'}</span>
      <div class="toggle">
        <button class:active={sortMode==='best'} onclick={() => (sortMode='best')}>FASTEST</button>
        <button class:active={sortMode==='cheapest'} onclick={() => (sortMode='cheapest')}>CHEAPEST</button>
      </div>
    </div>
    <div class="grid">
      {#each sortedResults() as r}
        <a class="card" class:best={bestId() === r.id} href={`/service/${r.id}`}>
          <div class="card-row">
            <strong>{r.name}</strong>
            <span class="price">{r.currency} {(r.price_atomic/1e6).toFixed(6)}</span>
          </div>
          <p class="card-desc">{r.description}</p>
          <div class="card-foot">
            <span class="tag">{r.match}</span>
            <span class="tag score">score {r.score}</span>
            {#if latencies[r.id]}
              <span class="tag" class:hot={latencies[r.id].ok}>{latencies[r.id].ok ? latencies[r.id].latency_ms + ' ms' : 'down'}</span>
            {/if}
          </div>
          {#if bestId() === r.id}
            <div class="best-banner">BEST: lowest ping</div>
          {/if}
        </a>
      {/each}
    </div>
  {:else if invoked && !loading}
    <p class="muted">No matches yet.</p>
  {/if}
</div>

<style>
  .muted { color:#8b93a7; } .small { font-size:12px; } .warn { color:#fca5a5; }
  h1 { font-size:clamp(26px,4vw,40px); margin:0 0 4px; font-weight:800; }
  .searchbar { display:flex; gap:0; margin:16px 0; border:1px solid #161d2a; background:#080b11; }
  .sinput { flex:1; background:transparent; border:none; outline:none; color:#e2e8f0; font-size:15px; padding:12px 14px; font-family:ui-monospace,SFMono-Regular,monospace; }
  .btn { background:#4ade80; color:#040609; border:none; padding:0 20px; font-weight:700; font-size:12px; letter-spacing:.08em; cursor:pointer; }
  .btn:disabled { opacity:.6; cursor:default; }
  .toolbar { display:flex; justify-content:space-between; align-items:center; margin:10px 0 14px; gap:12px; flex-wrap:wrap; }
  .toggle { display:flex; border:1px solid #161d2a; }
  .toggle button { background:#080b11; color:#94a3b8; border:none; padding:6px 12px; font-size:11px; letter-spacing:.08em; cursor:pointer; font-weight:700; }
  .toggle button.active { background:#4ade80; color:#040609; }
  .grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(280px,1fr)); gap:12px; }
  .card { display:block; text-decoration:none; color:#e2e8f0; border:1px solid #161d2a; background:#080b11; padding:16px; position:relative; transition:border-color .15s; }
  .card:hover { border-color:#4ade80; }
  .card.best { border-color:#4ade80; box-shadow:0 0 0 1px #4ade80; }
  .card-row { display:flex; justify-content:space-between; align-items:center; gap:8px; margin-bottom:6px; }
  .price { color:#4ade80; font-family:ui-monospace,SFMono-Regular,monospace; font-size:12px; }
  .card-desc { color:#94a3b8; font-size:13px; margin:0 0 10px; }
  .card-foot { display:flex; gap:6px; flex-wrap:wrap; font-size:11px; color:#64748b; }
  .tag { padding:2px 8px; border:1px solid #161d2a; font-family:ui-monospace,SFMono-Regular,monospace; }
  .tag.hot { border-color:#4ade80; color:#4ade80; }
  .score { font-family:ui-monospace,SFMono-Regular,monospace; }
  .best-banner { margin-top:8px; font-size:10px; letter-spacing:.12em; color:#040609; background:#4ade80; padding:3px 6px; display:inline-block; }
  .note { margin:14px 0 18px; padding:12px 14px; background:#080b11; border:1px solid #161d2a; font-size:12px; color:#94a3b8; line-height:1.5; }
  .note-id { display:block; font-family:ui-monospace,SFMono-Regular,monospace; font-size:10px; color:#4ade80; letter-spacing:.12em; margin-bottom:4px; }
  .container { max-width:1120px; margin:0 auto; padding:0 24px; }
</style>
