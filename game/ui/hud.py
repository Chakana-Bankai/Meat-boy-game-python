from __future__ import annotations

import pygame
import pygame.freetype

from game import config


class HUDRenderer:
    def __init__(self) -> None:
        self.font = pygame.freetype.SysFont("Consolas", 10)

    @staticmethod
    def fmt_time(seconds: float) -> str:
        ms = int((seconds % 1) * 100)
        total = int(seconds)
        return f"{total // 60:02d}:{total % 60:02d}.{ms:02d}"

    def draw(
        self,
        surface: pygame.Surface,
        *,
        current_time: float,
        best_time_ms: int | None,
        deaths: int,
        attempts: int,
        paused: bool,
        recording_ghost: bool,
        online: bool,
        progress: float,
        death_msg: str,
        debug_lines: list[str],
    ) -> None:
        if not config.HUD_ENABLED:
            return
        x, y = config.HUD_POS
        c = config.PALETTE
        pygame.draw.rect(surface, c["panel"], pygame.Rect(x - 2, y - 2, 170, 64))
        status = "Paused" if paused else ("Recording Ghost" if recording_ghost else "Playing")
        best_text = "--:--.--" if best_time_ms is None else self.fmt_time(best_time_ms / 1000)
        lines = [
            f"Time {self.fmt_time(current_time)}",
            f"Best {best_text}",
            f"Deaths {deaths} Retry {attempts}",
            f"{status} | {'ONLINE' if online else 'OFFLINE'}",
        ]
        for i, line in enumerate(lines):
            self.font.render_to(surface, (x, y + i * 12), line, c["text"])

        if death_msg:
            self.font.render_to(surface, (x, y + 50), death_msg, c["danger"])

        if config.SHOW_PROGRESS_BAR:
            bar_y = y + 60
            pygame.draw.rect(surface, (40, 40, 55), pygame.Rect(x, bar_y, 160, 4))
            pygame.draw.rect(surface, c["accent"], pygame.Rect(x, bar_y, int(160 * max(0.0, min(1.0, progress))), 4))

        for i, dbg in enumerate(debug_lines):
            self.font.render_to(surface, (5, 164 - i * 10), dbg, c["warn"])
