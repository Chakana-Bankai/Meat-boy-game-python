from __future__ import annotations

import json
import time
from pathlib import Path

import pygame

from game import config
from game.core.api_client import ApiClient
from game.core.level import LevelData, load_level
from game.core.player import InputState, Player
from game.core.replay import GhostPlayback, GhostRecorder
from shared.schemas import RunPayload


def tiles_to_rects(level: LevelData) -> list[pygame.Rect]:
    rects = []
    for y, row in enumerate(level.solids):
        for x, value in enumerate(row):
            if value:
                rects.append(pygame.Rect(x * config.TILE_SIZE, y * config.TILE_SIZE, config.TILE_SIZE, config.TILE_SIZE))
    return rects


def trap_rects(level: LevelData) -> list[pygame.Rect]:
    traps = [pygame.Rect(*s) for s in level.spikes]
    for x, y, r in level.saws:
        traps.append(pygame.Rect(x - r, y - r, r * 2, r * 2))
    return traps


def run() -> None:
    pygame.init()
    screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 20)

    levels = sorted(Path("game/levels").glob("level_*.json"))
    idx = 0
    level = load_level(levels[idx])
    solids = tiles_to_rects(level)
    traps = trap_rects(level)
    player = Player(pygame.Rect(level.spawn[0], level.spawn[1], *config.PLAYER_SIZE))
    ghost_best_blob = ""
    ghost = GhostPlayback.from_blob(ghost_best_blob) if ghost_best_blob else None
    recorder = GhostRecorder()
    api = ApiClient()

    mode = "menu"
    accumulator = 0.0
    previous = time.perf_counter()
    run_time = 0.0
    deaths = 0
    best_times = {}
    benchmark_mode = False

    while True:
        now = time.perf_counter()
        frame = min(now - previous, config.MAX_ACCUMULATOR)
        previous = now
        accumulator += frame

        jump_pressed = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                jump_pressed = True
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F3:
                benchmark_mode = not benchmark_mode

        keys = pygame.key.get_pressed()
        if mode == "menu":
            if keys[pygame.K_RETURN]:
                mode = "play"
            screen.fill((10, 10, 10))
            screen.blit(font.render("ENTER: Play | ESC: Quit", True, (250, 250, 250)), (20, 20))
            if keys[pygame.K_ESCAPE]:
                return
            pygame.display.flip()
            clock.tick(config.TARGET_FPS)
            continue

        while accumulator >= config.FIXED_DT:
            input_state = InputState(
                left=keys[pygame.K_a] or keys[pygame.K_LEFT],
                right=keys[pygame.K_d] or keys[pygame.K_RIGHT],
                jump_pressed=jump_pressed,
                jump_held=keys[pygame.K_SPACE],
                restart=keys[pygame.K_r],
            )

            if input_state.restart:
                player.rect.topleft = level.spawn
                player.vel.xy = (0, 0)
                run_time = 0
                deaths += 1
                recorder = GhostRecorder()

            player.update(config.FIXED_DT, input_state, solids)
            recorder.push(input_state)
            run_time += config.FIXED_DT

            if ghost:
                ghost.next()

            if any(player.rect.colliderect(t) for t in traps):
                player.rect.topleft = level.spawn
                player.vel.xy = (0, 0)
                deaths += 1
                run_time = 0
                recorder = GhostRecorder()

            goal_rect = pygame.Rect(*level.goal)
            if player.rect.colliderect(goal_rect):
                level_ms = int(run_time * 1000)
                best = best_times.get(level.level_id, 10**9)
                if level_ms < best:
                    best_times[level.level_id] = level_ms
                    ghost_best_blob = recorder.encode()
                    ghost = GhostPlayback.from_blob(ghost_best_blob)
                api.submit_run(
                    RunPayload(
                        level_id=level.level_id,
                        player_name="local_player",
                        best_time_ms=level_ms,
                        deaths=deaths,
                        seed=level.seed,
                        replay_data=ghost_best_blob or recorder.encode(),
                    )
                )
                idx = (idx + 1) % len(levels)
                level = load_level(levels[idx])
                solids = tiles_to_rects(level)
                traps = trap_rects(level)
                player.rect.topleft = level.spawn
                player.vel.xy = (0, 0)
                run_time = 0
                deaths = 0
                recorder = GhostRecorder()

            accumulator -= config.FIXED_DT
            jump_pressed = False

        screen.fill((25, 25, 35))
        for tile in solids:
            pygame.draw.rect(screen, (80, 80, 80), tile)
        for trap in traps:
            pygame.draw.rect(screen, (180, 40, 40), trap)
        pygame.draw.rect(screen, config.SPAWN_COLOR, pygame.Rect(level.spawn[0], level.spawn[1], 8, 8))
        pygame.draw.rect(screen, (40, 200, 80), pygame.Rect(*level.goal))
        pygame.draw.rect(screen, config.PLAYER_COLOR, player.rect)

        hud = f"lvl {level.level_id}  t={run_time:.2f}s  deaths={deaths}  fps={clock.get_fps():.1f}"
        screen.blit(font.render(hud, True, (255, 255, 255)), (10, 8))
        if benchmark_mode:
            screen.blit(font.render("BENCHMARK MODE ON (F3)", True, (255, 220, 60)), (10, 32))

        pygame.display.flip()
        clock.tick(config.TARGET_FPS)


if __name__ == "__main__":
    run()
