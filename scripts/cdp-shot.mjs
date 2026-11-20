// Screenshot sections of a live site through a headless Chrome started with --remote-debugging-port.
// usage: node cdp-shot.mjs <port> <url> <width> <height> <mobile 0|1> <outdir> '<jobs-json>'
// jobs: [{name, text, tag?, up?, pad?, maxH?}]  -> crops the smallest element whose text contains `text`, climbing `up` parents
//       [{name, viewport:true, scrollY?}]        -> plain viewport shot
const [port, url, w, h, mobile, outdir, jobsJson] = process.argv.slice(2);
const jobs = JSON.parse(jobsJson);
const fs = await import('node:fs');
const t = await (await fetch(`http://127.0.0.1:${port}/json/new?about:blank`, { method: 'PUT' })).json();
const ws = new WebSocket(t.webSocketDebuggerUrl);
await new Promise(r => ws.addEventListener('open', r, { once: true }));
let id = 0; const pend = new Map();
ws.addEventListener('message', e => { const m = JSON.parse(e.data); if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); } });
const send = (method, params = {}) => new Promise(r => { const i = ++id; pend.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
const sleep = ms => new Promise(r => setTimeout(r, ms));
const ev = async expr => (await send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true })).result?.result?.value;
await send('Page.enable');
await send('Emulation.setDeviceMetricsOverride', { width: +w, height: +h, deviceScaleFactor: 2, mobile: mobile === '1' });
if (mobile === '1') await send('Emulation.setUserAgentOverride', { userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1' });
await send('Page.navigate', { url });
await sleep(7000);
// scroll through once so lazy sections render
await ev(`(async()=>{for(let y=0;y<document.body.scrollHeight;y+=600){scrollTo(0,y);await new Promise(r=>setTimeout(r,120))}scrollTo(0,0)})()`);
await sleep(1500);
for (const j of jobs) {
  if (j.viewport) {
    await ev(`scrollTo(0,${j.scrollY || 0})`); await sleep(800);
    const r = await send('Page.captureScreenshot', { format: 'png' });
    fs.writeFileSync(`${outdir}/${j.name}.png`, Buffer.from(r.result.data, 'base64')); console.log(j.name, 'viewport'); continue;
  }
  const rect = await ev(`(()=>{const want=${JSON.stringify(j.text)};const tag=${JSON.stringify(j.tag || '*')};
    const els=[...document.querySelectorAll(tag)].filter(e=>e.textContent.trim().toLowerCase().includes(want.toLowerCase()));
    if(!els.length) return null; let el=els.sort((a,b)=>a.textContent.length-b.textContent.length)[0];
    for(let i=0;i<${j.up || 0};i++) el=el.parentElement;
    el.scrollIntoView({block:'center'}); const b=el.getBoundingClientRect();
    return {x:b.left+scrollX,y:b.top+scrollY,w:b.width,h:b.height,tag:el.tagName,txt:el.textContent.slice(0,80)};})()`);
  if (!rect) { console.log(j.name, 'NOT FOUND'); continue; }
  await sleep(1200);
  const p = j.pad ?? 24;
  const clip = { x: Math.max(0, rect.x - p), y: Math.max(0, rect.y - p), width: rect.w + 2 * p, height: Math.min(rect.h + 2 * p, j.maxH || 4000), scale: 1 };
  const r = await send('Page.captureScreenshot', { format: 'png', clip, captureBeyondViewport: true });
  fs.writeFileSync(`${outdir}/${j.name}.png`, Buffer.from(r.result.data, 'base64'));
  console.log(j.name, JSON.stringify(rect));
}
ws.close(); process.exit(0);
