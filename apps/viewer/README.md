# viewer

```bash
flyciv watch                 # run a short city and open the HUD in your browser
flyciv view runs/watch       # ASCII snapshot; opens hud.html if present
```

HUD layout: world on the left, one hero spike raster on the right, timeline at
the bottom. Replay is the recorded sim, not a live pygame loop.

`flyciv watch` paints the constructed city by default so there is something to
see (roads + trainer tile). That city is a **designed rule**, labeled as such.
Use `--plain` for an unpainted random mill.
