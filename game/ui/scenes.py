from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import random
import time

import pygame
import pygame.freetype

from game import config
from game.audio import AudioManager
from game.core.camera import world_to_screen_rect
from game.core.hazards import FallingBlock, Laser, PatrolEnemy, RailSaw
from game.core.level import load_level
from game.core.network import NetworkClient
from game.core.perf import PerfOverlay
from game.core.player import InputState, Player
from game.core.replay import GhostRecorder
from game.difficulty import build_profile
from game.ui.hud import HUDRenderer


@dataclass
class ProfileStore:
    best_times: dict[str, int] = field(default_factory=dict)


@dataclass
class GameContext:
    screen: pygame.Surface
    internal: pygame.Surface
    clock: pygame.time.Clock
    font: pygame.freetype.Font
    network: NetworkClient
    audio: AudioManager
    profile: ProfileStore
    hud: HUDRenderer
    perf: PerfOverlay
    running: bool = True
    fullscreen: bool = config.FULLSCREEN
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
        self.idx = 0

    def handle_event(self, event: pygame.event.Event, ctx: GameContext) -> Scene | None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F3:
                ctx.debug_overlay = not ctx.debug_overlay
            if event.key in (pygame.K_w, pygame.K_UP):
                self.idx = (self.idx - 1) % len(self.items)
                ctx.audio.play("menu_move")
            elif event.key in (pygame.K_s, pygame.K_DOWN):
                self.idx = (self.idx + 1) % len(self.items)
                ctx.audio.play("menu_move")
            elif event.key == pygame.K_RETURN:
                ctx.audio.play("menu_select")
                pick = self.items[self.idx]
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
            ctx.font.render_to(s, (24, 56 + i * 16), item, config.PALETTE["warn"] if i == self.idx else config.PALETTE["text"])


class OptionsScene(Scene):
    def __init__(self, back: Scene) -> None:
        self.back = back
        self.items = ["Viewport", "Test SFX", "Back"]
        self.idx = 0
        self.modes = ["letterbox", "integer", "stretch"]
        self.mode_idx = self.modes.index(config.VIEWPORT_MODE)

    def handle_event(self, event: pygame.event.Event, ctx: GameContext) -> Scene | None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return self.back
            if event.key in (pygame.K_w, pygame.K_UP):
                self.idx = (self.idx - 1) % len(self.items)
            elif event.key in (pygame.K_s, pygame.K_DOWN):
                self.idx = (self.idx + 1) % len(self.items)
            elif event.key == pygame.K_RETURN:
                if self.items[self.idx] == "Viewport":
                    self.mode_idx = (self.mode_idx + 1) % len(self.modes)
                elif self.items[self.idx] == "Test SFX":
                    ctx.audio.test_sfx()
                else:
                    return self.back
        return None

    def draw(self, ctx: GameContext) -> None:
        s = ctx.internal
        s.fill(config.PALETTE["bg"])
        ctx.font.render_to(s, (20, 20), "OPTIONS", config.PALETTE["accent"])
        for i, item in enumerate(self.items):
            text = item if item != "Viewport" else f"Viewport: {self.modes[self.mode_idx]}"
            ctx.font.render_to(s, (20, 50 + i * 16), text, config.PALETTE["warn"] if i == self.idx else config.PALETTE["text"])


class LevelSelectScene(Scene):
    def __init__(self) -> None:
        self.levels = sorted(Path("game/levels").glob("level_*.json"))
        self.idx = 0
        self.lb: list[dict] = []
        self.timer = 0.0

    def handle_event(self, event: pygame.event.Event, ctx: GameContext) -> Scene | None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return MenuScene()
            if event.key in (pygame.K_w, pygame.K_UP):
                self.idx = (self.idx - 1) % len(self.levels)
            elif event.key in (pygame.K_s, pygame.K_DOWN):
                self.idx = (self.idx + 1) % len(self.levels)
            elif event.key == pygame.K_RETURN:
                return LevelScene(self.idx)
        return None

    def update(self, dt: float, ctx: GameContext) -> Scene | None:
        self.timer += dt
        if self.timer > 1.0:
            self.timer = 0.0
            ctx.network.enqueue_leaderboard(self.levels[self.idx].stem)
        out = ctx.network.try_pop_leaderboard()
        if out is not None:
            self.lb = out[:5]
        return None

    def draw(self, ctx: GameContext) -> None:
        s = ctx.internal
        s.fill(config.PALETTE["bg"])
        ctx.font.render_to(s, (10, 10), "LEVEL SELECT", config.PALETTE["accent"])
        for i, p in enumerate(self.levels):
            lid = p.stem
            best = ctx.profile.best_times.get(lid, -1)
            txt = f"{lid} best={best if best>=0 else '-'}"
            ctx.font.render_to(s, (10, 28 + i * 12), txt, config.PALETTE["warn"] if i == self.idx else config.PALETTE["text"])
        y = 30
        for row in self.lb:
            ctx.font.render_to(s, (210, y), f"{row.get('player_name','?')} {row.get('best_time_ms','-')}", config.PALETTE["text"])
            y += 12


class LevelScene(Scene):
    def __init__(self, index: int) -> None:
        self.levels = sorted(Path("game/levels").glob("level_*.json"))
        self.index = index
        self.level = load_level(self.levels[self.index])
        self.profile = build_profile(self.index, self.level.difficulty_budget)
        self.solids = self._tiles()
        self.player = Player(pygame.Rect(*self.level.spawn, *config.PLAYER_SIZE))
        self.goal = pygame.Rect(*self.level.goal)
        self.rec = GhostRecorder()
        self.ghost_blob = ""
        self.rails = [RailSaw(f"rail_{i}", pygame.Vector2(*r["start"]), pygame.Vector2(*r["end"]), r.get("radius", 6), r.get("phase", 0.0)) for i, r in enumerate(self.level.rails)]
        self.lasers = [Laser(f"laser_{i}", pygame.Rect(*l["rect"]), l.get("phase", 0.0)) for i, l in enumerate(self.level.lasers)]
        self.falling = [FallingBlock(f"fall_{i}", pygame.Rect(*b["rect"])) for i, b in enumerate(self.level.falling_blocks)]
        self.patrols = [PatrolEnemy(f"pat_{i}", pygame.Rect(*p["rect"]), p["left"], p["right"]) for i, p in enumerate(self.level.patrols)]
        self.timer = 0.0
        self.complete = 0.0
        self.deaths = 0
        self.camera = pygame.Vector2(0, 0)
        self.t = 0.0
        self.prev_jump = False
        self.rng = random.Random(self.level.seed)

    def _tiles(self) -> list[pygame.Rect]:
        out=[]
        for y,row in enumerate(self.level.solids):
            for x,v in enumerate(row):
                if v: out.append(pygame.Rect(x*config.TILE_SIZE,y*config.TILE_SIZE,config.TILE_SIZE,config.TILE_SIZE))
        return out

    def _hurt(self) -> list[tuple[str, pygame.Rect]]:
        hurt=[("spike", pygame.Rect(*s)) for s in self.level.spikes]
        for h in self.rails:
            hurt += [(h.name, r) for r in h.hurt_rects(self.t, self.profile)]
        for h in self.lasers:
            hurt += [(h.name, r) for r in h.hurt_rects(self.t, self.profile)]
        for h in self.falling:
            hurt += [(h.name, r) for r in h.hurt_rects()]
        for h in self.patrols:
            hurt += [(h.name, r) for r in h.hurt_rects()]
        return hurt

    def handle_event(self, event: pygame.event.Event, ctx: GameContext) -> Scene | None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F3:
                ctx.debug_overlay = not ctx.debug_overlay
            if event.key == pygame.K_ESCAPE:
                return MenuScene()
        return None

    def update(self, dt: float, ctx: GameContext) -> Scene | None:
        self.t += dt
        if self.complete > 0:
            self.complete -= dt
            if self.complete <= 0:
                if self.index >= len(self.levels)-1:
                    return FinalScene()
                return LevelScene(self.index + 1)
            return None

        keys = pygame.key.get_pressed()
        jump_held = keys[pygame.K_SPACE]
        inp = InputState(
            left=keys[pygame.K_a] or keys[pygame.K_LEFT],
            right=keys[pygame.K_d] or keys[pygame.K_RIGHT],
            jump_pressed=jump_held and not self.prev_jump,
            jump_held=jump_held,
            restart=keys[pygame.K_r],
        )
        self.prev_jump = jump_held
        if inp.restart:
            self.deaths += 1
            self.player.rect.topleft = self.level.spawn
            self.player.vel.xy = (0, 0)

        self.player.update(dt, inp, self.solids)
        self.rec.push(inp)
        self.timer += dt

        for f in self.falling:
            f.update(dt, self.player.hitbox(), self.profile)
        for p in self.patrols:
            p.update(dt, self.profile, self.player.hitbox())

        for name, hr in self._hurt():
            if self.player.hitbox().colliderect(hr):
                self.deaths += 1
                self.player.rect.topleft = self.level.spawn
                self.player.vel.xy = (0, 0)
                break

        if self.player.hitbox().colliderect(self.goal):
            ms = int(self.timer * 1000)
            best = ctx.profile.best_times.get(self.level.level_id, 10**9)
            if ms < best:
                ctx.profile.best_times[self.level.level_id] = ms
                self.ghost_blob = self.rec.encode()
            ctx.network.enqueue_post_run({
                "level_id": self.level.level_id,
                "player_name": "local_player",
                "best_time_ms": ms,
                "deaths": self.deaths,
                "seed": self.level.seed,
                "replay_data": self.ghost_blob or "0",
            })
            self.complete = 2.0

        lead = config.CAMERA_LEAD if self.player.vel.x > 0 else -config.CAMERA_LEAD
        target_x = max(0, self.player.rect.centerx + lead - config.INTERNAL_RES[0]//2)
        target_y = max(0, self.player.rect.centery - config.INTERNAL_RES[1]//2)
        self.camera += (pygame.Vector2(target_x, target_y) - self.camera) * config.CAMERA_SMOOTH
        return None

    def draw(self, ctx: GameContext) -> None:
        s = ctx.internal
        c = config.PALETTE
        s.fill(c["bg"])
        ox = int((self.camera.x*0.2)%64)
        pygame.draw.rect(s,c["bg2"],pygame.Rect(-ox,40,800,30))
        for t in self.solids:
            r = world_to_screen_rect(t,self.camera)
            pygame.draw.rect(s,c["tile_shadow"],r.move(1,1))
            pygame.draw.rect(s,c["tile"],r)
            pygame.draw.rect(s,(15,15,25),r,1)
        for _,hr in self._hurt():
            pygame.draw.rect(s,c["danger"],world_to_screen_rect(hr,self.camera))
        goal = world_to_screen_rect(self.goal,self.camera)
        pygame.draw.rect(s,c["goal"],goal)
        pygame.draw.rect(s,c["accent"],goal.inflate(2,2),1)
        pygame.draw.rect(s,c["player"],world_to_screen_rect(self.player.rect,self.camera))

        debug=[]
        if ctx.debug_overlay:
            debug=[
                f"fps={ctx.clock.get_fps():.1f}",
                f"frame={ctx.perf.frame_ms:.2f}ms avg={ctx.perf.avg_ms:.2f} max={ctx.perf.max_ms:.2f}",
                f"haz={len(self._hurt())} q={ctx.network.queue_size()} online={ctx.network.online}",
            ]
            for t in self.solids:
                pygame.draw.rect(s,(70,130,255),world_to_screen_rect(t,self.camera),1)
            for _,hr in self._hurt():
                pygame.draw.rect(s,(255,30,30),world_to_screen_rect(hr,self.camera),1)
            pygame.draw.rect(s,(60,255,80),world_to_screen_rect(self.player.hitbox(),self.camera),1)
            pygame.draw.rect(s,(255,230,80),goal,1)

        ctx.hud.draw(
            s,
            current_time=self.timer,
            best_time_ms=ctx.profile.best_times.get(self.level.level_id),
            deaths=self.deaths,
            attempts=self.deaths + 1,
            paused=False,
            recording_ghost=True,
            online=ctx.network.online,
            progress=self.player.rect.centerx / max(1, self.goal.centerx),
            death_msg="",
            debug_lines=debug,
        )


class FinalScene(Scene):
    def __init__(self) -> None:
        self.story = [
            "El cuadradito huyo del laberinto...",
            "sobrevivio al drama, lasers y amor toxico.",
            "Ahora busca aventura... y terapia.",
        ]
        self.text = ""
        self.timer = 0.0
        self.idx = 0
        self.char = 0

    def handle_event(self, event: pygame.event.Event, ctx: GameContext) -> Scene | None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            return MenuScene()
        return None

    def update(self, dt: float, ctx: GameContext) -> Scene | None:
        self.timer += dt
        if self.idx < len(self.story) and self.timer > 0.035:
            self.timer = 0
            line = self.story[self.idx]
            self.char += 1
            self.text = line[:self.char]
            if self.char >= len(line):
                self.idx += 1
                self.char = 0
                ctx.audio.play("menu_select")
        return None

    def draw(self, ctx: GameContext) -> None:
        s = ctx.internal
        s.fill((0,0,0))
        pygame.draw.rect(s, config.PALETTE["player"], pygame.Rect(40, 120, 16, 16))
        ctx.font.render_to(s, (20, 24), "THE END", config.PALETTE["accent"])
        for i in range(self.idx):
            ctx.font.render_to(s, (20, 50 + i*16), self.story[i], config.PALETTE["text"])
        if self.idx < len(self.story):
            ctx.font.render_to(s, (20, 50 + self.idx*16), self.text, config.PALETTE["text"])
        ctx.font.render_to(s, (20, 156), "Enter: volver menu / New Game+", config.PALETTE["warn"])
