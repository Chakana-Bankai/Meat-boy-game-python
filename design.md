# Design

## Arquitectura
- `game/main.py`: loop principal con timestep semi-fijo + escalado pixel-art.
- `game/ui/scenes.py`: state machine (`MenuScene`, `LevelSelectScene`, `OptionsScene`, `LevelScene`).
- `game/ui/hud.py`: HUD desacoplado, render estable 60fps.
- `game/difficulty.py`: scalar por nivel + perfil de hazards.
- `game/core/hazards.py`: RailSaw, Laser telegraph, FallingBlock warning, PatrolEnemy.
- `game/audio.py`: AudioManager con fallback seguro.
- `server/`: FastAPI + SQLite para `/runs` y `/leaderboard/{level_id}`.

## Fixed timestep
- Física a `1/120` (`FIXED_DT`) con acumulador y cap `MAX_ACCUMULATOR`.
- Render a 60fps (`TARGET_FPS`) sobre surface interna `320x180`, luego upscale entero.

## Dificultad
- Cada nivel define `difficulty_budget` (1..10).
- `difficulty_scalar` escala hasta ~3x entre nivel 1 y 10.
- Hazards leen `DifficultyProfile` para subir velocidad/frecuencia.

## Replay
- Inputs por tick (left/right/jump) -> JSON compacto -> zlib -> base64.
- Se guarda en backend y sirve para ghost determinista local.

## Resiliencia online/offline
- API client hace `ping /health` periódico.
- Si `/runs` falla, guarda en `game_local_runs.json` y reintenta sync.
