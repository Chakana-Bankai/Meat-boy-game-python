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
    # Level 1..10 ramps strongly to feel ~3x harder
    progress = max(0.0, min(1.0, level_index / 9.0))
    budget_norm = max(0.1, min(1.0, level_budget / 10.0))
    return 1.0 + 2.0 * (progress * 0.65 + budget_norm * 0.35)


def build_profile(level_index: int, level_budget: int) -> DifficultyProfile:
    scalar = difficulty_scalar(level_index, level_budget)
    return DifficultyProfile(
        scalar=scalar,
        saw_speed=0.7 * scalar,
        laser_cycle=max(0.75, 2.2 / scalar),
        falling_delay=max(0.25, 1.0 / scalar),
        patrol_speed=25.0 * scalar,
    )
