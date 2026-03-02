from game.difficulty import difficulty_scalar


def test_difficulty_scales_up():
    assert difficulty_scalar(0, 1) < difficulty_scalar(9, 10)
