from __future__ import annotations

from dataclasses import dataclass
import math
import pygame

from game.difficulty import DifficultyProfile


@dataclass
class RailSaw:
    name: str
    start: pygame.Vector2
    end: pygame.Vector2
    radius: int
    phase: float

    def hurt_rects(self, t: float, profile: DifficultyProfile) -> list[pygame.Rect]:
        s = (math.sin((t * profile.saw_speed + self.phase) * math.pi * 2.0) + 1.0) * 0.5
        p = self.start.lerp(self.end, s)
        return [pygame.Rect(int(p.x - self.radius), int(p.y - self.radius), self.radius * 2, self.radius * 2)]

    def telegraph_rects(self, _t: float, _profile: DifficultyProfile) -> list[pygame.Rect]:
        return []


@dataclass
class Laser:
    name: str
    rect: pygame.Rect
    phase: float

    def state(self, t: float, profile: DifficultyProfile) -> tuple[bool, bool]:
        cycle = profile.laser_cycle
        u = ((t + self.phase) % cycle) / cycle
        active = u > 0.25
        telegraph = 0.0 <= u <= 0.25
        return active, telegraph

    def hurt_rects(self, t: float, profile: DifficultyProfile) -> list[pygame.Rect]:
        active, _ = self.state(t, profile)
        return [self.rect] if active else []

    def telegraph_rects(self, t: float, profile: DifficultyProfile) -> list[pygame.Rect]:
        active, tele = self.state(t, profile)
        return [] if active or not tele else [self.rect]


@dataclass
class FallingBlock:
    name: str
    rect: pygame.Rect
    triggered: bool = False
    warning_timer: float = 0.0
    velocity_y: float = 0.0

    def update(self, dt: float, player: pygame.Rect, profile: DifficultyProfile) -> None:
        trigger_zone = self.rect.inflate(8, 32)
        if not self.triggered and trigger_zone.colliderect(player):
            self.triggered = True
            self.warning_timer = profile.falling_delay
        if self.triggered:
            if self.warning_timer > 0:
                self.warning_timer -= dt
            else:
                self.velocity_y += 700 * dt * profile.scalar
                self.rect.y += int(self.velocity_y * dt)

    def hurt_rects(self) -> list[pygame.Rect]:
        if self.triggered and self.warning_timer <= 0:
            return [self.rect]
        return []

    def telegraph_rects(self) -> list[pygame.Rect]:
        return [self.rect] if self.triggered and self.warning_timer > 0 else []


@dataclass
class PatrolEnemy:
    name: str
    rect: pygame.Rect
    left: int
    right: int
    direction: int = 1
    chase_cooldown: float = 0.0

    def update(self, dt: float, profile: DifficultyProfile, player: pygame.Rect) -> None:
        if self.chase_cooldown <= 0 and abs(player.centerx - self.rect.centerx) < 40:
            self.direction = 1 if player.centerx > self.rect.centerx else -1
            self.chase_cooldown = 0.6
        self.chase_cooldown = max(0.0, self.chase_cooldown - dt)
        self.rect.x += int(self.direction * profile.patrol_speed * dt)
        if self.rect.left <= self.left:
            self.direction = 1
        elif self.rect.right >= self.right:
            self.direction = -1

    def hurt_rects(self) -> list[pygame.Rect]:
        return [self.rect]
