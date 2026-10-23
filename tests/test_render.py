from io import BytesIO

from PIL import Image, ImageDraw
import pytest

from ai_daily.render import PosterTooLarge, fit_png, render_poster


def report(items=None):
    return {"date": "2026-10-22",
            "lead": {"title": "OpenAI 披露 Patch the Planet 计划借助 GPT-5.6 Sol 发现 PHP 关键漏洞并协调全球修复",
                     "leadParagraph": "完整导语。"},
            "sections": [{"label": "模型", "items": items or []}], "flashes": []}


def test_png_preserves_approved_headline_and_all_copy(monkeypatch):
    texts = []
    original = ImageDraw.ImageDraw.text
    def capture(draw, xy, text, *args, **kwargs):
        texts.append((text, kwargs["font"].size))
        return original(draw, xy, text, *args, **kwargs)
    monkeypatch.setattr(ImageDraw.ImageDraw, "text", capture)
    summary = "摘要必须完整保留。" * 30
    raw = render_poster(report([{"title": "一条新闻", "summary": summary}]), {})
    with Image.open(BytesIO(raw)) as image:
        assert image.format == "PNG" and image.width == 760
    headline = [text for text, size in texts if size == 32]
    assert len(headline) == 2 and headline[-1].endswith("全球修复")
    assert summary in "".join(text for text, _ in texts)
    assert texts[-1][0] == "内部阅读"


def test_tall_report_is_not_clipped_at_prototype_canvas_limit(monkeypatch):
    positions = []
    original = ImageDraw.ImageDraw.text
    def capture(draw, xy, text, *args, **kwargs):
        positions.append((xy, text))
        return original(draw, xy, text, *args, **kwargs)
    monkeypatch.setattr(ImageDraw.ImageDraw, "text", capture)
    items = [{"title": f"Item {i}", "summary": "长段落完整保留。" * 16} for i in range(105)]
    with Image.open(BytesIO(render_poster(report(items), {}))) as image:
        assert image.height > 9600
        footer = positions[-1]
        assert footer[1] == "内部阅读"
        assert footer[0][1] < image.height - 14


def test_only_original_first_and_not_flash_is_pasted(monkeypatch):
    pasted = []
    original = Image.Image.paste
    def capture(canvas, picture, box=None, mask=None):
        pasted.append(picture.getpixel((0, 0)))
        return original(canvas, picture, box, mask)
    monkeypatch.setattr(Image.Image, "paste", capture)
    data = report([{"title": "First"}, {"title": "Later"}])
    data["flashes"] = [{"title": "Flash"}]
    pictures = {name: Image.new("RGB", (210, 210), color) for name, color in
                [("First", "red"), ("Later", "green"), ("Flash", "blue")]}
    render_poster(data, pictures)
    assert pasted == [(255, 0, 0)]


def test_fit_png_returns_small_image_unchanged():
    raw = render_poster(report(), {})
    assert fit_png(raw) == raw


def test_fit_png_shrinks_once_then_rejects_if_still_large(monkeypatch):
    buffer = BytesIO()
    Image.effect_noise((200, 200), 100).convert("RGB").save(buffer, format="PNG")
    sizes = []
    resize = Image.Image.resize
    def capture(image, size, *args, **kwargs):
        sizes.append(size)
        return resize(image, size, *args, **kwargs)
    monkeypatch.setattr(Image.Image, "resize", capture)
    with pytest.raises(PosterTooLarge):
        fit_png(buffer.getvalue(), limit=50)
    assert sizes == [(160, 160)]
