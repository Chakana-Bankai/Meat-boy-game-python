from __future__ import annotations

import pygame
import pygame.freetype

from game import config


class HUDRenderer:
    def __init__(self) -> None:
        self.font = pygame.freetype.SysFont("Consolas", 10)
        self.cache: dict[tuple[str, tuple[int, int, int]], pygame.Surface] = {}

    @staticmethod
    def fmt_time(seconds: float) -> str:
        ms = int((seconds % 1) * 100)
        total = int(seconds)
        return f"{total // 60:02d}:{total % 60:02d}.{ms:02d}"

    def _text(self, text: str, color: tuple[int, int, int]) -> pygame.Surface:
        key = (text, color)
        if key not in self.cache:
            surf, _ = self.font.render(text, fgcolor=color)
            self.cache[key] = surf.convert_alpha()
        return self.cache[key]

    def draw(self, surface: pygame.Surface, *, current_time: float, best_time_ms: int | None, deaths: int, attempts: int,
             paused: bool, recording_ghost: bool, online: bool, progress: float, death_msg: str, debug_lines: list[str]) -> None:
        if not config.HUD_ENABLED:
            return
        x, y = config.HUD_POS
        c = config.PALETTE
        pygame.draw.rect(surface, c["panel"], pygame.Rect(x - 2, y - 2, 220, 64))
        status = "Paused" if paused else ("Recording Ghost" if recording_ghost else "Playing")
        best_text = "--:--.--" if best_time_ms is None else self.fmt_time(best_time_ms / 1000)
        lines = [
            f"Time {self.fmt_time(current_time)}",
            f"Best {best_text}",
            f"Deaths {deaths} Retry {attempts}",
            f"{status} | {'ONLINE' if online else 'OFFLINE'}",
        ]
        for i, line in enumerate(lines):
            surface.blit(self._text(line, c["text"]), (x, y + i * 12))
        if death_msg:
            surface.blit(self._text(death_msg, c["danger"]), (x + 120, y + 2))
        if config.SHOW_PROGRESS_BAR:
            by = y + 60
            pygame.draw.rect(surface, (40, 40, 55), pygame.Rect(x, by, 200, 4))
            pygame.draw.rect(surface, c["accent"], pygame.Rect(x, by, int(200 * max(0.0, min(1.0, progress))), 4))
        for i, dbg in enumerate(debug_lines):
            surface.blit(self._text(dbg, c["warn"]), (5, config.INTERNAL_RES[1] - 12 - i * 10))
