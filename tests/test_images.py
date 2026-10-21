import struct
import zlib
from datetime import date
from ai_daily.aihot import Daily, Section, Story
from ai_daily.images import first_image_url, illustrate_first, load_story_images, shrink_image


def _png(width: int, height: int) -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    raw = b"".join(b"\x00" + bytes((180, 40, 60)) * width for _ in range(height))
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


def test_first_image_url_uses_proxied_article_image_not_icons():
    html = """
    <img src="data:image/png;base64,aaaa">
    <img src="/beian.png">
    <img alt="chart" src="/api/img-proxy?u=https%3A%2F%2Fexample.com%2Fa.png">
    """
    assert first_image_url(html, "https://aihot.news") == "https://aihot.news/api/img-proxy?u=https%3A%2F%2Fexample.com%2Fa.png"


def test_first_image_url_falls_back_to_og_image():
    html = '<meta property="og:image" content="https://cdn.example/a.jpg">'
    assert first_image_url(html, "https://aihot.news") == "https://cdn.example/a.jpg"
    assert first_image_url("<p>none</p>", "https://aihot.news") is None


def test_shrink_image_returns_a_jpeg_no_wider_than_asked():
    from io import BytesIO
    from PIL import Image

    wide = shrink_image(_png(900, 500), wide=160)
    assert wide.startswith("data:image/jpeg;base64,")
    raw = __import__("base64").b64decode(wide.split(",", 1)[1])
    assert Image.open(BytesIO(raw)).size[0] <= 160


def test_illustrate_first_asks_only_for_the_first_story_of_each_section():
    daily = Daily(
        date(2026, 10, 21),
        "Lead",
        "Deck",
        (
            Section("模型", (Story("Mercury", "很快。", "S", "https://aihot.news/items/mercury"), Story("Skip", "不画。", "S", "https://aihot.news/items/skip"))),
            Section("产品", (Story("Lead", "开源。", "S", "https://aihot.news/items/lead"),)),
        ),
    )
    asked = []

    def generate(title: str, summary: str) -> bytes:
        asked.append((title, summary))
        if title == "Mercury":
            raise RuntimeError("down")
        return _png(20, 10)

    found = illustrate_first(daily, generate)
    assert asked == [("Mercury", "很快。"), ("Lead", "开源。")]
    assert "https://aihot.news/items/mercury" not in found
    assert "https://aihot.news/items/skip" not in found
    assert found["https://aihot.news/items/lead"].startswith("data:image/jpeg;base64,")


def test_missing_image_key_does_not_call_the_model(monkeypatch):
    import httpx
    from ai_daily.__main__ import _load_images

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    calls = []
    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: calls.append(args))
    daily = Daily(date(2026, 10, 21), "Lead", "Deck", (Section("产品", (Story("Lead", "开源。", "S", "https://aihot.news/items/lead"),)),))
    assert _load_images(daily) == {}
    assert calls == []


def test_load_story_images_skips_a_failed_page_and_keeps_the_rest():
    daily = Daily(
        date(2026, 10, 21),
        "Lead",
        "Deck",
        (
            Section(
                "产品",
                (
                    Story("Lead", "a", "S", "https://aihot.news/items/lead"),
                    Story("Other", "b", "S", "https://aihot.news/items/other"),
                ),
            ),
        ),
    )

    def get_text(url: str) -> str:
        if url.endswith("lead"):
            raise RuntimeError("down")
        return '<img src="/api/img-proxy?u=https%3A%2F%2Fexample.com%2Fa.png">'

    def get_bytes(url: str) -> bytes:
        return _png(20, 10)

    found = load_story_images(daily, get_text, get_bytes)
    assert "https://aihot.news/items/lead" not in found
    assert found["https://aihot.news/items/other"].startswith("data:image/jpeg;base64,")
