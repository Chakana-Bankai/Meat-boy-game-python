from __future__ import annotations

from dataclasses import dataclass
import pygame


@dataclass
class CollisionResult:
    on_ground: bool = False
    on_wall_left: bool = False
    on_wall_right: bool = False


def resolve_axis_aligned(rect: pygame.Rect, solids: list[pygame.Rect], vel: pygame.Vector2, dt: float) -> CollisionResult:
    result = CollisionResult()

    rect.x += int(vel.x * dt)
    for tile in solids:
        if rect.colliderect(tile):
            if vel.x > 0:
                rect.right = tile.left
                result.on_wall_right = True
            elif vel.x < 0:
                rect.left = tile.right
                result.on_wall_left = True
            vel.x = 0

    rect.y += int(vel.y * dt)
    for tile in solids:
        if rect.colliderect(tile):
            if vel.y > 0:
                rect.bottom = tile.top
                result.on_ground = True
            elif vel.y < 0:
                rect.top = tile.bottom
            vel.y = 0

    return result
