from __future__ import annotations

from importlib.resources import files

# Tiny fixture used by unit tests. NOT MaleCNS.
STUB_NAME = "sha256-stub.txt"
STUB_SHA256 = "0e81927c8fe8835a2d9e6c5f1d6cceba5bc6d8687403aa584a86528a71cb1752"

MALE_CNS_V1 = {
    "dataset": "male-cns:v1.0",
    "license": "CC BY 4.0",
    "cite": "Berg et al., Cell 189(18):5504-5526 (2026) doi:10.1016/j.cell.2026.08.015",
    "page": "https://male-cns.janelia.org/",
    "download": "https://male-cns.janelia.org/download/",
    "neuprint": "https://neuprint.janelia.org/",
    "neuprint_dataset": "male-cns:v1.0",
    "gcs": "gs://flyem-male-cns/v1.0/",
    "neuprint_custom": "https://neuprint.janelia.org/api/custom/custom?dataset=male-cns:v1.0",
}


def stub_path() -> str:
    return str(files("flyciv.data.fixtures").joinpath(STUB_NAME))


DOWNLOAD_MD = """# Download male-cns:v1.0 (CC BY 4.0)

This directory is gitignored. Do not commit EM volumes, full synapse tables, or meshes.

## Cite

Berg, S. et al. Sexual dimorphism in the complete Drosophila male central nervous system
connectome. Cell 189, 5504–5526 (2026). doi:10.1016/j.cell.2026.08.015

HHMI Janelia FlyEM + University of Cambridge + MRC LMB + Google Research.
License: CC BY 4.0. https://male-cns.janelia.org/

## How to fetch (fly-brain-minecraft discipline)

1. Published tables: https://male-cns.janelia.org/download/
2. GCS: `gs://flyem-male-cns/v1.0/` (e.g. connectome-data/flat-connectome/)
3. neuPrint dataset `male-cns:v1.0` — prefer anonymous Cypher; do not commit tokens.
   POST https://neuprint.janelia.org/api/custom/custom?dataset=male-cns:v1.0
4. Compact to npz or FLYB here. Optional: drop edges with <5 synapses.
5. `flyciv fetch` SHA256-checks files listed in SHA256SUMS (if present).

Do not mix FlyWire female (often CC BY-NC) into this default path.

Header every derived file with: MaleCNS v1.0, CC BY 4.0, Berg et al. Cell 2026.
"""
