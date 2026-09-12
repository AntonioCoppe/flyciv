# flyciv

**code: MIT · data: CC BY 4.0 · dataset: male-cns:v1.0**

This is not a living fly and not AGI.

The connectome is frozen. Only adapters evolve.

City / roads / trainer are designed rules, labeled as such.

Data is downloaded, not vendored.

Cite Berg et al., *Cell* 189(18):5504–5526 (2026) doi:10.1016/j.cell.2026.08.015 for MaleCNS
(`male-cns:v1.0`; https://male-cns.janelia.org/). Cite Shiu et al., *Nature* 634:210–219 (2024)
doi:10.1038/s41586-024-07763-9 for the LIF constants. See `CITATION.cff` and `NOTICE.md`.

---

A colony of frozen fruit-fly brains that wear roads into a city, then invent the job of training flies.

Not a new connectome. Not a claim that flies become people. A stack that reuses what already exists
and only writes the missing middle: **colony**, **inheritance**, **trail-wear**, **trainer tile**.

```
MaleCNS graph (theirs, CC BY 4.0)
        ↓
LIF engine (Shiu 2024 constants; patterns from hobbyist engines)
        ↓
plastic adapter + dopamine map (ours; this is what evolves)
        ↓
grid world + wear (ours; ant/stigmergy ideas)
        ↓
trainer tile (ours; same job as today's hobbyist demos)
```

**Win condition:** a living city keeps a tile whose only output is a new fly adapter, for several
generations, without collapsing.

Janelia owns the map. Hobbyists own the engines. We own the civilization layer.

## What this is not

- A fly that “becomes superintelligent” by adding neurons
- Silent scripted cities passed off as emergence (roads and the trainer are **labeled designed rules**)
- Shipping the connectome inside git
- Minecraft, Doom, or Beat Saber as the product
- Training the full ~25M-edge graph by backprop every tick
- `$TOKEN`, memecoins, or a claim that the fly is conscious

If a PR makes the graph bigger or replaces it with an MLP, it is a different project. Close it.

## Install

```bash
python -m pip install -e ".[dev]"
```

No MaleCNS download is required for tests or smoke.

```bash
flyciv smoke                 # 20-neuron toy graph, no download
flyciv run --heroes 4 --crowd 64 --generations 20 --seed 7
flyciv report runs/latest    # trails, calories, whether trainer unlocked
flyciv watch                 # 3D fruit flies on the colony (default)
flyciv watch --lab           # 2D dashboard

Minecraft (people can actually join): see `apps/minecraft/README.md`.
Drop `apps/minecraft/dist/flyciv-mc-0.1.0.jar` into Fabric 1.21.1 + Fabric API, then `/flyciv start`.
flyciv watch --honest        # science run, same Watch skin
flyciv watch --lab           # cream Lab dashboard
flyciv cinema                # 13s 16:9 + 9:16 clip from the last Watch run
flyciv fetch --dataset male-cns:v1.0 --out data/derived/
```

`flyciv fetch` writes download instructions and SHA256-checks files you already have. It does not
commit a gigabyte of synapses. CI stays green on the toy graph.

## How it runs (v0, laptop)

- **4 hero flies:** full LIF on the committed 20-neuron toy graph (or a local FLYB/npz if you fetched
  MaleCNS). Heroes are the ones you screenshot.
- **64–256 crowd flies:** no spike graph. They carry an adapter genome and cheap sensors (local food,
  local wear, nearby fly). Crowd is the ant farm.
- **What evolves:** a small vector — encoder gains, readout weights, dopamine routing, role bias.
  Mutation is noise on that vector. The frozen `W` is never trained.
- **World:** 128×128 grid. Wear, trails, roads, blocks, a trainer tile unlocked by surplus calories.
  See `docs/HONESTY.md` for biological vs scripted.

## Cite

**MaleCNS (required if you use the dataset or derived graphs):**

Berg, S. et al. Sexual dimorphism in the complete *Drosophila* male central nervous system connectome.
*Cell* **189**, 5504–5526 (2026). https://doi.org/10.1016/j.cell.2026.08.015

Dataset: `male-cns:v1.0` — HHMI Janelia FlyEM, University of Cambridge, MRC LMB, Google Research.
License: CC BY 4.0. https://male-cns.janelia.org/

**LIF parameters:**

Shiu, P. K. et al. A *Drosophila* computational brain model reveals sensorimotor processing.
*Nature* **634**, 210–219 (2024). https://doi.org/10.1038/s41586-024-07763-9

**This software:** see `CITATION.cff`.

## Repo layout

```
packages/flyciv/          # installable Python package (data, brain, adapter, world, colony, viz)
packages/flyciv-*/        # logical package notes (same code)
apps/headless/            # CLI is `flyciv`
apps/viewer/              # ASCII HUD; pygame optional later
tests/
docs/                     # HONESTY, PROVENANCE, ROADMAP, ADR
third_party/
```

## License

- **Our code:** MIT (`LICENSE`)
- **MaleCNS data:** CC BY 4.0 (`DATA-LICENSE.md`)
- Credits: `NOTICE.md`
