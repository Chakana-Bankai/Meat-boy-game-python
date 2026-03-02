from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from server.models import Run
from shared.schemas import RunPayload


def create_run(db: Session, payload: RunPayload) -> Run:
    run = Run(**payload.model_dump())
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def leaderboard(db: Session, level_id: str, limit: int = 20) -> list[Run]:
    stmt = (
        select(Run)
        .where(Run.level_id == level_id)
        .order_by(Run.best_time_ms.asc(), Run.deaths.asc(), Run.created_at.asc())
        .limit(limit)
    )
    return list(db.scalars(stmt))
