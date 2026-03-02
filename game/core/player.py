from __future__ import annotations

from dataclasses import dataclass, field
import pygame

from game import config
from game.core.physics import CollisionResult, resolve_axis_aligned


@dataclass
class InputState:
    left: bool = False
    right: bool = False
    jump_pressed: bool = False
    jump_held: bool = False
    restart: bool = False


@dataclass
class Player:
    rect: pygame.Rect
    vel: pygame.Vector2 = field(default_factory=lambda: pygame.Vector2(0, 0))
    coyote_timer: float = 0.0
    jump_buffer_timer: float = 0.0
    was_on_ground: bool = False

    def hitbox(self) -> pygame.Rect:
        ox, oy = config.PLAYER_HITBOX_OFFSET
        w, h = config.PLAYER_HITBOX_SIZE
        return pygame.Rect(self.rect.x + ox, self.rect.y + oy, w, h)

    def set_from_hitbox(self, hb: pygame.Rect) -> None:
        ox, oy = config.PLAYER_HITBOX_OFFSET
        self.rect.x = hb.x - ox
        self.rect.y = hb.y - oy

    def update(self, dt: float, input_state: InputState, solids: list[pygame.Rect]) -> CollisionResult:
        if input_state.jump_pressed:
            self.jump_buffer_timer = config.JUMP_BUFFER_TIME
        else:
            self.jump_buffer_timer = max(0.0, self.jump_buffer_timer - dt)

        axis = float(input_state.right) - float(input_state.left)
        accel = config.RUN_ACCEL if abs(axis) > 0 else config.RUN_DECEL
        if not self.was_on_ground:
            accel = config.AIR_ACCEL if abs(axis) > 0 else accel

        target = axis * config.MAX_RUN_SPEED
        if self.vel.x < target:
            self.vel.x = min(target, self.vel.x + accel * dt)
        elif self.vel.x > target:
            self.vel.x = max(target, self.vel.x - accel * dt)

        self.vel.y += config.GRAVITY * dt

        if self.coyote_timer > 0 and self.jump_buffer_timer > 0:
            self.vel.y = config.JUMP_VELOCITY
            self.jump_buffer_timer = 0
            self.coyote_timer = 0

        if not input_state.jump_held and self.vel.y < 0:
            self.vel.y *= config.JUMP_CUT_MULTIPLIER

        hb = self.hitbox()
        collision = resolve_axis_aligned(hb, solids, self.vel, dt)
        self.set_from_hitbox(hb)

        if collision.on_ground:
            self.coyote_timer = config.COYOTE_TIME
        else:
            self.coyote_timer = max(0.0, self.coyote_timer - dt)

        if not collision.on_ground and (collision.on_wall_left or collision.on_wall_right):
            self.vel.y = min(self.vel.y, config.WALL_SLIDE_SPEED)
            if input_state.jump_pressed:
                self.vel.x = config.WALL_JUMP_X if collision.on_wall_left else -config.WALL_JUMP_X
                self.vel.y = config.WALL_JUMP_Y

        self.was_on_ground = collision.on_ground
        return collision
