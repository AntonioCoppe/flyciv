# PROVENANCE

Discipline copied from fly-brain-minecraft / doomfly: say which bytes you ran,
how you got them, and what you changed. Do not vendor the connectome.

## Toy graph (what CI and `flyciv smoke` run)

| Field | Value |
| --- | --- |
| id | `flyciv-toy-20-v1` |
| path | `packages/flyciv/brain/fixtures/toy20.json` |
| neurons | 20 |
| source | authored in this repo (MIT) |
| MaleCNS? | **no** |
| sugar circuit | **scripted** (see HONESTY.md) |
| weights | `W[post, pre] = n_syn * 0.275 mV * sign` (Shiu 2024 unitary synapse) |

Loader: `flyciv.brain.graph.load_graph`. Accepts this JSON, npz (`W`, `names`, `kinds`, `id`),
or a tiny FLYB binary (magic `FLYB`). `*.flyb` is gitignored; tests write FLYB to a temp file.

## MaleCNS v1.0 (optional local fetch)

| Field | Value |
| --- | --- |
| dataset | `male-cns:v1.0` |
| license | CC BY 4.0 |
| cite | Berg et al., *Cell* 189(18):5504–5526 (2026) doi:10.1016/j.cell.2026.08.015 |
| page | https://male-cns.janelia.org/ |
| download | https://male-cns.janelia.org/download/ |
| neuPrint | https://neuprint.janelia.org/ dataset `male-cns:v1.0` |
| GCS | `gs://flyem-male-cns/v1.0/` |
| git | **never** — only `data/derived/` (gitignored) |

### Recipe (fly-brain-minecraft pattern)

1. Prefer published tables / anonymous Cypher. Do not commit a neuPrint token.
2. Compact: keep edges, drop EM volumes and meshes. Optional ≥5-synapse threshold
   (the Minecraft mod’s ~23 MB FLYB idea).
3. Write npz or FLYB under `data/derived/`.
4. SHA256 the compact file. `flyciv fetch` refuses a bit-flipped copy.
5. Header every derived file with MaleCNS, CC BY 4.0, Berg et al. 2026.

`flyciv fetch --dataset male-cns:v1.0 --out data/derived/` writes `DOWNLOAD.md` and
hash-checks files already in that directory. Full table pull is network-dependent and
**not** required for CI.

Anonymous neuPrint POST (as of 2026-09, the hobbyist pattern):

```
POST https://neuprint.janelia.org/api/custom/custom?dataset=male-cns:v1.0
```

If Janelia requires a token, keep the hash-check stub and record the failure; do not
vendor data to make CI green.

## Engine parameters

`flyciv.brain.params` — Shiu et al., *Nature* 634:210–219 (2024).
We reimplemented LIF from those published numbers. We did **not** copy
fly-brain-minecraft or fly.ai source into this tree (see `NOTICE.md`).

## Adapter

Genome schema: `flyciv.adapter.genome`. Lineage JSON under `runs/<id>/lineages/`
(gitignored). This is the only evolving object.

## Hashes in-repo

Unit-test stub `packages/flyciv/data/fixtures/sha256-stub.txt`  
SHA256 `0e81927c8fe8835a2d9e6c5f1d6cceba5bc6d8687403aa584a86528a71cb1752`  
That file is **not** MaleCNS. It exists so fetch-hash is tested without a gigabyte download.
