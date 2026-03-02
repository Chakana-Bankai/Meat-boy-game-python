from __future__ import annotations

import json
import queue
import threading
from pathlib import Path
from typing import Any

import httpx


class NetworkClient:
    def __init__(self, base_url: str, fallback_path: Path | None = None) -> None:
        self.base_url = base_url
        self.fallback_path = fallback_path or Path("game_local_runs.json")
        self.jobs: queue.Queue[tuple[str, Any]] = queue.Queue()
        self.results: queue.Queue[tuple[str, Any]] = queue.Queue()
        self.online = False
        self._stop = False
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def _worker(self) -> None:
        while not self._stop:
            try:
                job, payload = self.jobs.get(timeout=0.1)
            except queue.Empty:
                continue
            try:
                if job == "ping":
                    r = httpx.get(f"{self.base_url}/health", timeout=0.6)
                    self.online = r.status_code == 200
                elif job == "post_run":
                    r = httpx.post(f"{self.base_url}/runs", json=payload, timeout=1.2)
                    r.raise_for_status()
                    self.online = True
                elif job == "leaderboard":
                    level_id = payload
                    r = httpx.get(f"{self.base_url}/leaderboard/{level_id}", timeout=1.0)
                    r.raise_for_status()
                    self.results.put(("leaderboard", r.json()))
                    self.online = True
                elif job == "sync":
                    self._sync_file()
            except Exception:
                self.online = False
                if job == "post_run":
                    self._append_fallback(payload)
            finally:
                self.jobs.task_done()

    def enqueue_ping(self) -> None:
        self.jobs.put(("ping", None))

    def enqueue_post_run(self, payload: dict[str, Any]) -> None:
        self.jobs.put(("post_run", payload))

    def enqueue_leaderboard(self, level_id: str) -> None:
        self.jobs.put(("leaderboard", level_id))

    def try_pop_leaderboard(self) -> list[dict[str, Any]] | None:
        try:
            kind, data = self.results.get_nowait()
            return data if kind == "leaderboard" and isinstance(data, list) else []
        except queue.Empty:
            return None

    def _append_fallback(self, run: dict[str, Any]) -> None:
        runs = []
        if self.fallback_path.exists():
            runs = json.loads(self.fallback_path.read_text(encoding="utf-8"))
        runs.append(run)
        self.fallback_path.write_text(json.dumps(runs), encoding="utf-8")

    def _sync_file(self) -> None:
        if not self.fallback_path.exists():
            return
        runs = json.loads(self.fallback_path.read_text(encoding="utf-8"))
        left = []
        for run in runs:
            try:
                r = httpx.post(f"{self.base_url}/runs", json=run, timeout=1.0)
                r.raise_for_status()
            except Exception:
                left.append(run)
        if left:
            self.fallback_path.write_text(json.dumps(left), encoding="utf-8")
        else:
            self.fallback_path.unlink(missing_ok=True)

    def queue_size(self) -> int:
        return self.jobs.qsize()
