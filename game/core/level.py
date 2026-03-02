from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class LevelData:
    level_id: str
    width: int
    height: int
    solids: list[list[int]]
    one_way: list[list[int]]
    spawn: tuple[int, int]
    goal: tuple[int, int, int, int]
    saws: list[tuple[int, int, int]]
    spikes: list[tuple[int, int, int, int]]
    seed: int


def load_level(path: Path) -> LevelData:
    data = json.loads(path.read_text(encoding="utf-8"))
    return LevelData(
        level_id=data["level_id"],
        width=data["width"],
        height=data["height"],
        solids=data["solids"],
        one_way=data.get("one_way", []),
        spawn=tuple(data["spawn"]),
        goal=tuple(data["goal"]),
        saws=[tuple(s) for s in data.get("saws", [])],
        spikes=[tuple(s) for s in data.get("spikes", [])],
        seed=data.get("seed", 1337),
    )
