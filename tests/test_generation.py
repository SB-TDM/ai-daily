from datetime import datetime, timezone
from io import BytesIO
import json

from PIL import Image
import pytest

import ai_daily.generate as generation
from ai_daily.generate import generate_poster
from ai_daily.storage import generation_lock

NOW = datetime(2026, 10, 22, 4, tzinfo=timezone.utc)


def report():
    return {"date": "2026-10-22",
            "lead": {"title": "Lead", "leadParagraph": "Full paragraph."},
            "sections": [
                {"label": "Industry", "items": [{"title": "Lead", "summary": "A"}, {"title": "Later"}]},
                {"label": "Models", "items": [{"title": "Other", "summary": "B"}]},
                {"label": "快讯", "items": [{"title": "Flash section"}]}],
            "flashes": [{"title": "Flash"}]}


def png(color="red"):
    buffer = BytesIO()
    Image.new("RGB", (20, 20), color).save(buffer, format="PNG")
    return buffer.getvalue()


def configure(root, model="model-a"):
    data = root / "data"
    data.mkdir(parents=True, exist_ok=True)
    (data / "image.json").write_text(json.dumps({"model": model, "base_url": "https://example.test/v1", "quality": "low"}), encoding="utf-8")
    (data / "image-secret.json").write_text(json.dumps({"key": "private-test-key"}), encoding="utf-8")


def forbidden(*args, **kwargs):
    pytest.fail("Unexpected network call")


def test_only_first_items_generated_and_one_failure_keeps_paper(tmp_path):
    configure(tmp_path)
    calls = []
    def image(settings, title, summary, *, scene=None):
        calls.append((title, summary))
        if title == "Lead":
            raise TimeoutError("private-test-key must not escape")
        return png()
    result = generate_poster(tmp_path, now=NOW, report=report(), fetch_image=image)
    assert result.status == "ready" and result.path.exists()
    assert result.illustrations == 1 and result.expected_illustrations == 2
    assert calls == [("Lead", "A"), ("Other", "B")]


def test_no_settings_produces_text_without_image_network(tmp_path):
    result = generate_poster(tmp_path, now=NOW, report=report(), fetch_image=forbidden)
    assert result.status == "ready" and result.illustrations == 0


def test_settings_are_snapshotted_before_fetch_and_reused_for_all_images(tmp_path):
    configure(tmp_path)
    seen = []
    def daily(etag):
        configure(tmp_path, "model-b")
        return 200, "first", {"report": report()}
    def image(settings, title, summary, *, scene=None):
        seen.append((settings.model, settings.extra["quality"]))
        assert "private-test-key" not in repr(settings)
        return png()
    result = generate_poster(tmp_path, now=NOW, fetch_daily=daily, fetch_image=image)
    assert result.status == "ready"
    assert seen == [("model-a", "low"), ("model-a", "low")]


def test_valid_existing_poster_does_not_fetch(tmp_path):
    assert generate_poster(tmp_path, now=NOW, report=report(), offline=True).status == "ready"
    result = generate_poster(tmp_path, now=NOW, fetch_daily=forbidden, fetch_image=forbidden)
    assert result.status == "already_ready"


def test_force_reuses_images_but_refetches_report_with_etag(tmp_path):
    configure(tmp_path)
    assert generate_poster(tmp_path, now=NOW, fetch_daily=lambda etag: (200, '"version-one"', {"report": report()}), fetch_image=lambda *args, **kwargs: png()).status == "ready"
    seen = []
    def fetch(etag):
        seen.append(etag)
        return 304, None, None
    result = generate_poster(tmp_path, now=NOW, force=True, fetch_daily=fetch, fetch_image=forbidden)
    assert result.status == "ready" and result.illustrations == 2
    assert seen == ['"version-one"']


def test_304_without_cache_is_not_ready(tmp_path):
    result = generate_poster(tmp_path, now=NOW, fetch_daily=lambda etag: (304, None, None))
    assert result.status == "not_ready"
    assert not (tmp_path / "data" / "posters" / "2026-10-22.png").exists()


def test_stale_report_never_generates_or_saves(tmp_path):
    configure(tmp_path)
    stale = report()
    stale["date"] = "2026-10-21"
    result = generate_poster(tmp_path, now=NOW, report=stale, fetch_image=forbidden)
    assert result.status == "not_ready" and result.path is None


def test_busy_lock_refuses_even_if_existing_poster_is_ready(tmp_path):
    generate_poster(tmp_path, now=NOW, report=report(), offline=True)
    with generation_lock(tmp_path):
        result = generate_poster(tmp_path, now=NOW, fetch_daily=forbidden)
        assert result.status == "busy"
    assert generate_poster(tmp_path, now=NOW).status == "already_ready"


def test_failed_force_keeps_previous_poster_and_releases_lock(tmp_path, monkeypatch):
    result = generate_poster(tmp_path, now=NOW, report=report(), offline=True)
    before = result.path.read_bytes()
    def fail(*args):
        raise OSError("renderer failure")
    monkeypatch.setattr(generation, "render_poster", fail)
    assert generate_poster(tmp_path, now=NOW, report=report(), force=True, offline=True).status == "not_ready"
    assert result.path.read_bytes() == before
    assert generate_poster(tmp_path, now=NOW).status == "already_ready"
    assert list(result.path.parent.glob("*.tmp")) == []


def test_offline_never_calls_network_and_requires_report_or_cache(tmp_path):
    assert generate_poster(tmp_path, now=NOW, offline=True, fetch_daily=forbidden, fetch_image=forbidden).status == "not_ready"
    configure(tmp_path)
    result = generate_poster(tmp_path, now=NOW, report=report(), offline=True, fetch_daily=forbidden, fetch_image=forbidden)
    assert result.status == "ready" and result.illustrations == 0


def test_invalid_image_bytes_are_not_cached(tmp_path):
    configure(tmp_path)
    result = generate_poster(tmp_path, now=NOW, report=report(), fetch_image=lambda *args, **kwargs: b"not an image")
    assert result.status == "ready" and result.illustrations == 0
    assert list((tmp_path / "data" / "artwork").glob("*.png")) == []


def test_tampered_existing_png_is_rebuilt(tmp_path):
    path = tmp_path / "data" / "posters" / "2026-10-22.png"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"incomplete")
    result = generate_poster(tmp_path, now=NOW, report=report(), offline=True)
    assert result.status == "ready"
    with Image.open(path) as image:
        assert image.format == "PNG" and image.width == 760
