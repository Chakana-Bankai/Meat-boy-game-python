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
    spikes: list[tuple[int, int, int, int]]
    rails: list[dict]
    lasers: list[dict]
    falling_blocks: list[dict]
    patrols: list[dict]
    jump_pads: list[tuple[int, int, int, int]]
    difficulty_budget: int
    chapter: str
    motif: str
    lore: str
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
        spikes=[tuple(s) for s in data.get("spikes", [])],
        rails=data.get("rails", []),
        lasers=data.get("lasers", []),
        falling_blocks=data.get("falling_blocks", []),
        patrols=data.get("patrols", []),
        jump_pads=[tuple(v) for v in data.get("jump_pads", [])],
        difficulty_budget=data.get("difficulty_budget", 1),
        chapter=data.get("chapter", "Unknown"),
        motif=data.get("motif", ""),
        lore=data.get("lore", ""),
        seed=data.get("seed", 1337),
    )
