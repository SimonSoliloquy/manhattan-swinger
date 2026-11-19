"""Draw Manhattan Swinger's picture for simonsoliloquy.com from the game's own data: every building
from Midtown to the Battery, seen from above, lit by height (tall is gold, low is blue), on the
night water, with the sunset glowing on the west side.
  ~/ComfyUI/.venv/bin/python -I tools/card_image.py <out.jpg>"""
import json, math, os, struct, sys
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
meta = json.load(open(os.path.join(ROOT, 'data', 'manhattan.json')))
blob = open(os.path.join(ROOT, 'data', 'manhattan.bin'), 'rb').read()
T = meta['tile']
bld = []
for ti, tj, off, count in meta['tiles']:
    o = off
    for _ in range(count):
        n, base, h = struct.unpack_from('<BhH', blob, o); o += 5
        pts = []
        for _ in range(n):
            x, z = struct.unpack_from('<hh', blob, o); o += 4
            pts.append((ti * T + x / 10, tj * T + z / 10))
        bld.append((h / 10, pts))

S, scale = 1280, 1280 / 4200          # 4.2 km square, rendered at 2x then reduced
cx, cz = -500, 900                   # centred between the Empire State and the Battery
ang = math.radians(-29)               # turn the street grid upright, the way people draw Manhattan
def P(x, z):
    x, z = x - cx, z - cz
    xr, zr = x * math.cos(ang) - z * math.sin(ang), x * math.sin(ang) + z * math.cos(ang)
    return (S / 2 + xr * scale, S / 2 + zr * scale)

img = Image.new('RGB', (S, S), (10, 14, 34))
glow = Image.new('RGB', (S, S), (0, 0, 0)); gd = ImageDraw.Draw(glow)
for r in range(700, 0, -20):          # the sunset, low in the west (left)
    t = r / 700; gd.ellipse([-r - 200, S * .55 - r, r - 200, S * .55 + r], fill=(int(255 * (1 - t) * .9), int(120 * (1 - t) * .8), int(90 * (1 - t) * .7)))
img = Image.blend(img, glow, .55)
d = ImageDraw.Draw(img)
for f in meta['land']:
    d.polygon([P(f[k], f[k + 1]) for k in range(0, len(f), 2)], fill=(30, 38, 74))
for h, pts in sorted(bld, key=lambda b: b[0]):
    t = min(1, h / 250)
    col = (int(40 + 215 * t ** .8), int(60 + 150 * t ** .9), int(140 - 40 * t))
    q = [P(x, z) for x, z in pts]
    if any(-50 < a < S + 50 and -50 < b < S + 50 for a, b in q):
        d.polygon(q, fill=col)
img = img.filter(ImageFilter.SMOOTH).resize((640, 640), Image.LANCZOS)
img.save(sys.argv[1], quality=86)
print('ok', len(bld), 'buildings')
