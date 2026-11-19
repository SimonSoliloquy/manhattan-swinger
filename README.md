# Manhattan Swinger

Swing anywhere in Manhattan: all 45,036 buildings on the island at their real heights, from NYC Open
Data, with the sun setting over the Hudson. Free roam from wherever you tap on the map, or timed races
between landmarks. One thumb: hold to swing (the rope goes to the side you tilt the phone), let go to
fly, tap to jump. Land on any roof or street and keep running; only the rivers set you back.

Live at https://manhattan-swinger.vercel.app. One `index.html` (three.js 0.170.0 from a CDN, no build)
plus `data/manhattan.bin` and `data/manhattan.json`. `DESIGN.md` holds every ruling. Bump `VERSION` on
every change. Made from City Swinger (`SimonSoliloquy/city-swinger`) by `tools/make_from_city_swinger.py`.

Rebuild the city: download the two NYC Open Data files into `data-raw/` (commands in
`tools/build_manhattan.py`), then `~/ComfyUI/.venv/bin/python -I tools/build_manhattan.py`.

Test: `PATH=/usr/local/bin:$PATH node tools/node_sim.mjs <path to three.module.js>` loads the real data,
checks the geometry, swings the computer player from six landmarks and runs every race. In a browser,
`python3 -m http.server` here; `#demo-6-empire` starts a computer-driven swing from a landmark. Never test
with headless Chrome without a kill timer (it hangs on this Mac).

Building data: NYC Open Data, Building Footprints (`5zhs-2jue`) and Borough Boundaries (`gthc-hcne`).
