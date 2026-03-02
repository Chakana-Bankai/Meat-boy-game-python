from __future__ import annotations

from dataclasses import dataclass
import pygame


@dataclass
class Viewport:
    dest: pygame.Rect
    scale: float


class ViewportManager:
    def __init__(self, internal_size: tuple[int, int], mode: str = "letterbox") -> None:
        self.internal_w, self.internal_h = internal_size
        self.mode = mode
        self.viewport = Viewport(pygame.Rect(0, 0, self.internal_w, self.internal_h), 1.0)

    def set_mode(self, mode: str, window_size: tuple[int, int]) -> None:
        self.mode = mode
        self.recalculate(window_size)

    def recalculate(self, window_size: tuple[int, int]) -> None:
        w, h = window_size
        if self.mode == "stretch":
            self.viewport = Viewport(pygame.Rect(0, 0, w, h), w / self.internal_w)
            return

        sx = w / self.internal_w
        sy = h / self.internal_h
        scale = min(sx, sy)

        if self.mode == "integer":
            scale = max(1.0, float(int(scale)))

        rw = int(self.internal_w * scale)
        rh = int(self.internal_h * scale)
        ox = (w - rw) // 2
        oy = (h - rh) // 2
        self.viewport = Viewport(pygame.Rect(ox, oy, rw, rh), scale)

    def blit(self, screen: pygame.Surface, internal: pygame.Surface) -> None:
        if self.viewport.dest.size != internal.get_size():
            scaled = pygame.transform.scale(internal, self.viewport.dest.size)
            screen.blit(scaled, self.viewport.dest.topleft)
        else:
            screen.blit(internal, self.viewport.dest.topleft)
