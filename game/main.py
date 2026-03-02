from __future__ import annotations

import time
import pygame
import pygame.freetype

from game import config
from game.audio import AudioManager
from game.core.api_client import ApiClient
from game.ui.hud import HUDRenderer
from game.ui.scenes import GameContext, MenuScene, ProfileStore, Scene


def run() -> None:
    pygame.init()
    pygame.freetype.init()
    screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    internal = pygame.Surface(config.INTERNAL_RES)
    clock = pygame.time.Clock()
    font = pygame.freetype.SysFont("Consolas", 12)

    api = ApiClient(config.API_URL)
    audio = AudioManager()
    audio.load()
    hud = HUDRenderer()
    ctx = GameContext(screen=screen, internal=internal, clock=clock, font=font, api=api, audio=audio, profile=ProfileStore(), hud=hud)

    scene: Scene = MenuScene()
    accumulator = 0.0
    previous = time.perf_counter()
    ping_timer = 0.0

    while ctx.running:
        now = time.perf_counter()
        frame = min(now - previous, config.MAX_ACCUMULATOR)
        previous = now
        accumulator += frame

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                ctx.running = False
            next_scene = scene.handle_event(event, ctx)
            if next_scene:
                scene = next_scene

        while accumulator >= config.FIXED_DT:
            next_scene = scene.update(config.FIXED_DT, ctx)
            if next_scene:
                scene = next_scene
            accumulator -= config.FIXED_DT
            ping_timer -= config.FIXED_DT
            if ping_timer <= 0:
                ctx.api.ping()
                ping_timer = 2.0

        scene.draw(ctx)

        scaled = pygame.transform.scale(ctx.internal, (config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        ctx.screen.blit(scaled, (0, 0))
        pygame.display.flip()
        clock.tick(config.TARGET_FPS)

    pygame.quit()


if __name__ == "__main__":
    run()
