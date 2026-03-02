# Design

## Núcleo técnico
- Loop semi-fixed (`FIXED_DT=1/120`) + render a 60 FPS.
- Colisiones en world coordinates exclusivamente.
- Cámara con lead suave según velocidad horizontal.

## Audio robusto
- `pygame.mixer.pre_init(44100, -16, 2, 512)` antes de `pygame.init()`.
- `AudioManager` con logging, fallback beeps y botón `Test SFX` en Options.

## Hitboxes y debug
- Player usa sprite rect + hitbox más pequeña (offset fijo).
- Hazards exponen `hurt_rects()` y `telegraph_rects()`.
- F3 activa overlay de hitboxes, estado audio/api y FPS.

## LevelComplete resiliente
- POST/GET server con timeout corto y fallback local.
- Si replay falla, se loggea y se envía payload mínimo.
- Panel de completado tolera leaderboard vacío.
