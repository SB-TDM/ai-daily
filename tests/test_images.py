import struct
import zlib
from datetime import date
from ai_daily.aihot import Daily, Section, Story
from ai_daily.images import first_image_url, load_story_images, shrink_image


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


def test_command_fetch_sends_a_browser_user_agent(monkeypatch):
    import httpx
    from ai_daily.__main__ import _load_images

    seen = []

    class Resp:
        text = '<img src="/api/img-proxy?u=https%3A%2F%2Fexample.com%2Fa.png">'
        content = _png(8, 8)

    def fake_get(url, timeout=None, follow_redirects=None, headers=None):
        seen.append(headers or {})
        return Resp()

    monkeypatch.setattr(httpx, "get", fake_get)
    daily = Daily(
        date(2026, 10, 21),
        "Lead",
        "Deck",
        (Section("产品", (Story("Other", "b", "S", "https://aihot.news/items/other"),)),),
    )
    found = _load_images(daily)
    assert "Mozilla" in seen[0].get("User-Agent", "")
    assert found["https://aihot.news/items/other"].startswith("data:image/jpeg;base64,")


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
