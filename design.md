# Design

## Entidades
- Player
- SolidTile
- OneWayPlatform (extensible)
- Spike
- Saw
- Goal
- Ghost (replay)

## Formato JSON de nivel
```json
{
  "level_id": "level_01",
  "width": 30,
  "height": 16,
  "solids": [[0,1]],
  "one_way": [],
  "spawn": [64, 400],
  "goal": [860, 430, 28, 28],
  "saws": [[300, 460, 14]],
  "spikes": [[450, 464, 64, 16]],
  "seed": 1001
}
```

## DB schema (runs)
- id (PK)
- level_id (indexed)
- player_name
- best_time_ms
- deaths
- seed
- replay_data (zlib+base64 json)
- created_at

## Replay/Ghost protocolo
1. Captura inputs por fixed tick: left/right/jump_pressed/jump_held.
2. Serializa como JSON compacto.
3. Comprime con zlib level 9.
4. Codifica base64 para transporte por API.
5. Playback aplica frames en orden con mismo fixed timestep para mantener determinismo.

## Timestep
Se usa semi-fixed loop con acumulador:
- Render variable.
- Física fija a `1/120` para precisión.
- `MAX_ACCUMULATOR` evita espiral de muerte.

## Backend resiliente
Si `/runs` falla, el cliente guarda en `game_local_runs.json`.
En cada submit exitoso, intenta sincronizar pendientes.
