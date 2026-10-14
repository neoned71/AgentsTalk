<!-- src/lib/AnimatedNote.svelte -->
<script>
  let { variant = 'flow', title = 'How it works', note = '' } = $props();
</script>

<div class="anote">
  <div class="anote-id">{title}</div>

  {#if variant === 'search'}
    <div class="demo demo-search">
      <div class="d-searchbar"><span class="typed">summarize url</span><span class="caret"></span></div>
      <div class="d-results">
        <div class="d-row hot"><span>summarize-url</span><span class="d-tag">exact</span><span class="d-ping">24 ms</span></div>
        <div class="d-row"><span>doc-extract</span><span class="d-tag">similar 0.91</span><span class="d-ping">48 ms</span></div>
        <div class="d-row"><span>web-scraper</span><span class="d-tag">similar 0.84</span><span class="d-ping">96 ms</span></div>
      </div>
    </div>

  {:else if variant === 'receipt'}
    <div class="demo demo-receipt">
      <div class="d-track"><div class="d-dot"></div></div>
      <div class="d-stages">
        <div class="d-stage s1">RESERVED</div>
        <div class="d-stage s2">CONSUMED</div>
        <div class="d-stage s3">VOIDED</div>
      </div>
      <div class="d-caption">credits deduct → hold → consume on success, refund on fail</div>
    </div>

  {:else if variant === 'escrow'}
    <div class="demo demo-escrow">
      <div class="d-bar"><div class="d-fill"></div></div>
      <div class="d-ticks">
        <span>day 0</span><span>day 15</span><span>day 30 release</span>
      </div>
      <div class="d-caption">funds held in escrow, then auto-release to provider</div>
    </div>

  {:else if variant === 'credits'}
    <div class="demo demo-credits">
      <div class="d-balance"><div class="d-bal-fill"></div><span>balance</span></div>
      <div class="d-arrow">↓ reserve</div>
      <div class="d-receipt">receipt · consumed / voided</div>
    </div>

  {:else if variant === 'keys'}
    <div class="demo demo-keys">
      <div class="d-key">ak_xxxxxxxx</div>
      <div class="d-flow">
        <span class="d-node">agent</span><span class="d-arrow2">→</span><span class="d-node">hub</span><span class="d-arrow2">→</span><span class="d-node">service</span>
      </div>
      <div class="d-caption">scoped, spend-capped, revocable</div>
    </div>

  {:else if variant === 'service'}
    <div class="demo demo-service">
      <div class="d-pkt">manifest</div>
      <div class="d-pipe"><div class="d-pkt2"></div></div>
      <div class="d-hub">HUB INDEX</div>
    </div>

  {:else if variant === 'publish'}
    <div class="demo demo-publish">
      <div class="d-stack">
        <div class="d-card c1">domain</div>
        <div class="d-card c2">wallet</div>
        <div class="d-card c3">manifest</div>
        <div class="d-card c4">price / call</div>
      </div>
      <div class="d-caption">verified → indexed → discoverable</div>
    </div>

  {:else}
    <div class="demo demo-flow">
      <div class="d-chain">
        <span class="d-node">query</span><span class="d-link"></span>
        <span class="d-node">match</span><span class="d-link"></span>
        <span class="d-node">pay</span><span class="d-link"></span>
        <span class="d-node">settle</span>
      </div>
    </div>
  {/if}

  {#if note}
    <p class="anote-text">{note}</p>
  {/if}
</div>

<style>
  .anote { margin:16px 0 20px; padding:14px 16px; background:rgba(10,13,18,.6); border:1px solid #161d2a; border-radius:10px; }
  .anote-id { font-family:ui-monospace,SFMono-Regular,monospace; font-size:10px; letter-spacing:.14em; color:#4ade80; margin-bottom:10px; }

  .demo { padding:6px 2px 2px; }
  .anote-text { margin:10px 0 0; font-size:12px; color:#8b95a5; line-height:1.55; }

  /* search */
  .demo-search { display:flex; flex-direction:column; gap:8px; }
  .d-searchbar { display:flex; align-items:center; gap:4px; padding:8px 10px; background:#06090f; border:1px solid #161d2a; font-family:ui-monospace,monospace; font-size:12px; }
  .typed { color:#e2e8f0; animation: type 2.4s steps(13,end) infinite; overflow:hidden; white-space:nowrap; max-width:0; display:inline-block; }
  @keyframes type { 0%{max-width:0} 40%,80%{max-width:120px} 100%{max-width:0} }
  .caret { width:7px; height:13px; background:#4ade80; animation: blink .9s steps(2) infinite; }
  @keyframes blink { 50%{opacity:0} }
  .d-results { display:flex; flex-direction:column; gap:6px; }
  .d-row { display:flex; justify-content:space-between; gap:8px; padding:6px 8px; background:#06090f; font-size:11px; font-family:ui-monospace,monospace; color:#94a3b8; opacity:.4; transform:translateX(-6px); animation: rowin .6s ease forwards; }
  .d-row.hot { color:#e2e8f0; border-left:2px solid #4ade80; }
  .d-row:nth-child(1){animation-delay:1.0s}
  .d-row:nth-child(2){animation-delay:1.4s}
  .d-row:nth-child(3){animation-delay:1.8s}
  @keyframes rowin { to { opacity:1; transform:translateX(0); } }
  .d-tag { color:#64748b; }
  .d-ping { color:#4ade80; }

  /* receipt */
  .demo-receipt { display:flex; flex-direction:column; gap:10px; }
  .d-track { height:4px; background:#161d2a; border-radius:999px; overflow:hidden; }
  .d-dot { height:100%; width:30%; background:linear-gradient(90deg,transparent,#4ade80,transparent); animation: sweep 2s ease-in-out infinite; }
  @keyframes sweep { 0%{transform:translateX(-100%)} 100%{transform:translateX(340%)} }
  .d-stages { display:flex; gap:8px; }
  .d-stage { flex:1; text-align:center; padding:6px 4px; background:#06090f; font-family:ui-monospace,monospace; font-size:10px; letter-spacing:.1em; color:#64748b; border-radius:6px; animation: stagepulse 2.4s ease-in-out infinite; }
  .d-stage.s1 { animation-delay:0s; }
  .d-stage.s2 { animation-delay:.8s; }
  .d-stage.s3 { animation-delay:1.6s; }
  @keyframes stagepulse { 0%,70%,100%{color:#64748b;background:#06090f} 30%{color:#04120a;background:#4ade80} }
  .d-caption { font-size:11px; color:#64748b; font-family:ui-monospace,monospace; }

  /* escrow */
  .demo-escrow { display:flex; flex-direction:column; gap:8px; }
  .d-bar { height:8px; background:#161d2a; border-radius:999px; overflow:hidden; }
  .d-fill { height:100%; width:0; background:linear-gradient(90deg,#4ade80,#63e79b); animation: fill30 3s ease-in-out infinite; }
  @keyframes fill30 { 0%{width:0} 60%{width:100%} 100%{width:100%} }
  .d-ticks { display:flex; justify-content:space-between; font-size:10px; color:#64748b; font-family:ui-monospace,monospace; }

  /* credits */
  .demo-credits { display:flex; flex-direction:column; gap:8px; align-items:center; }
  .d-balance { width:100%; height:12px; background:#161d2a; border-radius:999px; overflow:hidden; position:relative; }
  .d-bal-fill { position:absolute; inset:0; background:linear-gradient(90deg,#6ee7b7,#60a5fa); animation: bal 2.6s ease-in-out infinite; }
  @keyframes bal { 0%{transform:scaleX(1)} 40%{transform:scaleX(.6)} 100%{transform:scaleX(1)} }
  .d-balance span { position:absolute; right:8px; top:-18px; font-size:10px; color:#94a3b8; }
  .d-arrow { color:#4ade80; font-size:12px; animation: bounce 1.2s ease-in-out infinite; }
  @keyframes bounce { 0%,100%{transform:translateY(0)} 50%{transform:translateY(4px)} }
  .d-receipt { font-size:11px; color:#94a3b8; font-family:ui-monospace,monospace; }

  /* keys */
  .demo-keys { display:flex; flex-direction:column; gap:8px; align-items:center; }
  .d-key { font-family:ui-monospace,monospace; font-size:11px; color:#4ade80; padding:6px 10px; background:#06090f; border-radius:6px; animation: glow 2s ease-in-out infinite; }
  @keyframes glow { 0%,100%{box-shadow:0 0 0 rgba(74,222,128,0)} 50%{box-shadow:0 0 12px rgba(74,222,128,.35)} }
  .d-flow { display:flex; align-items:center; gap:6px; font-size:11px; color:#94a3b8; font-family:ui-monospace,monospace; }
  .d-node { padding:4px 8px; background:#06090f; border-radius:4px; animation: nodeblink 2s ease-in-out infinite; }
  .d-node:nth-child(1){animation-delay:0s}
  .d-node:nth-child(3){animation-delay:.6s}
  .d-node:nth-child(5){animation-delay:1.2s}
  @keyframes nodeblink { 0%,100%{opacity:.5} 50%{opacity:1} }
  .d-arrow2 { color:#4ade80; }

  /* service */
  .demo-service { display:flex; align-items:center; gap:10px; justify-content:center; }
  .d-pkt { padding:6px 10px; background:#4ade80; color:#04120a; font-size:11px; font-weight:700; border-radius:6px; }
  .d-pipe { position:relative; width:120px; height:2px; background:#161d2a; overflow:hidden; }
  .d-pkt2 { position:absolute; top:-3px; left:0; width:12px; height:8px; background:#4ade80; animation: movepkt 1.8s linear infinite; }
  @keyframes movepkt { 0%{left:0} 100%{left:108px} }
  .d-hub { padding:6px 10px; background:#06090f; color:#4ade80; font-size:11px; font-family:ui-monospace,monospace; border-radius:6px; animation: hubpulse 1.8s ease-in-out infinite; }
  @keyframes hubpulse { 0%,100%{transform:scale(1)} 50%{transform:scale(1.06)} }

  /* publish */
  .demo-publish { display:flex; flex-direction:column; gap:8px; align-items:center; }
  .d-stack { display:flex; gap:6px; flex-wrap:wrap; justify-content:center; }
  .d-card { padding:6px 10px; background:#06090f; color:#94a3b8; font-size:11px; font-family:ui-monospace,monospace; border-radius:6px; animation: cardpop 2.4s ease-in-out infinite; }
  .d-card.c1{animation-delay:0s}
  .d-card.c2{animation-delay:.4s}
  .d-card.c3{animation-delay:.8s}
  .d-card.c4{animation-delay:1.2s}
  @keyframes cardpop { 0%,80%,100%{transform:translateY(0);opacity:.6} 40%{transform:translateY(-6px);opacity:1} }

  /* flow */
  .demo-flow { display:flex; align-items:center; gap:6px; justify-content:center; flex-wrap:wrap; }
  .d-chain { display:flex; align-items:center; gap:6px; }
  .d-link { width:18px; height:2px; background:#161d2a; position:relative; overflow:hidden; }
  .d-link::after { content:''; position:absolute; inset:0; background:#4ade80; animation: linkflow 1.6s linear infinite; transform:translateX(-100%); }
  @keyframes linkflow { 100%{transform:translateX(100%)} }
</style>
