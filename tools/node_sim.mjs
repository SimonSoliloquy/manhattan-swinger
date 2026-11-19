// Run the game's physics and computer player in Node, with no browser and no screen.
// For when no browser tab is available: headless Chrome is banned on this Mac (L-269).
//   PATH=/usr/local/bin:$PATH node tools/node_sim.mjs [path to three.module.js]
// The page's script runs against stand-ins for the DOM, the canvas and the renderer; then
// window.__game.sim and a scripted fall are run and printed. Not part of the deployed game.
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { pathToFileURL, fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const threePath = process.argv[2] || path.join(here, '../node_modules/three/build/three.module.js');
const html = fs.readFileSync(path.join(here, '../index.html'), 'utf8');
let src = html.match(/<script type="module">([\s\S]*?)<\/script>/)[1];
src = src.replace("import * as THREE from 'three';", `import * as THREE from ${JSON.stringify(pathToFileURL(threePath).href)};`);
src = src.replace(/new THREE\.WebGLRenderer\([^)]*\)/, 'globalThis.__fakeRenderer');

// a stand-in that accepts anything: every property is another stand-in, and calling one returns one
const any = () => {
  const f = function () { return any(); };
  return new Proxy(f, {
    get(t, k) {
      if (k === Symbol.toPrimitive) return () => 0;
      if (k === 'then') return undefined;
      if (k in t) return t[k];
      t[k] = any(); return t[k];
    },
    set(t, k, v) { t[k] = v; return true; },
  });
};
const el = () => {
  const e = any(); e.hidden = false; e.style = {}; e.classList = { add() {}, remove() {}, toggle() {} };
  e.textContent = ''; e.innerHTML = ''; e.value = ''; e.addEventListener = () => {};
  e.getContext = () => any(); e.width = 64; e.height = 64; return e;
};
const els = {};
globalThis.document = {
  getElementById: id => (els[id] ||= el()), createElement: () => el(), createElementNS: () => el(), addEventListener: () => {},
  querySelector: () => el(), querySelectorAll: () => [], documentElement: el(), fullscreenElement: null, hidden: false,
};
globalThis.window = globalThis;
globalThis.addEventListener = () => {};
globalThis.matchMedia = () => ({ matches: false });
globalThis.innerWidth = 390; globalThis.innerHeight = 780; globalThis.devicePixelRatio = 1;
globalThis.requestAnimationFrame = () => 0;
globalThis.localStorage = { getItem: () => null, setItem: () => {} };
globalThis.location = { hostname: 'localhost', protocol: 'http:', pathname: '/', hash: '' };
globalThis.fetch = async (url) => {   // the game's own data comes from disk; everything else is offline
  const f = path.join(here, '..', String(url).split('?')[0]);
  if (!String(url).startsWith('data/') || !fs.existsSync(f)) return { ok: false, json: async () => null, text: async () => '' };
  const b = fs.readFileSync(f);
  return { ok: true, json: async () => JSON.parse(b.toString('utf8')), text: async () => b.toString('utf8'), arrayBuffer: async () => b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) };
};
globalThis.screen = { orientation: { angle: 0 } };
globalThis.__fakeRenderer = { setPixelRatio() {}, setSize() {}, render() {}, domElement: el() };
globalThis.Image = class { set src(v) {} };

const tmp = path.join(os.tmpdir(), 'city-swinger-node-sim.mjs');
fs.writeFileSync(tmp, src);
await import(pathToFileURL(tmp).href);
const g = globalThis.__game;

for (let k = 0; k < 200 && !g.CITY.ready; k++) await new Promise(r => setTimeout(r, 50));
console.log('version', g.VERSION, '· buildings', g.CITY.b.length, '· ground at Times Square', g.groundAt(0, 0).toFixed(1), 'm, at the Cloisters', g.groundAt(g.CITY.meta.landmarks.cloisters.x, g.CITY.meta.landmarks.cloisters.z).toFixed(1), 'm');
const emp = g.CITY.meta.landmarks.empire, eb = g.near(emp.x, emp.z, 30).sort((a, b) => b.top - a.top)[0];
console.log('Empire State Building found:', eb ? `${eb.top.toFixed(0)} m to the roof (real: 381 m)` : 'no');
{ // geometry: build every block around Times Square the way the phone would, and check it
  const tA = Date.now(); g.CITY.meshes.clear?.(); g.updateWorld(0, 0); let budget = 0;
  for (let k = 0; k < 200; k++) g.updateWorld(0, 0);
  const meshes = [...g.CITY.meshes.values()], tris = meshes.reduce((n, m) => n + m.geometry.attributes.position.count / 3, 0);
  let out = 0, walls = 0;
  for (const m of meshes) {
    const P = m.geometry.attributes.position, N = m.geometry.attributes.normal, grp = m.geometry.groups;
    for (const gr of grp.slice(0, 3)) for (let v = gr.start; v < gr.start + gr.count; v += 3) {
      // a wall's normal must point away from its building: test against the outline it came from
      const cx = (P.getX(v) + P.getX(v + 1) + P.getX(v + 2)) / 3, cz = (P.getZ(v) + P.getZ(v + 1) + P.getZ(v + 2)) / 3;
      const px = cx + N.getX(v) * .5, pz = cz + N.getZ(v) * .5, qx = cx - N.getX(v) * .5, qz = cz - N.getZ(v) * .5;
      const bs = g.near(cx, cz, 1), y = (P.getY(v) + P.getY(v + 1) + P.getY(v + 2)) / 3;
      const solid = (x, z) => bs.some(b => y >= b.base && y <= b.top && (() => { let c = false; for (let i = 0, j = b.n - 1; i < b.n; j = i++) if ((b.z[i] > z) !== (b.z[j] > z) && x < (b.x[j] - b.x[i]) * (z - b.z[i]) / (b.z[j] - b.z[i]) + b.x[i]) c = !c; return c; })());
      walls++; if (!solid(px, pz) && solid(qx, qz)) out++;
    }
  }
  console.log(`geometry around Times Square: ${meshes.length} blocks, ${Math.round(tris / 1000)}k triangles in view, built in ${Date.now() - tA} ms (${((Date.now() - tA) / meshes.length).toFixed(1)} ms a block)`);
  console.log(`  wall triangles facing out of their building: ${(100 * out / walls).toFixed(1)}% of ${walls} (the rest touch a neighbour)`);
}
let t0 = Date.now();
for (const r of g.sim(40)) console.log(`  roam from ${r.start}: travelled ${r.travelled} m (${r.straight} m from the start), on rope ${r.onRope}, ${r.street}s on the street, ${r.splashes} splashes, ${r.ropes} ropes`);
console.log('  (', Date.now() - t0, 'ms )');
for (let i = 0; i < g.CITY.meta.races.length; i++) { const r = g.raceSim(i); console.log(`  race ${i}: ${r.race}: ${r.finished ? 'finished in ' + r.time + ' s' : 'did not finish, reached checkpoint ' + r.checkpoint + ' in ' + r.time + ' s'}`); }
