from __future__ import annotations

from pathlib import Path
import pygame


class AudioManager:
    def __init__(self) -> None:
        self.enabled = False
        self.sfx_volume = 0.5
        self.music_volume = 0.25
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        try:
            pygame.mixer.init()
            self.enabled = True
        except Exception:
            self.enabled = False

    def load(self, base: Path = Path("game/assets/audio")) -> None:
        if not self.enabled:
            return
        for name in ["jump", "land", "death", "goal", "menu_move", "menu_select"]:
            path = base / f"{name}.wav"
            if path.exists():
                self.sounds[name] = pygame.mixer.Sound(str(path))
                self.sounds[name].set_volume(self.sfx_volume)

    def play(self, name: str) -> None:
        if not self.enabled:
            return
        snd = self.sounds.get(name)
        if snd:
            snd.play()

    def set_sfx_volume(self, volume: float) -> None:
        self.sfx_volume = max(0.0, min(1.0, volume))
        for s in self.sounds.values():
            s.set_volume(self.sfx_volume)

    def set_music_volume(self, volume: float) -> None:
        self.music_volume = max(0.0, min(1.0, volume))
        if self.enabled:
            pygame.mixer.music.set_volume(self.music_volume)
