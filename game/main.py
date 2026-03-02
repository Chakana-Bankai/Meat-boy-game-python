from __future__ import annotations

import logging
import time

import pygame
import pygame.freetype

from game import config
from game.audio import AudioManager
from game.core.network import NetworkClient
from game.core.perf import PerfOverlay
from game.core.viewport import ViewportManager
from game.ui.hud import HUDRenderer
from game.ui.scenes import GameContext, MenuScene, ProfileStore, Scene


def _create_screen(fullscreen: bool) -> pygame.Surface:
    if fullscreen:
        flags = pygame.FULLSCREEN | (pygame.NOFRAME if config.BORDERLESS else 0)
        return pygame.display.set_mode((0, 0), flags)
    return pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.RESIZABLE)


def run() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    AudioManager.configure_pre_init()
    pygame.init()
    pygame.freetype.init()

    screen = _create_screen(config.FULLSCREEN)
    internal = pygame.Surface(config.INTERNAL_RES).convert()
    clock = pygame.time.Clock()
    font = pygame.freetype.SysFont("Consolas", 12)

    viewport = ViewportManager(config.INTERNAL_RES, config.VIEWPORT_MODE)
    viewport.recalculate(screen.get_size())

    network = NetworkClient(config.API_URL)
    audio = AudioManager()
    audio.load()
    hud = HUDRenderer()
    perf = PerfOverlay()

    ctx = GameContext(screen=screen, internal=internal, clock=clock, font=font, network=network, audio=audio, profile=ProfileStore(), hud=hud, perf=perf)

    scene: Scene = MenuScene()
    accumulator = 0.0
    previous = time.perf_counter()
    ping_timer = 0.0

    while ctx.running:
        now = time.perf_counter()
        frame = min(now - previous, config.MAX_ACCUMULATOR)
        previous = now
        accumulator += frame
        perf.push(frame)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                ctx.running = False
            elif event.type == pygame.VIDEORESIZE:
                if not ctx.fullscreen:
                    ctx.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                    viewport.recalculate((event.w, event.h))
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                ctx.fullscreen = not ctx.fullscreen
                ctx.screen = _create_screen(ctx.fullscreen)
                viewport.recalculate(ctx.screen.get_size())
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
                network.enqueue_ping()
                network.jobs.put(("sync", None))
                ping_timer = 2.0

        scene.draw(ctx)
        ctx.screen.fill((0, 0, 0))
        viewport.blit(ctx.screen, ctx.internal)
        pygame.display.flip()
        clock.tick(config.TARGET_FPS)

    pygame.quit()


if __name__ == "__main__":
    run()
