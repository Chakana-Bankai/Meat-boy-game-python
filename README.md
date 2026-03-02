# Meat Boy Style Platformer (Python)

Proyecto full-stack con cliente `pygame-ce` y backend `FastAPI` para runs/leaderboard local.

## Requisitos
- Python 3.12+
- pip

## Instalación
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecutar backend
```bash
python -m server.app
```
API en `http://127.0.0.1:8000`.

## Ejecutar juego
```bash
python -m game.main
```

## Tests
```bash
pytest -q
```

## Build ejecutable (PyInstaller)
```bash
pyinstaller game.spec
```

## Scripts rápidos
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

## Estructura
- `game/`: cliente pygame
- `server/`: API FastAPI + SQLite
- `shared/`: schemas y utilidades compartidas
- `tests/`: unit tests
- `design.md`: decisiones técnicas
- `qa_checklist.md`: validación manual
