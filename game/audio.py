from __future__ import annotations

import logging
import math
import struct
from pathlib import Path

import pygame

LOGGER = logging.getLogger("game.audio")


class AudioManager:
    @staticmethod
    def configure_pre_init() -> None:
        pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)

    def __init__(self) -> None:
        self.audio_enabled = False
        self.sfx_volume = 0.6
        self.music_volume = 0.25
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        try:
            pygame.mixer.init()
            self.audio_enabled = True
            LOGGER.info("Mixer initialized: %s", pygame.mixer.get_init())
        except Exception as exc:
            self.audio_enabled = False
            LOGGER.exception("Failed to init mixer: %s", exc)

    def _tone(self, hz: float, ms: int = 90) -> pygame.mixer.Sound | None:
        if not self.audio_enabled:
            return None
        sample_rate = 44100
        frames = int(sample_rate * (ms / 1000.0))
        raw = bytearray()
        amp = int(32767 * 0.25)
        for i in range(frames):
            v = int(math.sin(2.0 * math.pi * hz * i / sample_rate) * amp)
            raw.extend(struct.pack("<hh", v, v))
        return pygame.mixer.Sound(buffer=bytes(raw))

    def load(self) -> None:
        if not self.audio_enabled:
            LOGGER.warning("Audio disabled; using silent mode")
            return
        base = Path(__file__).resolve().parent / "assets" / "sfx"
        names = ["jump", "land", "death", "goal", "menu_move", "menu_select"]
        loaded = 0
        for name in names:
            path = base / f"{name}.wav"
            if path.exists():
                try:
                    snd = pygame.mixer.Sound(str(path))
                    snd.set_volume(self.sfx_volume)
                    self.sounds[name] = snd
                    loaded += 1
                except Exception as exc:
                    LOGGER.exception("Failed loading %s: %s", path, exc)

        if loaded == 0:
            LOGGER.warning("No SFX files found in %s, creating beep fallback", base)
            tones = {
                "jump": 660,
                "land": 220,
                "death": 110,
                "goal": 880,
                "menu_move": 330,
                "menu_select": 520,
            }
            for key, hz in tones.items():
                tone = self._tone(hz)
                if tone is not None:
                    tone.set_volume(self.sfx_volume)
                    self.sounds[key] = tone

    def play(self, name: str) -> None:
        if not self.audio_enabled:
            return
        snd = self.sounds.get(name)
        if snd is None:
            LOGGER.debug("Sound not loaded: %s", name)
            return
        snd.play()

    def test_sfx(self) -> None:
        self.play("menu_select")

    def set_sfx_volume(self, volume: float) -> None:
        self.sfx_volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            sound.set_volume(self.sfx_volume)

    def set_music_volume(self, volume: float) -> None:
        self.music_volume = max(0.0, min(1.0, volume))
        if self.audio_enabled:
            pygame.mixer.music.set_volume(self.music_volume)

    def debug_status(self) -> str:
        return f"audio={self.audio_enabled} mixer={pygame.mixer.get_init()}"
