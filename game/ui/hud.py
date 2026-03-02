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
        mm = total // 60
        ss = total % 60
        return f"{mm:02d}:{ss:02d}.{ms:02d}"

    def draw(self, surface: pygame.Surface, *, current_time: float, best_time_ms: int | None, deaths: int, attempts: int,
             paused: bool, recording_ghost: bool, online: bool, progress: float) -> None:
        if not config.HUD_ENABLED:
            return
        x, y = config.HUD_POS
        c = config.PALETTE
        panel = pygame.Rect(x - 2, y - 2, 160, 56)
        pygame.draw.rect(surface, c["panel"], panel)
        status = "Paused" if paused else ("Recording Ghost" if recording_ghost else "Playing")
        net = "ONLINE" if online else "OFFLINE"
        best_text = "--:--.--" if best_time_ms is None else self.fmt_time(best_time_ms / 1000)
        lines = [
            f"Time {self.fmt_time(current_time)}",
            f"Best {best_text}",
            f"Deaths {deaths}  Retry {attempts}",
            f"{status} | {net}",
        ]
        for i, line in enumerate(lines):
            self.font.render_to(surface, (x, y + i * 12), line, c["text"])
        if config.SHOW_PROGRESS_BAR:
            bar = pygame.Rect(x, y + 50, 150, 4)
            fill = pygame.Rect(x, y + 50, int(150 * max(0.0, min(1.0, progress))), 4)
            pygame.draw.rect(surface, (40, 40, 55), bar)
            pygame.draw.rect(surface, c["accent"], fill)
