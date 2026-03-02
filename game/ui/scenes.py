from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import time
import pygame
import pygame.freetype

from game import config
from game.audio import AudioManager
from game.core.api_client import ApiClient
from game.core.hazards import FallingBlock, Laser, PatrolEnemy, RailSaw
from game.core.level import LevelData, load_level
from game.core.player import InputState, Player
from game.core.replay import GhostPlayback, GhostRecorder
from game.difficulty import DifficultyProfile, build_profile
from game.ui.hud import HUDRenderer
from shared.schemas import RunPayload


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

    def handle_event(self, event: pygame.event.Event, ctx: GameContext) -> Scene | None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE,):
                return MenuScene()
            if event.key in (pygame.K_w, pygame.K_UP):
                self.index = (self.index - 1) % len(self.levels)
            elif event.key in (pygame.K_s, pygame.K_DOWN):
                self.index = (self.index + 1) % len(self.levels)
            elif event.key == pygame.K_RETURN:
                return LevelScene(self.index)
        if self.levels:
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
            ctx.font.render_to(s, (170, y), f"{row['player_name']} {row['best_time_ms']}ms", config.PALETTE["text"])
            y += 12


class OptionsScene(Scene):
    def __init__(self, back_scene: Scene) -> None:
        self.back_scene = back_scene
        self.items = ["SFX +", "SFX -", "Music +", "Music -", "Fullscreen", "Screen Shake", "Ghost", "Back"]
        self.idx = 0

    def handle_event(self, event: pygame.event.Event, ctx: GameContext) -> Scene | None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE,):
                return self.back_scene
            if event.key in (pygame.K_w, pygame.K_UP):
                self.idx = (self.idx - 1) % len(self.items)
            elif event.key in (pygame.K_s, pygame.K_DOWN):
                self.idx = (self.idx + 1) % len(self.items)
            elif event.key == pygame.K_RETURN:
                pick = self.items[self.idx]
                if pick == "SFX +":
                    ctx.audio.set_sfx_volume(ctx.audio.sfx_volume + 0.1)
                elif pick == "SFX -":
                    ctx.audio.set_sfx_volume(ctx.audio.sfx_volume - 0.1)
                elif pick == "Music +":
                    ctx.audio.set_music_volume(ctx.audio.music_volume + 0.1)
                elif pick == "Music -":
                    ctx.audio.set_music_volume(ctx.audio.music_volume - 0.1)
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
            ctx.font.render_to(s, (14, 30 + i * 14), item, col)


class LevelScene(Scene):
    def __init__(self, level_index: int = 0) -> None:
        self.levels = sorted(Path("game/levels").glob("level_*.json"))
        self.level_index = level_index % max(1, len(self.levels))
        self.level = load_level(self.levels[self.level_index])
        self.profile = build_profile(self.level_index, self.level.difficulty_budget)
        self.solids = self._tiles_to_rects(self.level)
        self.player = Player(pygame.Rect(self.level.spawn[0], self.level.spawn[1], *config.PLAYER_SIZE))
        self.goal = pygame.Rect(*self.level.goal)
        self.ghost_blob = ""
        self.ghost = None
        self.recorder = GhostRecorder()
        self.timer = 0.0
        self.deaths = 0
        self.attempts = 1
        self.paused = False
        self.complete_panel_timer = 0.0
        self.complete_data: dict | None = None
        self.shake = 0.0
        self.rails = [RailSaw(pygame.Vector2(*r["start"]), pygame.Vector2(*r["end"]), r.get("radius", 6), r.get("phase", 0.0)) for r in self.level.rails]
        self.lasers = [Laser(pygame.Rect(*l["rect"]), l.get("phase", 0.0)) for l in self.level.lasers]
        self.falling = [FallingBlock(pygame.Rect(*b["rect"])) for b in self.level.falling_blocks]
        self.patrols = [PatrolEnemy(pygame.Rect(*p["rect"]), p["left"], p["right"]) for p in self.level.patrols]

    def _tiles_to_rects(self, level: LevelData) -> list[pygame.Rect]:
        out = []
        for y, row in enumerate(level.solids):
            for x, v in enumerate(row):
                if v:
                    out.append(pygame.Rect(x * config.TILE_SIZE, y * config.TILE_SIZE, config.TILE_SIZE, config.TILE_SIZE))
        return out

    def _reset_run(self) -> None:
        self.player.rect.topleft = self.level.spawn
        self.player.vel.xy = (0, 0)
        self.timer = 0.0
        self.deaths += 1
        self.attempts += 1
        self.recorder = GhostRecorder()
        self.shake = 0.15

    def _hazard_rects(self, now: float) -> list[pygame.Rect]:
        rects = [pygame.Rect(*s) for s in self.level.spikes]
        rects.extend(r.rect(now, self.profile) for r in self.rails)
        for laser in self.lasers:
            active, _ = laser.state(now, self.profile)
            if active:
                rects.append(laser.rect)
        for b in self.falling:
            if b.warning_timer <= 0 and b.triggered:
                rects.append(b.rect)
        rects.extend(p.rect for p in self.patrols)
        return rects

    def handle_event(self, event: pygame.event.Event, ctx: GameContext) -> Scene | None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.paused = not self.paused
            if self.paused and event.key == pygame.K_q:
                return MenuScene()
            if self.paused and event.key == pygame.K_o:
                return OptionsScene(self)
        return None

    def update(self, dt: float, ctx: GameContext) -> Scene | None:
        if self.complete_panel_timer > 0:
            self.complete_panel_timer -= dt
            if self.complete_panel_timer <= 0:
                return LevelScene(self.level_index + 1)
        if self.paused:
            return None

        keys = pygame.key.get_pressed()
        inp = InputState(
            left=keys[pygame.K_a] or keys[pygame.K_LEFT],
            right=keys[pygame.K_d] or keys[pygame.K_RIGHT],
            jump_pressed=keys[pygame.K_SPACE],
            jump_held=keys[pygame.K_SPACE],
            restart=keys[pygame.K_r],
        )
        if inp.restart:
            self._reset_run()

        self.player.update(dt, inp, self.solids)
        self.recorder.push(inp)
        self.timer += dt
        now = time.perf_counter()
        for f in self.falling:
            f.update(dt, self.player.rect, self.profile)
        for p in self.patrols:
            p.update(dt, self.profile)

        if any(self.player.rect.colliderect(r) for r in self._hazard_rects(now)):
            ctx.audio.play("death")
            self._reset_run()

        if self.player.rect.colliderect(self.goal):
            ctx.audio.play("goal")
            run_ms = int(self.timer * 1000)
            best = ctx.profile.best_times.get(self.level.level_id)
            if best is None or run_ms < best:
                ctx.profile.best_times[self.level.level_id] = run_ms
                self.ghost_blob = self.recorder.encode()
                self.ghost = GhostPlayback.from_blob(self.ghost_blob)
            payload = RunPayload(
                level_id=self.level.level_id,
                player_name="local_player",
                best_time_ms=run_ms,
                deaths=self.deaths,
                seed=self.level.seed,
                replay_data=self.ghost_blob or self.recorder.encode(),
            )
            ctx.api.submit_run(payload)
            lb = ctx.api.get_leaderboard(self.level.level_id)[:5]
            self.complete_data = {"run_ms": run_ms, "best": ctx.profile.best_times.get(self.level.level_id), "deaths": self.deaths, "lb": lb}
            self.complete_panel_timer = 2.5

        self.shake = max(0.0, self.shake - dt)
        return None

    def draw(self, ctx: GameContext) -> None:
        s = ctx.internal
        c = config.PALETTE
        s.fill(c["bg"])
        for tile in self.solids:
            pygame.draw.rect(s, c["tile"], tile)
            pygame.draw.rect(s, (20, 20, 30), tile, 1)
        now = time.perf_counter()
        for rect in self._hazard_rects(now):
            pygame.draw.rect(s, c["danger"], rect)
        for laser in self.lasers:
            active, tele = laser.state(now, self.profile)
            col = c["danger"] if active else (c["warn"] if tele else (80, 70, 70))
            pygame.draw.rect(s, col, laser.rect, 1 if not active else 0)
        for b in self.falling:
            col = c["warn"] if b.warning_timer > 0 else c["tile"]
            pygame.draw.rect(s, col, b.rect)

        pygame.draw.rect(s, c["goal"], self.goal)
        pr = self.player.rect.copy()
        if self.player.vel.y > 50:
            pr.h = max(10, pr.h - 1)
        pygame.draw.rect(s, c["player"], pr)

        progress = self.player.rect.centerx / max(1, self.goal.centerx)
        online = ctx.api.online
        ctx.hud.draw(s, current_time=self.timer, best_time_ms=ctx.profile.best_times.get(self.level.level_id), deaths=self.deaths,
                     attempts=self.attempts, paused=self.paused, recording_ghost=True, online=online, progress=progress)

        if self.paused:
            ctx.font.render_to(s, (104, 80), "PAUSED - ESC resume / Q menu / O options", c["warn"])
        if self.complete_data:
            d = self.complete_data
            pygame.draw.rect(s, c["panel"], pygame.Rect(70, 40, 180, 100))
            ctx.font.render_to(s, (78, 48), f"LEVEL COMPLETE {d['run_ms']}ms", c["accent"])
            ctx.font.render_to(s, (78, 62), f"Best: {d['best']}  Deaths: {d['deaths']}", c["text"])
            y = 76
            for row in d["lb"]:
                ctx.font.render_to(s, (78, y), f"{row['player_name']} {row['best_time_ms']}ms", c["text"])
                y += 12
