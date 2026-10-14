<!-- src/routes/demo/+page.svelte -->
<script>
  const API = import.meta.env.PUBLIC_API_BASE || 'http://localhost:8000';
  let flow = $state(null);
  let idx = $state(0);
  let playing = $state(false);
  let timer = null;

  async function load() {
    const r = await fetch('/demo-flow.json');
    flow = await r.json();
  }
  $effect(() => { load(); });

  function play() {
    if (!flow) return;
    playing = true;
    timer = setInterval(() => {
      if (idx < flow.steps.length - 1) idx++;
      else { playing = false; clearInterval(timer); }
    }, 2200);
  }
  function pause() { playing = false; if (timer) clearInterval(timer); }
  function next() { pause(); if (flow && idx < flow.steps.length-1) idx++; }
  function prev() { pause(); if (idx > 0) idx--; }
  function reset() { pause(); idx = 0; }

  $effect(() => () => { if (timer) clearInterval(timer); });

  let total = $derived(flow ? flow.steps.length : 0);
  let step = $derived(flow ? flow.steps[idx] : null);
  let progress = $derived(total ? ((idx+1)/total*100) : 0);
</script>

<div class="container" style="max-width:1080px;">
  <div class="demo-head">
    <div>
      <h1>Demo replay</h1>
      <p class="muted">Self-running walkthrough of a real AgentTalk end-to-end flow. {flow ? `v${flow.version}` : ''}</p>
    </div>
    <div class="demo-controls">
      <button class="ghost" onclick={reset}>Reset</button>
      <button class="ghost" onclick={prev} disabled={idx===0}>Prev</button>
      {#if playing}
        <button class="primary" onclick={pause}>Pause</button>
      {:else}
        <button class="primary" onclick={play}>Play</button>
      {/if}
      <button class="ghost" onclick={next} disabled={idx>=total-1}>Next</button>
    </div>
  </div>

  {#if !flow}
    <div class="empty">Loading demo fixture…</div>
  {:else}
    <div class="progress-wrap">
      <div class="progress"><span style="width:{progress}%"></span></div>
      <span class="meta">{idx+1} / {total}</span>
    </div>

    <div class="demo-grid">
      <div class="demo-side">
        <div class="side-title">JOURNEY</div>
        {#each flow.steps as s, i}
          <button class="side-step" class:active={i===idx} class:done={i<idx} onclick={() => { pause(); idx = i; }}>
            <span class="side-num">{String(i+1).padStart(2,'0')}</span>
            <span class="side-lab">{s.id}</span>
          </button>
        {/each}
      </div>

      <div class="demo-main">
        {#if step}
          <div class="panel">
            <div class="panel-head">
              <span class="tag">{step.method || 'UI'}</span>
              <span class="panel-title">{step.id}</span>
              {#if step.status}<span class="tag ok">{step.status}</span>{/if}
            </div>
            {#if step.path}<div class="row"><span class="k">endpoint</span><span class="v">{step.path}</span></div>{/if}
            {#if step.ui}<div class="row"><span class="k">ui</span><span class="v">{step.ui}</span></div>{/if}
            {#if step.payload}
              <div class="row-block">
                <div class="k">payload</div>
                <pre>{JSON.stringify(step.payload, null, 2)}</pre>
              </div>
            {/if}
            {#if step.resultCount !== undefined}
              <div class="row"><span class="k">results</span><span class="v">{step.resultCount} (top: {step.top}, {step.match})</span></div>
            {/if}
            {#if step.receipt}
              <div class="row"><span class="k">receipt</span><span class="v">{step.receipt} ({step.receiptStatus})</span></div>
            {/if}
            {#if step.callStatus}
              <div class="row"><span class="k">call</span><span class="v">{step.callStatus} · receiptConsumed={step.receiptConsumed}</span></div>
            {/if}
            {#if step.platformFeeAtomic !== undefined}
              <div class="row"><span class="k">fees</span><span class="v">platform {step.platformFeeAtomic}, developer {step.developerShareAtomic} (atomic)</span></div>
            {/if}
            {#if step.receiptConsumed === false && step.note}
              <div class="row"><span class="k">note</span><span class="v">{step.note}</span></div>
            {/if}
            {#if step.best !== undefined}
              <div class="row"><span class="k">best</span><span class="v">{step.best ?? 'none (demo endpoints down)'}</span></div>
            {/if}
            {#if step.balance_atomic !== undefined}
              <div class="row"><span class="k">balance</span><span class="v">{step.balance_atomic} atomic</span></div>
            {/if}
            {#if step.note && step.receiptConsumed !== false}
              <div class="row"><span class="k">note</span><span class="v">{step.note}</span></div>
            {/if}
          </div>
        {/if}

        <div class="flow-strip">
          {#each (flow.steps || []) as s, i}
            <div class="strip-node" class:active={i===idx} class:done={i<idx}>
              {s.id}
            </div>
            {#if i < flow.steps.length-1}<div class="strip-link" class:done={i<idx}></div>{/if}
          {/each}
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .container { max-width:1080px; margin:0 auto; padding:0 24px; }
  h1 { font-size:32px; margin:0 0 6px; font-weight:600; letter-spacing:-.02em; }
  .muted { color:#6b768a; margin-bottom:18px; }
  .meta { font-size:11px; color:#6b768a; font-family:ui-monospace,SFMono-Regular,monospace; margin-left:10px; }

  .demo-head { display:flex; justify-content:space-between; align-items:flex-end; gap:16px; flex-wrap:wrap; margin-bottom:20px; }
  .demo-controls { display:flex; gap:8px; flex-wrap:wrap; }
  button { font:inherit; cursor:pointer; border-radius:6px; padding:7px 12px; font-size:12px; font-weight:600; background:#0f1624; color:#dbe4f0; }
  button:disabled { opacity:.4; cursor:default; }
  .ghost { background:#0f1624; }
  .primary { background:#4ade80; color:#04120a; }
  .primary:hover { background:#63e79b; }

  .progress-wrap { display:flex; align-items:center; gap:12px; margin:12px 0 20px; }
  .progress { flex:1; height:4px; background:#161d2a; border-radius:999px; overflow:hidden; }
  .progress span { display:block; height:100%; background:#4ade80; transition:width .3s ease; }

  .demo-grid { display:grid; grid-template-columns:220px 1fr; gap:16px; }
  @media (max-width:760px){ .demo-grid { grid-template-columns:1fr; } }

  .demo-side { background:#090c12; border-radius:10px; padding:8px; max-height:520px; overflow:auto; }
  .side-title { font-size:10px; letter-spacing:.14em; color:#6b768a; padding:6px 8px; }
  .side-step { width:100%; display:flex; gap:8px; align-items:center; background:transparent; color:#8b95a5; padding:6px 8px; text-align:left; border-radius:6px; margin:2px 0; }
  .side-step.active { background:#121d14; color:#4ade80; }
  .side-step.done { color:#6be0a0; }
  .side-num { font-family:ui-monospace,SFMono-Regular,monospace; font-size:10px; color:#5b6472; }
  .side-step.active .side-num { color:#4ade80; }
  .side-lab { font-size:12px; }

  .demo-main { display:flex; flex-direction:column; gap:14px; }
  .panel { background:#090c12; border-radius:10px; padding:18px; }
  .panel-head { display:flex; gap:10px; align-items:center; margin-bottom:12px; }
  .panel-title { font-size:18px; font-weight:600; letter-spacing:-.01em; }
  .tag { font-family:ui-monospace,SFMono-Regular,monospace; font-size:10px; padding:3px 7px; border-radius:999px; background:#0f1624; color:#94a3b8; letter-spacing:.08em; text-transform:uppercase; }
  .tag.ok { background:rgba(74,222,128,.15); color:#4ade80; }
  .row { display:flex; gap:12px; padding:6px 0; font-size:13px; }
  .row-block { padding:6px 0; }
  .k { min-width:90px; font-size:10px; text-transform:uppercase; letter-spacing:.12em; color:#7b8494; font-family:ui-monospace,monospace; }
  .v { color:#e2e8f0; font-size:13px; word-break:break-word; }
  .row-block .k { display:block; margin-bottom:4px; }
  pre { margin:0; padding:10px 12px; background:#05070a; border-radius:6px; color:#b9c3d1; font-size:11px; overflow:auto; font-family:ui-monospace,SFMono-Regular,monospace; }

  .flow-strip { display:flex; align-items:center; justify-content:center; flex-wrap:wrap; gap:6px; padding:12px 4px; }
  .strip-node { padding:6px 10px; background:#05070a; color:#64748b; font-size:10px; letter-spacing:.1em; text-transform:uppercase; border-radius:4px; font-family:ui-monospace,monospace; transition:all .2s; }
  .strip-node.active { background:#4ade80; color:#04120a; font-weight:700; }
  .strip-node.done { color:#4ade80; }
  .strip-link { width:14px; height:2px; background:#161d2a; }
  .strip-link.done { background:#4ade80; }

  .empty { padding:30px 0; color:#6b768a; }
  .container { max-width:1080px; margin:0 auto; padding:0 24px; }
</style>
