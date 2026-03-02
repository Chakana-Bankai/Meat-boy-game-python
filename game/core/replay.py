from __future__ import annotations

from dataclasses import dataclass, field

from game.core.player import InputState
from shared.replay import compress_replay, decompress_replay

LEFT = 1
RIGHT = 2
JUMP_PRESSED = 4
JUMP_HELD = 8


def pack_input(inp: InputState) -> int:
    mask = 0
    mask |= LEFT if inp.left else 0
    mask |= RIGHT if inp.right else 0
    mask |= JUMP_PRESSED if inp.jump_pressed else 0
    mask |= JUMP_HELD if inp.jump_held else 0
    return mask


def unpack_input(mask: int) -> InputState:
    return InputState(
        left=bool(mask & LEFT),
        right=bool(mask & RIGHT),
        jump_pressed=bool(mask & JUMP_PRESSED),
        jump_held=bool(mask & JUMP_HELD),
        restart=False,
    )


@dataclass
class GhostRecorder:
    frames: bytearray = field(default_factory=bytearray)

    def push(self, input_state: InputState) -> None:
        self.frames.append(pack_input(input_state) & 0xFF)

    def encode(self) -> str:
        return compress_replay(list(self.frames))


@dataclass
class GhostPlayback:
    frames: list[int]
    index: int = 0

    @classmethod
    def from_blob(cls, blob: str) -> "GhostPlayback":
        data = decompress_replay(blob)
        return cls(frames=[int(v) for v in data])

    def next(self) -> InputState:
        if self.index >= len(self.frames):
            return InputState()
        mask = self.frames[self.index]
        self.index += 1
        return unpack_input(mask)
