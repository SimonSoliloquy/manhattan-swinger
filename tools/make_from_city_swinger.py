"""One-off: make Manhattan Swinger's index.html from City Swinger's (v2026-11-19j).
Sections of City Swinger are cut by their markers and replaced; every step must match.
  python3 tools/make_from_city_swinger.py <city swinger index.html> <out index.html>"""
import re, sys
s = open(sys.argv[1]).read()


def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n: sys.exit('%d matches (want %d) for: %s' % (c, n, a[:100]))
    s = s.replace(a, b)


def span(start, end, new):
    """Replace from the line holding `start` up to (not including) the line holding `end`."""
    global s
    i = s.find(start)
    if i < 0: sys.exit('no start: ' + start[:80])
    i = s.rfind('\n', 0, i) + 1
    j = s.find(end, i + len(start))
    if j < 0: sys.exit('no end: ' + end[:80])
    j = s.rfind('\n', 0, j) + 1
    s = s[:i] + new + s[j:]


def func(name, new):
    """Replace a top-level `function name(...) {...}` (it ends at the first line that is exactly `}`)."""
    global s
    m = re.search(r'(?m)^(async )?function %s\(' % re.escape(name), s)
    if not m: sys.exit('no function ' + name)
    j = s.find('\n}\n', m.start())
    s = s[:m.start()] + new.rstrip('\n') + '\n' + s[j + 3:]


# =============================================================== page
rep('<meta name="description" content="Swing across a city of towers above the clouds at night. Don\'t fall into the clouds.">',
    '<meta name="description" content="Swing anywhere in Manhattan: every building on the island, at its real height, with a sunset over the Hudson. Free roam and landmark races.">')
rep('<title>City Swinger</title>', '<title>Manhattan Swinger</title>')
rep('.short h1 { font-size: 46px; }',
    '#tag2 { font-size: 14px; opacity: .8; margin-top: 2px; }\n'
    '#arrow { width: 34px; height: 34px; margin: 2px auto 0; display: block; }\n'
    '.races { display: grid; gap: 6px; margin: 10px 0 0; text-align: left; }\n'
    '.races button { font: inherit; font-size: 14px; text-align: left; padding: 7px 10px; background: transparent; color: var(--paper); border: 2px solid rgba(242,239,230,.45); cursor: pointer; display: flex; justify-content: space-between; gap: 8px; }\n'
    '.races button b { font-family: "Bebas Neue", Impact, sans-serif; font-weight: 400; font-size: 18px; letter-spacing: 1px; }\n'
    '.races button span { opacity: .7; white-space: nowrap; }\n'
    '#mapScreen { padding: 0; flex-direction: column; background: #050813; }\n'
    '#mapScreen p { margin: 8px 12px; text-align: center; font-size: 15px; }\n'
    '#map { flex: 1; width: 100%; min-height: 0; touch-action: none; }\n'
    '.short h1 { font-size: 46px; }')
span('  <div id="hud" hidden>', '  <div id="tools">',
     '  <div id="hud" hidden><div id="dist" class="big">0:00</div><div id="tag2"></div><svg id="arrow" viewBox="0 0 34 34" hidden><path d="M17 3l11 22-11-6-11 6z" fill="#ffd27a" stroke="#070b1c" stroke-width="2" stroke-linejoin="round"/></svg></div>\n')
span('  <div class="screen" id="menu">', '  <div class="screen" id="paused"',
     '  <div class="screen" id="menu"><div class="card">\n'
     '    <h1 class="big">Manhattan Swinger</h1>\n'
     '    <p class="tag">Every building on the island, at its real height. Sunset over the Hudson.</p>\n'
     '    <p class="line" id="loading">Loading Manhattan</p>\n'
     '    <div id="menuButtons" hidden><button class="btn" id="roam">Free roam</button><button class="btn alt" id="showRaces">Races</button></div>\n'
     '    <div class="races" id="raceList" hidden></div>\n'
     '    <p class="how" id="howTouch">Hold to swing, let go to fly, tap to jump. The rope goes to the side you tilt the phone. Land anywhere and keep running.</p>\n'
     '    <p class="how" id="howKeys">Hold the mouse button to swing, let go to fly, Space jumps. The rope goes to the side you steer with A and D. Land anywhere and keep running.</p>\n'
     '    <p class="by">by <a href="https://simonsoliloquy.com" target="_blank" rel="noopener">simonsoliloquy.com</a> · building data: NYC Open Data</p>\n'
     '  </div></div>\n\n'
     '  <div class="screen" id="mapScreen" hidden>\n'
     '    <p class="big" style="font-size:24px">Tap where to start</p>\n'
     '    <canvas id="map"></canvas>\n'
     '    <p><button class="btn alt small" id="mapBack">Back</button></p>\n'
     '  </div>\n\n')
rep('<h2 class="big" id="enddist">0 m</h2>', '<h2 class="big" id="enddist">0:00</h2><p class="line" id="endrace"></p>')
rep('<button class="btn alt" id="quit">Menu</button>', '<button class="btn alt" id="quit">Menu</button><button class="btn alt" id="restartRace" hidden>Restart race</button>')

# =============================================================== tuning, constants
rep("const VERSION = 'v2026-11-19j';", "const VERSION = 'v2026-11-19a';")
span('const STEP = 1 / 180, R_H = 0.45;', 'let seed = 1;',
     "const STEP = 1 / 180, R_H = 0.45;\n"
     "// The city is real Manhattan (NYC Open Data, built by tools/build_manhattan.py): metres, x east, y up,\n"
     "// z SOUTH, origin at Times Square. North is -z. The sun sets in the west (-x), over the Hudson.\n"
     "const VIEW = 760, DROP = 980;      // build the blocks within VIEW of the camera, drop them past DROP\n")

# =============================================================== the sky, the sun in the west, water
span('function cloudTex(size, n, rMin, rMax) {', '// THE CITY:', r'''// sky, stars, moon and the setting sun. The sky is drawn with its sunset toward local +z, and then
// turned to face west (-x), over the Hudson (Simon, 2026-11-19: "sunset over the Hudson").
const WEST = -Math.PI / 2;
const sky = (() => {
  const g = new THREE.SphereGeometry(1400, 48, 24), pos = g.attributes.position, col = [];
  const top = new THREE.Color(0x02040c), mid = new THREE.Color(0x0a1436), low = new THREE.Color(0x2a3a78);
  const gold = new THREE.Color(0xffa24a), rose = new THREE.Color(0xff6470), plum = new THREE.Color(0x7a3f86), night = new THREE.Color(), sun = new THREE.Color();
  const smooth = (a, b, x) => { const t = clamp((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); };
  for (let i = 0; i < pos.count; i++) {
    const y = pos.getY(i) / 1400, z = pos.getZ(i) / 1400;
    if (y < 0.02) night.copy(low); else if (y < 0.3) night.copy(low).lerp(mid, (y - 0.02) / 0.28); else night.copy(mid).lerp(top, Math.min(1, (y - 0.3) / 0.5));
    const yy = Math.max(0, y);
    if (yy < 0.07) sun.copy(gold).lerp(rose, yy / 0.07); else if (yy < 0.2) sun.copy(rose).lerp(plum, (yy - 0.07) / 0.13); else sun.copy(plum).lerp(mid, Math.min(1, (yy - 0.2) / 0.3));
    const w = Math.pow(smooth(-0.25, 0.95, z), 1.4) * (1 - smooth(0.05, 0.6, y));
    night.lerp(sun, w); col.push(night.r, night.g, night.b);
  }
  g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  const m = new THREE.Mesh(g, new THREE.MeshBasicMaterial({ vertexColors: true, side: THREE.BackSide, fog: false, depthWrite: false }));
  m.rotation.y = WEST; m.renderOrder = -3; scene.add(m); return m;
})();
const stars = (() => {
  const p = [];
  for (let i = 0; i < 900; i++) {
    const a = Math.random() * Math.PI * 2, y = 0.12 + Math.random() * 0.88, r = Math.sqrt(1 - y * y), z = Math.sin(a) * r;
    if (z > 0.15 && y < 0.55) continue;   // no stars in the sunset
    p.push(Math.cos(a) * r * 1350, y * 1350, z * 1350);
  }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(p, 3));
  const s = new THREE.Points(g, new THREE.PointsMaterial({ color: 0xdfe6ff, size: 1.6, sizeAttenuation: false, fog: false, depthWrite: false, transparent: true, opacity: .85 }));
  s.rotation.y = WEST; s.renderOrder = -2; scene.add(s); return s;
})();
const moon = (() => {
  const [c, g] = canvas(128, 128);
  const gr = g.createRadialGradient(64, 64, 0, 64, 64, 64); gr.addColorStop(0, 'rgba(235,240,255,.55)'); gr.addColorStop(1, 'rgba(235,240,255,0)');
  g.fillStyle = gr; g.fillRect(0, 0, 128, 128);
  g.fillStyle = '#eef2ff'; g.beginPath(); g.arc(64, 64, 20, 0, Math.PI * 2); g.fill();
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex(c, false), fog: false, depthWrite: false, transparent: true }));
  s.scale.set(220, 220, 1); s.renderOrder = -2; scene.add(s); return s;
})();
const sunDisc = (() => {   // the setting sun, low over New Jersey
  const [c, g] = canvas(256, 256);
  let gr = g.createRadialGradient(128, 128, 0, 128, 128, 128);
  gr.addColorStop(0, 'rgba(255,214,150,.95)'); gr.addColorStop(.2, 'rgba(255,170,90,.55)'); gr.addColorStop(.5, 'rgba(255,110,80,.18)'); gr.addColorStop(1, 'rgba(255,90,90,0)');
  g.fillStyle = gr; g.fillRect(0, 0, 256, 256);
  gr = g.createRadialGradient(128, 128, 0, 128, 128, 30); gr.addColorStop(0, '#fff6dc'); gr.addColorStop(.75, '#ffd27a'); gr.addColorStop(1, '#ff9a4a');
  g.fillStyle = gr; g.beginPath(); g.arc(128, 128, 30, 0, Math.PI * 2); g.fill();
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex(c, false), fog: false, depthWrite: false, transparent: true }));
  s.scale.set(380, 380, 1); s.renderOrder = -2; scene.add(s); return s;
})();
// the rivers and the harbour: one wide sheet of water at sea level, catching the sunset
const water = (() => {
  const m = new THREE.Mesh(new THREE.PlaneGeometry(9000, 9000), new THREE.MeshPhongMaterial({ color: 0x1b2148, specular: 0xff9a6a, shininess: 40 }));
  m.rotation.x = -Math.PI / 2; m.position.y = -0.4; scene.add(m); return m;
})();
// a checkpoint: a tall beam of light, seen from across the island
const beam = (() => {
  const g = new THREE.CylinderGeometry(6, 6, 900, 20, 1, true).translate(0, 450, 0);
  const m = new THREE.Mesh(g, new THREE.MeshBasicMaterial({ color: 0xffc35a, transparent: true, opacity: .32, blending: THREE.AdditiveBlending, depthWrite: false, fog: false, side: THREE.DoubleSide }));
  m.visible = false; scene.add(m); return m;
})();

// ============================================================================================
''')

# =============================================================== the city
span('// THE CITY:', '// THE HERO\n', r'''// MANHATTAN: 45,000 buildings from NYC Open Data, each its real outline extruded to its real height.
// Everything is loaded at the start (about 2 MB); the meshes are built block by block (200 m tiles)
// around the camera and dropped behind it. Collisions, ropes and the camera use the outlines.
// ============================================================================================
const world = new THREE.Group(); scene.add(world);
const CITY = { ready: false, b: [], grid: new Map(), cell: 32, tiles: new Map(), meshes: new Map(), meta: null, gh: null, gk: null };
const blinkers = [];
async function loadCity() {
  const [meta, buf] = await Promise.all([fetch('data/manhattan.json').then(r => r.json()), fetch('data/manhattan.bin').then(r => r.arrayBuffer())]);
  const dv = new DataView(buf), T0 = meta.tile;
  for (const [ti, tj, off, count] of meta.tiles) {
    const ids = []; let o = off;
    for (let k = 0; k < count; k++) {
      const n = dv.getUint8(o), base = dv.getInt16(o + 1, true) / 10, h = dv.getUint16(o + 3, true) / 10; o += 5;
      const x = new Float32Array(n), z = new Float32Array(n);
      let x0 = 1e9, x1 = -1e9, z0 = 1e9, z1 = -1e9;
      for (let q = 0; q < n; q++) {
        x[q] = ti * T0 + dv.getInt16(o, true) / 10; z[q] = tj * T0 + dv.getInt16(o + 2, true) / 10; o += 4;
        if (x[q] < x0) x0 = x[q]; if (x[q] > x1) x1 = x[q]; if (z[q] < z0) z0 = z[q]; if (z[q] > z1) z1 = z[q];
      }
      const id = CITY.b.length;
      CITY.b.push({ x, z, n, base, top: base + h, x0, x1, z0, z1, v: (id * 2654435761 >>> 0) % 3, ou: ((id * 40503 >>> 0) % 8) / 8 });
      ids.push(id);
      for (let gx = Math.floor(x0 / CITY.cell); gx <= Math.floor(x1 / CITY.cell); gx++)
        for (let gz = Math.floor(z0 / CITY.cell); gz <= Math.floor(z1 / CITY.cell); gz++) {
          const key = gx * 100000 + gz; let a = CITY.grid.get(key); if (!a) CITY.grid.set(key, a = []); a.push(id);
        }
    }
    CITY.tiles.set(ti * 1000 + tj, { ti, tj, ids });
  }
  const G = meta.grid;
  CITY.gh = new Uint8Array(buf, G.height, G.nx * G.nz); CITY.gk = new Uint8Array(buf, G.kind, G.nx * G.nz);
  CITY.meta = meta; CITY.ready = true;
  buildGround(); buildOtherBoroughs();
}
// the ground: streets and parks on a 40 m grid, at the real height of the land (Washington Heights is 80 m up)
function gridAt(x, z) { const G = CITY.meta.grid; return [(x - G.x0) / G.cell - .5, (z - G.z0) / G.cell - .5]; }
function kindAt(x, z) {   // 0 water, 1 street, 2 park
  if (!CITY.ready) return 1;
  const G = CITY.meta.grid, i = Math.floor((x - G.x0) / G.cell), j = Math.floor((z - G.z0) / G.cell);
  return i < 0 || j < 0 || i >= G.nx || j >= G.nz ? 0 : CITY.gk[j * G.nx + i];
}
function groundAt(x, z) {
  if (!CITY.ready) return 0;
  const G = CITY.meta.grid, [fx, fz] = gridAt(x, z);
  const i = clamp(Math.floor(fx), 0, G.nx - 2), j = clamp(Math.floor(fz), 0, G.nz - 2), u = clamp(fx - i, 0, 1), w = clamp(fz - j, 0, 1);
  const h = (a, b) => CITY.gh[b * G.nx + a] / 2;
  return (h(i, j) * (1 - u) + h(i + 1, j) * u) * (1 - w) + (h(i, j + 1) * (1 - u) + h(i + 1, j + 1) * u) * w;
}
function buildGround() {
  const G = CITY.meta.grid, pos = [], col = [], street = new THREE.Color(0x2a2c3a), park = new THREE.Color(0x2c5236), c = new THREE.Color();
  const corner = (i, j) => groundAt(G.x0 + i * G.cell, G.z0 + j * G.cell);
  for (let j = 0; j < G.nz; j++) for (let i = 0; i < G.nx; i++) {
    const k = CITY.gk[j * G.nx + i]; if (!k) continue;
    c.copy(k === 2 ? park : street).offsetHSL(0, 0, ((i * 7 + j * 13) % 5) * .006);
    const xa = G.x0 + i * G.cell, xb = xa + G.cell, za = G.z0 + j * G.cell, zb = za + G.cell;
    const ya = corner(i, j), yb = corner(i + 1, j), yc = corner(i, j + 1), yd = corner(i + 1, j + 1);
    pos.push(xa, ya, za, xa, yc, zb, xb, yb, za, xb, yb, za, xa, yc, zb, xb, yd, zb);
    for (let q = 0; q < 6; q++) col.push(c.r, c.g, c.b);
  }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3)); g.computeVertexNormals();
  scene.add(new THREE.Mesh(g, new THREE.MeshLambertMaterial({ vertexColors: true })));
}
function buildOtherBoroughs() {   // the Bronx, Brooklyn and Queens across the rivers: low and dark, scenery only
  const mat = new THREE.MeshLambertMaterial({ color: 0x1c1f30 });
  for (const flat of CITY.meta.others) {
    const pts = []; for (let k = 0; k < flat.length; k += 2) pts.push(new THREE.Vector2(flat[k], flat[k + 1]));
    const tris = THREE.ShapeUtils.triangulateShape(pts, []), pos = [];
    for (const t of tris) for (const q of t) pos.push(pts[q].x, 1.2, pts[q].y);
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.computeVertexNormals();
    const m = new THREE.Mesh(g, mat); m.material.side = THREE.DoubleSide; scene.add(m);
  }
}
// one block's mesh: walls with the window texture (three looks, by building), roofs flat
function buildTile(tile) {
  const groups = [[], [], [], []], uvs = [[], [], [], []], nrm = [[], [], [], []];
  for (const id of tile.ids) {
    const b = CITY.b[id], W = groups[b.v], U = uvs[b.v], N = nrm[b.v], h = b.top - b.base;
    let run = b.ou * TILE;
    for (let q = 0; q < b.n; q++) {
      const ax = b.x[q], az = b.z[q], bx = b.x[(q + 1) % b.n], bz = b.z[(q + 1) % b.n], len = Math.hypot(bx - ax, bz - az);
      if (len < .05) continue;
      const nx = (bz - az) / len, nz = -(bx - ax) / len, u0 = run / TILE, u1 = (run + len) / TILE, v1 = h / TILE; run += len;
      W.push(ax, b.base, az, bx, b.top, bz, bx, b.base, bz, ax, b.base, az, ax, b.top, az, bx, b.top, bz);
      U.push(u0, 0, u1, v1, u1, 0, u0, 0, u0, v1, u1, v1);
      for (let k = 0; k < 6; k++) N.push(nx, 0, nz);
    }
    const pts = []; for (let q = 0; q < b.n; q++) pts.push(new THREE.Vector2(b.x[q], b.z[q]));
    for (const t of THREE.ShapeUtils.triangulateShape(pts, [])) for (const q of t) { groups[3].push(b.x[q], b.top, b.z[q]); uvs[3].push(0, 0); nrm[3].push(0, 1, 0); }
  }
  const g = new THREE.BufferGeometry(), P = [], UV = [], NN = [];
  let start = 0;
  groups.forEach((arr, k) => { P.push(...arr); UV.push(...uvs[k]); NN.push(...nrm[k]); g.addGroup(start, arr.length / 3, k); start += arr.length / 3; });
  g.setAttribute('position', new THREE.Float32BufferAttribute(P, 3)); g.setAttribute('uv', new THREE.Float32BufferAttribute(UV, 2)); g.setAttribute('normal', new THREE.Float32BufferAttribute(NN, 3));
  const m = new THREE.Mesh(g, CITY_MATS); world.add(m); return m;
}
const CITY_MATS = [...wallMats, roofMat];
for (const m of CITY_MATS) m.side = THREE.DoubleSide;
function updateWorld(x, z) {   // build the blocks near the camera (a few a frame), drop the far ones
  if (!CITY.ready) return;
  const T0 = CITY.meta.tile, ci = Math.floor(x / T0), cj = Math.floor(z / T0), r = Math.ceil(VIEW / T0);
  const want = [];
  for (let i = ci - r; i <= ci + r; i++) for (let j = cj - r; j <= cj + r; j++) {
    const key = i * 1000 + j; if (CITY.meshes.has(key) || !CITY.tiles.has(key)) continue;
    const d = Math.hypot((i + .5) * T0 - x, (j + .5) * T0 - z); if (d < VIEW) want.push([d, key]);
  }
  want.sort((a, b) => a[0] - b[0]);
  for (const [, key] of want.slice(0, buildBudget)) CITY.meshes.set(key, buildTile(CITY.tiles.get(key)));
  for (const [key, m] of CITY.meshes) {
    const t = CITY.tiles.get(key);
    if (Math.hypot((t.ti + .5) * T0 - x, (t.tj + .5) * T0 - z) > DROP) { world.remove(m); m.geometry.dispose(); CITY.meshes.delete(key); }
  }
}
let buildBudget = 3;
// the buildings whose outline is near a point (within `r` metres)
function near(x, z, r, out = []) {
  out.length = 0; const c = CITY.cell, seen = near.seen || (near.seen = new Set()); seen.clear();
  for (let gx = Math.floor((x - r) / c); gx <= Math.floor((x + r) / c); gx++)
    for (let gz = Math.floor((z - r) / c); gz <= Math.floor((z + r) / c); gz++) {
      const a = CITY.grid.get(gx * 100000 + gz); if (!a) continue;
      for (const id of a) if (!seen.has(id)) { seen.add(id); const b = CITY.b[id]; if (b.x0 - r <= x && x <= b.x1 + r && b.z0 - r <= z && z <= b.z1 + r) out.push(b); }
    }
  return out;
}
function inside(b, x, z) {
  let c = false;
  for (let i = 0, j = b.n - 1; i < b.n; j = i++) if ((b.z[i] > z) !== (b.z[j] > z) && x < (b.x[j] - b.x[i]) * (z - b.z[i]) / (b.z[j] - b.z[i]) + b.x[i]) c = !c;
  return c;
}
const EDGE = { x: 0, z: 0, d: 0, nx: 0, nz: 0 };
function nearestEdge(b, x, z) {   // the closest point on the outline, its distance, and the outward normal there
  let best = 1e18;
  for (let i = 0; i < b.n; i++) {
    const ax = b.x[i], az = b.z[i], bx = b.x[(i + 1) % b.n], bz = b.z[(i + 1) % b.n], dx = bx - ax, dz = bz - az, L2 = dx * dx + dz * dz || 1e-9;
    const t = clamp(((x - ax) * dx + (z - az) * dz) / L2, 0, 1), px = ax + dx * t, pz = az + dz * t, d2 = (x - px) ** 2 + (z - pz) ** 2;
    if (d2 < best) { best = d2; const L = Math.sqrt(L2); EDGE.x = px; EDGE.z = pz; EDGE.nx = dz / L; EDGE.nz = -dx / L; }
  }
  EDGE.d = Math.sqrt(best); return EDGE;
}
const solidAt = (x, y, z) => { for (const b of near(x, z, 0, rayTmp)) if (y >= b.base && y <= b.top && inside(b, x, z)) return true; return false; };
const rayTmp = [];
function rayCity(o, d, maxT) {   // how far a ray goes before it enters a building, or null
  const stepL = .75;
  for (let t = .3; t <= maxT; t += stepL) {
    if (solidAt(o.x + d.x * t, o.y + d.y * t, o.z + d.z * t)) {
      let lo = t - stepL, hi = t;
      for (let k = 0; k < 5; k++) { const m = (lo + hi) / 2; if (solidAt(o.x + d.x * m, o.y + d.y * m, o.z + d.z * m)) hi = m; else lo = m; }
      return lo;
    }
  }
  return null;
}
function tallestNear(x, z, r) { let best = null; for (const b of near(x, z, r)) if (!best || b.top > best.top) best = b; return best; }

// ============================================================================================
''')

# =============================================================== the hero: state, start, ropes
rep("const S = { phase: 'menu', dist: 0,", "const S = { phase: 'menu', mode: 'roam', race: null, cp: 0, dist: 0,")
rep("  thumbReel: 0, thumbSlide: 0 };", "  thumbReel: 0, thumbSlide: 0, lastSafe: null, splashT: 0 };")
rep("function runSpeed() { return T.roofRun + Math.min(T.runGain, S.dist / 500); }", "function runSpeed() { return T.roofRun; }")
func('startHero', r'''function startHero(x = 0, z = 0, face = null) {   // on the roof of the tallest building near the point, or on the street
  H.v.set(0, 0, 0); H.state = 'air'; H.wallCool = 0; H.rollT = 0;
  S.fallT = 0; S.splashT = 0; hero.visible = true;
  for (const h of hooks) { h.state = 'off'; h.reel = 0; }
  const b = tallestNear(x, z, 70);
  if (b && b.top > groundAt(x, z) + 15) { let cx = 0, cz = 0; for (let q = 0; q < b.n; q++) { cx += b.x[q]; cz += b.z[q]; } H.p.set(cx / b.n, b.top + 2, cz / b.n); }
  else H.p.set(x, groundAt(x, z) + 2, z);
  if (face) camDir.set(face.x - H.p.x, 0, face.z - H.p.z).normalize(); else camDir.set(0, 0, -1);   // facing the next landmark, or north
  H.heading.copy(camDir); H.v.copy(camDir).multiplyScalar(6); H.v.y = 6;
  camPos.copy(H.p).addScaledVector(camDir, -9).add(tA.set(0, 3, 0));
  S.dist = 0; S.t = 0; S.hooks = 0; S.crashed = false; S.lastSafe = H.p.clone();
}''')
func('autoAnchor', r'''const aR = new V3(), aP = new V3(), aQ = new V3(), aD = new V3(), nearTmp = [];
function autoAnchor(side) {   // up and ahead on a real building, on the side you lean to
  const p = H.p, f = camDir, r = rightOf(camDir, aR);
  const lead = clamp(H.v.x * f.x + H.v.z * f.z, 0, 50) * .45;
  let best = null, bs = -1e9;
  for (const ahead of [14, 24, 36]) {
    aP.copy(p).addScaledVector(f, ahead + lead);
    for (const b of near(aP.x, aP.z, 34, nearTmp)) {
      if (b.top < p.y + 7) continue;
      const e = nearestEdge(b, aP.x, aP.z);
      aQ.set(e.x + e.nx * .3, Math.min(b.top - .6, Math.max(b.base + .5, p.y + T.anchorRise)), e.z + e.nz * .3);
      const d = aQ.distanceTo(p); if (d > T.hookRange * .75 || d < 9) continue;
      const lat = (aQ.x - p.x) * r.x + (aQ.z - p.z) * r.z, fwd = (aQ.x - p.x) * f.x + (aQ.z - p.z) * f.z;
      if (fwd < 4) continue;
      if (side && lat * side < 1) continue;
      if (Math.abs(lat) > 45 || Math.abs(lat) > fwd * 2.2) continue;
      const s = (aQ.y - p.y) - Math.abs(d - 36) * .6 + fwd * .3 - Math.abs(lat) * (side ? .25 : .4);
      if (s > bs) { bs = s; best = (best || new V3()).copy(aQ); }
    }
  }
  if (!best) return null;
  handPos(0, aP); aD.subVectors(best, aP); const d = aD.length(); aD.divideScalar(d);   // the rope stops at whatever is in the way
  const t = rayCity(aP, aD, d - 1);
  if (t != null) { best.copy(aP).addScaledVector(aD, t); if (best.y < p.y + 4) return null; }
  return best;
}''')
rep("  if (H.state === 'roof') { H.v.y = T.jump;", "  if (H.state === 'roof' || H.state === 'street') { H.v.y = T.jump;")
rep("  else if (H.state === 'roof') { H.v.y = Math.max(H.v.y, 7); H.state = 'air'; SFX.step(); }", "  else if (H.state === 'roof' || H.state === 'street') { H.v.y = Math.max(H.v.y, 7); H.state = 'air'; SFX.step(); }")
rep("  if (H.state !== 'roof') v.addScaledVector(rightOf(camDir, tA), H.steer", "  if (H.state !== 'roof' && H.state !== 'street') v.addScaledVector(rightOf(camDir, tA), H.steer")

# =============================================================== collisions with real buildings, the streets and the rivers
func('collide', r'''const colTmp = [];
function collide(dt) {
  const p = H.p, v = H.v, was = H.state, hs0 = Math.hypot(v.x, v.z);
  let roof = null, wall = null, wallTop = 0, step = null;
  for (const b of near(p.x, p.z, R_H + .1, colTmp)) {
    if (p.y > b.top + R_H + .06 || p.y < b.base - R_H) continue;
    const inPoly = inside(b, p.x, p.z), e = nearestEdge(b, p.x, p.z);
    if (inPoly && p.y >= b.top - .9 && v.y <= .5) { p.y = b.top + R_H; if (v.y < 0) v.y = 0; roof = b; continue; }   // on its roof
    if (!inPoly && e.d >= R_H + .06) continue;
    if (!inPoly && p.y > b.top) {   // the edge of a roof: stand on it if mostly above it
      if (p.y - b.top > R_H * .5) { p.y = Math.max(p.y, b.top + R_H); if (v.y < 0) v.y = 0; roof = b; continue; }
    }
    const rise = b.top - (p.y - R_H);   // a wall: how far its top is above your feet
    if (rise > 0 && rise < 2.7 && hs0 > 3 && (was === 'roof' || was === 'street' || was === 'air') && v.y < 9.5) { step = { b, nx: e.nx, nz: e.nz }; continue; }
    if (inPoly || e.d < R_H) { p.x = e.x + e.nx * R_H; p.z = e.z + e.nz * R_H; }
    const vn = v.x * e.nx + v.z * e.nz; if (vn < 0) { v.x -= vn * e.nx; v.z -= vn * e.nz; }
    if (!wall) { wall = b; wallTop = b.top; H.wallN.set(e.nx, 0, e.nz); }
  }
  // the ground: streets and parks you land on and keep running; the rivers and the harbour
  let street = false;
  const k = kindAt(p.x, p.z);
  if (k) { const g = groundAt(p.x, p.z); if (p.y - R_H <= g) { p.y = g + R_H; if (v.y < 0) v.y = 0; street = !roof; } }
  else if (p.y < .4) { onFall(); return; }
  if (step) {   // a roof edge or a higher roof within reach: straight up onto it, still running
    p.y = step.b.top + R_H + .02; p.x -= step.nx * .3; p.z -= step.nz * .3;
    tA.set(v.x - step.nx * 3, 0, v.z - step.nz * 3).normalize();
    const hs = Math.max(hs0, runSpeed() * .7);
    v.set(tA.x * hs, 0, tA.z * hs); H.heading.copy(tA); H.state = 'air';
  } else if (roof || street) {
    if (was !== 'roof' && was !== 'street') land();
    H.state = roof ? 'roof' : 'street'; H.roof = roof || { top: p.y - R_H };
    H.heading.applyAxisAngle(Y, -H.steer * T.steerRoof * dt);
    if (wall) {   // a taller wall beside you: run along it, not into it
      const into = H.heading.dot(H.wallN);
      if (into < 0) { H.heading.addScaledVector(H.wallN, -into); if (H.heading.lengthSq() < .01) rightOf(H.wallN, H.heading); H.heading.normalize(); }
    }
    const hs = Math.max(Math.hypot(v.x, v.z) * (1 - .6 * dt), runSpeed());
    v.x = H.heading.x * hs; v.z = H.heading.z * hs; if (v.y < 0) v.y = 0;
    S.lastSafe.copy(p);
  } else if (wall && H.wallCool <= 0) {
    tA.copy(v).addScaledVector(H.wallN, -v.dot(H.wallN)); tA.y = Math.max(0, tA.y);   // falling down a wall is not running on it
    if (was === 'wall' || tA.length() >= T.wallMinSpeed) {
      if (was !== 'wall') { H.wallT = 0; SFX.step(); }
      H.state = 'wall'; H.wallB = { y1: wallTop }; H.wallT += dt;
      v.addScaledVector(H.wallN, -2 * dt);   // stay against it
      if (H.wallT > T.wallTime) { H.state = 'air'; H.wallCool = .5; v.addScaledVector(H.wallN, 3); }
    } else if (was === 'wall') H.state = 'air';
  } else {
    if (was === 'wall' && H.wallB && p.y > H.wallB.y1 - 1.2) { v.y = Math.max(v.y, 7); v.addScaledVector(H.wallN, -3); }   // over the top: up onto the roof
    H.state = 'air';
  }
  S.lastVy = v.y;
}''')
func('towardSunset', "// (free roam: no direction is forced; the sunset is west, over the Hudson)")
func('land', r'''function land() {   // you land running; a drop rolls by itself and costs no speed
  tA.set(H.v.x, 0, H.v.z); H.heading.copy(tA.lengthSq() > 1 ? tA.normalize() : camDir);
  if (S.lastVy < -9) { H.rollT = .55; SFX.roll(); } else if (S.lastVy < -4) SFX.step();
}''')
rep('''// Falling off the map (Simon, 2026-11-19: "when you fall, you should just go fall through the clouds off
// the map. you shouldn't hit the bottom"): nothing stops you. The ropes let go, the camera stays above
// the cloud sea and watches you drop into it and out of sight, and only then does the run end.
''', '''// Into the river: a splash, and you are back on the last roof or street you stood on (Simon,
// 2026-11-19: land on the streets and keep going; only the rivers set you back). A race's clock runs on.
''')
func('onFall', r'''function onFall() {
  if (S.phase !== 'play') { S.crashed = true; return; }
  S.phase = 'splash'; S.splashT = 0; SFX.crash();
  for (const h of hooks) h.state = 'off';
  for (const id of [...ptrs.keys()]) lift(id);
}''')
func('fallStep', r'''function splashStep(dt) {   // sink a little, then come back to dry land
  S.splashT += dt; H.v.multiplyScalar(1 - 3 * dt); H.v.y = Math.max(H.v.y - 4 * dt, -3); H.p.addScaledVector(H.v, dt);
  if (S.splashT > 1.1) {
    H.p.copy(S.lastSafe); H.p.y += 1; H.v.set(0, 0, 0); H.state = 'air';
    camPos.copy(H.p).addScaledVector(camDir, -9).add(tA.set(0, 3, 0));
    S.phase = 'play';
  }
}''')

# =============================================================== the computer player: heads for a landmark
span('const B = { t: 0, next: 0, held: 0 };', '// ============================================================================================\n// THE HERO, DRAWN', r'''const B = { t: 0, next: 0, held: 0, goal: null };
function botThink(dt) {
  const p = H.p, v = H.v; B.t += dt;
  const g = B.goal || (B.goal = randomLandmark());
  tB.set(g.x - p.x, 0, g.z - p.z); const dist = tB.length(); tB.divideScalar(dist || 1);
  if (dist < 40 && S.phase === 'menu') B.goal = randomLandmark();
  const r = rightOf(camDir, tA), lat = tB.x * r.x + tB.z * r.z, fwd = tB.x * camDir.x + tB.z * camDir.z;
  H.steer = clamp(fwd < 0 ? Math.sign(lat || 1) : lat * 2.5, -1, 1);   // lean toward the goal
  const on = hooks.find(h => h.state === 'on' || h.state === 'fly');
  if (on) {
    if (on.state !== 'on') return;
    B.held += dt;
    const past = (p.x - on.a.x) * camDir.x + (p.z - on.a.z) * camDir.z;
    if (B.held > 3.5 || (past > 2 && v.y > 0 && (on.a.y - p.y) < on.L * .55)) { release(on.i); B.t = 0; B.held = 0; return; }
    on.reel = p.y < groundAt(p.x, p.z) + 15 ? 1 : 0;
  } else if ((v.y < 1 || H.state !== 'air') && B.t > .15) {
    const side = Math.abs(lat) > .25 ? Math.sign(lat) : (B.next ? 1 : -1);
    if (swing(side) >= 0) { B.next ^= 1; B.t = 0; } else if (H.state !== 'air' && B.t > .6) { jump(); B.t = 0; }
  }
}
function randomLandmark() { const L = Object.values(CITY.meta?.landmarks || { t: { x: 0, z: -500 } }); return L[(Math.random() * L.length) | 0]; }

''')

# =============================================================== camera
func('updateCamera', r'''function updateCamera(dt, snap) {
  const p = H.p, v = H.v;
  tA.set(v.x, 0, v.z);
  if (tA.lengthSq() > 9) camDir.lerp(tA.normalize(), snap ? 1 : 1 - Math.exp(-2.6 * dt)).normalize();
  const speed = v.length(), up = tall() ? T.camUpTall : T.camUp;
  tB.copy(p).addScaledVector(camDir, -(tall() ? T.camBackTall : T.camBack)).add(tC.set(0, up, 0));
  tD.subVectors(tB, p); const want = tD.length(); tD.divideScalar(want);
  const hit = CITY.ready ? rayCity(p, tD, want) : null;   // keep the camera out of buildings
  if (hit != null) tB.copy(p).addScaledVector(tD, Math.max(.8, hit - .4));
  tB.y = Math.max(tB.y, (kindAt(tB.x, tB.z) ? groundAt(tB.x, tB.z) : 0) + 1.2);
  if (S.phase === 'splash') { /* the camera holds while you sink */ }
  else if (snap) camPos.copy(tB); else camPos.lerp(tB, 1 - Math.exp(-9 * dt));
  camera.position.copy(camPos);
  camera.lookAt(tA.copy(p).addScaledVector(camDir, 5).add(tC.set(0, .9, 0)));
  setFov(Math.min(T.fovMax, Math.max(0, speed - 12) * T.fovSpeed));
  sky.position.copy(camPos); stars.position.copy(camPos);
  moon.position.copy(camPos).add(tA.set(820, 520, 380));     // the moon rises in the east, behind you if you face the sunset
  sunDisc.position.copy(camPos).add(tA.set(-1250, 70, 0));   // the sun sets in the west
  water.position.set(camPos.x, -0.4, camPos.z);
}''')

# =============================================================== flow: free roam, races, the map
span('const HINTS = isTouch', '// ---------- high scores', r'''const HINTS = isTouch ? ['Hold to swing. Tilt to pick the side', 'Let go to fly. Tap to jump', 'Slide your thumb up to reel in'] : ['Hold the mouse button to swing', 'Let go to fly. Space jumps', 'A and D pick the side, the wheel reels in'];
function hintNext() { if (S.hint >= HINTS.length) store.set(learnedKey(), '1'); S.hint++; S.hintT = 0; showHint(); }
function showHint() { const t = HINTS[S.hint - 1]; $('hint').textContent = t || ''; $('hint').classList.toggle('on', !!t); }
const learnedKey = () => 'ms-learned';
const fmt = s => { const m = Math.floor(s / 60), r = s - m * 60; return `${m}:${r < 10 ? '0' : ''}${r.toFixed(1)}`; };
const LM = k => CITY.meta.landmarks[k];
function raceName(r) { return r.map(k => LM(k).name).join(' to '); }
function startRun(mode, opts = {}) {   // mode 'roam' (opts.x, opts.z) or 'race' (opts.race: its index)
  S.mode = mode; S.race = mode === 'race' ? opts.race : null; S.cp = 1;
  const route = S.race != null ? CITY.meta.races[S.race] : null;
  const start = route ? LM(route[0]) : { x: opts.x, z: opts.z };
  startHero(start.x, start.z, route ? LM(route[1]) : null);
  updateWorld(camPos.x, camPos.z); buildBudget = 40; updateWorld(H.p.x, H.p.z); buildBudget = 3;   // the blocks around you, at once
  updateCamera(0, true);
  S.phase = 'play'; S.bot = !!opts.bot; S.tiltZero = null; S.reeled = false;
  S.hint = store.get(learnedKey()) === '1' || S.bot ? 0 : 1; S.hintT = 0; showHint();
  for (const id of [...ptrs.keys()]) lift(id);
  $('menu').hidden = $('end').hidden = $('paused').hidden = $('mapScreen').hidden = true; $('hud').hidden = false; $('pause').hidden = false;
  $('restartRace').hidden = !route;
  $('dist').hidden = !route; $('arrow').hidden = !route;
  showCheckpoint();
}
function showCheckpoint() {
  const route = S.race != null ? CITY.meta.races[S.race] : null;
  if (!route) { beam.visible = false; $('tag2').textContent = ''; return; }
  const c = LM(route[S.cp]); beam.position.set(c.x, groundAt(c.x, c.z), c.z); beam.visible = true;
  $('tag2').textContent = (S.cp === route.length - 1 ? 'Finish: ' : 'Next: ') + c.name;
}
function checkpoints() {   // within 35 m of the landmark, at any height, counts
  const route = CITY.meta.races[S.race], c = LM(route[S.cp]);
  if (Math.hypot(H.p.x - c.x, H.p.z - c.z) > 35) return;
  SFX.pickup?.();
  if (S.cp === route.length - 1) return finishRace();
  S.cp++; showCheckpoint();
}
const bestKey = r => 'ms-best-' + r;
function finishRace() {
  S.phase = 'end'; S.endT = 0; beam.visible = false;
  for (const h of hooks) h.state = 'off';
  $('hint').classList.remove('on'); $('pause').hidden = true;
  const t = S.t, prev = +store.get(bestKey(S.race)) || 0;
  $('enddist').textContent = fmt(t); $('endrace').textContent = raceName(CITY.meta.races[S.race]);
  $('pb').textContent = !prev || t < prev ? 'New best!' : `Best ${fmt(prev)}.`;
  if ((!prev || t < prev) && !S.bot) store.set(bestKey(S.race), String(t));
  $('rank').textContent = ''; $('endboards').hidden = true; $('namebox').hidden = S.bot;
  $('nick').value = (store.get('ms-name') || '').slice(0, 20);
  endRunData = S.bot ? null : { race: S.race, sent: false, run: { player: playerId(), score: Math.max(0, 1000000 - Math.round(t * 100)), centis: Math.round(t * 100), version: VERSION } };
  showBoards(S.race, $('ebDay'), $('ebAll'), $('endboards'));
  setTimeout(() => { if (S.phase === 'end') $('end').hidden = false; }, 400);
}
function toMenu() {
  S.phase = 'menu'; S.bot = false; beam.visible = false;
  for (const id of [...ptrs.keys()]) lift(id);
  $('end').hidden = $('paused').hidden = $('mapScreen').hidden = true; $('hud').hidden = true; $('pause').hidden = true; $('menu').hidden = false;
  $('hint').classList.remove('on');
  menuRun(); loadMenu();
}
function menuRun() {   // behind the menu the computer swings through Midtown
  if (!CITY.ready) return;
  S.mode = 'roam'; S.race = null; beam.visible = false; B.goal = null;
  startHero(0, 0); updateWorld(H.p.x, H.p.z); updateCamera(0, true);
}
function pauseGame() { if (S.phase !== 'play') return; S.phase = 'paused'; $('paused').hidden = false; for (const id of [...ptrs.keys()]) lift(id); }
function prepare() {
  audio(); goFullScreen();
  if (typeof DeviceOrientationEvent !== 'undefined' && typeof DeviceOrientationEvent.requestPermission === 'function') DeviceOrientationEvent.requestPermission().catch(() => {});
}
// the map: Manhattan, north up; tap to start there
const MAP = { k: 1, ox: 0, oz: 0 };
function drawMap() {
  const cv2 = $('map'), r = cv2.getBoundingClientRect(), dpr = Math.min(devicePixelRatio || 1, 2);
  cv2.width = Math.max(10, r.width * dpr); cv2.height = Math.max(10, r.height * dpr);
  const g = cv2.getContext('2d'), L = CITY.meta.land;
  let x0 = 1e9, x1 = -1e9, z0 = 1e9, z1 = -1e9;
  for (const f of L) for (let k = 0; k < f.length; k += 2) { x0 = Math.min(x0, f[k]); x1 = Math.max(x1, f[k]); z0 = Math.min(z0, f[k + 1]); z1 = Math.max(z1, f[k + 1]); }
  const pad = 16 * dpr; MAP.k = Math.min((cv2.width - pad * 2) / (x1 - x0), (cv2.height - pad * 2) / (z1 - z0));
  MAP.ox = (cv2.width - (x1 - x0) * MAP.k) / 2 - x0 * MAP.k; MAP.oz = (cv2.height - (z1 - z0) * MAP.k) / 2 - z0 * MAP.k;
  const X = x => x * MAP.k + MAP.ox, Z = z => z * MAP.k + MAP.oz;
  g.fillStyle = '#0b1230'; g.fillRect(0, 0, cv2.width, cv2.height);
  g.fillStyle = '#1e2a5c';
  for (const f of L) { g.beginPath(); for (let k = 0; k < f.length; k += 2) (k ? g.lineTo : g.moveTo).call(g, X(f[k]), Z(f[k + 1])); g.closePath(); g.fill(); }
  const G = CITY.meta.grid; g.fillStyle = '#2c5236';   // the parks
  for (let j = 0; j < G.nz; j++) for (let i = 0; i < G.nx; i++) if (CITY.gk[j * G.nx + i] === 2) g.fillRect(X(G.x0 + i * G.cell), Z(G.z0 + j * G.cell), G.cell * MAP.k + .6, G.cell * MAP.k + .6);
  g.font = `${11 * dpr}px -apple-system, Helvetica, Arial`; g.textBaseline = 'middle';
  for (const l of Object.values(CITY.meta.landmarks)) {
    g.fillStyle = '#ffd27a'; g.beginPath(); g.arc(X(l.x), Z(l.z), 3.5 * dpr, 0, Math.PI * 2); g.fill();
    g.fillStyle = 'rgba(242,239,230,.85)'; g.fillText(l.name, X(l.x) + 6 * dpr, Z(l.z));
  }
}
$('map').addEventListener('pointerup', e => {
  const r = $('map').getBoundingClientRect(), dpr = $('map').width / r.width;
  const x = ((e.clientX - r.left) * dpr - MAP.ox) / MAP.k, z = ((e.clientY - r.top) * dpr - MAP.oz) / MAP.k;
  if (!kindAt(x, z)) return;   // on land only
  startRun('roam', { x, z });
});
$('roam').onclick = () => { prepare(); $('menu').hidden = true; $('mapScreen').hidden = false; drawMap(); };
$('mapBack').onclick = () => { $('mapScreen').hidden = true; $('menu').hidden = false; };
$('showRaces').onclick = () => { $('raceList').hidden = !$('raceList').hidden; };
function fillRaces() {
  const box = $('raceList'); box.innerHTML = '';
  CITY.meta.races.forEach((r, i) => {
    const b = document.createElement('button'), best = +store.get(bestKey(i)) || 0;
    b.innerHTML = `<b></b><span>${best ? 'best ' + fmt(best) : ''}</span>`; b.firstChild.textContent = raceName(r);
    b.onclick = () => { prepare(); startRun('race', { race: i }); };
    box.appendChild(b);
  });
}
$('again').onclick = () => S.race != null ? startRun('race', { race: S.race }) : toMenu();
$('tomenu').onclick = toMenu; $('quit').onclick = toMenu;
$('restartRace').onclick = () => startRun('race', { race: S.race });
$('resume').onclick = () => { $('paused').hidden = true; S.phase = 'play'; S.tiltZero = null; };
$('pause').onclick = pauseGame;
document.addEventListener('visibilitychange', () => { if (document.hidden) pauseGame(); else if (S.phase === 'menu') checkVersion(); });

''')
rep('$("again")', '$("again")', 0)
# ---- high scores: one board per race on the shared Worker; a time is stored as 1,000,000 minus hundredths
rep("function playerId() { let id = store.get('gc-player');", "function playerId() { let id = store.get('ms-player');")
rep("store.set('gc-player', id); } return id; }", "store.set('ms-player', id); } return id; }")
rep("  url: 'https://leaderboards.ai-wizards.workers.dev/grapple-city/',", "  url: 'https://leaderboards.ai-wizards.workers.dev/manhattan-swinger-r',")
rep("  async submit(run) {", "  async submit(race, run) {")
rep("this.req('submit', {", "this.req(race + '/submit', {")
rep("  async top(scope, n = 5) {", "  async top(race, scope, n = 5) {")
rep("this.req(`top?scope=${scope}&n=${n}`);", "this.req(`${race}/top?scope=${scope}&n=${n}`);")
rep("({ name: String(x?.name || 'Anonymous').slice(0, 20), score: +x?.score || 0 }))", "({ name: String(x?.name || 'Anonymous').slice(0, 20), time: (1000000 - (+x?.score || 0)) / 100 }))")
rep("for (const r of rows) { const li = document.createElement('li'); li.textContent = `${r.name} ${r.score} m`; ol.appendChild(li); }",
    "for (const r of rows) { const li = document.createElement('li'); li.textContent = `${r.name} ${fmt(r.time)}`; ol.appendChild(li); }")
func('showBoards', r'''async function showBoards(race, day, all, wrap) {
  const [d, a] = await Promise.all([LB.top(race, 'daily'), LB.top(race, 'alltime')]);
  if (wrap) { if (!d && !a) return; wrap.hidden = false; }
  fillList(day, d); fillList(all, a);
}''')
func('loadMenu', r'''function loadMenu() { if (CITY.ready) fillRaces(); }''')
rep("const name = $('nick').value.trim().slice(0, 20); store.set('gc-name', name);", "const name = $('nick').value.trim().slice(0, 20); store.set('ms-name', name);")
rep("  const res = await LB.submit({ ...st.run, name: name || null });", "  const res = await LB.submit(st.race, { ...st.run, name: name || null });")
rep("  showBoards($('ebDay'), $('ebAll'), $('endboards'));\n};", "  showBoards(st.race, $('ebDay'), $('ebAll'), $('endboards'));\n};")

# =============================================================== main loop
func('tick', r'''function tick(dt) {
  if (S.phase === 'play' || S.phase === 'menu') {
    if (S.phase === 'menu' || S.bot) botThink(dt); else readSteer(dt);
    acc += dt;
    while (acc >= STEP) { step(STEP); acc -= STEP; if (S.phase !== 'play' && S.phase !== 'menu') break; }
    if (S.phase === 'play') {
      S.t += dt;
      if (S.hint) { S.hintT += dt; if (S.hint >= 2 && S.hintT > 4.5) hintNext(); }
      if (S.race != null) { checkpoints(); $('dist').textContent = fmt(S.t); }
    }
    if (S.phase === 'menu' && S.crashed) menuRun();
  } else acc = 0;
  if (S.phase === 'splash') { splashStep(dt); if (S.race != null) S.t += dt; }
  if (S.phase === 'end') S.endT += dt;
  updateWorld(camPos.x, camPos.z);
  if (S.race != null && S.phase === 'play') {   // the arrow points at the next landmark
    const c = LM(CITY.meta.races[S.race][S.cp]), r = rightOf(camDir, tA);
    const dx = c.x - H.p.x, dz = c.z - H.p.z;
    $('arrow').style.transform = `rotate(${Math.atan2(dx * r.x + dz * r.z, dx * camDir.x + dz * camDir.z)}rad)`;
  }
  drawHero(dt);
  updateCamera(dt);
  updateAudio(dt);
}''')
rep("resize(); menuRun(); loadMenu(); checkVersion();",
    "resize(); checkVersion();\n"
    "loadCity().then(() => { $('loading').hidden = true; $('menuButtons').hidden = false; menuRun(); loadMenu(); })\n"
    "  .catch(e => { $('loading').textContent = 'Manhattan did not load. Check your connection and reload.'; console.error(e); });")

# =============================================================== tests
func('sim', r'''function sim(secs, starts = [[0, 0], [-300, -2500], [600, 3000], [-1500, 4500], [900, -5000]]) {
  // free roam: the computer heads for random landmarks from several starts
  const out = [];
  for (const [x, z] of starts) {
    startHero(x, z); B.goal = null; updateWorld(H.p.x, H.p.z); updateCamera(0, true);
    S.phase = 'menu'; let t = 0, path = 0, onT = 0, splash = 0, minY = 1e9, street = 0; const p0 = H.p.clone(), prev = H.p.clone();
    while (t < secs) {
      botThink(1 / 60);
      for (let k = 0; k < 3; k++) step(STEP);
      if (S.phase === 'splash' || S.crashed) { splash++; S.crashed = false; S.phase = 'menu'; H.p.copy(S.lastSafe); H.p.y += 1; H.v.set(0, 0, 0); }
      updateCamera(1 / 60);
      t += 1 / 60; path += prev.distanceTo(H.p); prev.copy(H.p); minY = Math.min(minY, H.p.y);
      if (hooks.some(h => h.state === 'on')) onT += 1 / 60; if (H.state === 'street') street += 1 / 60;
    }
    out.push({ start: [x, z], secs, travelled: Math.round(path), straight: Math.round(H.p.distanceTo(p0)), onRope: +(onT / secs).toFixed(2), street: +street.toFixed(1), splashes: splash, ropes: S.hooks });
  }
  menuRun();
  return out;
}
function raceSim(i, secs = 240) {   // the computer runs a race; how long it takes, if it finishes
  startRun('race', { race: i, bot: true }); B.goal = null;
  let t = 0;
  while (t < secs && S.phase !== 'end') {
    const route = CITY.meta.races[S.race]; B.goal = LM(route[S.cp]);
    tick(1 / 60); t += 1 / 60;
  }
  const r = { race: raceName(CITY.meta.races[i]), finished: S.phase === 'end', time: +S.t.toFixed(1), checkpoint: S.cp };
  toMenu(); return r;
}''')
func('trace', r'''function trace(secs, x = 0, z = 0, every = .5) {
  startHero(x, z); B.goal = null; updateWorld(H.p.x, H.p.z); updateCamera(0, true); S.phase = 'menu';
  const log = [];
  for (let t = 0; t < secs; t += 1 / 60) {
    botThink(1 / 60); for (let k = 0; k < 3; k++) step(STEP); updateCamera(1 / 60);
    if (Math.abs(t / every - Math.round(t / every)) < 1 / 120) log.push(`${t.toFixed(1)} ${S.phase} ${H.state} p=${H.p.toArray().map(x => x.toFixed(0))} v=${H.v.toArray().map(x => x.toFixed(1))} goal=${B.goal?.name}`);
  }
  menuRun(); return log.join('\n');
}''')
rep("window.__game = { S, H, T, hooks, boxes: () => boxes, trace,", "window.__game = { S, H, T, hooks, CITY, near, groundAt, kindAt, rayCity, raceSim, updateWorld, trace,")
rep("if (hash.startsWith('demo')) { const s = hash.split('-')[1]; startRun(true); for (let i = 0; i < (+s || 0) * 60; i++) tick(1 / 60); }", "")

# =============================================================== leftovers from the cloud city
for gone in ('CLOUD', 'PARK', 'ROWS', 'boxes', 'cloudFloor', 'veil', 'skyline', 'parks', 'puffMats', 'blinkers.length = 0', 'resetWorld', 'towardSunset('):
    pass
s = s.replace("  for (const b of blinkers) b.visible = (performance.now() / 700 | 0) % 2 === 0;\n", "")
open(sys.argv[2], 'w').write(s)
left = [l.strip()[:120] for l in s.split('\n') if re.search(r'\bCLOUD\b|\bPARK\b|\bROWS\b|\bboxes\b|cloudFloor|\bveil\b|skyline|\bparks\b|puffMats|resetWorld|towardSunset\(|rayBoxes|roofAt|S\.dist\b|startZ', l)]
print('ok, leftovers:', len(left))
for l in left: print('  ', l)
