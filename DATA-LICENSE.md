# Data license

Our code is MIT (see `LICENSE`). **Connectome data is not.**

## MaleCNS (default dataset)

The adult male *Drosophila* central nervous system connectome **male-cns:v1.0** is published by
HHMI Janelia FlyEM, the University of Cambridge (Dept. of Zoology), the MRC Laboratory of
Molecular Biology, and Google Research.

- License: [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)
- Dataset id: `male-cns:v1.0`
- Project page: https://male-cns.janelia.org/
- Download: https://male-cns.janelia.org/download/
- neuPrint: https://neuprint.janelia.org/?dataset=male-cns%3Av1.0
- Object store: `gs://flyem-male-cns/v1.0/`
- Paper: Berg et al., *Cell* 189(18):5504–5526 (2026). doi:10.1016/j.cell.2026.08.015

You must give appropriate credit when you use MaleCNS or any graph derived from it.

## How flyciv modifies MaleCNS (when you fetch it)

flyciv **does not vendor** EM volumes, full synapse tables, or meshes. A local fetch may:

1. Query neuPrint (`male-cns:v1.0`) and/or read published GCS tables.
2. Compact the graph (threshold synapses, CSR/npz, optional FLYB) under gitignored `data/derived/`.
3. Record SHA256 hashes and the transform recipe in `docs/PROVENANCE.md` / a local manifest.

Those compact graphs are still MaleCNS derivatives and remain **CC BY 4.0**. Do not strip attribution.
Every derived file header should name MaleCNS, CC BY 4.0, and Berg et al., *Cell* 2026.

## What this repo commits

- A **20-neuron toy graph** (`flyciv-toy-20-v1`) authored here as a stand-in for tests and `flyciv smoke`.
  It is **not** MaleCNS. It is MIT like the rest of our code.
- A **soma-location subsample** (`packages/flyciv/viz/fixtures/malecns_somas_viz.npz`) for the spectator
  brain view: xyz + superclass only, CC BY 4.0, Berg et al. *Cell* 2026. Not meshes, not synapses.
- Hash-check fixtures of a few dozen bytes for unit tests. Not connectome data.

## Do not mix FlyWire female data into the default path

FlyWire / FAFB female releases are often **CC BY-NC**. flyciv’s default dataset is MaleCNS (CC BY 4.0).
Do not add FlyWire female graphs to the default fetch, smoke, or CI path.

## Shiu 2024 parameters

Leaky integrate-and-fire constants used by the engine follow Shiu et al., *Nature* 634:210–219 (2024)
doi:10.1038/s41586-024-07763-9 (the parameter set commonly reused by hobbyist fly-brain engines).
That paper’s model is a scientific result to cite; it is not a data dump in this repository.
