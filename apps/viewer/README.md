# viewer

```bash
flyciv watch                 # run a short city and open the HUD in your browser
flyciv view runs/watch       # ASCII snapshot; opens hud.html if present
```

Split-screen spectator (the X-clip layout, not Neuroglancer):

- **W world** — isometric colony grid (Minecraft-without-Minecraft)
- **B brain** — MaleCNS soma point cloud; toy-LIF spikes light 20 stand-in cells + a labeled halo. Drag to orbit.
- **H neuroscope** — raster, a few named rates, 2×2 food “eye”

Keys: `W` / `B` / `H` / space. Replay of a recorded run, read-only.

`flyciv watch` defaults to 6 generations × 80 steps and paints the constructed
city so the colony is visible. That city is a **designed rule**, labeled as such.
Use `--plain` for an unpainted random mill. Playback is slow and does not loop
unless you check **loop**.
