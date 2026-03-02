import pygame

from game.core.camera import world_to_screen_rect


def test_world_to_screen_rect_translation() -> None:
    rect = pygame.Rect(100, 50, 10, 8)
    cam = pygame.Vector2(20, 5)
    out = world_to_screen_rect(rect, cam)
    assert out.topleft == (80, 45)
    assert out.size == rect.size
