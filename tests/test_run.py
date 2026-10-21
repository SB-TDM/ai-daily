from datetime import date
from pathlib import Path
from ai_daily.run import run_once
from ai_daily.state import already_sent, mark_sent

DAY = date(2026, 10, 21)
PAYLOAD = {
    "report": {
        "date": "2026-10-21",
        "lead": {"title": "DeepSeek 开源 DeepInfer", "leadParagraph": "同步开源。"},
        "sections": [{"label": "论文研究", "items": [{"title": "一篇论文", "summary": "一句。", "source": {"name": "HF"}}]}],
        "flashes": [{"title": "快讯不该进图"}],
    }
}

def test_already_sent_does_not_shoot(tmp_path: Path):
    mark_sent(tmp_path / "sent.json", DAY)
    assert run_once(DAY, tmp_path / "sent.json", PAYLOAD, None, lambda html: b"\x89PNG", lambda json: {"errcode": 0}) == "already-sent"

def test_not_ready_does_not_mark_sent(tmp_path: Path):
    path = tmp_path / "sent.json"
    result = run_once(DAY, path, {}, RuntimeError("404"), lambda html: b"\x89PNG", lambda json: {"errcode": 0})
    assert result == "not-ready"
    assert already_sent(path, DAY) is False

def test_oversized_image_does_not_post_or_mark_sent(tmp_path: Path):
    path = tmp_path / "sent.json"
    posts = []
    result = run_once(DAY, path, PAYLOAD, None, lambda html: b"\x89PNG" + b"x" * 3_000_000, lambda json: posts.append(json))
    assert result == "delivery-failed"
    assert posts == []
    assert already_sent(path, DAY) is False

def test_webhook_failure_does_not_mark_sent(tmp_path: Path):
    path = tmp_path / "sent.json"
    result = run_once(DAY, path, PAYLOAD, None, lambda html: b"\x89PNG-ok", lambda json: {"errcode": 1, "errmsg": "no"})
    assert result == "delivery-failed"
    assert already_sent(path, DAY) is False

def test_success_posts_one_image_and_marks_sent(tmp_path: Path):
    path = tmp_path / "sent.json"
    seen = []
    def shoot(html):
        seen.append(html)
        return b"\x89PNG-ok"
    posts = []
    result = run_once(DAY, path, PAYLOAD, None, shoot, lambda json: posts.append(json) or {"errcode": 0})
    assert result == "sent"
    assert "快讯不该进图" not in seen[0]
    assert posts[0]["msgtype"] == "image"
    assert already_sent(path, DAY) is True
