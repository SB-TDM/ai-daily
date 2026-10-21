from html import escape
from ai_daily.aihot import Daily

def render_html(daily: Daily) -> str:
    day = daily.day
    blocks = [
        "<!DOCTYPE html><html><head><meta charset='utf-8'></head>",
        "<body style='margin:0;background:#fbf6f8;color:#2b2140;font-family:Microsoft YaHei,sans-serif'>",
        "<article style='width:720px;padding:24px'>",
        f"<h1>AI 日报</h1><p>{day.year}年{day.month}月{day.day}日</p>",
        f"<h2>{escape(daily.lead_title)}</h2><p>{escape(daily.lead_paragraph)}</p>",
    ]
    for section in daily.sections:
        blocks.append(f"<h3 style='color:#e23e78'>{escape(section.label)}</h3>")
        for story in section.stories:
            blocks.append(f"<h4>{escape(story.title)}</h4><p>{escape(story.summary)}</p><p>{escape(story.source_name)}</p>")
    blocks.append("<footer>内部传阅</footer></article></body></html>")
    return "".join(blocks)
