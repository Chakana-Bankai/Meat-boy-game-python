from __future__ import annotations

from dataclasses import dataclass
import math
import pygame

from game.difficulty import DifficultyProfile


@dataclass
class RailSaw:
    start: pygame.Vector2
    end: pygame.Vector2
    radius: int
    phase: float

    def rect(self, t: float, profile: DifficultyProfile) -> pygame.Rect:
        s = (math.sin((t * profile.saw_speed + self.phase) * math.pi * 2.0) + 1.0) * 0.5
        p = self.start.lerp(self.end, s)
        return pygame.Rect(int(p.x - self.radius), int(p.y - self.radius), self.radius * 2, self.radius * 2)


@dataclass
class Laser:
    rect: pygame.Rect
    phase: float

    def state(self, t: float, profile: DifficultyProfile) -> tuple[bool, bool]:
        cycle = profile.laser_cycle
        u = ((t + self.phase) % cycle) / cycle
        active = u > 0.35
        telegraph = 0.25 < u <= 0.35
        return active, telegraph


@dataclass
class FallingBlock:
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


@dataclass
class PatrolEnemy:
    rect: pygame.Rect
    left: int
    right: int
    direction: int = 1

    def update(self, dt: float, profile: DifficultyProfile) -> None:
        self.rect.x += int(self.direction * profile.patrol_speed * dt)
        if self.rect.left <= self.left:
            self.direction = 1
        elif self.rect.right >= self.right:
            self.direction = -1
