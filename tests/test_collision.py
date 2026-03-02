import pygame

from game.core.physics import resolve_axis_aligned
from game.core.player import Player


def test_collision_stops_fall() -> None:
    pygame.init()
    rect = pygame.Rect(10, 10, 12, 14)
    floor = pygame.Rect(0, 25, 100, 10)
    vel = pygame.Vector2(0, 400)
    result = resolve_axis_aligned(rect, [floor], vel, 0.1)
    assert result.on_ground is True
    assert vel.y == 0


def test_player_hitbox_is_smaller_than_sprite() -> None:
    player = Player(pygame.Rect(20, 30, 12, 14))
    hb = player.hitbox()
    assert hb.width < player.rect.width
    assert hb.height < player.rect.height
