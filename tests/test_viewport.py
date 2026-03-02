from game.core.viewport import ViewportManager


def test_viewport_centered_letterbox() -> None:
    vp = ViewportManager((640, 360), "letterbox")
    vp.recalculate((1920, 1080))
    assert vp.viewport.dest.topleft == (0, 0)
    assert vp.viewport.dest.size == (1920, 1080)


def test_viewport_integer_centering() -> None:
    vp = ViewportManager((640, 360), "integer")
    vp.recalculate((1366, 768))
    assert vp.viewport.dest.width % 640 == 0
    assert vp.viewport.dest.height % 360 == 0
