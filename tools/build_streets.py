"""Street names for Manhattan Swinger: one label point per block of street, from NYC Open Data.

Source (downloaded into data-raw/, not committed): Centerline `inkn-q76z`, Manhattan only:
  curl -G -o data-raw/streets.json https://data.cityofnewyork.us/resource/inkn-q76z.json \
    --data-urlencode "\$where=boroughcode='1'" \
    --data-urlencode '$select=the_geom,stname_label,rw_type,from_level_code,to_level_code' --data-urlencode '$limit=50000'

Run:  python3 -I tools/build_streets.py
Writes data/streets.json: {"names": [...], "seg": [name index, x, z, angle in tenths of a degree, length, ...]}
in the game's metres (x east, z south, origin at Times Square, as tools/build_manhattan.py).
Kept: streets and highways (rw_type 1, 2) at ground level (level code 13), blocks of 40 m or more.
"""
import json, math, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LAT0, LON0 = 40.7580, -73.9855
KX, KZ = 111320 * math.cos(math.radians(LAT0)), 110574
def xz(lon, lat): return ((lon - LON0) * KX, -(lat - LAT0) * KZ)

WORD = {'ST': 'St', 'AVE': 'Ave', 'DR': 'Dr', 'PL': 'Pl', 'BLVD': 'Blvd', 'RD': 'Rd', 'SQ': 'Sq', 'TER': 'Ter',
        'LN': 'Ln', 'PKWY': 'Pkwy', 'HWY': 'Hwy', 'JR': 'Jr', 'SLIP': 'Slip', 'ALY': 'Aly', 'CT': 'Ct', 'EXPWY': 'Expy',
        'FDR': 'FDR', 'OF': 'of', 'THE': 'the', 'AND': 'and', 'LOOP': 'Loop', 'PLZ': 'Plaza', 'CIR': 'Circle', 'APPR': 'Approach'}
def ordinal(n):
    n = int(n); s = 'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return f'{n}{s}'
def pretty(label):
    out = []
    for i, w in enumerate(label.split()):
        if re.fullmatch(r'\d+', w): out.append(ordinal(w))
        elif w in WORD: out.append(WORD[w] if i else WORD[w][0].upper() + WORD[w][1:])
        elif len(w) == 1: out.append(w)
        else: out.append(w.capitalize())
    return ' '.join(out)

rows = json.load(open(os.path.join(ROOT, 'data-raw', 'streets.json')))
names, index, seg = [], {}, []
for r in rows:
    if r.get('rw_type') not in ('1', '2') or '13' not in (r.get('from_level_code'), r.get('to_level_code')): continue
    label = r.get('stname_label'); g = r.get('the_geom')
    if not label or not g: continue
    for line in g['coordinates']:
        pts = [xz(lon, lat) for lon, lat in line]
        lens = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:])]
        L = sum(lens)
        if L < 40: continue
        half, acc = L / 2, 0.0   # the label sits at the middle of the block, along the street there
        for (a, b), l in zip(zip(pts, pts[1:]), lens):
            if acc + l >= half:
                t = (half - acc) / (l or 1); x, z = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
                ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
                break
            acc += l
        name = pretty(label)
        if name not in index: index[name] = len(names); names.append(name)
        seg += [index[name], round(x, 1), round(z, 1), round(ang * 10), round(L)]
out = os.path.join(ROOT, 'data', 'streets.json')
json.dump({'names': names, 'seg': seg}, open(out, 'w'), separators=(',', ':'))
print(len(names), 'names,', len(seg) // 5, 'blocks,', os.path.getsize(out) // 1024, 'KB')
print('examples:', [names[i] for i in range(0, len(names), max(1, len(names) // 12))])
