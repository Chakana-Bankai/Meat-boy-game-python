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
        self.music_channel: pygame.mixer.Channel | None = None
        self.music_sound: pygame.mixer.Sound | None = None
        try:
            pygame.mixer.init()
            self.audio_enabled = True
            LOGGER.info("Mixer initialized: %s", pygame.mixer.get_init())
        except Exception as exc:
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

    def _square_wave(self, hz: float, duration_s: float) -> bytes:
        sample_rate = 44100
        frames = int(sample_rate * duration_s)
        amp = int(32767 * 0.18)
        out = bytearray()
        period = max(1, int(sample_rate / hz))
        for i in range(frames):
            v = amp if (i % period) < (period // 2) else -amp
            out.extend(struct.pack("<hh", v, v))
        return bytes(out)

    def _generate_chiptune(self) -> pygame.mixer.Sound | None:
        if not self.audio_enabled:
            return None
        notes = [261.63, 329.63, 392.0, 523.25, 392.0, 329.63]
        chunks = [self._square_wave(n, 0.18) for n in notes]
        return pygame.mixer.Sound(buffer=b"".join(chunks))

    def load(self) -> None:
        if not self.audio_enabled:
            LOGGER.warning("Audio disabled; using silent mode")
            return

        base = Path(__file__).resolve().parent
        sfx_dir = base / "assets" / "sfx"
        music_dir = base / "assets" / "music"

        names = ["jump", "land", "death", "goal", "menu_move", "menu_select"]
        loaded = 0
        for name in names:
            path = sfx_dir / f"{name}.wav"
            if path.exists():
                snd = pygame.mixer.Sound(str(path))
                snd.set_volume(self.sfx_volume)
                self.sounds[name] = snd
                loaded += 1

        if loaded == 0:
            tones = {"jump": 660, "land": 220, "death": 110, "goal": 880, "menu_move": 330, "menu_select": 520}
            for key, hz in tones.items():
                tone = self._tone(hz)
                if tone:
                    tone.set_volume(self.sfx_volume)
                    self.sounds[key] = tone

        music_asset = music_dir / "music.ogg"
        if music_asset.exists():
            try:
                pygame.mixer.music.load(str(music_asset))
                pygame.mixer.music.set_volume(self.music_volume)
                pygame.mixer.music.play(-1)
            except Exception as exc:
                LOGGER.warning("music.ogg failed (%s), fallback chiptune", exc)
                self.music_sound = self._generate_chiptune()
        else:
            self.music_sound = self._generate_chiptune()

        if self.music_sound is not None:
            self.music_sound.set_volume(self.music_volume)
            self.music_channel = pygame.mixer.Channel(7)
            self.music_channel.play(self.music_sound, loops=-1)

    def play(self, name: str) -> None:
        if self.audio_enabled and name in self.sounds:
            self.sounds[name].play()

    def test_sfx(self) -> None:
        self.play("menu_select")

    def set_sfx_volume(self, volume: float) -> None:
        self.sfx_volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            sound.set_volume(self.sfx_volume)

    def set_music_volume(self, volume: float) -> None:
        self.music_volume = max(0.0, min(1.0, volume))
        if self.music_sound is not None:
            self.music_sound.set_volume(self.music_volume)
        if self.audio_enabled:
            pygame.mixer.music.set_volume(self.music_volume)

    def debug_status(self) -> str:
        return f"audio={self.audio_enabled} mixer={pygame.mixer.get_init()}"
