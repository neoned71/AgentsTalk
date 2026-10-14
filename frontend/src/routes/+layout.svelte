<!-- src/routes/+layout.svelte -->
<script>
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import '../app.css';

  const API = import.meta.env.PUBLIC_API_BASE || 'http://localhost:8000';

  if (typeof window !== 'undefined') {
    const _fetch = window.fetch.bind(window);
    window.fetch = (input, init = {}) => {
      const url = typeof input === 'string' ? input : (input && input.url) || '';
      if (url.startsWith(API)) {
        init = { credentials: 'include', ...init };
      }
      return _fetch(input, init);
    };
  }

  let { children } = $props();
  let user = $state(null);
  let checked = $state(false);

  async function loadMe() {
    try {
      const r = await fetch(`${API}/auth/me`, { credentials: 'include' });
      if (r.ok) user = await r.json();
      else user = null;
    } catch (e) { user = null; }
    finally {
      checked = true;
      const path = $page.url.pathname;
      const pub = path === '/' || path === '/login';
      if (!user && !pub) goto('/login');
    }
  }

  $effect(() => {
    $page.url.pathname;
    loadMe();
  });

  async function logout() {
    await fetch(`${API}/auth/logout`, { method: 'POST', credentials: 'include' });
    user = null;
    await goto('/');
  }
</script>

<nav class="topnav-bar">
  <div class="container" style="display:flex;gap:16px;align-items:center;justify-content:space-between;">
    <a href="/" class="brand"><span class="dot"></span> AgentsHub</a>
    <div class="navlinks">
      {#if user}
        <a href="/discover">Discover</a>
        <a href="/publish">Publish</a>
        <a href="/my/services">My Services</a>
        <a href="/my/calls">My Calls</a>
        <a href="/credits">Credits</a>
        <a href="/keys">API Keys</a>
        <a href="/dashboard">Dashboard</a>
        <button class="ghostbtn" onclick={logout}>Log out ({user.display_name || user.email})</button>
      {:else}
        <a href="/login" class="navcta primary">Log in</a>
      {/if}
    </div>
  </div>
</nav>

{@render children()}

<style>
  .topnav-bar { position:sticky; top:0; z-index:10; padding:10px 0; background:rgba(11,15,25,.7); backdrop-filter:blur(10px); border-bottom:1px solid #1f2a44; }
  .brand { color:#e6e9f0; text-decoration:none; font-weight:800; font-size:20px; display:flex; align-items:center; gap:8px; }
  .dot { width:10px; height:10px; border-radius:50%; background:#6ee7b7; box-shadow:0 0 12px #6ee7b7; }
  .navlinks { display:flex; gap:14px; align-items:center; font-size:14px; flex-wrap:wrap; }
  .navlinks a { color:#b4bcd0; text-decoration:none; }
  .navlinks a:hover { color:#e6e9f0; }
  .navcta.primary { background:#6ee7b7; color:#0b0f19; padding:7px 12px; border-radius:8px; font-weight:600; }
  .ghostbtn { background:transparent; color:#b4bcd0; border:1px solid #1f2a44; padding:6px 10px; border-radius:7px; cursor:pointer; font-size:13px; }
  .container { max-width:1180px; margin:0 auto; padding:0 24px; }
</style>
