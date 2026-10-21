from html import escape
from ai_daily.aihot import Daily

PAPER = "#fbf6f8"
INK = "#2b2140"
ACCENT = "#e23e78"


def _sticker(text: str) -> str:
    return (
        f"<span style='display:inline-block;background:{ACCENT};color:#fff;"
        f"font-size:15px;padding:3px 8px;border-radius:999px'>{escape(text)}</span>"
    )


def render_html(daily: Daily) -> str:
    day = daily.day
    blocks = [
        "<!DOCTYPE html><html><head><meta charset='utf-8'></head>",
        f"<body style='margin:0;background:{PAPER};color:{INK};font-family:Microsoft YaHei,sans-serif;font-size:18px'>",
        "<article style='width:720px;padding:28px 24px 32px'>",
        "<header style='text-align:center'>",
        f"<div style='font-family:Georgia,serif;font-size:40px;letter-spacing:.14em;line-height:1'>AI 日报</div>",
        f"<div style='font-size:16px;margin-top:8px'>{day.year}年{day.month}月{day.day}日</div>",
        "</header>",
        f"<div style='height:2px;background:{INK};margin:12px 0'></div>",
        _sticker("头条"),
        f"<h2 style='font-family:Georgia,serif;font-size:32px;line-height:1.2;margin:10px 0 8px'>{escape(daily.lead_title)}</h2>",
        f"<p style='font-size:18px;line-height:1.55;margin:0 0 18px'>{escape(daily.lead_paragraph)}</p>",
    ]
    for section in daily.sections:
        blocks.append(_sticker(section.label))
        for story in section.stories:
            blocks.append(
                f"<h3 style='font-family:Georgia,serif;font-size:22px;line-height:1.3;margin:12px 0 6px'>{escape(story.title)}</h3>"
                f"<p style='font-size:18px;line-height:1.55;margin:0'>{escape(story.summary)}</p>"
                f"<p style='font-size:15px;margin:6px 0 16px'>{escape(story.source_name)}</p>"
            )
    blocks.append("</article></body></html>")
    return "".join(blocks)
