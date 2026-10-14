<!-- src/routes/+page.svelte (linear, statistical, smart) -->
<script>
  import { goto } from '$app/navigation';
  const API = import.meta.env.PUBLIC_API_BASE || 'http://localhost:8000';
  let query = $state('');
  let results = $state([]);
  let loading = $state(false);
  let error = $state(null);
  let invoked = $state(false);
  let loginRequired = $state(false);
  let activeTool = $state('mcp');
  let snippet = $state('Loading integration guide...');
  let copied = $state(false);

  const iconMap = {
    mcp: '/icons/mcp.svg',
    langchain: '/icons/langchain.svg',
    openai: '/icons/openai.svg',
    autogen: '/icons/microsoft.svg',
    crewai: '/icons/crewai.svg',
    llamaindex: '/icons/llamaindex.svg',
    vercel: '/icons/vercel.svg',
    n8n: '/icons/n8n.svg',
    curl: '/icons/curl.svg',
    fastapi: '/icons/fastapi.svg'
  };

  const guides = [
    { id: 'mcp', name: 'Claude / Cursor / Cline / Windsurf', description: 'Discover and expose a provider MCP endpoint through npx mcp-remote.', steps: ['Install the bridge: npm i -g mcp-remote', 'Search using /search and inspect the result payload.', 'Copy the selected service mcp_endpoint value.', 'Add it to your editor MCP JSON config.', 'Restart the editor and test tools/list / tools/call.'] , env: 'AGENTTALK_BASE, AGENTTALK_KEY or personal wallet' },
    { id: 'langchain', name: 'LangChain', description: 'Define search and invoke helpers, then wrap them as @tool.', steps: ['Set AGENTTALK_BASE and AGENTTALK_KEY environment variables.', 'Create reusable get_services/search and invoke functions.', 'Wrap them with the LangChain decorator or tool function.', 'Attach tools to the agent or chat chain.', 'Handle 402 responses for x402 wallet branch.'] , env: 'AGENTTALK_BASE, AGENTTALK_KEY' },
    { id: 'openai', name: 'OpenAI Agents / Function Calling', description: 'Expose search and invoke as JSON function tools.', steps: ['Publish the function tool schemas for search and invoke.', 'Route tool calls through /search or /calls/invoke.', 'Normalize payment required 402 responses for the frontend/user.', 'Map results back to model final state.', 'Use key scopes and spend caps for safety.'] , env: 'AGENTTALK_BASE, AGENTTALK_KEY' },
    { id: 'autogen', name: 'AutoGen', description: 'Expose callable helpers and register them with AssistantAgent.', steps: ['Implement search_services and invoke_service in Python.', 'Register them as helper tools.', 'Add exception handling for invalid service IDs.', 'Use /routing/probe to sort low-latency providers.', 'Validate refunds and escrow intent separately.'] , env: 'AGENTTALK_BASE, AGENTTALK_KEY' },
    { id: 'crewai', name: 'CrewAI', description: 'Create task tools that search and invoke services.', steps: ['Create API access helpers using crewai @tool.', 'Assign tools to agents according to roles.', 'Use search output to select provider.', 'Invoke with structured request_payload.', 'Log call IDs and endpoints for audit.'] , env: 'AGENTTALK_BASE, AGENTTALK_KEY' },
    { id: 'llamaindex', name: 'LlamaIndex', description: 'Convert search and invoke functions into FunctionTool instances.', steps: ['Create search_tool using FunctionTool.from_defaults.', 'Create invoke_tool with typed payload.', 'Register both in a QueryEngine or agent.', 'Use results as tool context returned to the user.', 'Inspect returned call_id after invocation.'] , env: 'AGENTTALK_BASE, AGENTTALK_KEY' },
    { id: 'vercel', name: 'Vercel AI SDK', description: 'Wire search and invoke in TypeScript tool definitions.', steps: ['Install ai and zod.', 'Define parameters with valid schema.', 'Fetch results for /search and /calls/invoke.', 'Pass tools into generateText or streamText.', 'Add server-side env and secret management.'] , env: 'AGENTTALK_BASE, AGENTTALK_KEY' },
    { id: 'n8n', name: 'n8n', description: 'Use Header Auth and HTTP nodes to automate discovery and calls.', steps: ['Create an HTTP credential with Authorization header.', 'Search in one request node.', 'Extract service_id using a Function node.', 'Call /calls/invoke for execution.', 'Branch on 402 for wallet payments.'] , env: 'HUB URL, API token' },
    { id: 'curl', name: 'HTTP / curl', description: 'Use shell and any HTTP client in any language.', steps: ['Export HUB and KEY environment variables.', 'List service candidates with search.', 'Record candidate service_id.', 'Invoke and inspect returned endpoint.', 'Productize with retry and key budgeting.'] , env: 'HUB, KEY' },
    { id: 'fastapi', name: 'FastAPI proxy', description: 'Wrap AgentsTalk behind your own backend.', steps: ['Load HUB and KEY from environment.', 'Implement a gateway route.', 'Forward payload as request_payload.', 'Return JSON result to callers.', 'Handle payment required properly.'] , env: 'HUB, KEY' }
  ];
  const guide = $derived(guides.find(g => g.id === activeTool) ?? guides[0]);

  async function copyGuide() {
    try {
      await navigator.clipboard.writeText(snippet);
      copied = true;
      setTimeout(() => (copied = false), 1600);
    } catch (e) { copied = false; }
  }
  const tools = [
    { id:'mcp', name:'MCP (Claude/Cursor/Cline)' },
    { id:'langchain', name:'LangChain' },
    { id:'openai', name:'OpenAI Agents' },
    { id:'autogen', name:'AutoGen' },
    { id:'crewai', name:'CrewAI' },
    { id:'llamaindex', name:'LlamaIndex' },
    { id:'vercel', name:'Vercel AI SDK' },
    { id:'n8n', name:'n8n' },
    { id:'curl', name:'HTTP / curl' },
    { id:'fastapi', name:'FastAPI proxy' }
  ];
  $effect(() => {
    fetch(`/integrations/${activeTool}.txt`)
      .then(r => r.text())
      .then(v => (snippet = v))
      .catch(() => (snippet = 'Unable to load integration guide.'));
  });

  let stage = $state(0);

  $effect(() => {
    const id = setInterval(() => { stage = (stage + 1) % 4; }, 3200);
    return () => clearInterval(id);
  });

  function reveal(node) {
    const io = new IntersectionObserver((entries) => {
      for (const e of entries) if (e.isIntersecting) { node.classList.add('revealed'); io.unobserve(node); }
    }, { threshold: 0.08 });
    io.observe(node);
    return { destroy() { io.disconnect(); } };
  }

  async function search() {
    if (!query.trim()) return;
    loading = true; error = null; invoked = true; loginRequired = false;
    try {
      const r = await fetch(`${API}/search`, {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, limit: 20 })
      });
      if (r.status === 401) {
        if (typeof sessionStorage !== 'undefined') sessionStorage.setItem('pendingSearch', query);
        await goto(`/login?q=${encodeURIComponent(query)}&next=/dashboard`);
        return;
      }
      if (!r.ok) throw new Error(await r.text());
      results = (await r.json()).results;
    } catch (e) { error = e.message; }
    finally { loading = false; }
  }
</script>

<svelte:head>
  <title>AgentsTalk — machine service hub</title>
  <meta name="description" content="Discovery and payments for machine-to-machine services." />
</svelte:head>

<div class="backdrop"></div>

<!-- HERO -->
<section class="hero">
  <div class="container">
    <div class="topline">
      <span class="label">AGENTS HUB / v0.1</span>
      <span class="label muted">status: online</span>
    </div>
    <h1>One hub for every service<br/>agents need to call.</h1>
    <p class="lead">
      Providers publish MCP services with a price per call. Agents discover them
      by vector search and pay per invocation. No app stores. No seats. No humans
      in the loop.
    </p>

    <div class="searchbar">
      <input class="sinput" bind:value={query} placeholder="query: summarize url, translate, analyze image…" onkeydown={(e) => e.key === 'Enter' && search()} />
      <button class="sbtn" onclick={search} disabled={loading}>{loading ? '…' : 'SEARCH'}</button>
    </div>

    <div class="kpi-strip">
      <div class="kpi"><div class="kpi-num">98%</div><div class="kpi-lbl">provider share</div></div>
      <div class="kpi"><div class="kpi-num">2%</div><div class="kpi-lbl">platform fee</div></div>
      <div class="kpi"><div class="kpi-num">30d</div><div class="kpi-lbl">escrow hold</div></div>
      <div class="kpi"><div class="kpi-num">1¢</div><div class="kpi-lbl">min per call</div></div>
      <div class="kpi"><div class="kpi-num">768</div><div class="kpi-lbl">embed dims</div></div>
    </div>
  </div>
</section>


<div class="container">
  <div class="integrate">
    <div class="integrate-head">QUICK INTEGRATE · PICK YOUR TOOL (10 TARGETS)</div>
    <div class="tool-tabs">
      {#each tools as t}
        <button class="tool-tab" class:active={activeTool === t.id} type="button"
                onclick={() => activeTool = t.id}>
          <img class="tool-icon" src={iconMap[t.id] || '/icons/mcp.svg'} alt="" width="15" height="15" />
          {t.name}
        </button>
      {/each}
    </div>

    <section class="guide-card">
      <h3><img class="tool-icon" src={iconMap[activeTool] || '/icons/mcp.svg'} alt="" width="16" height="16" />{guide?.name}</h3>
      <p class="guide-desc">{guide?.description}</p>
      <ol class="guide-steps">
        {#each guide?.steps ?? [] as step}
          <li>{step}</li>
        {/each}
      </ol>
      <p class="guide-env"><strong>Required:</strong> {guide?.env}</p>
    </section>

    <div class="integrate-code-shell">
      <div class="code-head">
        <span class="code-title">{tools.find(t => t.id === activeTool)?.name || activeTool}</span>
        <button class="copy-btn" type="button" onclick={copyGuide}>
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
               stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <rect x="9" y="9" width="13" height="13" rx="2"/>
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
          </svg>
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>
      <pre class="integrate-code"><code>{snippet}</code></pre>
    </div>
    <p class="integrate-note">
      Hosted guide: <code>docs/DOCUMENTATION.md</code> plus reproducible files under
      <code>frontend/static/integrations/&lt;tab&gt;.txt</code>.
    </p>
  </div>
</div>

<!-- DEMO -->
<section class="section demo-section" use:reveal>
  <div class="container">
    <div class="section-head">
      <span class="section-id">00</span>
      <h2>Live flow</h2>
      <span class="count">loop · 4 stages</span>
    </div>
    <div class="demo">
      <div class="demo-col">
        <div class="demo-row">
          <span class="prompt">$</span>
          <span class="typed">agent.query("summarize url")</span>
          <span class="cursor" class:blink={stage >= 0}></span>
        </div>

        <div class="demo-block" class:active={stage >= 1}>
          <div class="block-head">01 DISCOVER</div>
          <div class="demo-list">
            <div class="demo-item hot">
              <span class="name">summarize-url</span>
              <span class="meta">exact · USDC 0.002</span>
            </div>
            <div class="demo-item">
              <span class="name">doc-extract</span>
              <span class="meta">similar 0.91</span>
            </div>
            <div class="demo-item">
              <span class="name">web-scraper</span>
              <span class="meta">similar 0.84</span>
            </div>
          </div>
        </div>

        <div class="demo-block" class:active={stage >= 2}>
          <div class="block-head">02 PAY · x402</div>
          <div class="demo-line">sign USDC 0.002 → facilitator → settled</div>
          <div class="meter"><span class="meter-fill" class:done={stage >= 2}></span></div>
        </div>

        <div class="demo-block" class:active={stage >= 3}>
          <div class="block-head">03 SETTLE</div>
          <div class="demo-grid">
            <div><span class="k">receipt</span><span class="v">consumed</span></div>
            <div><span class="k">escrow</span><span class="v">30d hold</span></div>
            <div><span class="k">provider</span><span class="v">98% accrued</span></div>
            <div><span class="k">call_id</span><span class="v">c_8f2a…</span></div>
          </div>
        </div>
      </div>
      <div class="demo-col demo-status">
        <div class="status-head">STAGE</div>
        <div class="stage-list">
          <div class="stage" class:active={stage === 0}>00 query</div>
          <div class="stage" class:active={stage === 1}>01 discover</div>
          <div class="stage" class:active={stage === 2}>02 pay</div>
          <div class="stage" class:active={stage === 3}>03 settle</div>
        </div>
        <div class="status-foot">looping · no human in loop</div>
      </div>
    </div>
  </div>
</section>

<!-- RESULTS -->
{#if invoked}
  <section class="section" use:reveal>
    <div class="container">
      <div class="section-head">
        <span class="section-id">01</span>
        <h2>Results</h2>
        <span class="count">{results.length}</span>
      </div>
      {#if loginRequired}
        <div class="panel center">
          <p>Authentication required to read the registry.</p>
          <a class="btn" href="/login">LOGIN</a>
        </div>
      {:else if error}
        <div class="panel warn">{error}</div>
      {:else}
        <div class="grid">
          {#each results as r}
            <a class="card" href={`/service/${r.id}`}>
              <div class="card-row">
                <span class="card-name">{r.name}</span>
                <span class="price">{r.currency} {(r.price_atomic/1e6).toFixed(6)}</span>
              </div>
              <p class="card-desc">{r.description}</p>
              <div class="card-foot">
                <span class="tag">{r.match}</span>
                <span class="score">score {r.score}</span>
              </div>
            </a>
          {/each}
        </div>
        {#if !loading && results.length === 0}
          <div class="panel muted">NO_MATCHES. Publish one.</div>
        {/if}
      {/if}
    </div>
  </section>
{/if}

<!-- VISION -->
<section class="section" use:reveal>
  <div class="container">
    <div class="section-head">
      <span class="section-id">02</span>
      <h2>Thesis</h2>
    </div>
    <p class="lead-plain">
      HTTP gave humans pages. MCP gave agents tools. AgentsTalk gives the machine economy
      a registry: one searchable index, one payment rail, one settlement window.
    </p>
    <div class="cols3">
      <div class="stat-card">
        <div class="stat-big">QUERY</div>
        <h3>Discovery</h3>
        <p>Embed the query. Rank exact name/id matches first, then cosine-similar services above a 0.25 floor.</p>
      </div>
      <div class="stat-card">
        <div class="stat-big">x402</div>
        <h3>Payment</h3>
        <p>Per call in USDC on Base. No accounts, no seats. Agent signs; server settles via facilitator.</p>
      </div>
      <div class="stat-card">
        <div class="stat-big">30d</div>
        <h3>Trust</h3>
        <p>Receipts, escrow hold, spend caps, domain verification. Enforcement in code, not fine print.</p>
      </div>
    </div>
  </div>
</section>

<!-- HOW -->
<section class="section alt" use:reveal>
  <div class="container">
    <div class="section-head">
      <span class="section-id">03</span>
      <h2>Pipeline</h2>
    </div>
    <div class="pipeline">
      <div class="pipeline-track"><div class="pipeline-pulse"></div></div>
      <div class="pipeline-nodes">
        <div class="node"><div class="node-num">01</div><div class="node-lab">PUBLISH</div><p class="node-desc">Manifest + price per call</p></div>
        <div class="node"><div class="node-num">02</div><div class="node-lab">DISCOVER</div><p class="node-desc">Exact → semantic ranking</p></div>
        <div class="node"><div class="node-num">03</div><div class="node-lab">PAY</div><p class="node-desc">x402 USDC on Base</p></div>
        <div class="node"><div class="node-num">04</div><div class="node-lab">SETTLE</div><p class="node-desc">30-day hold, auto release</p></div>
      </div>
    </div>
  </div>
</section>

<!-- ECONOMICS -->
<section class="section" use:reveal>
  <div class="container">
    <div class="section-head">
      <span class="section-id">04</span>
      <h2>Economics</h2>
    </div>
    <div class="econ">
      <div class="econ-card"><div class="econ-num">98%</div><div class="econ-lbl">provider share</div><p>Per call. No subscriptions, tiers, or minimums.</p></div>
      <div class="econ-card"><div class="econ-num">2%</div><div class="econ-lbl">platform fee</div><p>Covers embedding, pgvector search, registry, payouts.</p></div>
      <div class="econ-card"><div class="econ-num">30d</div><div class="econ-lbl">cashback hold</div><p>Every call escrowed a month. Refunds funded from hold.</p></div>
    </div>
  </div>
</section>

<!-- STANDARDS -->
<section class="section alt" use:reveal>
  <div class="container">
    <div class="section-head">
      <span class="section-id">05</span>
      <h2>Standards</h2>
    </div>
    <div class="chips">
      <span class="chip">MCP</span>
      <span class="chip">x402</span>
      <span class="chip">AP2</span>
      <span class="chip">USDC / Base</span>
      <span class="chip">pgvector + HNSW</span>
      <span class="chip">RFC 8615</span>
    </div>
    <p class="lead-plain small">Reuse MCP. Add pricing, trust metadata, payment rail. No SDK rewrite required.</p>
  </div>
</section>

<!-- CTA -->
<section class="cta" use:reveal>
  <div class="container center">
    <h2>List a service. Let agents find it.</h2>
    <div class="ctarow">
      <a href="/publish" class="btn primary">PUBLISH →</a>
      <a href="/login" class="btn ghost">LOGIN</a>
    </div>
  </div>
</section>

<footer class="footer">
  <div class="container footrow">
    <span>AgentsTalk — machine service registry</span>
    <span class="muted">MCP · x402 · USDC on Base</span>
  </div>
</footer>

<style>
  .backdrop { position:fixed; inset:0; z-index:-1; background:#040609; }
  .backdrop::after {
    content:''; position:absolute; inset:0;
    background-image: linear-gradient(rgba(148,163,184,.05) 1px, transparent 1px),
      linear-gradient(90deg, rgba(148,163,184,.05) 1px, transparent 1px);
    background-size: 64px 64px;
    mask-image: radial-gradient(900px 600px at 50% 20%, #000 40%, transparent 85%);
  }

  .hero { padding: 24px 0 64px; }
  .topline { display:flex; justify-content:space-between; font-size:11px; letter-spacing:.14em; margin-bottom:28px; }
  .label { color:#4ade80; }
  .label.muted { color:#64748b; }
  h1 { font-size: clamp(40px, 6vw, 76px); line-height:1.02; letter-spacing:-0.02em; margin:0 0 18px; font-weight:700; }
  .lead { color:#94a3b8; font-size:18px; max-width:720px; line-height:1.55; margin-bottom:26px; }
  .lead-plain { color:#94a3b8; font-size:17px; max-width:820px; line-height:1.55; margin-bottom:28px; }
  .lead-plain.small { font-size:14px; margin-top:18px; }

  .searchbar { display:flex; gap:0; max-width:720px; background:#080b11; }
  .sinput { flex:1; background:transparent; outline:none; color:#e2e8f0; font-size:15px; padding:12px 14px; font-family:ui-monospace,SFMono-Regular,monospace; }
  .sbtn { background:#4ade80; color:#040609; padding:0 20px; font-weight:700; font-size:12px; letter-spacing:.1em; cursor:pointer; }
  .sbtn:disabled { opacity:.6; }

  .kpi-strip { display:flex; gap:24px; flex-wrap:wrap; margin-top:30px; padding-top:20px; }
  .kpi { display:flex; flex-direction:column; }
  .kpi-num { font-size:28px; font-weight:700; color:#e2e8f0; font-family:ui-monospace,SFMono-Regular,monospace; }
  .kpi-lbl { font-size:11px; text-transform:uppercase; letter-spacing:.1em; color:#64748b; }

  .section { padding:72px 0; position:relative; }
  .section.alt { background:rgba(13,18,28,.6); }
  .container { max-width:1120px; margin:0 auto; padding:0 24px; }
  .section-head { display:flex; align-items:baseline; gap:14px; margin-bottom:24px; }
  .section-id { font-family:ui-monospace,SFMono-Regular,monospace; color:#4ade80; font-size:12px; }
  h2 { font-size: clamp(24px, 3.2vw, 38px); margin:0; font-weight:700; letter-spacing:-0.01em; }
  .count { margin-left:auto; font-family:ui-monospace,SFMono-Regular,monospace; color:#64748b; font-size:12px; }

  .cols3 { display:grid; grid-template-columns:repeat(3,1fr); gap:16px; }
  .stat-card { background:#080b11; padding:20px; }
  .stat-big { font-family:ui-monospace,SFMono-Regular,monospace; color:#4ade80; font-size:13px; margin-bottom:10px; }
  .stat-card h3 { margin:0 0 6px; font-size:16px; }
  .stat-card p { color:#94a3b8; margin:0; font-size:13px; line-height:1.5; }

  .pipeline { padding:12px 0 4px; }
  .pipeline-track { position:relative; height:2px; background:#141b26; margin:0 32px 26px; overflow:hidden; }
  .pipeline-pulse { position:absolute; top:-3px; left:0; width:28px; height:8px; background:linear-gradient(90deg,transparent,#4ade80,transparent); animation: travel 4s linear infinite; }
  @keyframes travel { 0% { left:0%; } 100% { left:100%; } }
  .pipeline-nodes { display:grid; grid-template-columns:repeat(4,1fr); gap:14px; }
  .node { text-align:center; opacity:.35; animation: nodeflash 4s linear infinite; }
  .node:nth-child(1) { animation-delay:0s; }
  .node:nth-child(2) { animation-delay:1s; }
  .node:nth-child(3) { animation-delay:2s; }
  .node:nth-child(4) { animation-delay:3s; }
  @keyframes nodeflash { 0% { opacity:.35; transform:scale(1); } 12% { opacity:1; transform:scale(1.06); } 32% { opacity:1; transform:scale(1); } 42% { opacity:.35; transform:scale(1); } 100% { opacity:.35; transform:scale(1); } }
  .node-num { font-family:ui-monospace,SFMono-Regular,monospace; color:#334155; font-size:28px; font-weight:700; margin-bottom:8px; animation: numcolor 4s linear infinite; }
  .node:nth-child(1) .node-num { animation-delay:0s; }
  .node:nth-child(2) .node-num { animation-delay:1s; }
  .node:nth-child(3) .node-num { animation-delay:2s; }
  .node:nth-child(4) .node-num { animation-delay:3s; }
  @keyframes numcolor { 0% { color:#334155; } 12%,32% { color:#4ade80; } 42%,100% { color:#334155; } }
  .node-lab { font-size:13px; letter-spacing:.1em; font-weight:600; color:#e2e8f0; margin-bottom:4px; }
  .node-desc { color:#64748b; margin:0; font-size:12px; }

  .econ { display:grid; grid-template-columns:repeat(3,1fr); gap:16px; }
  .econ-card { background:#080b11; padding:24px; }
  .econ-num { font-size:44px; font-weight:700; color:#e2e8f0; font-family:ui-monospace,SFMono-Regular,monospace; line-height:1; }
  .econ-lbl { font-size:11px; text-transform:uppercase; letter-spacing:.1em; color:#64748b; margin:8px 0 6px; }
  .econ-card p { color:#94a3b8; margin:0; font-size:13px; }

  .chips { display:flex; flex-wrap:wrap; gap:8px; margin-top:8px; }
  .chip { padding:6px 12px; font-size:12px; color:#94a3b8; font-family:ui-monospace,SFMono-Regular,monospace; background:#080b11; }

  .cta { padding:80px 0; text-align:center; }
  .center { text-align:center; }
  .ctarow { display:flex; gap:12px; justify-content:center; margin-top:20px; }
  .btn { display:inline-block; padding:10px 18px; text-decoration:none; font-weight:700; font-size:12px; letter-spacing:.08em; color:#e2e8f0; background:#080b11; }
  .btn.primary { background:#4ade80; color:#040609; }
  .btn.ghost { color:#94a3b8; }
  .btn:hover { }
  .btn.big { padding:12px 22px; }

  .results { padding:40px 0 16px; }
  .grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(280px,1fr)); gap:12px; }
  .card { display:block; text-decoration:none; color:#e2e8f0; background:#080b11; padding:16px; transition:border-color .15s; }
  .card:hover { }
  .card-row { display:flex; justify-content:space-between; align-items:center; gap:8px; margin-bottom:6px; }
  .card-name { font-weight:600; font-size:15px; }
  .price { color:#4ade80; font-family:ui-monospace,SFMono-Regular,monospace; font-size:12px; }
  .card-desc { color:#94a3b8; font-size:13px; margin:0 0 10px; }
  .card-foot { display:flex; justify-content:space-between; font-size:11px; color:#64748b; }
  .tag { padding:2px 8px; font-family:ui-monospace,SFMono-Regular,monospace; }
  .score { font-family:ui-monospace,SFMono-Regular,monospace; }

  .panel { background:#080b11; padding:18px; }
  .panel.warn { color:#fca5a5; background:#1a0e0e; }
  .panel.muted { color:#64748b; font-family:ui-monospace,SFMono-Regular,monospace; }
  .panel.center { text-align:center; }

  .footer { padding:32px 0; color:#64748b; font-size:12px; }
  .footrow { display:flex; justify-content:space-between; flex-wrap:wrap; gap:10px; font-family:ui-monospace,SFMono-Regular,monospace; }

  .muted { color:#64748b; }
  .warn { color:#fca5a5; }

  /* ---- demo ---- */
  .demo-section { }
  .demo { display:grid; grid-template-columns: 2fr 1fr; gap:18px; background:#080b11; padding:18px; }
  .demo-col { display:flex; flex-direction:column; gap:12px; }
  .demo-row { display:flex; align-items:center; gap:8px; font-family:ui-monospace,SFMono-Regular,monospace; font-size:14px; padding:10px 12px; background:#040609; }
  .prompt { color:#4ade80; font-weight:700; }
  .typed { color:#e2e8f0; }
  .cursor { width:8px; height:16px; background:#4ade80; animation: blink .9s steps(2) infinite; }
  @keyframes blink { 50% { opacity:0; } }

  .demo-block { background:#040609; padding:12px; opacity:.35; transform:translateY(6px); transition:opacity .4s ease, transform .4s ease, border-color .4s; }
  .demo-block.active { opacity:1; transform:none; }
  .block-head { font-family:ui-monospace,SFMono-Regular,monospace; font-size:11px; letter-spacing:.1em; color:#4ade80; margin-bottom:8px; }

  .demo-list { display:flex; flex-direction:column; gap:6px; }
  .demo-item { display:flex; justify-content:space-between; padding:6px 8px; font-size:12px; }
  .demo-item.hot { }
  .demo-item .name { font-family:ui-monospace,SFMono-Regular,monospace; color:#e2e8f0; }
  .demo-item .meta { color:#64748b; font-family:ui-monospace,SFMono-Regular,monospace; }

  .demo-line { font-family:ui-monospace,SFMono-Regular,monospace; font-size:12px; color:#94a3b8; margin-bottom:8px; }
  .meter { height:6px; background:#161d2a; overflow:hidden; }
  .meter-fill { display:block; height:100%; width:0%; background:#4ade80; transition:width .9s ease; }
  .meter-fill.done { width:100%; }

  .demo-grid { display:grid; grid-template-columns:1fr 1fr; gap:6px; }
  .demo-grid div { display:flex; flex-direction:column; gap:2px; padding:6px 8px; }
  .demo-grid .k { font-size:10px; text-transform:uppercase; letter-spacing:.1em; color:#64748b; font-family:ui-monospace,SFMono-Regular,monospace; }
  .demo-grid .v { font-size:12px; color:#e2e8f0; font-family:ui-monospace,SFMono-Regular,monospace; }

  .demo-status { padding:12px; }
  .status-head { font-family:ui-monospace,SFMono-Regular,monospace; font-size:11px; color:#64748b; letter-spacing:.1em; margin-bottom:8px; }
  .stage-list { display:flex; flex-direction:column; gap:6px; }
  .stage { padding:6px 8px; font-family:ui-monospace,SFMono-Regular,monospace; font-size:12px; color:#64748b; transition:all .3s; }
  .stage.active { color:#040609; background:#4ade80; font-weight:700; }
  .status-foot { margin-top:12px; color:#64748b; font-size:11px; font-family:ui-monospace,SFMono-Regular,monospace; }

  @media (max-width:860px) {
    .cols3, .pipeline-nodes, .econ { grid-template-columns:1fr; }
    h1 { font-size:44px; }
    .demo { grid-template-columns:1fr; }
  }

  .integrate { background:#0d1117; border-radius:12px; padding:16px; margin:18px 0 0;
                border:0; }
  .guide-card { background:#101620; border-radius:12px; padding:14px; margin:12px 0; }
  .guide-card h3 { margin:0 0 4px; font-size:15px; color:#5eead4; }
  .guide-desc { color:#b8c3d0; font-size:12px; margin:0 0 8px; }
  .guide-steps { margin:0; padding-inline-start:20px; color:#dbe6f0; font-size:12px; line-height:1.5; }
  .guide-env { font-size:11px; color:#8a95a4; margin-top:8px; }
  .integrate-head { color:#4ade80; font-size:11px; letter-spacing:.1em;
                    text-transform:uppercase; font-weight:700; margin-bottom:10px; }
  .tool-tabs { display:flex; flex-wrap:wrap; gap:6px; margin-bottom:10px; }
  .tool-tab { border:0; background:#151b24; color:#b5c1cf; border-radius:999px;
               padding:7px 10px; font-size:11px; cursor:pointer; }
  .tool-tab.active { background:#4ade80; color:#07150d; font-weight:700; }
  .tool-icon { border-radius:3px; background:#1a1f29; object-fit:contain;
               vertical-align:text-bottom; }
  .integrate-code-shell { background:#070a0f; border-radius:12px; padding:10px;
                          overflow:hidden; }
  .code-head { display:flex; justify-content:space-between; align-items:center;
               padding:8px 10px 10px; color:#9ca7b8; font-size:11px; }
  .code-title { letter-spacing:.08em; text-transform:uppercase; color:#5eead4; }
  .copy-btn { display:flex; align-items:center; gap:6px; border:0; background:#171f2a;
              color:#e5edf6; border-radius:8px; padding:6px 10px; font-size:11px;
              cursor:pointer; }
  .copy-btn:hover { background:#223041; }
  .integrate-code { background:#040609; color:#d7e1ea; padding:14px; border-radius:10px;
                    overflow-x:auto; font-size:12px; line-height:1.45; margin:0; }
  .integrate-code code { font-family:ui-monospace,SFMono-Regular,monospace; }
  .integrate-note { color:#8b93a7; font-size:12px; margin-top:10px; }
  .integrate-note code { color:#9cc0ff; }
</style>
