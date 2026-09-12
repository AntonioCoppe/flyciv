# ADR 0002 — Frozen graph, small adapter

The connectome `W` is frozen. Evolution is a small vector: encoder gains, readout
weights, dopamine routing, role bias (~46 parameters). This is the flm lesson
(~278k was already “tiny”; we go smaller because the world is a grid).

A PR that backprops `W` or swaps the graph for an MLP is a different project.
