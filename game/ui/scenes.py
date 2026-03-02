from __future__ import annotations

from dataclasses import dataclass, field
import logging
from pathlib import Path
import random
import time

import pygame
import pygame.freetype

from game import config
from game.audio import AudioManager
from game.core.api_client import ApiClient
from game.core.camera import world_to_screen_rect
from game.core.hazards import FallingBlock, Laser, PatrolEnemy, RailSaw
from game.core.level import LevelData, load_level
from game.core.player import InputState, Player
from game.core.replay import GhostRecorder
from game.difficulty import build_profile
from game.ui.hud import HUDRenderer
from shared.schemas import RunPayload

LOGGER = logging.getLogger("game.scenes")


@dataclass
class ProfileStore:
    best_times: dict[str, int] = field(default_factory=dict)
    deaths: dict[str, int] = field(default_factory=dict)


@dataclass
class GameContext:
    screen: pygame.Surface
    internal: pygame.Surface
    clock: pygame.time.Clock
    font: pygame.freetype.Font
    api: ApiClient
    audio: AudioManager
    profile: ProfileStore
    hud: HUDRenderer
    running: bool = True
    fullscreen: bool = False
    screen_shake: bool = config.SCREEN_SHAKE
    ghost_enabled: bool = config.GHOST_ENABLED
    debug_overlay: bool = False


class Scene:
    def handle_event(self, event: pygame.event.Event, ctx: GameContext) -> Scene | None:
        return None

    def update(self, dt: float, ctx: GameContext) -> Scene | None:
        return None

    def draw(self, ctx: GameContext) -> None:
        raise NotImplementedError


class MenuScene(Scene):
    def __init__(self) -> None:
        self.items = ["Play", "Level Select", "Options", "Quit"]
        self.index = 0

    def handle_event(self, event: pygame.event.Event, ctx: GameContext) -> Scene | None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F3:
                ctx.debug_overlay = not ctx.debug_overlay
            if event.key in (pygame.K_w, pygame.K_UP):
                self.index = (self.index - 1) % len(self.items)
                ctx.audio.play("menu_move")
            elif event.key in (pygame.K_s, pygame.K_DOWN):
                self.index = (self.index + 1) % len(self.items)
                ctx.audio.play("menu_move")
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                ctx.audio.play("menu_select")
                pick = self.items[self.index]
                if pick == "Play":
                    return LevelScene(0)
                if pick == "Level Select":
                    return LevelSelectScene()
                if pick == "Options":
                    return OptionsScene(self)
                ctx.running = False
        return None

    def draw(self, ctx: GameContext) -> None:
        s = ctx.internal
        s.fill(config.PALETTE["bg"])
        ctx.font.render_to(s, (20, 20), "MEAT BOY PYTHON", config.PALETTE["accent"])
        for i, item in enumerate(self.items):
            color = config.PALETTE["warn"] if i == self.index else config.PALETTE["text"]
            ctx.font.render_to(s, (28, 50 + i * 16), item, color)


class LevelSelectScene(Scene):
    def __init__(self) -> None:
        self.levels = sorted(Path("game/levels").glob("level_*.json"))
        self.index = 0
        self.cache_lb: list[dict] = []
        self.last_fetch = 0.0

    def handle_event(self, event: pygame.event.Event, ctx: GameContext) -> Scene | None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE,):
                return MenuScene()
            if event.key == pygame.K_F3:
                ctx.debug_overlay = not ctx.debug_overlay
            if event.key in (pygame.K_w, pygame.K_UP):
                self.index = (self.index - 1) % len(self.levels)
                ctx.audio.play("menu_move")
            elif event.key in (pygame.K_s, pygame.K_DOWN):
                self.index = (self.index + 1) % len(self.levels)
                ctx.audio.play("menu_move")
            elif event.key == pygame.K_RETURN:
                ctx.audio.play("menu_select")
                return LevelScene(self.index)
        return None

    def update(self, dt: float, ctx: GameContext) -> Scene | None:
        self.last_fetch += dt
        if self.levels and self.last_fetch >= 0.5:
            self.last_fetch = 0.0
            lid = self.levels[self.index].stem
            self.cache_lb = ctx.api.get_leaderboard(lid)[:5]
        return None

    def draw(self, ctx: GameContext) -> None:
        s = ctx.internal
        s.fill(config.PALETTE["bg"])
        ctx.font.render_to(s, (12, 10), "LEVEL SELECT", config.PALETTE["accent"])
        for i, level in enumerate(self.levels[:10]):
            lid = level.stem
            best = ctx.profile.best_times.get(lid)
            color = config.PALETTE["warn"] if i == self.index else config.PALETTE["text"]
            ctx.font.render_to(s, (12, 28 + i * 12), f"{lid} best={best if best else '-'}", color)
        y = 28
        ctx.font.render_to(s, (170, 18), "Top 5", config.PALETTE["accent"])
        for row in self.cache_lb:
            ctx.font.render_to(s, (170, y), f"{row.get('player_name','?')} {row.get('best_time_ms','-')}ms", config.PALETTE["text"])
            y += 12


class OptionsScene(Scene):
    def __init__(self, back_scene: Scene) -> None:
        self.back_scene = back_scene
        self.items = ["SFX +", "SFX -", "Music +", "Music -", "Test SFX", "Fullscreen", "Screen Shake", "Ghost", "Back"]
        self.idx = 0

    def handle_event(self, event: pygame.event.Event, ctx: GameContext) -> Scene | None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE,):
                return self.back_scene
            if event.key == pygame.K_F3:
                ctx.debug_overlay = not ctx.debug_overlay
            if event.key in (pygame.K_w, pygame.K_UP):
                self.idx = (self.idx - 1) % len(self.items)
                ctx.audio.play("menu_move")
            elif event.key in (pygame.K_s, pygame.K_DOWN):
                self.idx = (self.idx + 1) % len(self.items)
                ctx.audio.play("menu_move")
            elif event.key == pygame.K_RETURN:
                pick = self.items[self.idx]
                ctx.audio.play("menu_select")
                if pick == "SFX +":
                    ctx.audio.set_sfx_volume(ctx.audio.sfx_volume + 0.1)
                elif pick == "SFX -":
                    ctx.audio.set_sfx_volume(ctx.audio.sfx_volume - 0.1)
                elif pick == "Music +":
                    ctx.audio.set_music_volume(ctx.audio.music_volume + 0.1)
                elif pick == "Music -":
                    ctx.audio.set_music_volume(ctx.audio.music_volume - 0.1)
                elif pick == "Test SFX":
                    ctx.audio.test_sfx()
                elif pick == "Fullscreen":
                    ctx.fullscreen = not ctx.fullscreen
                    flags = pygame.FULLSCREEN if ctx.fullscreen else 0
                    ctx.screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), flags)
                elif pick == "Screen Shake":
                    ctx.screen_shake = not ctx.screen_shake
                elif pick == "Ghost":
                    ctx.ghost_enabled = not ctx.ghost_enabled
                elif pick == "Back":
                    return self.back_scene
        return None

    def draw(self, ctx: GameContext) -> None:
        s = ctx.internal
        s.fill(config.PALETTE["bg"])
        ctx.font.render_to(s, (14, 10), "OPTIONS", config.PALETTE["accent"])
        for i, item in enumerate(self.items):
            col = config.PALETTE["warn"] if i == self.idx else config.PALETTE["text"]
            ctx.font.render_to(s, (14, 28 + i * 12), item, col)
        ctx.font.render_to(s, (14, 145), ctx.audio.debug_status(), config.PALETTE["safe"])


class LevelScene(Scene):
    def __init__(self, level_index: int = 0) -> None:
        self.levels = sorted(Path("game/levels").glob("level_*.json"))
        self.level_index = level_index % max(1, len(self.levels))
        self.level = load_level(self.levels[self.level_index])
        self.profile = build_profile(self.level_index, self.level.difficulty_budget)

        self.solids = self._tiles_to_rects(self.level)
        self.player = Player(pygame.Rect(self.level.spawn[0], self.level.spawn[1], *config.PLAYER_SIZE))
        self.goal = pygame.Rect(*self.level.goal)
        self.recorder = GhostRecorder()

        self.timer = 0.0
        self.deaths = 0
        self.attempts = 1
        self.pause = False
        self.complete_panel_timer = 0.0
        self.complete_data: dict | None = None

        self.death_reason = ""
        self.death_timer = 0.0
        self.consecutive_quick_deaths = 0

        self.shake = 0.0
        self.camera = pygame.Vector2(0, 0)
        self.camera_target = pygame.Vector2(0, 0)
        self.t = 0.0
        self.prev_jump_held = False

        self.rng = random.Random(self.level.seed)
        self.rails = [RailSaw(f"rail_{i}", pygame.Vector2(*r["start"]), pygame.Vector2(*r["end"]), r.get("radius", 6), r.get("phase", 0.0)) for i, r in enumerate(self.level.rails)]
        self.lasers = [Laser(f"laser_{i}", pygame.Rect(*l["rect"]), l.get("phase", 0.0)) for i, l in enumerate(self.level.lasers)]
        self.falling = [FallingBlock(f"falling_{i}", pygame.Rect(*b["rect"])) for i, b in enumerate(self.level.falling_blocks)]
        self.patrols = [PatrolEnemy(f"patrol_{i}", pygame.Rect(*p["rect"]), p["left"], p["right"]) for i, p in enumerate(self.level.patrols)]

    def _tiles_to_rects(self, level: LevelData) -> list[pygame.Rect]:
        out = []
        for y, row in enumerate(level.solids):
            for x, value in enumerate(row):
                if value:
                    out.append(pygame.Rect(x * config.TILE_SIZE, y * config.TILE_SIZE, config.TILE_SIZE, config.TILE_SIZE))
        return out

    def _danger_sets(self) -> tuple[list[tuple[str, pygame.Rect]], list[pygame.Rect]]:
        hurt: list[tuple[str, pygame.Rect]] = [("spike", pygame.Rect(*s)) for s in self.level.spikes]
        tele: list[pygame.Rect] = []
        for saw in self.rails:
            for r in saw.hurt_rects(self.t, self.profile):
                hurt.append((saw.name, r))
        for laser in self.lasers:
            for r in laser.hurt_rects(self.t, self.profile):
                hurt.append((laser.name, r))
            tele.extend(laser.telegraph_rects(self.t, self.profile))
        for block in self.falling:
            for r in block.hurt_rects():
                hurt.append((block.name, r))
            tele.extend(block.telegraph_rects())
        for patrol in self.patrols:
            for r in patrol.hurt_rects():
                hurt.append((patrol.name, r))
        return hurt, tele

    def _kill(self, source: str, ctx: GameContext) -> None:
        self.deaths += 1
        self.attempts += 1
        self.death_reason = f"Died: {source}"
        self.death_timer = 1.0
        if self.timer < 10.0:
            self.consecutive_quick_deaths += 1
        else:
            self.consecutive_quick_deaths = 0
        self.player.rect.topleft = self.level.spawn
        self.player.vel.xy = (0, 0)
        self.timer = 0.0
        self.recorder = GhostRecorder()
        self.shake = 0.18 if ctx.screen_shake else 0.0
        ctx.audio.play("death")

    def handle_event(self, event: pygame.event.Event, ctx: GameContext) -> Scene | None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F3:
                ctx.debug_overlay = not ctx.debug_overlay
            if event.key == pygame.K_ESCAPE:
                self.pause = not self.pause
            if self.pause and event.key == pygame.K_q:
                return MenuScene()
            if self.pause and event.key == pygame.K_o:
                return OptionsScene(self)
        return None

    def update(self, dt: float, ctx: GameContext) -> Scene | None:
        self.t += dt
        self.death_timer = max(0.0, self.death_timer - dt)

        if self.complete_panel_timer > 0:
            self.complete_panel_timer -= dt
            if self.complete_panel_timer <= 0:
                return LevelScene(self.level_index + 1)
            return None

        if self.pause:
            return None

        keys = pygame.key.get_pressed()
        jump_held = keys[pygame.K_SPACE]
        jump_pressed = jump_held and not self.prev_jump_held
        inp = InputState(
            left=keys[pygame.K_a] or keys[pygame.K_LEFT],
            right=keys[pygame.K_d] or keys[pygame.K_RIGHT],
            jump_pressed=jump_pressed,
            jump_held=jump_held,
            restart=keys[pygame.K_r],
        )

        if inp.restart:
            self._kill("manual_restart", ctx)

        if jump_pressed and self.player.coyote_timer > 0:
            ctx.audio.play("jump")

        # Adaptive assist one-attempt softening after repeated quick fails
        assist = 0.9 if self.consecutive_quick_deaths >= 3 else 1.0
        old = self.profile
        self.profile = build_profile(self.level_index, max(1, int(self.level.difficulty_budget * assist)))

        was_ground_before = self.player.was_on_ground
        collision = self.player.update(dt, inp, self.solids)
        self.profile = old if assist == 1.0 else self.profile

        if collision.on_ground and not was_ground_before:
            ctx.audio.play("land")

        self.prev_jump_held = jump_held
        self.recorder.push(inp)
        self.timer += dt

        for falling in self.falling:
            falling.update(dt, self.player.hitbox(), self.profile)
        for patrol in self.patrols:
            patrol.update(dt, self.profile, self.player.hitbox())

        hurt, _ = self._danger_sets()
        for name, rect in hurt:
            if self.player.hitbox().colliderect(rect):
                self._kill(name, ctx)
                break

        if self.player.hitbox().colliderect(self.goal):
            run_ms = int(self.timer * 1000)
            best = ctx.profile.best_times.get(self.level.level_id)
            if best is None or run_ms < best:
                ctx.profile.best_times[self.level.level_id] = run_ms

            replay_data = ""
            try:
                replay_data = self.recorder.encode()
            except Exception as exc:
                LOGGER.exception("Replay serialization failed: %s", exc)

            payload = RunPayload(
                level_id=self.level.level_id,
                player_name="local_player",
                best_time_ms=run_ms,
                deaths=self.deaths,
                seed=self.level.seed,
                replay_data=replay_data or "fallback",
            )

            offline_saved = False
            try:
                ctx.api.submit_run(payload)
            except Exception as exc:
                LOGGER.exception("POST /runs crashed, saved offline fallback expected: %s", exc)
                offline_saved = True

            lb: list[dict] = []
            try:
                lb = ctx.api.get_leaderboard(self.level.level_id)[:5] or []
            except Exception as exc:
                LOGGER.exception("GET leaderboard failed: %s", exc)
                lb = []

            self.complete_data = {
                "run_ms": run_ms,
                "best": ctx.profile.best_times.get(self.level.level_id),
                "deaths": self.deaths,
                "lb": lb,
                "offline": offline_saved or (not ctx.api.online),
            }
            self.complete_panel_timer = 2.6
            ctx.audio.play("goal")

        lead = config.CAMERA_LEAD if self.player.vel.x > 5 else (-config.CAMERA_LEAD if self.player.vel.x < -5 else 0)
        self.camera_target.x = max(0, self.player.rect.centerx + lead - config.INTERNAL_RES[0] // 2)
        self.camera_target.y = max(0, self.player.rect.centery - config.INTERNAL_RES[1] // 2)
        self.camera += (self.camera_target - self.camera) * config.CAMERA_SMOOTH

        self.shake = max(0.0, self.shake - dt)
        return None

    def draw(self, ctx: GameContext) -> None:
        s = ctx.internal
        c = config.PALETTE

        # parallax layers
        s.fill(c["bg"])
        p1 = int((self.camera.x * 0.2) % 40)
        p2 = int((self.camera.x * 0.35) % 60)
        pygame.draw.rect(s, c["bg2"], pygame.Rect(-p1, 30, 400, 20))
        pygame.draw.rect(s, c["bg2"], pygame.Rect(-p2, 70, 420, 20))

        shake_off = pygame.Vector2(0, 0)
        if self.shake > 0 and ctx.screen_shake:
            shake_off.x = self.rng.uniform(-2, 2)
            shake_off.y = self.rng.uniform(-2, 2)

        hurt, tele = self._danger_sets()

        for tile in self.solids:
            r = world_to_screen_rect(tile, self.camera - shake_off)
            pygame.draw.rect(s, c["tile_shadow"], r.move(1, 1))
            pygame.draw.rect(s, c["tile"], r)
            pygame.draw.rect(s, (20, 20, 30), r, 1)

        for tr in tele:
            pygame.draw.rect(s, c["warn"], world_to_screen_rect(tr, self.camera - shake_off), 1)

        for _, hr in hurt:
            pygame.draw.rect(s, c["danger"], world_to_screen_rect(hr, self.camera - shake_off))

        pulse = 2 + int((time.perf_counter() * 6) % 3)
        goal_screen = world_to_screen_rect(self.goal, self.camera - shake_off)
        pygame.draw.rect(s, c["goal"], goal_screen)
        pygame.draw.rect(s, c["accent"], goal_screen.inflate(pulse, pulse), 1)

        player_draw = world_to_screen_rect(self.player.rect, self.camera - shake_off)
        pygame.draw.rect(s, c["player"], player_draw)

        progress = self.player.rect.centerx / max(1, self.goal.centerx)
        death_msg = self.death_reason if self.death_timer > 0 else ""
        debug_lines = []
        if ctx.debug_overlay:
            debug_lines = [
                f"FPS={ctx.clock.get_fps():.1f}",
                ctx.audio.debug_status(),
                f"api_online={ctx.api.online}",
            ]

        ctx.hud.draw(
            s,
            current_time=self.timer,
            best_time_ms=ctx.profile.best_times.get(self.level.level_id),
            deaths=self.deaths,
            attempts=self.attempts,
            paused=self.pause,
            recording_ghost=True,
            online=ctx.api.online,
            progress=progress,
            death_msg=death_msg,
            debug_lines=debug_lines,
        )

        if self.pause:
            ctx.font.render_to(s, (72, 82), "PAUSED - ESC resume / Q menu / O options", c["warn"])

        if self.complete_data:
            d = self.complete_data
            pygame.draw.rect(s, c["panel"], pygame.Rect(64, 36, 192, 110))
            ctx.font.render_to(s, (72, 44), f"LEVEL COMPLETE {d.get('run_ms',0)}ms", c["accent"])
            ctx.font.render_to(s, (72, 58), f"Best: {d.get('best','-')}  Deaths: {d.get('deaths',0)}", c["text"])
            if d.get("offline"):
                ctx.font.render_to(s, (72, 70), "Saved offline", c["warn"])
            y = 82
            for row in d.get("lb", []):
                ctx.font.render_to(s, (72, y), f"{row.get('player_name','?')} {row.get('best_time_ms','-')}ms", c["text"])
                y += 10

        if ctx.debug_overlay:
            for tile in self.solids:
                pygame.draw.rect(s, (70, 130, 255), world_to_screen_rect(tile, self.camera - shake_off), 1)
            for _, hr in hurt:
                pygame.draw.rect(s, (255, 50, 50), world_to_screen_rect(hr, self.camera - shake_off), 1)
            pygame.draw.rect(s, (255, 215, 70), goal_screen, 1)
            pygame.draw.rect(s, (60, 255, 80), world_to_screen_rect(self.player.hitbox(), self.camera - shake_off), 1)
