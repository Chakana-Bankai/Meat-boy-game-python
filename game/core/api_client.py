from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx

from shared.schemas import RunPayload


class ApiClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000", fallback_path: Path | None = None) -> None:
        self.base_url = base_url
        self.fallback_path = fallback_path or Path("game_local_runs.json")

    def submit_run(self, payload: RunPayload) -> None:
        try:
            r = httpx.post(f"{self.base_url}/runs", json=payload.model_dump(), timeout=1.5)
            r.raise_for_status()
            self.sync_fallback()
        except Exception:
            self._append_fallback(payload.model_dump())

    def get_leaderboard(self, level_id: str) -> list[dict[str, Any]]:
        try:
            r = httpx.get(f"{self.base_url}/leaderboard/{level_id}", timeout=1.0)
            r.raise_for_status()
            return r.json()
        except Exception:
            return []

    def _append_fallback(self, run: dict[str, Any]) -> None:
        existing = []
        if self.fallback_path.exists():
            existing = json.loads(self.fallback_path.read_text(encoding="utf-8"))
        existing.append(run)
        self.fallback_path.write_text(json.dumps(existing), encoding="utf-8")

    def sync_fallback(self) -> None:
        if not self.fallback_path.exists():
            return
        pending = json.loads(self.fallback_path.read_text(encoding="utf-8"))
        left: list[dict[str, Any]] = []
        for run in pending:
            try:
                r = httpx.post(f"{self.base_url}/runs", json=run, timeout=1.0)
                r.raise_for_status()
            except Exception:
                left.append(run)
        if left:
            self.fallback_path.write_text(json.dumps(left), encoding="utf-8")
        else:
            self.fallback_path.unlink(missing_ok=True)
