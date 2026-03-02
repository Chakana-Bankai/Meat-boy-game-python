# Meat Boy Style Platformer (Python)

Cliente arcade 2D (`pygame-ce`) + backend local (`FastAPI`) para runs y leaderboard.

## Instalación
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecutar server
```bash
uvicorn server.main:app --reload
# o
python -m server.app
```

## Ejecutar juego
```bash
python -m game.main
```

## Controles
- Menús: `W/S` o `↑/↓`, `Enter`, `Esc`
- Juego: `A/D` o `←/→`, `Space`, `R` (retry), `Esc` (pause)
- Pause: `Esc` resume, `O` options, `Q` menu
- Debug overlay: `F3`

## Pruebas rápidas manuales
1. Ir a Options -> `Test SFX` y verificar audio.
2. Presionar `F3` y revisar hitboxes (player verde, sólidos azul, hazards rojo, goal amarillo).
3. Apagar server, completar nivel y verificar `Saved offline`.
4. Levantar server de nuevo y repetir completado para sincronización.

## Tests
```bash
pytest -q
```

## Build (PyInstaller)
```bash
pyinstaller game.spec
```
