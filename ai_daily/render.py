"""Approved long newspaper rendering without network access or output-file writes."""
import os
from datetime import date
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .report import first_items, item_key, lead_picture, section_rows, source_name

PAPER, INK, MUTED, RULE, HAIRLINE = "#f4f1ea", "#1a1a1a", "#5c564c", "#565047", "#d9d3c7"
W, MARGIN = 760, 28
SERIF_NAME = "NotoSerifSC-VF.ttf"
SANS_NAME = "SourceHanSansCN-Regular.otf"
SANS_MED_NAME = "SourceHanSansCN-Medium.otf"
MAX_BYTES = 2_097_152


def font_path(name):
    root = os.environ.get("AI_DAILY_FONT_DIR")
    base = Path(root) if root else Path(r"C:\Windows\Fonts")
    path = base / name
    if root and "/" in root:
        return path.as_posix()
    return str(path)


class PosterTooLarge(ValueError):
    pass


def face(path, size):
    return ImageFont.truetype(path, size)


def wrap(text, font, width):
    lines, line, i = [], "", 0
    text = text or ""
    while i < len(text):
        ch = text[i]
        if ch == "\n":
            lines.append(line.rstrip())
            line, i = "", i + 1
            continue
        if ch.isascii() and (ch.isalnum() or ch in "-_/.'"):
            j = i + 1
            while j < len(text) and text[j].isascii() and (text[j].isalnum() or text[j] in "-_/.'"):
                j += 1
            word = text[i:j]
            if font.getlength(line + word) <= width:
                line, i = line + word, j
                continue
            if line.strip():
                lines.append(line.rstrip())
                line = ""
            if font.getlength(word) <= width:
                line, i = word, j
                continue
        trial = line + ch
        if font.getlength(trial) <= width:
            line = trial
        else:
            if line.strip():
                lines.append(line.rstrip())
            line = "" if ch.isspace() else ch
        i += 1
    if line.strip():
        lines.append(line.rstrip())
    return lines or [""]


class _Canvas:
    """Record layout, then allocate exactly the measured page height."""
    def __init__(self):
        self.operations = []

    def text(self, xy, text, **kwargs):
        self.operations.append(("text", (xy, text), kwargs))

    def line(self, xy, **kwargs):
        self.operations.append(("line", (xy,), kwargs))

    def paste(self, picture, xy):
        self.operations.append(("paste", (picture, xy), {}))

    def png(self, height):
        image = Image.new("RGB", (W, int(height)), PAPER)
        draw = ImageDraw.Draw(image)
        for operation, args, kwargs in self.operations:
            if operation == "paste":
                image.paste(*args, **kwargs)
            else:
                getattr(draw, operation)(*args, **kwargs)
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()


def paint_lines(draw, lines, x, y, font, fill, step):
    for line in lines:
        draw.text((x, y), line, fill=fill, font=font)
        y += step
    return y


def _story(canvas, item, x, y, width, picture, title_font, body, small, *, beside):
    y = paint_lines(canvas, wrap(item.get("title") or "", title_font, width), x, y, title_font, INK, 30) + 4
    if picture and not beside:
        canvas.paste(picture, (int(x), int(y)))
        y += picture.height + 8
    text_width = width - picture.width - 14 if picture and beside else width
    bottom = y
    if item.get("summary"):
        bottom = paint_lines(canvas, wrap(item["summary"], body, text_width), x, bottom, body, INK, 26)
    source = source_name(item)
    if source:
        bottom = paint_lines(canvas, wrap(source, small, text_width), x, bottom + 4, small, MUTED, 20)
    if picture and beside:
        canvas.paste(picture, (int(x + width - picture.width), int(y)))
        bottom = max(bottom, y + picture.height)
    return bottom + 14


def render_poster(report, pictures):
    allowed = {item_key(item) for item in first_items(report)}
    fitted = {}
    for key, picture in pictures.items():
        if key in allowed:
            picture = picture.convert("RGB").copy()
            picture.thumbnail((210, 210))
            fitted[key] = picture
    pictures = fitted
    lead = report["lead"]
    picture, lead_item = lead_picture(report, pictures)
    title_font, name_font = face(font_path(SERIF_NAME), 32), face(font_path(SERIF_NAME), 42)
    body, small = face(font_path(SANS_NAME), 18), face(font_path(SANS_NAME), 14)
    section_font, story_title = face(font_path(SANS_MED_NAME), 17), face(font_path(SERIF_NAME), 22)
    canvas = _Canvas()
    y = 28
    name = "AI 日报"
    canvas.text(((W - name_font.getlength(name)) / 2, y), name, fill=INK, font=name_font)
    y += 58
    day = date.fromisoformat(report["date"])
    dateline = f"{day.year}年{day.month}月{day.day}日"
    canvas.line((MARGIN, y, W - MARGIN, y), fill=INK, width=3)
    y += 8
    canvas.text(((W - small.getlength(dateline)) / 2, y), dateline, fill=INK, font=small)
    y += 24
    canvas.line((MARGIN, y, W - MARGIN, y), fill=INK, width=1)
    y += 20
    y = paint_lines(canvas, wrap(lead["title"], title_font, W - MARGIN * 2), MARGIN, y, title_font, INK, 44) + 8
    text_width = W - MARGIN * 2 - (picture.width + 18 if picture else 0)
    copy_y = paint_lines(canvas, wrap(lead["leadParagraph"], body, text_width), MARGIN, y, body, INK, 28)
    if lead_item and source_name(lead_item):
        copy_y = paint_lines(canvas, wrap(source_name(lead_item), small, text_width), MARGIN, copy_y + 4, small, MUTED, 20)
    if picture:
        canvas.paste(picture, (W - MARGIN - picture.width, y))
        y = max(copy_y, y + picture.height) + 22
    else:
        y = copy_y + 22
    for label, items, flashes in section_rows(report):
        canvas.text((MARGIN, y), label, fill=INK, font=section_font)
        rule_x = MARGIN + section_font.getlength(label) + 12
        canvas.line((rule_x, y + 12, W - MARGIN, y + 12), fill=RULE, width=1)
        y += 32
        if len(items) == 1:
            y = _story(canvas, items[0], MARGIN, y, W - MARGIN * 2,
                       None if flashes else pictures.get(item_key(items[0])),
                       story_title, body, small, beside=True) + 8
            continue
        column_width = (W - MARGIN * 2 - 24) / 2
        columns = [items[0::2], items[1::2]]
        bottoms = []
        for index, column in enumerate(columns):
            x = MARGIN + index * (column_width + 24)
            bottom = y
            for item in column:
                art = None if flashes else pictures.get(item_key(item))
                bottom = _story(canvas, item, x, bottom, column_width, art, story_title, small, small, beside=False)
                canvas.line((x, bottom - 6, x + column_width, bottom - 6), fill=HAIRLINE, width=1)
            bottoms.append(bottom)
        y = max(bottoms) + 8
    y += 8
    canvas.line((MARGIN, y, W - MARGIN, y), fill=INK, width=1)
    y += 12
    foot = "内部阅读"
    canvas.text(((W - small.getlength(foot)) / 2, y), foot, fill=MUTED, font=small)
    return canvas.png(y + 36)


def fit_png(raw, limit=MAX_BYTES):
    if len(raw) <= limit:
        return raw
    with Image.open(BytesIO(raw)) as image:
        image.load()
        image = image.resize((max(1, int(image.width * 0.8)), max(1, int(image.height * 0.8))), Image.Resampling.LANCZOS)
        buffer = BytesIO()
        image.save(buffer, format="PNG")
    resized = buffer.getvalue()
    if len(resized) > limit:
        raise PosterTooLarge("PNG still exceeds the size limit")
    return resized
