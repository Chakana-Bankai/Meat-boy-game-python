from __future__ import annotations

from dataclasses import dataclass, field

from game.core.player import InputState
from shared.replay import compress_replay, decompress_replay


@dataclass
class GhostRecorder:
    frames: list[dict[str, bool]] = field(default_factory=list)

    def push(self, input_state: InputState) -> None:
        self.frames.append(
            {
                "left": input_state.left,
                "right": input_state.right,
                "jump_pressed": input_state.jump_pressed,
                "jump_held": input_state.jump_held,
            }
        )

    def encode(self) -> str:
        return compress_replay(self.frames)


@dataclass
class GhostPlayback:
    frames: list[dict[str, bool]]
    index: int = 0

    @classmethod
    def from_blob(cls, blob: str) -> "GhostPlayback":
        return cls(frames=decompress_replay(blob))

    def next(self) -> InputState:
        if self.index >= len(self.frames):
            return InputState()
        frame = self.frames[self.index]
        self.index += 1
        return InputState(**frame, restart=False)
