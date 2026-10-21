from datetime import date
from ai_daily.aihot import Daily, Section, Story
from ai_daily.html import render_html

def test_page_has_masthead_lead_section_and_footer_without_url_or_issue():
    daily = Daily(
        date(2026, 10, 21),
        "DeepSeek <开源>",
        "同步开源。",
        (Section("模型发布/更新", (Story("Mercury 3", "速度达 1068 tokens/秒。", "Inception Labs：Blog"),)),),
    )
    html = render_html(daily)
    assert "AI 日报" in html
    assert "2026年10月21日" in html
    assert "DeepSeek &lt;开源&gt;" in html
    assert "同步开源。" in html
    assert "模型发布/更新" in html
    assert "Mercury 3" in html
    assert "速度达 1068 tokens/秒。" in html
    assert "Inception Labs：Blog" in html
    assert "内部传阅" not in html
    assert "头条" not in html
    assert "border-radius:999px" not in html
    assert "http" not in html
    assert "第" not in html
    assert "快讯" not in html
    assert "角色" not in html
    assert "<img" not in html


def test_lead_photo_is_not_repeated_and_other_stories_keep_a_thumb():
    lead = Story("DeepSeek 开源", "同步开源。", "DeepSeek", "https://aihot.news/items/lead")
    other = Story("Mercury 3", "很快。", "Inception", "https://aihot.news/items/mercury")
    daily = Daily(date(2026, 10, 21), "DeepSeek 开源", "同步开源。", (Section("产品发布/更新", (lead, other)),))
    images = {
        lead.page_url: "data:image/jpeg;base64,LEAD",
        other.page_url: "data:image/jpeg;base64,THUMB",
    }
    html = render_html(daily, images)
    assert html.count("data:image/jpeg;base64,LEAD") == 1
    assert html.count("data:image/jpeg;base64,THUMB") == 1
    assert "https://aihot.news/items/" not in html
    assert "width:96px" not in html
    assert "float:left" not in html
    assert html.count("height:200px") == 2
