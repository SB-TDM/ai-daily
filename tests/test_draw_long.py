import base64
import json
from io import BytesIO

from PIL import Image, ImageDraw

from preview import draw_long as d


def test_lead_headline_fits_two_lines_without_an_orphan(monkeypatch, tmp_path):
    title = "OpenAI 披露 Patch the Planet 计划借助 GPT-5.6 Sol 发现 PHP 关键漏洞并协调全球修复"
    report = {
        "date": "2026-10-22",
        "lead": {"title": title, "leadParagraph": "正文。"},
        "sections": [],
        "flashes": [],
    }
    (tmp_path / "data" / "posters").mkdir(parents=True)
    monkeypatch.setattr(d, "ROOT", tmp_path)
    monkeypatch.setattr(d, "fetch_report", lambda: report)
    monkeypatch.setattr(d, "beijing_today", lambda: "2026-10-22")
    painted = []
    original = ImageDraw.ImageDraw.text

    def record(draw, xy, text, *args, **kwargs):
        font = kwargs.get("font")
        if font and 30 <= font.size <= 34:
            painted.append((text, font.getlength(text)))
        return original(draw, xy, text, *args, **kwargs)

    monkeypatch.setattr(ImageDraw.ImageDraw, "text", record)
    d.main()

    assert len(painted) == 2
    assert painted[-1][0].endswith("全球修复")
    assert all(width <= 704 for _, width in painted)
    assert "".join(text for text, _ in painted).replace(" ", "") == title.replace(" ", "")


def test_repair_scene_does_not_send_article_brands_or_statistics(monkeypatch, tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    (data / "image.json").write_text(
        json.dumps({"model": "test-model", "base_url": "https://example.test/v1"}),
        encoding="utf-8",
    )
    (data / "image-secret.json").write_text(
        json.dumps({"key": "test-key"}), encoding="utf-8"
    )
    monkeypatch.setattr(d, "ROOT", tmp_path)
    output = BytesIO()
    Image.new("RGB", (4, 4), "white").save(output, format="PNG")
    raw = output.getvalue()
    captured = []

    def fake_urlopen(request, timeout):
        captured.append(json.loads(request.data))
        return BytesIO(json.dumps({"data": [{"b64_json": base64.b64encode(raw).decode()}]}).encode())

    monkeypatch.setattr(d.urllib.request, "urlopen", fake_urlopen)
    scene = "A mechanical arm passes plain clay blocks through a narrow inspection gate."
    result = d.illustrate("ExampleAI reaches 42%", "The report claims 99% growth.", scene=scene)

    assert result == raw
    assert len(captured) == 1
    prompt = captured[0]["prompt"]
    assert scene in prompt
    assert "ExampleAI" not in prompt
    assert "42%" not in prompt and "99%" not in prompt
