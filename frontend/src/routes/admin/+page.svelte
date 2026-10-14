<!-- src/routes/admin/+page.svelte -->
<script>
  import { goto } from '$app/navigation';
  const API = import.meta.env.PUBLIC_API_BASE || 'http://localhost:8000';
  let overview = $state(null);
  let analytics = $state(null);
  let error = $state(null);
  let loading = $state(true);

  async function load() {
    loading = true; error = null;
    try {
      const [o, a] = await Promise.all([
        fetch(`${API}/admin/overview`, { credentials: 'include' }).then(async r => {
          if (r.status === 401 || r.status === 403) throw new Error('Admin access required');
          return r.json();
        }),
        fetch(`${API}/analytics/summary?days=7`, { credentials: 'include' }).then(async r => {
          if (r.status === 401 || r.status === 403) throw new Error('Admin access required');
          return r.json();
        })
      ]);
      overview = o; analytics = a;
    } catch (e) { error = e.message || 'Failed to load admin data'; if (error === 'Admin access required') goto('/'); }
    finally { loading = false; }
  }

  $effect(() => { load(); });
</script>

<div class="page">
  <header class="head">
    <div>
      <h1>Admin dashboard</h1>
      <p class="muted">Platform totals, usage, and analytics.</p>
    </div>
    <button class="ghost" onclick={load} disabled={loading}>{loading ? 'Loading…' : 'Refresh'}</button>
  </header>

  {#if error}<div class="banner">{error}</div>{/if}

  {#if loading}
    <p class="muted">Loading admin overview…</p>
  {:else if overview}
    <section class="metrics">
      <div class="metric"><span class="label">Users</span><span class="value">{overview.totals.users}</span></div>
      <div class="metric"><span class="label">Publishers</span><span class="value">{overview.totals.publishers}</span></div>
      <div class="metric"><span class="label">Services</span><span class="value">{overview.totals.services}</span></div>
      <div class="metric"><span class="label">Calls</span><span class="value">{overview.totals.calls}</span></div>
      <div class="metric"><span class="label">Receipts</span><span class="value">{overview.totals.receipts}</span></div>
      <div class="metric"><span class="label">Page views</span><span class="value">{overview.totals.page_views}</span></div>
      <div class="metric"><span class="label">Unique visitors</span><span class="value">{overview.totals.unique_visitors}</span></div>
      <div class="metric"><span class="label">Call value</span><span class="value">{(overview.totals.total_call_value_atomic / 1e6).toFixed(4)}</span></div>
    </section>

    <section class="block">
      <div class="block-head"><h2>Page analytics</h2><span class="meta">{analytics?.period_days ?? 7} day window</span></div>
      {#if analytics?.pages?.length}
        <div class="table">
          <table>
            <thead><tr><th>Path</th><th>Views</th><th>Visitors</th><th>Total dwell (ms)</th><th>Average dwell (ms)</th></tr></thead>
            <tbody>
              {#each analytics.pages as page}
                <tr>
                  <td class="mono">{page.path}</td>
                  <td>{page.views}</td>
                  <td>{page.visitors}</td>
                  <td>{page.total_duration_ms}</td>
                  <td>{page.avg_duration_ms}</td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      {:else}
        <div class="empty">No analytics events yet.</div>
      {/if}
    </section>
  {/if}
</div>

<style>
  .page { max-width: 1120px; margin: 0 auto; padding: 48px 24px 80px; }
  .head { display: flex; justify-content: space-between; align-items: flex-end; gap: 18px; margin-bottom: 28px; flex-wrap: wrap; }
  h1 { margin: 0; font-size: 36px; letter-spacing: -0.03em; }
  .muted { color: #7b8494; font-size: 13px; }
  .meta { color: #7b8494; font-size: 12px; }
  .banner { color: #fca5a5; background: rgba(248, 113, 113, .08); padding: 12px 14px; border-radius: 8px; margin-bottom: 20px; }
  .metrics { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 32px; }
  .metric { background: #0f1624; border: 1px solid #162033; border-radius: 12px; padding: 16px; }
  .label { display: block; color: #7b8494; font-size: 10px; text-transform: uppercase; letter-spacing: .14em; }
  .value { display: block; margin-top: 8px; font-size: 24px; font-weight: 700; font-family: ui-monospace, SFMono-Regular, monospace; color: #e7ecf3; }
  .block-head { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 14px; }
  .block-head h2 { margin: 0; font-size: 17px; }
  .table { overflow-x: auto; }
  table { width: 100%; border-collapse: separate; border-spacing: 0 10px; min-width: 720px; }
  thead th { color: #7b8494; font-size: 10px; text-transform: uppercase; letter-spacing: .14em; text-align: left; padding: 0 14px 10px; font-weight: 500; }
  tbody tr { background: #111827; }
  tbody td { padding: 14px; font-size: 13px; color: #e7ecf3; }
  tbody td:first-child { border-radius: 8px 0 0 8px; }
  tbody td:last-child { border-radius: 0 8px 8px 0; }
  .mono { font-family: ui-monospace, SFMono-Regular, monospace; color: #b9c3d1; font-size: 12px; }
  .empty { color: #8b95a5; padding: 22px 2px; }
  .ghost { background: #111725; color: #c8cfda; border: 0; padding: 9px 14px; border-radius: 8px; cursor: pointer; }
  .ghost:disabled { opacity: .55; cursor: default; }
  @media (max-width: 900px) { .metrics { grid-template-columns: repeat(2, 1fr); } }
  @media (max-width: 560px) { .metrics { grid-template-columns: 1fr; } }
</style>
