# Meat Boy Style Platformer (Python)

Cliente arcade 2D (`pygame-ce`) + backend local (`FastAPI`) para runs y leaderboard.

## Requisitos
- Python 3.12+ (funciona también con 3.10+ en desarrollo)
- `pip`

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

## Tests
```bash
pytest -q
```

## Build (PyInstaller)
```bash
pyinstaller game.spec
```

## Scripts
Unix:
```bash
./scripts/run_server.sh
./scripts/run_game.sh
./scripts/test.sh
```
Windows:
```bat
scripts\run_server.bat
scripts\run_game.bat
scripts\test.bat
```
