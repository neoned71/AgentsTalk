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
    await goto('/login');
  }

  const links = [
    { href: '/discover', label: 'Discover' },
    { href: '/publish', label: 'Publish' },
    { href: '/my/services', label: 'My services' },
    { href: '/my/calls', label: 'My calls' },
    { href: '/credits', label: 'Credits' },
    { href: '/keys', label: 'API keys' },
    { href: '/dashboard', label: 'Dashboard' },
  ];
</script>

<header class="sitebar">
  <div class="sitebar-inner">
    <a href="/" class="brand">
      <span class="brand-dot"></span>
      <span class="brand-name">AgentTalk</span>
    </a>

    <nav class="site-nav" aria-label="primary">
      {#if user}
        {#each links as l}
          <a href={l.href} class:active={$page.url.pathname === l.href}>{l.label}</a>
        {/each}
      {:else}
        <a href="/" class:active={$page.url.pathname === '/'}>Home</a>
        <a href="/discover" class:active={$page.url.pathname === '/discover'}>Discover</a>
      {/if}
    </nav>

    <div class="site-actions">
      {#if user}
        <span class="user-chip">{user.display_name || user.email}</span>
        <button class="ghost" onclick={logout}>Log out</button>
      {:else}
        <a href="/login" class="login-btn">Log in</a>
      {/if}
    </div>
  </div>
</header>

{@render children()}

<style>
  .sitebar {
    position: sticky;
    top: 0;
    z-index: 20;
    background: rgba(5, 7, 10, .82);
    backdrop-filter: blur(12px);
    border-bottom: 1px solid #141b26;
  }
  .sitebar-inner {
    max-width: 1240px;
    margin: 0 auto;
    padding: 12px 24px;
    display: grid;
    grid-template-columns: auto 1fr auto;
    align-items: center;
    gap: 16px;
  }
  .brand { display: flex; align-items: center; gap: 9px; text-decoration: none; color: #e7ecf3; }
  .brand-dot { width: 9px; height: 9px; border-radius: 50%; background: #4ade80; box-shadow: 0 0 12px #4ade80; }
  .brand-name { font-weight: 700; font-size: 15px; letter-spacing: .02em; }
  .site-nav { display: flex; gap: 2px; justify-content: center; flex-wrap: wrap; }
  .site-nav a {
    color: #8b95a5;
    text-decoration: none;
    font-size: 12px;
    letter-spacing: .04em;
    text-transform: uppercase;
    font-weight: 500;
    padding: 6px 9px;
    border-radius: 6px;
    transition: color .15s, background .15s;
  }
  .site-nav a:hover { color: #e7ecf3; background: #0f1624; }
  .site-nav a.active { color: #4ade80; background: #0d1f18; }
  .site-actions { display: flex; align-items: center; gap: 8px; }
  .user-chip { font-size: 12px; color: #b9c3d1; background: #0f1624; padding: 6px 10px; border-radius: 999px; max-width: 160px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .ghost { background: transparent; color: #b9c3d1; border: 1px solid #1f2937; padding: 6px 10px; border-radius: 6px; cursor: pointer; font-size: 12px; }
  .ghost:hover { border-color: #4ade80; color: #4ade80; }
  .login-btn { background: #4ade80; color: #04120a; padding: 7px 12px; border-radius: 6px; text-decoration: none; font-size: 12px; font-weight: 700; letter-spacing: .04em; text-transform: uppercase; }
  @media (max-width: 860px) {
    .sitebar-inner { grid-template-columns: auto auto; }
    .site-nav { display: none; }
    .user-chip { display: none; }
  }
</style>
