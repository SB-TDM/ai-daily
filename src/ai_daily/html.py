from html import escape
from ai_daily.aihot import Daily

PAPER = "#f4f1ea"
INK = "#1a1a1a"
RULE = "#1a1a1a"
MUTED = "#5c564c"
HAIR = "#d9d3c7"
SPAN = "grid-column:1 / -1"
FRAME = "width:100%;height:auto;display:block;margin:6px 0 0"


def _img(src: str, extra: str = "") -> str:
    style = FRAME if not extra else f"{FRAME};{extra}"
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
        "<article style='box-sizing:border-box;display:grid;grid-template-columns:1fr 1fr;width:760px;column-gap:16px;row-gap:4px;padding:18px 16px 24px'>",
        f"<header style='{SPAN};text-align:center'>",
        f"<div style='font-family:SimSun,serif;font-size:42px;letter-spacing:.2em;font-weight:700;line-height:1.1'>AI 日报</div>",
        f"<div style='border-top:4px solid {RULE};border-bottom:1px solid {RULE};margin:8px 0 0;padding:4px 0;font-size:16px'>{day.year}年{day.month}月{day.day}日</div>",
        "</header>",
        f"<div style='{SPAN}'>",
        _img(lead_src, "float:right;width:46%;margin:4px 0 8px 12px") if lead_src else "",
        f"<h1 style='font-family:SimSun,serif;font-size:32px;line-height:1.25;margin:10px 0 6px'>{escape(daily.lead_title)}</h1>",
        f"<p style='font-size:18px;line-height:1.55;margin:0'>{escape(daily.lead_paragraph)}</p>",
        "</div>",
    ]
    for section in daily.sections:
        stories = tuple(story for story in section.stories if story.title != daily.lead_title)
        if not stories:
            continue
        blocks.append(
            f"<h2 style='{SPAN};text-align:center;font-size:15px;letter-spacing:.12em;font-weight:700;border-top:1px solid {RULE};border-bottom:1px solid {RULE};padding:4px 0;margin:8px 0 0'>{escape(section.label)}</h2>"
        )
        for story in stories:
            image = ""
            span = ""
            if story.page_url in images:
                image = _img(images[story.page_url], "float:right;width:42%;margin:0 0 6px 12px")
                span = SPAN + ";"
            blocks.append(
                f"<div style='{span}min-width:0;padding:6px 0 8px;border-bottom:1px solid {HAIR}'>"
                + image
                + f"<h3 style='font-family:SimSun,serif;font-size:22px;line-height:1.3;margin:0'>{escape(story.title)}</h3>"
                + f"<p style='font-size:18px;line-height:1.55;margin:6px 0 0'>{escape(story.summary)}</p>"
                + f"<p style='font-size:14px;color:{MUTED};margin:4px 0 0'>{escape(story.source_name)}</p>"
                + "</div>"
            )
    blocks.append("</article></body></html>")
    return "".join(blocks)
