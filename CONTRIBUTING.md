# Contributing to flyciv

Thank you. This project is deliberately small: frozen brains, evolving adapters,
designed stigmergy, a trainer tile. Please keep it that way.

## Setup

```bash
python -m pip install -e ".[dev]"
pytest
flyciv smoke
```

CI runs `pytest` plus a ≤30 s smoke generation on the **20-neuron toy graph**.
Forks must stay green **without** downloading MaleCNS.

## Rules that will get a PR closed

- Replacing the graph with an MLP, or backprop through `W`
- Committing `data/raw/`, `*.flyb`, EM volumes, full synapse tables, meshes, or `.env`
- Mixing FlyWire female (often CC BY-NC) into the default path
- Minecraft / Doom / Beat Saber as the core loop
- Silent scripted cities passed off as emergence
- `$TOKEN`, memecoins, or “the fly is conscious / AGI / a living fly”
- Growing the default hero graph to “more neurons so it becomes smart”

## Honesty

If you add a pathway, update `docs/HONESTY.md`. If it uses real GRN/MN9 (or other)
names from a validated circuit, say so. Otherwise label it **scripted**.

World events → LIF activity → body programs stay labeled as in neurocraft-fly.

## Data

Fetch with `flyciv fetch --dataset male-cns:v1.0 --out data/derived/`.
Record hashes in the local manifest. Cite Berg et al., *Cell* 2026 and CC BY 4.0
on every derived file header. See `docs/PROVENANCE.md` and `DATA-LICENSE.md`.

If you paste fetch/LIF source from fly-brain-minecraft, fly.ai, or doomfly,
keep their copyright lines in the copied file **and** in `NOTICE.md`.

## Tests

- Drive shipped functions (engine, world, genome, colony, trainer, fetch-hash, win-check).
- Do not reimplement the code under test inside the test.
- Default every test to the toy graph.

## Issues

Use the templates: data-pipeline, engine, world, honesty-regression.

## License

Contributions are MIT for code. MaleCNS derivatives remain CC BY 4.0.
