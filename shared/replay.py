from __future__ import annotations

import base64
import json
import zlib
from typing import Iterable


InputFrame = dict[str, bool]


def compress_replay(frames: Iterable[InputFrame]) -> str:
    payload = json.dumps(list(frames), separators=(",", ":")).encode("utf-8")
    compressed = zlib.compress(payload, level=9)
    return base64.b64encode(compressed).decode("ascii")


def decompress_replay(blob: str) -> list[InputFrame]:
    compressed = base64.b64decode(blob.encode("ascii"))
    payload = zlib.decompress(compressed)
    parsed = json.loads(payload.decode("utf-8"))
    if not isinstance(parsed, list):
        raise ValueError("Replay payload must be a list")
    return parsed
