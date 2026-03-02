from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class RunPayload(BaseModel):
    level_id: str = Field(min_length=1, max_length=64)
    player_name: str = Field(default="player", max_length=64)
    best_time_ms: int = Field(ge=1)
    deaths: int = Field(ge=0)
    seed: int
    replay_data: str = Field(min_length=1)


class RunRecord(RunPayload):
    id: int
    created_at: datetime


class LeaderboardEntry(BaseModel):
    player_name: str
    best_time_ms: int
    deaths: int
    created_at: datetime
