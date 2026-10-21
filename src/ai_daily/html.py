from html import escape
from ai_daily.aihot import Daily

PAPER = "#f4f1ea"
INK = "#1a1a1a"
RULE = "#1a1a1a"
MUTED = "#5c564c"
HAIR = "#d9d3c7"


def _img(src: str, style: str) -> str:
    return f"<img src='{src}' style='{style}'>"


def render_html(daily: Daily, images: dict[str, str] | None = None) -> str:
    images = images or {}
    day = daily.day
    lead_src = ""
    for section in daily.sections:
        for story in section.stories:
            if story.title == daily.lead_title and story.page_url in images:
                lead_src = images[story.page_url]
                break
        if lead_src:
            break
    blocks = [
        "<!DOCTYPE html><html><head><meta charset='utf-8'></head>",
        f"<body style='margin:0;background:{PAPER};color:{INK};font-family:Microsoft YaHei,sans-serif;font-size:18px'>",
        "<article style='width:720px;padding:28px 24px 36px'>",
        "<header style='text-align:center'>",
        f"<div style='font-family:SimSun,serif;font-size:42px;letter-spacing:.2em;font-weight:700;line-height:1.1'>AI 日报</div>",
        f"<div style='border-top:4px solid {RULE};border-bottom:1px solid {RULE};margin:10px 0 0;padding:6px 0;font-size:16px'>{day.year}年{day.month}月{day.day}日</div>",
        "</header>",
        f"<h1 style='font-family:SimSun,serif;font-size:32px;line-height:1.25;margin:16px 0 8px'>{escape(daily.lead_title)}</h1>",
        f"<p style='font-size:18px;line-height:1.55;margin:0 0 12px'>{escape(daily.lead_paragraph)}</p>",
    ]
    if lead_src:
        blocks.append(_img(lead_src, "width:100%;height:auto;display:block;margin:0 0 8px"))
    for section in daily.sections:
        blocks.append(
            f"<h2 style='text-align:center;font-size:15px;letter-spacing:.12em;font-weight:700;border-top:1px solid {RULE};border-bottom:1px solid {RULE};padding:6px 0;margin:18px 0 4px'>{escape(section.label)}</h2>"
        )
        for story in section.stories:
            thumb = ""
            if story.title != daily.lead_title and story.page_url in images:
                thumb = _img(images[story.page_url], f"float:left;width:96px;height:72px;object-fit:cover;margin:4px 12px 8px 0;border:1px solid {HAIR}")
            blocks.append(
                f"<div style='overflow:hidden;border-bottom:1px solid {HAIR};padding:10px 0'>"
                f"{thumb}"
                f"<h3 style='font-family:SimSun,serif;font-size:22px;line-height:1.3;margin:0 0 6px'>{escape(story.title)}</h3>"
                f"<p style='font-size:18px;line-height:1.55;margin:0'>{escape(story.summary)}</p>"
                f"<p style='font-size:14px;color:{MUTED};margin:6px 0 0'>{escape(story.source_name)}</p>"
                "</div>"
            )
    blocks.append("</article></body></html>")
    return "".join(blocks)
