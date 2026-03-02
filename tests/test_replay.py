from game.core.player import InputState
from game.core.replay import pack_input, unpack_input


def test_replay_bitmask_roundtrip() -> None:
    src = InputState(left=True, right=False, jump_pressed=True, jump_held=False)
    mask = pack_input(src)
    dst = unpack_input(mask)
    assert dst.left is True
    assert dst.right is False
    assert dst.jump_pressed is True
    assert dst.jump_held is False
