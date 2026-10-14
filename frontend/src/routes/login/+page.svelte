<!-- src/routes/login/+page.svelte -->
<script>
  import { API } from '$lib/api';
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';

  let next = $derived($page.url.searchParams.get('next') || '/dashboard');
  let q = $derived($page.url.searchParams.get('q') || '');

  let mode = $state('login'); // login | signup
  let email = $state(''); let password = $state(''); let displayName = $state('');
  let error = $state(null); let loading = $state(false);
  let walletStatus = $state('');

  async function submit() {
    loading = true; error = null;
    const path = mode === 'login' ? '/auth/login' : '/auth/register';
    const payload = mode === 'login'
      ? { email, password }
      : { email, password, display_name: displayName || email };
    try {
      const r = await fetch(`${API}${path}`, {
        method:'POST', credentials:'include',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify(payload)
      });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail || JSON.stringify(d));
      const target = q ? `${next}?q=${encodeURIComponent(q)}` : next;
      await goto(target);
    } catch (e) { error = e.message; }
    finally { loading = false; }
  }

  async function walletLogin() {
    if (!window.ethereum) { error = 'No wallet detected.'; return; }
    loading = true; error = null; walletStatus = 'connecting…';
    try {
      const [address] = await window.ethereum.request({ method:'eth_requestAccounts' });
      walletStatus = 'requesting challenge…';
      const cr = await fetch(`${API}/auth/wallet/challenge`, {
        method:'POST', credentials:'include',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({ address })
      });
      const cd = await cr.json();
      if (!cr.ok) throw new Error(cd.detail || JSON.stringify(cd));
      walletStatus = 'signing…';
      const signature = await window.ethereum.request({ method:'personal_sign', params:[cd.message, address] });
      walletStatus = 'verifying…';
      const vr = await fetch(`${API}/auth/wallet/verify`, {
        method:'POST', credentials:'include',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({ address, signature, message: cd.message })
      });
      const vd = await vr.json();
      if (!vr.ok) throw new Error(vd.detail || JSON.stringify(vd));
      const target = q ? `${next}?q=${encodeURIComponent(q)}` : next;
      await goto(target);
    } catch (e) { error = e.message; }
    finally { loading = false; walletStatus = ''; }
  }
</script>

<div class="container authwrap">
  <div class="authcard">
    <h1>{mode === 'login' ? 'Welcome back' : 'Create account'}</h1>
    <p class="muted">Sign in to discover services, publish, and manage your dashboard.</p>

    <div class="tabs">
      <button class:active={mode==='login'} onclick={() => (mode='login')}>Log in</button>
      <button class:active={mode==='signup'} onclick={() => (mode='signup')}>Sign up</button>
    </div>

    {#if mode === 'signup'}
      <input class="input" bind:value={displayName} placeholder="Display name" />
      <div style="height:8px"></div>
    {/if}
    <input class="input" bind:value={email} placeholder="Email" type="email" />
    <div style="height:8px"></div>
    <input class="input" bind:value={password} placeholder="Password" type="password" onkeydown={(e)=>e.key==='Enter' && submit()} />
    <div style="height:12px"></div>
    <button class="btn" onclick={submit} disabled={loading}>{loading ? 'Please wait…' : (mode==='login'?'Log in':'Create account')}</button>

    <div class="divider">or</div>
    <button class="ghostbtn full" onclick={walletLogin} disabled={loading}>
      {walletStatus || 'Sign in with wallet'}
    </button>

    {#if error}<p class="warn">{error}</p>{/if}
    <p class="muted small" style="margin-top:12px;">
      {mode === 'login' ? "Don't have an account? Switch to Sign up." : 'Already have an account? Switch to Log in.'}
    </p>
  </div>
</div>

<style>
  .authwrap { display:flex; justify-content:center; padding:60px 24px; }
  .authcard { background:rgba(18,24,38,.7); border:1px solid #1f2a44; border-radius:14px; padding:28px; width:100%; max-width:420px; }
  h1 { margin:0 0 6px; }
  .muted { color:#8b93a7; }
  .small { font-size:12px; }
  .tabs { display:flex; gap:6px; margin:16px 0; background:#0e1320; padding:4px; border-radius:8px; }
  .tabs button { flex:1; background:transparent; color:#8b93a7; border:none; padding:8px; border-radius:6px; cursor:pointer; font-weight:600; }
  .tabs button.active { background:#1f2a44; color:#e6e9f0; }
  .input { background:#0e1320; color:#e6e9f0; border:1px solid #1f2a44; padding:10px 12px; border-radius:8px; width:100%; box-sizing:border-box; }
  .btn { background:#6ee7b7; color:#0b0f19; border:none; padding:10px 16px; border-radius:8px; font-weight:700; cursor:pointer; width:100%; }
  .btn:disabled { opacity:.6; cursor:default; }
  .ghostbtn { background:transparent; color:#e6e9f0; border:1px solid #1f2a44; padding:10px 16px; border-radius:8px; cursor:pointer; width:100%; font-weight:600; }
  .ghostbtn:disabled { opacity:.6; }
  .ghostbtn.full { width:100%; }
  .divider { text-align:center; color:#8b93a7; margin:14px 0; position:relative; }
  .divider::before, .divider::after { content:''; position:absolute; top:50%; width:42%; height:1px; background:#1f2a44; }
  .divider::before { left:0; } .divider::after { right:0; }
  .warn { color:#fca5a5; margin-top:12px; }
</style>
