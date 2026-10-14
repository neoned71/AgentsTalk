<!-- src/routes/my/calls/+page.svelte -->
<script>
  import AnimatedNote from '$lib/AnimatedNote.svelte';
  const API = import.meta.env.PUBLIC_API_BASE || 'http://localhost:8000';
  let receipts = $state([]);
  let loading = $state(true);
  let error = $state(null);

  async function load() {
    loading = true; error = null;
    try {
      const r = await fetch(`${API}/receipts`, { credentials:'include' });
      const d = await r.json();
      if (!r.ok) throw new Error(JSON.stringify(d));
      receipts = Array.isArray(d) ? d : [];
    } catch (e) { error = e.message; }
    finally { loading = false; }
  }
  $effect(() => { load(); });
</script>

<div class="container">
  <h1>My calls</h1>
  <p class="muted">Credit-based calls and their receipt status. Failed calls void the receipt and restore credits.</p>
  <AnimatedNote variant="receipt" title="HOW MY CALLS WORK" note="Rows are receipts created when you invoked with credits. reserved = credits held; consumed = call succeeded and funds in escrow; voided = call failed and refunded. Direct x402 calls are not listed here." />
  {#if loading}<div class="skel"></div>
  {:else if error}<p class="warn">{error}</p>
  {:else if receipts.length === 0}
    <div class="empty"><div class="emptyico">📞</div><div>No credit calls yet. Invoke a service with a receipt to see them here.</div></div>
  {:else}
    <div class="card">
      <div class="tablewrap">
        <table>
          <thead><tr><th>Receipt</th><th>Service</th><th>Amount</th><th>Status</th><th>Created</th></tr></thead>
          <tbody>
            {#each receipts as r}
              <tr>
                <td class="mono small">{r.receipt_number}</td>
                <td class="mono small">{r.service_id.slice(0,8)}…</td>
                <td>{(r.amount_atomic/1e6).toFixed(6)} USDC</td>
                <td><span class="badge {r.status}">{r.status}</span></td>
                <td class="muted small">{new Date(r.created_at).toLocaleString()}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </div>
  {/if}
</div>

<style>
  .muted { color:#8b93a7; } .small { font-size:12px; } .warn { color:#fca5a5; } .mono { font-family:ui-monospace,monospace; }
  h1 { font-size:clamp(26px,4vw,40px); margin:0 0 4px; font-weight:800; }
  .card { background:rgba(18,24,38,.6); border:1px solid #1f2a44; border-radius:12px; padding:18px; margin:16px 0; }
  .tablewrap { overflow-x:auto; } table { width:100%; border-collapse:collapse; font-size:13px; }
  th { color:#8b93a7; font-size:11px; text-transform:uppercase; letter-spacing:.08em; }
  .badge { padding:3px 8px; border-radius:999px; font-size:11px; font-weight:600; }
  .badge.reserved { background:rgba(250,204,21,.15); color:#facc15; }
  .badge.consumed { background:rgba(110,231,183,.15); color:#6ee7b7; }
  .badge.voided { background:rgba(252,165,165,.15); color:#fca5a5; }
  .empty { text-align:center; padding:40px 12px; color:#8b93a7; }
  .emptyico { font-size:32px; margin-bottom:8px; }
  .skel { height:34px; background:linear-gradient(90deg,#121826,#1f2a44,#121826); background-size:200%; animation:shim 1.2s linear infinite; border-radius:8px; margin:10px 0; }
  @keyframes shim { 0%{background-position:200% 0} 100%{background-position:-200% 0} }
  .container { max-width:960px; margin:0 auto; padding:0 24px; }
</style>
