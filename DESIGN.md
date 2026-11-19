# Manhattan Swinger: design

A version of City Swinger in real Manhattan (Simon, 2026-11-19: "I want to do a version of it and call it manhattan swinger and build as much of manhattan as possible to be swingable"). Same engine, controls and hero as City Swinger (`SimonSoliloquy/city-swinger`); this file holds only what differs. Where a later ruling disagrees, the later one wins.

## The city
- **All of Manhattan, every building swingable.** 45,036 buildings from NYC Open Data's Building Footprints (`5zhs-2jue`, updated weekly), each its real outline (simplified to within about 0.6 m) extruded to its real roof height, standing on the real ground height. 136 footprints with no usable height are left out. The island's shape, the parks and the other boroughs come from Borough Boundaries (`gthc-hcne`).
- Everything loads at the start (about 2 MB). Blocks of 200 m are built around you as you go: about 1.3 km of city in view, roughly 70,000 triangles near Times Square.
- Roofs are flat boxes (LOD1). The real roof shapes, spires and the Empire State's mast are not in this data; the city's 3D model has full roof detail for only about 100 buildings (Atlas, NYC datasets research, 2026-11-18).
- `tools/build_manhattan.py` rebuilds `data/` from fresh downloads (instructions inside); `data-raw/` is not committed.

## Rulings from the interview (Simon, 2026-11-19)
- **Below you:** real streets. Land on a street or a roof and keep running, then swing up again. Only the rivers set you back: a splash, and you are back on the last roof or street you stood on. (No falling to an ending.)
- **Free roam, plus landmark races.** Free roam has no score or timer. Races are timed runs between landmarks, with a beam of light at each checkpoint, an arrow pointing to it, and best times on the shared leaderboard, one board per race.
- **Sunset over the Hudson:** the same sky as City Swinger, with the sun setting in the real west, over New Jersey. The moon rises in the east.
- **Start where you pick on a map** of Manhattan (free roam). You start in the air over the street near that point, below the tall buildings around, moving north, so there is always something to swing from. Races start at their first landmark, facing the next.

## Races (data/manhattan.json `races`)
Empire State to Chrysler · Times Square to Bethesda Fountain · One World Trade to Washington Square · Flatiron to Empire State · the Battery to One World Trade · Washington Square to Union Square to Flatiron · Hudson Yards to Times Square to Rockefeller Center to Grand Central · Brooklyn Bridge to One World Trade to Empire State. A checkpoint counts within 35 m of the landmark, at any height. A splash keeps the clock running.

## Hosting
Repo `SimonSoliloquy/manhattan-swinger`, Vercel, live at https://manhattan-swinger.vercel.app; a push to `main` deploys. Boards `manhattan-swinger-r0` … `r7` on the shared Worker (score = 1,000,000 minus hundredths of a second).
