"""Join OpenStreetMap (data-raw/osm.json from tools/fetch_osm.py) to the game's buildings and write
data/osm.json:
  tint    [building id, 0xRRGGBB, ...]   building:colour, else a colour for building:material
  named   [building id, name index, ...] named buildings of 60 m or more (their names go on the roof)
  shop    [x, z, nx, nz, kind, name index, ...] named shops and places, moved onto the nearest wall
          within 25 m, (nx, nz) the wall's outward normal, x z in tenths of a metre
  names, kinds: the strings the indexes point at
Building ids are the order data/manhattan.bin lists them, as the game loads them.
OpenStreetMap data is (c) OpenStreetMap contributors, ODbL; the game credits it on the menu.
  python3 -I tools/build_osm.py
"""
import json, math, os, re, struct
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
LAT0, LON0 = 40.7580, -73.9855
KX, KZ = 111320 * math.cos(math.radians(LAT0)), 110574
def xz(lon, lat): return ((lon - LON0) * KX, -(lat - LAT0) * KZ)

meta = json.load(open(os.path.join(ROOT, 'data', 'manhattan.json')))
blob = open(os.path.join(ROOT, 'data', 'manhattan.bin'), 'rb').read()
T = meta['tile']; B = []   # (top height above base, base, [(x, z)...])
for ti, tj, off, count in meta['tiles']:
    o = off
    for _ in range(count):
        n, base, h = struct.unpack_from('<BhH', blob, o); o += 5; pts = []
        for _ in range(n):
            x, z = struct.unpack_from('<hh', blob, o); o += 4; pts.append((ti * T + x / 10, tj * T + z / 10))
        B.append((h / 10, base / 10, pts))
C = 50; grid = defaultdict(list)
for i, (_, _, pts) in enumerate(B):
    xs = [p[0] for p in pts]; zs = [p[1] for p in pts]
    for gx in range(int(min(xs) // C), int(max(xs) // C) + 1):
        for gz in range(int(min(zs) // C), int(max(zs) // C) + 1): grid[(gx, gz)].append(i)
def near(x, z, r):
    out = set()
    for gx in range(int((x - r) // C), int((x + r) // C) + 1):
        for gz in range(int((z - r) // C), int((z + r) // C) + 1): out.update(grid.get((gx, gz), ()))
    return out
def inside(pts, x, z):
    c = False
    for k in range(len(pts)):
        (ax, az), (bx, bz) = pts[k], pts[k - 1]
        if (az > z) != (bz > z) and x < ax + (z - az) * (bx - ax) / (bz - az): c = not c
    return c
def edges(pts, x, z):   # every wall's nearest point to (x, z): (distance, x, z, outward normal x, z)
    area = sum(pts[k - 1][0] * pts[k][1] - pts[k][0] * pts[k - 1][1] for k in range(len(pts)))
    for k in range(len(pts)):
        (ax, az), (bx, bz) = pts[k - 1], pts[k]; dx, dz = bx - ax, bz - az; L2 = dx * dx + dz * dz or 1e-9
        t = max(0, min(1, ((x - ax) * dx + (z - az) * dz) / L2)); px, pz = ax + dx * t, az + dz * t
        L = math.sqrt(L2); nx, nz = (-dz / L, dx / L) if area < 0 else (dz / L, -dx / L)
        yield (math.hypot(x - px, z - pz), px, pz, nx, nz)
def edge(pts, x, z): return min(edges(pts, x, z), key=lambda q: q[0])
def open_air(x, z): return not any(inside(B[i][2], x, z) for i in near(x, z, 1))
def building_at(x, z, slack):
    ids = near(x, z, slack)
    for i in ids:
        if inside(B[i][2], x, z): return i
    best = min(((edge(B[i][2], x, z)[0], i) for i in ids), default=None)
    return best[1] if best and best[0] <= slack else None

CSS = {'white': 0xf2f0ea, 'black': 0x2a2a2a, 'grey': 0x8c8c8c, 'gray': 0x8c8c8c, 'beige': 0xd8c8a8, 'brown': 0x7a4e32,
       'red': 0x9a3a2e, 'tan': 0xc8a878, 'yellow': 0xd8c070, 'cream': 0xeee2c8, 'silver': 0xb8bcc4, 'blue': 0x4a6a9a,
       'green': 0x4a7a5a, 'darkgray': 0x555555, 'darkgrey': 0x555555, 'lightgray': 0xc8c8c8, 'lightgrey': 0xc8c8c8,
       'orange': 0xc0703a, 'pink': 0xd8a0a0, 'maroon': 0x6a2a2a, 'ivory': 0xf0ead8, 'sandybrown': 0xd8a060}
MAT = {'brick': 0x8a4b3a, 'plaster': 0xcfc6b4, 'concrete': 0x9a9a96, 'stone': 0xc2b79e, 'limestone': 0xd2c7ab,
       'marble': 0xdcd8cc, 'sandstone': 0xc89a6a, 'wood': 0x7a5a3a, 'cast_iron': 0x4a4a4a, 'granite': 0x9a8f88}
def colour(tags):
    c = (tags.get('building:colour') or '').strip().lower()
    if re.fullmatch(r'#[0-9a-f]{6}', c): return int(c[1:], 16)
    if re.fullmatch(r'#[0-9a-f]{3}', c): return int(''.join(ch * 2 for ch in c[1:]), 16)
    if c in CSS: return CSS[c]
    return MAT.get((tags.get('building:material') or '').strip().lower())   # glass and metal stay the default towers

els = json.load(open(os.path.join(ROOT, 'data-raw', 'osm.json')))['elements']
tint, named, shop, names, kinds, nidx, kidx = {}, {}, [], [], [], {}, {}
def ix(table, index, s):
    if s not in index: index[s] = len(table); table.append(s)
    return index[s]
seen_shop = set()
for e in els:
    t = e.get('tags', {}); p = e.get('center') or ({'lat': e['lat'], 'lon': e['lon']} if 'lat' in e else None)
    if not p: continue
    x, z = xz(p['lon'], p['lat'])
    if 'building' in t:
        i = building_at(x, z, 8)
        if i is None: continue
        c = colour(t)
        if c is not None: tint[i] = c
        if t.get('name') and B[i][0] >= 60: named[i] = t['name']
    elif t.get('name') and ('shop' in t or 'amenity' in t):
        lv = t.get('level', '0').split(';')[0]
        if lv not in ('0', '', '-0'): continue   # only shops at street level
        cand = near(x, z, 25)
        if not cand: continue
        # the nearest wall that faces open street (not a wall shared with the next building)
        best = next((q for q in sorted(e for i in cand for e in edges(B[i][2], x, z)) if q[0] <= 25 and open_air(q[1] + q[3] * 2, q[2] + q[4] * 2)), None)
        if best is None: continue
        d, px, pz, nx, nz = best
        key = (round(px / 3), round(pz / 3), t['name'])
        if key in seen_shop: continue
        seen_shop.add(key)
        kind = t.get('amenity') or 'shop'
        shop += [round(px * 10), round(pz * 10), round(nx, 2), round(nz, 2), ix(kinds, kidx, kind), ix(names, nidx, t['name'][:40])]
out = {'tint': [v for i, c in sorted(tint.items()) for v in (i, c)],
       'named': [v for i, n in sorted(named.items()) for v in (i, ix(names, nidx, n[:48]))],
       'shop': shop, 'names': names, 'kinds': kinds,
       'note': 'Building colours, building names and shops (c) OpenStreetMap contributors, ODbL. Built by tools/build_osm.py.'}
f = os.path.join(ROOT, 'data', 'osm.json'); json.dump(out, open(f, 'w'), separators=(',', ':'), ensure_ascii=False)
print('tinted buildings', len(tint), '| named tall buildings', len(named), '| shops', len(shop) // 6, '|', os.path.getsize(f) // 1024, 'KB')
print('named examples:', sorted(named.values(), key=len)[:0] or [named[i] for i in sorted(named, key=lambda i: -B[i][0])[:12]])
