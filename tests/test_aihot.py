from datetime import date
import pytest
from ai_daily.aihot import DailyNotReady, parse_daily

PAYLOAD = {
    "report": {
        "date": "2026-10-21",
        "lead": {"title": "DeepSeek 开源 DeepInfer", "leadParagraph": "同步开源 deepseek-recipe。"},
        "sections": [
            {"label": "模型发布/更新", "items": [{"title": "Mercury 3", "summary": "速度达 1068 tokens/秒。", "source": {"name": "Inception Labs：Blog（网页）"}, "links": {"aihot": "https://aihot.news/items/mercury", "original": "https://example.com/mercury"}}]},
            {"label": "快讯", "items": [{"title": "不该出现", "summary": "快讯。", "source": {"name": "X"}}]},
        ],
        "flashes": [{"title": "也不该出现", "source": {"name": "X"}}],
    }
}

def test_parse_keeps_lead_and_sections_but_drops_flashes_and_urls():
    daily = parse_daily(PAYLOAD, date(2026, 10, 21))
    assert daily.lead_title == "DeepSeek 开源 DeepInfer"
    assert daily.lead_paragraph == "同步开源 deepseek-recipe。"
    assert [section.label for section in daily.sections] == ["模型发布/更新"]
    story = daily.sections[0].stories[0]
    assert story.source_name == "Inception Labs：Blog"
    assert story.page_url == "https://aihot.news/items/mercury"
    assert "http" not in story.source_name
    assert "example.com" not in story.page_url

def test_yesterday_or_missing_report_is_not_ready():
    with pytest.raises(DailyNotReady):
        parse_daily({"report": {"date": "2026-10-20", "lead": {"title": "旧", "leadParagraph": "旧"}}}, date(2026, 10, 21))
    with pytest.raises(DailyNotReady):
        parse_daily({}, date(2026, 10, 21))
