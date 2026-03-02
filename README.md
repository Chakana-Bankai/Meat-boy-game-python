# Meat Boy Style Platformer (Python)

## Run
```bash
python -m game.main
```

Server (optional):
```bash
uvicorn server.main:app --reload
```

## Controls
- Move: A/D or Arrows
- Jump: Space (wall slide + wall jump enabled)
- Retry: R
- Debug/perf overlay: F3
- Fullscreen toggle: F11

## Viewport modes
- Internal render: `640x360`.
- Final output handled by `ViewportManager`:
  - `letterbox` (default)
  - `integer` (pixel-perfect)
  - `stretch`
- Toggle viewport mode from `Options`.

## Performance checks
- F3 overlay shows: FPS, frame ms avg/max spikes, hazards count, network queue size, online status.
- Networking is async worker-thread based: gameplay loop never performs blocking HTTP.

## Final scene
Complete all 10 levels to reach `FinalScene` (8-bit comedy typing sequence + return menu).

## Quick validation
1. Resize window repeatedly and verify centered render (no top-offset shrink).
2. Toggle F11 in 1080p and verify proper centering/scaling.
3. Play with server off; complete level; verify no hitch + offline run queueing.
4. Start server; verify queued runs sync and leaderboard fetch in LevelSelect.
