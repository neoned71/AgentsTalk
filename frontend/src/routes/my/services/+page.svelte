<!-- src/routes/my/services/+page.svelte -->
<script>
  import AnimatedNote from '$lib/AnimatedNote.svelte';
  const API = import.meta.env.PUBLIC_API_BASE || 'http://localhost:8000';
  let publishers = $state([]);
  let services = $state([]);
  let loading = $state(true);
  let error = $state(null);

  async function load() {
    loading = true; error = null;
    try {
      const pr = await fetch(`${API}/publishers/mine`, { credentials:'include' });
      const pud = await pr.json();
      if (!pr.ok) throw new Error(JSON.stringify(pud));
      publishers = Array.isArray(pud) ? pud : [];
      let all = [];
      for (const p of publishers) {
        const sr = await fetch(`${API}/services?publisher_id=${p.id}`, { credentials:'include' });
        const sd = await sr.json();
        if (sr.ok && Array.isArray(sd)) all = all.concat(sd.map(s => ({...s, publisher_domain: p.domain})));
      }
      services = all;
    } catch (e) { error = e.message; }
    finally { loading = false; }
  }
  $effect(() => { load(); });
</script>

<div class="container">
  <div class="row" style="justify-content:space-between;align-items:center;">
    <h1>My services</h1>
    <a class="btn" href="/publish">+ Publish</a>
  </div>
  <p class="muted">Services owned by your publishers.</p>
  <AnimatedNote variant="service" title="HOW MY SERVICES WORK" note="Publishers bind your account to a domain and USDC receive wallet; services are indexed (name/description/schemas) and discoverable. Payouts accrue after the 30-day escrow window." />
  {#if loading}<div class="skel"></div>
  {:else if error}<p class="warn">{error}</p>
  {:else if publishers.length === 0}
    <div class="empty"><div class="emptyico">🏪</div><div>No publishers yet. Import or create one from the Publish page.</div></div>
  {:else}
    {#each publishers as p}
      <div class="card">
        <div class="cardhead"><h3>{p.display_name || p.domain}</h3><span class="muted small">{p.domain} · {p.verified ? 'verified' : 'unverified'}</span></div>
        <div class="tablewrap">
          <table>
            <thead><tr><th>Name</th><th>Price</th><th>Currency</th><th>Status</th><th>Action</th></tr></thead>
            <tbody>
              {#each services.filter(s => s.publisher_domain === p.domain) as s}
                <tr>
                  <td><a href={`/service/${s.id}`}>{s.name}</a></td>
                  <td>{(s.price_atomic/1e6).toFixed(6)}</td>
                  <td>{s.currency}</td>
                  <td><span class="badge {s.active!==false?'active':'paused'}">{s.active!==false?'active':'paused'}</span></td>
                  <td><a href={`/service/${s.id}`} class="ghostbtn">View</a></td>
                </tr>
              {:else}
                <tr><td colspan="5" class="muted">No services yet.</td></tr>
              {/each}
            </tbody>
          </table>
        </div>
      </div>
    {/each}
  {/if}
</div>

<style>
  .muted { color:#8b93a7; } .small { font-size:12px; } .warn { color:#fca5a5; }
  h1 { font-size:clamp(26px,4vw,40px); margin:0 0 4px; font-weight:800; }
  .row { display:flex; }
  .btn { background:#6ee7b7; color:#0b0f19; border:none; padding:8px 14px; border-radius:8px; font-weight:700; text-decoration:none; }
  .card { background:rgba(18,24,38,.6); border:1px solid #1f2a44; border-radius:12px; padding:18px; margin:14px 0; }
  .cardhead { display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; }
  .card h3 { margin:0; font-size:16px; }
  .tablewrap { overflow-x:auto; } table { width:100%; border-collapse:collapse; font-size:13px; }
  th { color:#8b93a7; font-size:11px; text-transform:uppercase; letter-spacing:.08em; }
  a { color:#6ee7b7; text-decoration:none; }
  .ghostbtn { background:transparent; color:#b4bcd0; border:1px solid #1f2a44; padding:4px 8px; border-radius:6px; cursor:pointer; font-size:12px; text-decoration:none; }
  .empty { text-align:center; padding:40px 12px; color:#8b93a7; }
  .emptyico { font-size:32px; margin-bottom:8px; }
  .badge { padding:3px 8px; border-radius:999px; font-size:11px; font-weight:600; background:rgba(110,231,183,.15); color:#6ee7b7; }
  .skel { height:34px; background:linear-gradient(90deg,#121826,#1f2a44,#121826); background-size:200%; animation:shim 1.2s linear infinite; border-radius:8px; margin:10px 0; }
  @keyframes shim { 0%{background-position:200% 0} 100%{background-position:-200% 0} }
  .container { max-width:1120px; margin:0 auto; padding:0 24px; }
</style>
