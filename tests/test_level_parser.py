from pathlib import Path

from game.core.level import load_level


def test_load_level_sample():
    level = load_level(Path('game/levels/level_01.json'))
    assert level.level_id == 'level_01'
    assert level.width > 0
    assert len(level.solids) == level.height
