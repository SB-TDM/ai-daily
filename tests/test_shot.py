import pytest
from ai_daily.shot import MAX_IMAGE_BYTES, accept_image

def test_accepts_a_small_png():
    png = b"\x89PNG" + b"ok"
    assert accept_image(png) == png

def test_rejects_a_broken_or_oversized_image():
    with pytest.raises(RuntimeError):
        accept_image(b"not-a-png")
    with pytest.raises(RuntimeError):
        accept_image(b"\x89PNG" + b"x" * MAX_IMAGE_BYTES)
