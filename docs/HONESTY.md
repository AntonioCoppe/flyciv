# HONESTY

This is not a living fly and not AGI. The connectome is frozen. Only adapters evolve.
City / roads / trainer are designed rules, labeled as such.

doomfly’s public notes are the model: say what was demonstrated, and what was not.

## Biological vs scripted

| Piece | Kind | Notes |
| --- | --- | --- |
| MaleCNS graph (when fetched) | **biological data** | Berg et al., *Cell* 2026. CC BY 4.0. Downloaded, not vendored. |
| Toy graph `flyciv-toy-20-v1` | **scripted stand-in** | 20 neurons authored here for CI/smoke. Not MaleCNS. Not a connectome. |
| LIF constants (τ_m, τ_syn, V_rest, V_th, refrac, delay, 0.275 mV/syn) | **published model params** | Shiu et al., *Nature* 2024. Discrete `dt` rounding is a sim approximation. |
| Frozen `W` | **data / frozen** | Never trained. No backprop. Heroes load `W` and leave it alone. |
| Sugar → walk on the toy graph | **scripted** | Toy cells are named `sugar_sensor`, `dn_walk`, `mn_forward`. They are **not** GRN/MN9. We did **not** port a validated sugar circuit. |
| Encoder gains (sugar / light / loom / bitter → sensory types) | **ours, evolving** | Adapter genome. Not biological weights. |
| Readout (DN/motor rates → walk, turn, linger, follow) | **ours, evolving** | Reservoir-style readout, fly.ai pattern. |
| Dopamine routing onto PPL1-style cells | **ours, evolving** | Named after PPL1 as in doomfly’s *idea*. Toy cells `ppl1_reward` / `ppl1_punish` are stand-ins, not reconstructed PPL1. Learning on `W` is **not** demonstrated. |
| Role bias (forage / guard / nurse / scout) | **ours, evolving** | A prior on actions. Roles are **not painted on** the map; they appear only if the bias survives selection. |
| Crowd flies | **scripted cheap body** | No spike graph. Local food / wear / nearby-fly sensors + the same genome. |
| Body programs (walk, turn, linger, follow, chemotaxis threshold, return-to-nest when full) | **scripted** | neurocraft-fly split: world events → activity → **scripted body programs**. |
| 128×128 food / brood | **designed world** | Patches respawn; brood cells need visits. Not a physics body. |
| Wear += 1 per occupancy | **designed stigmergy** | Ant/RAnt idea, our rule. |
| Trail = high wear + food at both ends | **designed rule** | See `flyciv.world.stigmergy`. |
| Road = durable trail after makers leave | **designed rule** | Wear can harden to a road. |
| Block = 3-road junction + store + brood | **designed rule** | City morphology, not self-described by the flies. |
| Surplus → trainer tile | **designed rule** | Not an LLM inside the fly. Inner eval + `write_child_adapter`. |
| Selection / mutation | **designed evolution** | Fitness = nest calories + brood adults + trail stability + trainer success. |
| Win-check | **designed metric** | City + roads + live trainer + K generations without collapse. |
| 3D fly bodies (`world3d.html`) | **designed viz** | Three.js fruit-fly meshes (eyes, wings, striped abdomen, legs). Not NeuroMechFly physics and not Minecraft. Crowd is instanced copies of the same mesh. |
| Watch skin vs Lab skin | **designed viz** | Watch default is the 3D fly scene. `spectator.html` is the 2D dashboard. |
| Showcase run (`flyciv watch`) | **scripted choreography** | 4 heroes walk the cardinal axes; wear is overcranked; trainer unlock is forced at generation 3 if surplus is short. Labeled showcase vs `--honest`. Not emergence. |
| Spectator world camera | **designed viz** | Isometric grid of the colony. Not Minecraft. |
| Spectator brain view (soma cloud) | **data + scripted mapping** | Point cloud is a MaleCNS `somaLocation` subsample (CC BY 4.0). Spikes come from the **20-neuron toy LIF**, mapped onto 20 stand-in somata plus a nearest-neighbor halo. This is not 176k cells firing. |
| Neuroscope / “eye” | **scripted HUD** | Raster + a few toy-cell rates. The 2×2 “eye” is local food sensors, not 1,771 optic-lobe columns. |

## Split we keep labeled (neurocraft-fly)

1. **World events** — food odor, loom, brood, wear, nearby fly.
2. **Activity** — LIF spikes on heroes; genome features on crowd.
3. **Body programs** — discrete walk / turn / linger / follow, plus chemotaxis when sugar encoder gain is high enough.

If a PR wires a real GRN→MN9 sugar circuit from MaleCNS, change this table and say the pathway follows that circuit. Until then it is scripted.

## Learning

We mutate a ~46-parameter adapter. We do **not** demonstrate that the frozen brain learned.
PPL1-style injection changes *current*, not `W`.
