"""Turn NYC Open Data into the compact Manhattan the game loads.

Sources (NYC Open Data, downloaded into data-raw/, which is not committed):
  footprints.geojson  Building Footprints `5zhs-2jue`, Manhattan only (base_bbl starts with 1):
                      outline, height_roof (ft above ground), ground_elevation (ft)
  boroughs.geojson    Borough Boundaries `gthc-hcne` (clipped to the shoreline)
  terrarium/          bare-earth elevation tiles from tools/fetch_dem.py (optional; the ground uses them when present)

Download again with:
  curl -G -o data-raw/footprints.geojson https://data.cityofnewyork.us/resource/5zhs-2jue.geojson \
    --data-urlencode "$where=starts_with(base_bbl,'1')" \
    --data-urlencode '$select=the_geom,bin,height_roof,ground_elevation,base_bbl' --data-urlencode '$limit=60000'
  curl -o data-raw/boroughs.geojson https://data.cityofnewyork.us/resource/gthc-hcne.geojson

Run with a Python that has numpy (ComfyUI's works):
  ~/ComfyUI/.venv/bin/python -I tools/build_manhattan.py

Writes data/manhattan.bin (buildings and the ground grid) and data/manhattan.json (the index,
the land outlines, the landmarks). Metres, x east, y up, z SOUTH (so three.js stays right-handed),
origin at Times Square.
"""
import json, math, os, struct, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAW, OUT = os.path.join(ROOT, 'data-raw'), os.path.join(ROOT, 'data')
LAT0, LON0 = 40.7580, -73.9855
KX, KZ = 111320 * math.cos(math.radians(LAT0)), 110574
TILE, CELL = 200, 40
FT = 0.3048

def xz(lon, lat): return ((lon - LON0) * KX, -(lat - LAT0) * KZ)

def area(r):
    a = 0.0
    for i in range(len(r)):
        x0, z0 = r[i]; x1, z1 = r[(i + 1) % len(r)]; a += x0 * z1 - x1 * z0
    return a / 2

def simplify(pts, tol):
    """Douglas-Peucker on an open polyline."""
    if len(pts) < 3: return pts
    keep = [False] * len(pts); keep[0] = keep[-1] = True; stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop(); (ax, az), (bx, bz) = pts[a], pts[b]; dx, dz = bx - ax, bz - az; L = math.hypot(dx, dz) or 1e-9
        best, bi = -1, -1
        for i in range(a + 1, b):
            px, pz = pts[i]; d = abs(dx * (az - pz) - (ax - px) * dz) / L
            if d > best: best, bi = d, i
        if best > tol: keep[bi] = True; stack += [(a, bi), (bi, b)]
    return [p for p, k in zip(pts, keep) if k]

def ring(coords, tol):
    pts = [xz(lon, lat) for lon, lat in coords]
    if len(pts) > 1 and pts[0] == pts[-1]: pts = pts[:-1]
    if len(pts) < 3: return None
    # split the closed ring at its two farthest points so D-P keeps the shape
    far = max(range(len(pts)), key=lambda i: (pts[i][0] - pts[0][0]) ** 2 + (pts[i][1] - pts[0][1]) ** 2)
    a = simplify(pts[:far + 1], tol); b = simplify(pts[far:] + [pts[0]], tol)
    r = a[:-1] + b[:-1]
    if len(r) < 3 or abs(area(r)) < 1: return None
    if area(r) < 0: r.reverse()   # every ring counter-clockwise in x-z
    return r

# ---------------- land ----------------
bor = json.load(open(os.path.join(RAW, 'boroughs.geojson')))
land, others = [], []
for f in bor['features']:
    code = str(f['properties'].get('borocode'))
    for poly in f['geometry']['coordinates']:
        r = ring(poly[0], 4 if code == '1' else 20)
        if not r: continue
        a = abs(area(r))
        if code == '1':
            if a > 20000: land.append(r)
        elif a > 200000 and code in ('2', '3', '4'):   # the Bronx, Brooklyn, Queens: scenery across the rivers
            others.append(r)
print('manhattan land polygons', len(land), 'points', sum(map(len, land)), '| other boroughs', len(others), 'points', sum(map(len, others)))

# ---------------- buildings ----------------
src = json.load(open(os.path.join(RAW, 'footprints.geojson')))['features']
bld, skipped = [], 0
for f in src:
    p, g = f['properties'], f['geometry']
    try: h = float(p.get('height_roof') or 0) * FT; base = float(p.get('ground_elevation') or 0) * FT
    except ValueError: skipped += 1; continue
    if not g or h < 2.5: skipped += 1; continue
    polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
    best = None
    for poly in polys:
        r = ring(poly[0], .6)
        if r and (best is None or abs(area(r)) > abs(area(best))): best = r
    if not best: skipped += 1; continue
    tol = .6
    while len(best) > 64 and tol < 8:   # very detailed outlines: coarser until they fit
        tol *= 1.6; best = ring([(LON0 + x / KX, LAT0 - z / KZ) for x, z in best] + [(LON0 + best[0][0] / KX, LAT0 - best[0][1] / KZ)], tol) or best
    best = best[:255]
    cx = sum(x for x, _ in best) / len(best); cz = sum(z for _, z in best) / len(best)
    bld.append((cx, cz, base, h, best))
print('buildings kept', len(bld), 'skipped', skipped, 'vertices', sum(len(b[4]) for b in bld), 'tallest', round(max(b[3] for b in bld)), 'm')

# ---------------- tiles ----------------
tiles = {}
for b in bld: tiles.setdefault((math.floor(b[0] / TILE), math.floor(b[1] / TILE)), []).append(b)
blob, index = bytearray(), []
for (i, j), bs in sorted(tiles.items()):
    ox, oz, off = i * TILE, j * TILE, len(blob)
    for cx, cz, base, h, r in bs:
        blob += struct.pack('<BhH', len(r), round(base * 10), min(65535, round(h * 10)))
        for x, z in r: blob += struct.pack('<hh', round((x - ox) * 10), round((z - oz) * 10))
    index.append([i, j, off, len(bs)])

# ---------------- ground grid: elevation, land, park ----------------
allx = [x for r in land for x, _ in r]; allz = [z for r in land for _, z in r]
x0, z0 = math.floor(min(allx) / CELL) * CELL - CELL * 4, math.floor(min(allz) / CELL) * CELL - CELL * 4
nx, nz = int((max(allx) - x0) / CELL) + 5, int((max(allz) - z0) / CELL) + 5
cxs = x0 + (np.arange(nx) + .5) * CELL; czs = z0 + (np.arange(nz) + .5) * CELL
PX, PZ = np.meshgrid(cxs, czs)   # [nz, nx]
inside = np.zeros(PX.shape, bool)
for r in land:   # even-odd ray casting, vectorised over every cell
    xs = np.array([p[0] for p in r]); zs = np.array([p[1] for p in r]); xs2 = np.roll(xs, -1); zs2 = np.roll(zs, -1)
    acc = np.zeros(PX.shape, bool)
    for a, b, c, d in zip(xs, zs, xs2, zs2):
        cond = (b > PZ) != (d > PZ)
        with np.errstate(divide='ignore', invalid='ignore'): xi = a + (PZ - b) * (c - a) / (d - b)
        acc ^= cond & (PX < xi)
    inside |= acc
hsum = np.zeros(PX.shape); hcnt = np.zeros(PX.shape)
for cx, cz, base, h, r in bld:
    gi, gj = int((cx - x0) // CELL), int((cz - z0) // CELL)
    if 0 <= gi < nx and 0 <= gj < nz: hsum[gj, gi] += base; hcnt[gj, gi] += 1
ground = np.where(hcnt > 0, hsum / np.maximum(hcnt, 1), np.nan)
for _ in range(80):   # fill land with no buildings (parks, streets) from the neighbours
    nan = np.isnan(ground) & inside
    if not nan.any(): break
    pad = np.pad(ground, 1, constant_values=np.nan)
    nb = np.stack([pad[1:-1, :-2], pad[1:-1, 2:], pad[:-2, 1:-1], pad[2:, 1:-1]])
    with np.errstate(invalid='ignore'): m = np.nanmean(nb, axis=0)
    ground[nan] = m[nan]
ground = np.where(inside, np.nan_to_num(ground, nan=2.0), 0.0)
# Real bare-earth terrain when tools/fetch_dem.py has downloaded it (USGS 3DEP lidar, through the
# Terrain Tiles on AWS Open Data): each cell is the mean of 9 samples across it. Without it, the
# ground stays the mean of the buildings' recorded ground heights, filled in across the parks.
DEM = os.path.join(RAW, 'terrarium')
if os.path.isdir(DEM) and os.listdir(DEM):
    from PIL import Image
    tiles = {}
    for f in os.listdir(DEM):
        if not f.endswith('.png'): continue
        zl, tx, ty = map(int, f[:-4].split('_'))
        a = np.asarray(Image.open(os.path.join(DEM, f)).convert('RGB')).astype(np.float64)
        tiles[(tx, ty)] = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
    ZL = zl; NPX = 2 ** ZL * 256
    def dem(x, z):   # metres above sea level at game coordinates (arrays)
        lon = x / KX + LON0; lat = LAT0 - z / KZ
        px = (lon + 180) / 360 * NPX; py = (1 - np.arcsinh(np.tan(np.radians(lat))) / np.pi) / 2 * NPX
        out = np.full(np.shape(x), np.nan)
        tx, ty = (px // 256).astype(int), (py // 256).astype(int)
        for (a, b), t in tiles.items():
            m = (tx == a) & (ty == b)
            if m.any(): out[m] = t[(py[m] % 256).astype(int), (px[m] % 256).astype(int)]
        return out
    acc = np.zeros(PX.shape); n = np.zeros(PX.shape)
    for dx in (-CELL / 3, 0, CELL / 3):
        for dz in (-CELL / 3, 0, CELL / 3):
            v = dem(PX + dx, PZ + dz); ok = ~np.isnan(v); acc[ok] += v[ok]; n[ok] += 1
    terrain = np.where(n > 0, acc / np.maximum(n, 1), np.nan)
    use = inside & ~np.isnan(terrain)
    diff = terrain[use & (hcnt > 0)] - ground[use & (hcnt > 0)]
    print('terrain: cells', int(use.sum()), 'vs the buildings\' ground: mean', round(float(diff.mean()), 1), 'm, 90% within', round(float(np.percentile(np.abs(diff), 90)), 1), 'm')
    ground = np.where(use, np.clip(terrain, 0.5, None), ground)
# a park: land with no building in this cell or any neighbour (Central Park, Riverside, the Battery...)
busy = (hcnt > 0).astype(np.uint8); pad = np.pad(busy, 1)
near = sum(pad[1 + dj:1 + dj + nz, 1 + di:1 + di + nx] for dj in (-1, 0, 1) for di in (-1, 0, 1))
kind = np.where(inside, np.where(near == 0, 2, 1), 0).astype(np.uint8)
gh = np.clip(np.round(ground * 2), 0, 255).astype(np.uint8)
goff = len(blob); blob += gh.tobytes(); koff = len(blob); blob += kind.tobytes()
print('ground grid', nx, 'x', nz, 'land cells', int(inside.sum()), 'park cells', int((kind == 2).sum()), 'highest ground', round(float(ground.max()), 1), 'm')

# ---------------- landmarks and races ----------------
L = {
    'empire': ('Empire State Building', 40.74844, -73.98566), 'chrysler': ('Chrysler Building', 40.75162, -73.97554),
    'times': ('Times Square', 40.75800, -73.98550), 'columbus': ('Columbus Circle', 40.76808, -73.98193),
    'bethesda': ('Bethesda Fountain', 40.77405, -73.97082), 'wtc': ('One World Trade Center', 40.71274, -74.01338),
    'battery': ('The Battery', 40.70341, -74.01700), 'washsq': ('Washington Square Arch', 40.73116, -73.99712),
    'flatiron': ('Flatiron Building', 40.74106, -73.98966), 'grandcentral': ('Grand Central', 40.75273, -73.97723),
    'rockefeller': ('Rockefeller Center', 40.75874, -73.97868), 'brooklynbridge': ('Brooklyn Bridge', 40.71070, -74.00410),
    'unionsq': ('Union Square', 40.73590, -73.99067), 'hudsonyards': ('Hudson Yards', 40.75374, -74.00186),
    'cathedral': ('St. John the Divine', 40.80382, -73.96187), 'cloisters': ('The Cloisters', 40.86493, -73.93171),
}
landmarks = {k: {'name': n, 'x': round(xz(lon, lat)[0], 1), 'z': round(xz(lon, lat)[1], 1)} for k, (n, lat, lon) in L.items()}
races = [['empire', 'chrysler'], ['times', 'bethesda'], ['wtc', 'washsq'], ['flatiron', 'empire'], ['battery', 'wtc'],
         ['washsq', 'unionsq', 'flatiron'], ['hudsonyards', 'times', 'rockefeller', 'grandcentral'], ['brooklynbridge', 'wtc', 'empire']]

os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, 'manhattan.bin'), 'wb').write(bytes(blob))
meta = {
    'note': 'Built by tools/build_manhattan.py from NYC Open Data: Building Footprints 5zhs-2jue and Borough Boundaries gthc-hcne; ground from USGS 3DEP via the AWS Terrain Tiles.',
    'origin': [LAT0, LON0], 'tile': TILE, 'tiles': index, 'buildings': len(bld),
    'grid': {'x0': x0, 'z0': z0, 'cell': CELL, 'nx': nx, 'nz': nz, 'height': goff, 'kind': koff},
    'land': [[round(c, 1) for p in r for c in p] for r in land],
    'others': [[round(c) for p in r for c in p] for r in others],
    'landmarks': landmarks, 'races': races,
}
json.dump(meta, open(os.path.join(OUT, 'manhattan.json'), 'w'), separators=(',', ':'))
print('wrote', len(blob), 'bytes of buildings and ground,', os.path.getsize(os.path.join(OUT, 'manhattan.json')), 'bytes of index')
