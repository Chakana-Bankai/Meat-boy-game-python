from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DifficultyProfile:
    scalar: float
    saw_speed: float
    laser_cycle: float
    falling_delay: float
    patrol_speed: float


def difficulty_scalar(level_index: int, level_budget: int) -> float:
    return 0.9 + (level_index * 0.22) + (level_budget * 0.08)


def build_profile(level_index: int, level_budget: int) -> DifficultyProfile:
    scalar = max(1.0, difficulty_scalar(level_index, level_budget))
    return DifficultyProfile(
        scalar=scalar,
        saw_speed=0.9 * scalar,
        laser_cycle=max(0.5, 2.0 / scalar),
        falling_delay=max(0.2, 0.8 / scalar),
        patrol_speed=30.0 * scalar,
    )
