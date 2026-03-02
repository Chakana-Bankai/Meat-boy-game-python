import pygame

from game.core.physics import resolve_axis_aligned


def test_collision_stops_fall():
    pygame.init()
    rect = pygame.Rect(10, 10, 10, 10)
    floor = pygame.Rect(0, 25, 100, 10)
    vel = pygame.Vector2(0, 400)
    result = resolve_axis_aligned(rect, [floor], vel, 0.1)
    assert result.on_ground is True
    assert vel.y == 0
