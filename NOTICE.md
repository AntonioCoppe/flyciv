# NOTICE

flyciv is original software under the MIT License (see `LICENSE`).

This file records credit. Janelia owns the map. Hobbyists own the engines we learned from.
We own the civilization layer (colony, adapter genome, wear-roads, trainer tile).

## MaleCNS data (CC BY 4.0) — not in git

The default connectome is **male-cns:v1.0**:

> Sexual dimorphism in the complete *Drosophila* male central nervous system connectome.
> Berg, S. et al. *Cell* 189, 5504–5526 (2026). doi:10.1016/j.cell.2026.08.015

Produced by:

- HHMI Janelia Research Campus, FlyEM Project Team
- University of Cambridge, Department of Zoology
- MRC Laboratory of Molecular Biology, Neurobiology Division
- Google Research (neural mapping)

Project: https://male-cns.janelia.org/  
License: https://creativecommons.org/licenses/by/4.0/

Do not commit EM images, full synapse tables, or meshes from this dataset.

## LIF parameters (cite, do not pretend we measured them)

Shiu, P. K. et al. A *Drosophila* computational brain model reveals sensorimotor processing.
*Nature* 634, 210–219 (2024). doi:10.1038/s41586-024-07763-9

Constants in `flyciv.brain.params` follow that paper’s widely reused LIF set
(τ_m 20 ms, τ_syn 5 ms, V_rest/reset −52 mV, V_th −45 mV, refractory 2.2 ms,
delay 1.8 ms, 0.275 mV/synapse).

## Hobbyist engines — ideas we reused (no source copied into this tree)

We reimplemented patterns from published code and docs. **No files were copied** from
these repositories into flyciv, so their copyright headers do not appear in our `.py` files.
If a future PR pastes their fetch/LIF code, that PR must add the upstream copyright lines
here and in the copied file.

| Project | What we took | License | URL |
| --- | --- | --- | --- |
| blendi-remade/fly-brain-minecraft | Engine-independent LIF + FLYB/CSR + neuPrint fetch + Shiu params + real cell-type sensors. Copy the *brain package pattern*, not the Fabric mod. | Code MIT, data CC BY 4.0 | https://github.com/blendi-remade/fly-brain-minecraft |
| alextitonis/fly.ai | Frozen-brain-as-reservoir: encoder → full graph → descending-neuron readout. Batch of flies. We do **not** ship token materials. | MIT + CC BY data | https://github.com/alextitonis/fly.ai |
| nftechie/doomfly | Provenance files, dopamine-on-PPL1 as an *adapter* idea, honesty docs (“learning not demonstrated”). Discipline, not the Doom loop. | MIT | https://github.com/nftechie/doomfly |
| nftechie/flm | Proof that only a tiny adapter should be trained. Same rule here. | see upstream | https://github.com/nftechie/flm |
| AbijahKaj/fruit-fly-brain-research | Optic-lobe closed loop in the browser — optional later “hero fly sees,” not v0. | MIT + CC BY derived graph | https://github.com/AbijahKaj/fruit-fly-brain-research |
| evnsnclr/neurocraft-fly-public | Design note: world events → activity → scripted body programs. We keep that split labeled. | MIT landing page | https://github.com/evnsnclr/neurocraft-fly-public |
| NeLy-EPFL/flygym | Optional later 3D body. Too heavy for v0. | Apache-2.0 | https://github.com/NeLy-EPFL/flygym |
| FLY ATLAS | Optional viewer, not the sim. | their viz + CC BY data | https://fly-atlas.vercel.app |

## Stigmergy / roads

City roads are **designed ant/stigmergy rules** on fly bodies (pheromone-like wear), not a
copied codebase. Cite the Harvard RAnts / stigmergy literature in papers; do not drop
their source into this repo.

## What this project is not

Not a living fly. Not AGI. Not a claim that flies become people. Not a memecoin.
The connectome is frozen; only adapters evolve.
