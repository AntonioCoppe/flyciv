# flyciv for Minecraft 1.21.1

A Fabric mod you can actually drop in and walk around.

Four **hero** bees (stand-in fly bodies) walk the cardinal axes. Sixty-four crowd bees mill the nest. Gold blocks appear under their feet. Generation 3 lights the nest (trainer ON). Generation 4 spawns a gold-named **child** at the nest.

This is the **showcase** walk: labeled choreography, not 176k-neuron LIF. Frozen-brain honesty still applies. Vanilla bees are the bodies so you can install this without a 23 MB connectome jar.

## Install (Prism / official launcher)

1. Minecraft **Java 1.21.1**
2. [Fabric Loader](https://fabricmc.net/use/) 0.16+
3. [Fabric API](https://modrinth.com/mod/fabric-api) for 1.21.1
4. Copy `build/libs/flyciv-mc-0.1.0.jar` into `.minecraft/mods/`
5. New world (creative is easiest), then:

```
/flyciv start
```

Stand on the black platform. Gold = wear-roads. Blue nest → sea lantern when the trainer unlocks. `/flyciv stop` clears the bees.

Build from this folder (JDK 21):

```bash
export JAVA_HOME=$(/usr/libexec/java_home -v 21)
./gradlew build
```

Jar lands in `build/libs/flyciv-mc-0.1.0.jar`.

## Commands

| Command | What it does |
| --- | --- |
| `/flyciv start` | Build the 48×48 colony at your feet and run 6 generations |
| `/flyciv stop` | Remove the bees |

## Credit

Minecraft fly *brains* live in [blendi-remade/fly-brain-minecraft](https://github.com/blendi-remade/fly-brain-minecraft) (MIT, MaleCNS CC BY 4.0). This jar is the **civilization layer** in vanilla mobs so a friend can join without compiling that mod.
