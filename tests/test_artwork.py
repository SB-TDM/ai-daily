import base64
from io import BytesIO
import json

from PIL import Image
import pytest

from ai_daily.artwork import cache_key, request_image, read_image
from ai_daily.settings import load_image_settings


def settings(root, **extra):
    data = root / "data"
    data.mkdir(exist_ok=True)
    (data / "image.json").write_text(json.dumps({"model": "m", "base_url": "https://example.test/v1/", **extra}), encoding="utf-8")
    (data / "image-secret.json").write_text('{"key": "secret"}', encoding="utf-8")
    return load_image_settings(root)


def test_request_keeps_endpoint_and_controlled_fields(tmp_path):
    config = settings(tmp_path, quality="low", extra={"prompt": "unsafe override", "n": 8})
    buffer = BytesIO()
    Image.new("RGB", (2, 2)).save(buffer, format="PNG")
    raw = buffer.getvalue()
    captured = []
    def open_request(request, timeout):
        captured.append(request)
        return BytesIO(json.dumps({"data": [{"b64_json": base64.b64encode(raw).decode()}]}).encode())
    assert request_image(config, "Brand 42%", "stats", scene="Blank clay blocks", opener=open_request) == raw
    request = captured[0]
    body = json.loads(request.data)
    assert request.full_url == "https://example.test/v1/images/generations"
    assert body["model"] == "m" and body["n"] == 1 and body["quality"] == "low"
    assert "Blank clay blocks" in body["prompt"] and "Brand 42%" not in body["prompt"]
    assert body["prompt"] != "unsafe override"


def test_cache_key_changes_with_content_model_and_scene(tmp_path):
    config = settings(tmp_path)
    first = {"title": "same prefix " * 10 + "A", "summary": "summary"}
    second = {**first, "title": "same prefix " * 10 + "B"}
    key = cache_key(config, first)
    assert key != cache_key(config, second)
    assert key != cache_key(config, {**first, "summary": "revised"})
    assert key != cache_key(config, first, scene="different scene")
    other = settings(tmp_path, model="different")
    assert key != cache_key(other, first)


def test_image_validation_rejects_non_image_payload():
    with pytest.raises(ValueError):
        read_image(b"invalid")
