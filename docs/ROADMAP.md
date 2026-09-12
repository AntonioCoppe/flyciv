# ROADMAP

## M0 — weekend: empty but honest repo (this tree)

README, licenses, NOTICE, CI on a 20-neuron toy graph, fetch stub + hash check,
issue templates. Headless colony, wear/trails, adapter evolution, trainer mechanism
run on the **toy graph** so the civilization layer is testable without MaleCNS.

## M1 — week 1: one brain walks (local MaleCNS)

Fetch `male-cns:v1.0` the way fly-brain-minecraft does (anonymous Cypher or GCS).
Build a compact graph under `data/derived/` only. One hero: food odor → walk toward
food → eat. If real GRN/MN9 names are used, update HONESTY; otherwise keep **scripted**.

## M2 — week 2: colony + wear

4 heroes + 64 crowd, wear map, trail metric, generation counter, HUD.
Civilization events: `first_trail`, `first_store`.

## M3 — week 3–4: evolution

`lineages/*.json`, mutate / select / replace. Roles appear only if they survive.
Hand-written good-forager genome beats random on calories (already gated in tests).

## M4 — month 2: trainer tile

Surplus unlocks tile; tile writes child adapters; win-check for K generations.
`docs/RUNS.md` with seeds once someone replays “they invented training” for real.
v0 gates the **mechanism** plus a constructed/seeded win-check, not viral-scale
emergence on 176k-neuron heroes.

## M5 — later, optional

FlyGym body, AbijahKaj optic-lobe hero, Minecraft as a *client* of our colony server.
Do not make Doom the core loop.
