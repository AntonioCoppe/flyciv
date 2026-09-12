from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CivEvent:
    generation: int
    step: int
    name: str

    def as_dict(self) -> dict:
        return {"generation": self.generation, "step": self.step, "name": self.name}
