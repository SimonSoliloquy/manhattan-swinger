"""Download what OpenStreetMap knows about Manhattan's buildings and shops into data-raw/osm.json
(not committed): building colours, materials and names, and named shops, restaurants, cafes, bars.
One Overpass query; OpenStreetMap data is (c) OpenStreetMap contributors, ODbL.
  python3 -I tools/fetch_osm.py
"""
import os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), 'data-raw', 'osm.json')
B = '40.69,-74.03,40.885,-73.90'   # south, west, north, east: Manhattan with a margin
Q = f"""[out:json][timeout:240][bbox:{B}];
(
  way["building"]["building:colour"];
  way["building"]["building:material"];
  way["building"]["roof:colour"];
  way["building"]["name"];
  relation["building"]["name"];
  nwr["shop"]["name"];
  nwr["amenity"~"^(restaurant|cafe|bar|pub|fast_food|bank|pharmacy|cinema|theatre|ice_cream)$"]["name"];
);
out tags center;"""
# curl, because the Mac's built-in Python cannot complete the TLS handshake with overpass-api.de
q = OUT + '.query'; open(q, 'w').write(Q)
subprocess.run(['curl', '-sS', '--fail', '-A', 'manhattan-swinger-build/1.0', '--max-time', '300', '-o', OUT,
                '--data-urlencode', 'data@' + q, 'https://overpass-api.de/api/interpreter'], check=True)
os.remove(q)
print('wrote', os.path.getsize(OUT) // 1024, 'KB to', OUT)
