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
  const REPO_URL = 'https://github.com/neoned71/AgentsTalk';

  async function loadMe() {
    try {
      const r = await fetch(`${API}/auth/me`, { credentials: 'include' });
      if (r.ok) user = await r.json();
      else user = null;
    } catch (e) { user = null; }
    finally {
      checked = true;
      const path = $page.url.pathname;
      const pub = path === '/' || path === '/login' || path === '/docs' || path === '/privacy' || path === '/terms' || path === '/license' || path === '/security' || path === '/demo';
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
    { href: '/my/services', label: 'Services' },
    { href: '/my/calls', label: 'Calls' },
    { href: '/credits', label: 'Credits' },
    { href: '/wallet', label: 'Wallet' },
    { href: '/keys', label: 'Keys' },
    { href: '/dashboard', label: 'Dashboard' },
  ];

  const footerLinks = [
    { href: '/demo', label: 'Demo' },
    { href: '/docs', label: 'Docs' },
    { href: '/privacy', label: 'Privacy' },
    { href: '/terms', label: 'Terms' },
    { href: '/license', label: 'License' },
    { href: '/security', label: 'Security' },
  ];
</script>

<div class="site-shell">
  <header class="sitebar">
    <div class="sitebar-inner">
      <a href="/" class="brand">
        <span class="brand-dot"></span>
        <span class="brand-name">AgentsTalk</span>
      </a>

      <nav class="site-nav" aria-label="primary">
        {#if user}
          {#each links as l}
            <a href={l.href} class:active={$page.url.pathname === l.href}>{l.label}</a>
          {/each}
        {:else}
          <a href="/" class:active={$page.url.pathname === '/'}>Home</a>
          <a href="/discover" class:active={$page.url.pathname === '/discover'}>Discover</a>
          <a href="/docs" class:active={$page.url.pathname === '/docs'}>Docs</a>
        {/if}
      </nav>

      <div class="site-actions">
        <a href={REPO_URL} class="github-btn" aria-label="AgentsTalk GitHub repository" target="_blank" rel="noopener noreferrer">
          <svg viewBox="0 0 24 24" aria-hidden="true" fill="currentColor"><path d="M12 .5A11.5 11.5 0 0 0 .5 12a11.5 11.5 0 0 0 7.86 10.92c.58.1.79-.25.79-.56v-2.17c-3.2.7-3.87-1.36-3.87-1.36-.52-1.33-1.28-1.68-1.28-1.68-1.05-.71.08-.7.08-.7 1.16.08 1.77 1.19 1.77 1.19 1.03 1.77 2.7 1.26 3.36.96.1-.75.4-1.26.73-1.55-2.55-.29-5.24-1.28-5.24-5.69 0-1.26.45-2.28 1.19-3.09-.12-.29-.52-1.46.11-3.04 0 0 .97-.31 3.19 1.18a11.1 11.1 0 0 1 5.82 0c2.22-1.49 3.19-1.18 3.19-1.18.63 1.58.23 2.75.11 3.04.74.81 1.19 1.83 1.19 3.09 0 4.42-2.69 5.39-5.25 5.68.41.35.78 1.04.78 2.1v3.1c0 .31.21.67.8.56A11.5 11.5 0 0 0 23.5 12 11.5 11.5 0 0 0 12 .5Z"/></svg>
        </a>
        {#if user}
          <span class="user-chip">{user.display_name || user.email}</span>
          <button class="ghost" onclick={logout}>Log out</button>
        {:else}
          <a href="/login" class="login-btn">Get started</a>
        {/if}
      </div>
    </div>
  </header>

  <main class="site-main">
    {@render children()}
  </main>

  <footer class="site-footer">
    <div class="footer-inner">
      <div class="footer-brand">
        <span class="brand-dot"></span>
        <span>AgentsTalk</span>
        <span class="footer-meta">machine service registry · v0.1</span>
        <a href={REPO_URL} class="footer-github" aria-label="AgentsTalk GitHub repository" target="_blank" rel="noopener noreferrer">
          <svg viewBox="0 0 24 24" aria-hidden="true" fill="currentColor"><path d="M12 .5A11.5 11.5 0 0 0 .5 12a11.5 11.5 0 0 0 7.86 10.92c.58.1.79-.25.79-.56v-2.17c-3.2.7-3.87-1.36-3.87-1.36-.52-1.33-1.28-1.68-1.28-1.68-1.05-.71.08-.7.08-.7 1.16.08 1.77 1.19 1.77 1.19 1.03 1.77 2.7 1.26 3.36.96.1-.75.4-1.26.73-1.55-2.55-.29-5.24-1.28-5.24-5.69 0-1.26.45-2.28 1.19-3.09-.12-.29-.52-1.46.11-3.04 0 0 .97-.31 3.19 1.18a11.1 11.1 0 0 1 5.82 0c2.22-1.49 3.19-1.18 3.19-1.18.63 1.58.23 2.75.11 3.04.74.81 1.19 1.83 1.19 3.09 0 4.42-2.69 5.39-5.25 5.68.41.35.78 1.04.78 2.1v3.1c0 .31.21.67.8.56A11.5 11.5 0 0 0 23.5 12 11.5 11.5 0 0 0 12 .5Z"/></svg>
          <span>GitHub</span>
        </a>
      </div>
      <nav class="footer-nav">
        {#each footerLinks as l}
          <a href={l.href}>{l.label}</a>
        {/each}
      </nav>
      <div class="footer-legal">
        © {new Date().getFullYear()} AgentsTalk. Code licensed under the MIT License. Trading is at your own risk.
      </div>
    </div>
  </footer>
</div>

<style>
  .site-shell {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }
  .site-main { flex: 1 1 auto; }
  .sitebar {
    position: sticky;
    top: 0;
    z-index: 20;
    background: rgba(5, 7, 10, .86);
    backdrop-filter: blur(12px);
  }
  .sitebar-inner {
    max-width: 1240px;
    margin: 0 auto;
    padding: 18px 24px;
    display: grid;
    grid-template-columns: auto 1fr auto;
    align-items: center;
    gap: 16px;
  }
  .brand { display: flex; align-items: center; gap: 9px; text-decoration: none; color: #e7ecf3; }
  .brand-dot { width: 9px; height: 9px; border-radius: 50%; background: #4ade80; box-shadow: 0 0 12px #4ade80; }
  .brand-name { font-weight: 700; font-size: 16px; letter-spacing: .04em; text-transform: uppercase; }
  .site-nav { display: flex; gap: 4px; justify-content: center; flex-wrap: wrap; }
  .site-nav a {
    color: #8b95a5;
    text-decoration: none;
    font-size: 12px;
    letter-spacing: .06em;
    text-transform: uppercase;
    font-weight: 500;
    padding: 8px 10px;
    border-radius: 6px;
    transition: color .15s, background .15s;
  }
  .site-nav a:hover { color: #e7ecf3; background: #0f1624; }
  .site-nav a.active { color: #4ade80; background: #0d1f18; }
  .site-actions { display: flex; align-items: center; gap: 8px; }
  .user-chip { font-size: 12px; color: #b9c3d1; background: #0f1624; padding: 7px 11px; border-radius: 999px; max-width: 160px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .ghost { background: transparent; color: #b9c3d1; padding: 7px 11px; border-radius: 6px; cursor: pointer; font-size: 12px; }
  .login-btn { background: #4ade80; color: #04120a; padding: 8px 13px; border-radius: 6px; text-decoration: none; font-size: 12px; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; }
  .github-btn { width: 34px; height: 34px; display: inline-flex; align-items: center; justify-content: center; border-radius: 6px; color: #9aa4b2; text-decoration: none; background: #0f1624; border: 1px solid #1f2937; transition: color .15s, background .15s, transform .15s; }
  .github-btn:hover { color: #e7ecf3; background: #162033; transform: translateY(-1px); }
  .github-btn svg { width: 18px; height: 18px; }
  .footer-github { display: inline-flex; align-items: center; gap: 6px; color: #9aa4b2; text-decoration: none; font-size: 12px; font-weight: 600; }
  .footer-github:hover { color: #4ade80; }
  .footer-github svg { width: 16px; height: 16px; }
  @media (max-width: 860px) {
    .sitebar-inner { grid-template-columns: auto auto; }
    .site-nav { display: none; }
    .user-chip { display: none; }
  }

  .site-footer {
    background: #040609;
    padding: 28px 24px 32px;
  }
  .footer-inner {
    max-width: 1240px;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }
  .footer-brand { display: flex; align-items: center; gap: 8px; color: #e7ecf3; font-weight: 600; font-size: 13px; }
  .footer-brand .brand-dot { width: 8px; height: 8px; }
  .footer-meta { margin-left: 8px; color: #64748b; font-size: 11px; letter-spacing: .08em; text-transform: uppercase; font-weight: 400; }
  .footer-nav { display: flex; gap: 16px; flex-wrap: wrap; }
  .footer-nav a { color: #8b95a5; text-decoration: none; font-size: 12px; letter-spacing: .04em; text-transform: uppercase; }
  .footer-nav a:hover { color: #4ade80; }
  .footer-legal { color: #5b6472; font-size: 11px; line-height: 1.5; max-width: 760px; }
</style>
