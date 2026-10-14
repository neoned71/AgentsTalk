<!-- src/routes/keys/+page.svelte -->
<script>
  import AnimatedNote from '$lib/AnimatedNote.svelte';
  const API = import.meta.env.PUBLIC_API_BASE || 'http://localhost:8000';
  let keys = $state([]);
  let name = $state('agent-1');
  let spend = $state('0');
  let loading = $state(true);
  let error = $state(null);
  let newKey = $state(null);

  async function load() {
    loading = true; error = null;
    try {
      const r = await fetch(`${API}/keys`, { credentials:'include' });
      const d = await r.json();
      if (!r.ok) throw new Error(JSON.stringify(d));
      keys = Array.isArray(d) ? d : [];
    } catch (e) { error = e.message; }
    finally { loading = false; }
  }
  async function create() {
    error = null; newKey = null;
    try {
      const r = await fetch(`${API}/keys`, {
        method:'POST', credentials:'include',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({ name, spend_limit_atomic: Number(spend) })
      });
      const d = await r.json();
      if (!r.ok) throw new Error(JSON.stringify(d));
      newKey = d.key;
      await load();
    } catch (e) { error = e.message; }
  }
  async function revoke(id) {
    await fetch(`${API}/keys/${id}/revoke`, { method:'POST', credentials:'include' });
    await load();
  }
  $effect(() => { load(); });
</script>

<div class="container">
  <h1>API Keys</h1>
  <p class="muted">Scoped keys for agents. Pass as <code>Authorization: Bearer ah_...</code> to call the hub programmatically.</p>
  <AnimatedNote variant="keys" title="HOW API KEYS WORK" note="Create a key with an optional spend limit (atomic USDC). The key maps to your account, so caps and revocation are enforced server-side. Agents use it as a Bearer token; revoking stops further calls." />
  <div class="card">
    <h3>Create a key</h3>
    <input class="input" bind:value={name} placeholder="key name" />
    <div style="height:8px"></div>
    <input class="input" bind:value={spend} placeholder="spend limit in USDC atomic (0 = unlimited)" />
    <div style="height:12px"></div>
    <button class="btn" onclick={create}>Create key</button>
    {#if newKey}
      <div class="box">
        <div class="boxtitle">Key created (copy now)</div>
        <code class="key">{newKey}</code>
        <p class="muted small">This value will not be shown again.</p>
      </div>
    {/if}
  </div>

  {#if loading}<div class="skel"></div>
  {:else if error}<p class="warn">{error}</p>
  {:else if keys.length === 0}
    <div class="empty"><div class="emptyico">🔑</div><div>No keys yet.</div></div>
  {:else}
    <div class="card">
      <div class="tablewrap">
        <table>
          <thead><tr><th>Name</th><th>Prefix</th><th>Spent / Limit</th><th>Status</th><th>Action</th></tr></thead>
          <tbody>
            {#each keys as k}
              <tr>
                <td>{k.name}</td>
                <td class="mono small">{k.prefix}</td>
                <td>{(k.spent_atomic/1e6).toFixed(6)} / {k.spend_limit_atomic ? (k.spend_limit_atomic/1e6).toFixed(6) : '∞'}</td>
                <td><span class="badge {k.revoked?'revoked':'active'}">{k.revoked?'revoked':'active'}</span></td>
                <td>{#if !k.revoked}<button class="ghostbtn" onclick={() => revoke(k.id)}>Revoke</button>{/if}</td>
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
  .card { background:rgba(18,24,38,.6); border-radius:12px; padding:18px; margin:14px 0; }
  .card h3 { margin:0 0 8px; font-size:16px; }
  .input { background:#0e1320; color:#e6e9f0; padding:10px 12px; border-radius:8px; width:100%; box-sizing:border-box; }
  .btn { background:#6ee7b7; color:#0b0f19; padding:10px 16px; border-radius:8px; font-weight:700; cursor:pointer; }
  .ghostbtn { background:transparent; color:#b4bcd0; padding:5px 9px; border-radius:6px; cursor:pointer; font-size:12px; }
  .box { background:#0e1320; border-radius:10px; padding:12px; margin-top:12px; }
  .boxtitle { font-weight:700; margin-bottom:6px; }
  .key { color:#6ee7b7; word-break:break-all; font-size:12px; }
  .tablewrap { overflow-x:auto; } table { width:100%; border-collapse:collapse; font-size:13px; }
  th { color:#8b93a7; font-size:11px; text-transform:uppercase; letter-spacing:.08em; }
  .badge { padding:3px 8px; border-radius:999px; font-size:11px; font-weight:600; }
  .badge.active { background:rgba(110,231,183,.15); color:#6ee7b7; }
  .badge.revoked { background:rgba(252,165,165,.15); color:#fca5a5; }
  .empty { text-align:center; padding:40px 12px; color:#8b93a7; }
  .emptyico { font-size:32px; margin-bottom:8px; }
  .skel { height:34px; background:linear-gradient(90deg,#121826,#1f2a44,#121826); background-size:200%; animation:shim 1.2s linear infinite; border-radius:8px; margin:10px 0; }
  @keyframes shim { 0%{background-position:200% 0} 100%{background-position:-200% 0} }
  .container { max-width:960px; margin:0 auto; padding:0 24px; }
</style>
