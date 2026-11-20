"""Download the bare-earth elevation of Manhattan into data-raw/terrarium/ (not committed).

Source: Terrain Tiles on the AWS Registry of Open Data (s3://elevation-tiles-prod, Terrarium PNG
encoding: metres = R*256 + G + B/256 - 32768). Over New York City they come from USGS 3DEP lidar.
Zoom 14 is about 7 m a pixel here, finer than the game's 40 m ground grid.
  python3 -I tools/fetch_dem.py
"""
import math, os, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), 'data-raw', 'terrarium')
Z = 14
W, E, S, N = -74.03, -73.90, 40.69, 40.885   # Manhattan with a margin
def tile(lon, lat):
    n = 2 ** Z; x = int((lon + 180) / 360 * n)
    y = int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n)
    return x, y
x0, y0 = tile(W, N); x1, y1 = tile(E, S)
os.makedirs(OUT, exist_ok=True); got = 0
for x in range(x0, x1 + 1):
    for y in range(y0, y1 + 1):
        f = os.path.join(OUT, f'{Z}_{x}_{y}.png')
        if os.path.exists(f): continue
        url = f'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{Z}/{x}/{y}.png'
        with urllib.request.urlopen(url, timeout=30) as r: data = r.read()
        if data[:8] != b'\x89PNG\r\n\x1a\n': raise SystemExit(f'not a PNG: {url}')
        open(f, 'wb').write(data); got += 1
print('tiles', (x1 - x0 + 1) * (y1 - y0 + 1), 'downloaded', got, 'x', x0, x1, 'y', y0, y1)
