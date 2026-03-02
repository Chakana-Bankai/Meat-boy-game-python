from __future__ import annotations

import pygame


def world_to_screen_rect(rect: pygame.Rect, camera: pygame.Vector2) -> pygame.Rect:
    return pygame.Rect(int(rect.x - camera.x), int(rect.y - camera.y), rect.w, rect.h)
