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
    assert "头条" in html
    assert "内部传阅" not in html
    assert "font-size:18px" in html
    assert "http" not in html
    assert "第" not in html
    assert "快讯" not in html
    assert "角色" not in html
