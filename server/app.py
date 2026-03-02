from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
import uvicorn

from server.database import Base, SessionLocal, engine
from server.repository import create_run, leaderboard
from shared.logging_config import configure_logging
from shared.schemas import LeaderboardEntry, RunPayload, RunRecord

configure_logging()
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Meat Boy Local Leaderboard API")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/runs", response_model=RunRecord)
def post_run(payload: RunPayload, db: Session = Depends(get_db)) -> RunRecord:
    try:
        run = create_run(db, payload)
        return RunRecord(
            id=run.id,
            level_id=run.level_id,
            player_name=run.player_name,
            best_time_ms=run.best_time_ms,
            deaths=run.deaths,
            seed=run.seed,
            replay_data=run.replay_data,
            created_at=run.created_at,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid run payload: {exc}") from exc


@app.get("/leaderboard/{level_id}", response_model=list[LeaderboardEntry])
def get_leaderboard(level_id: str, db: Session = Depends(get_db)) -> list[LeaderboardEntry]:
    return [
        LeaderboardEntry(
            player_name=r.player_name,
            best_time_ms=r.best_time_ms,
            deaths=r.deaths,
            created_at=r.created_at,
        )
        for r in leaderboard(db, level_id)
    ]


if __name__ == "__main__":
    uvicorn.run("server.app:app", host="127.0.0.1", port=8000, reload=False)
