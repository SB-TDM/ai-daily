from datetime import date

_WEEKDAYS = ("星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日")


def assign_plates(daily, on=None):
    lead = daily.get("lead")
    if not lead:
        return None
    rows = _rows(daily)
    plates = {
        "报头": {
            "name": "AI 日报",
            "date": on,
            "weekday": _WEEKDAYS[date.fromisoformat(on).weekday()],
            "mark": "内部阅读",
        },
        "头版": {
            "title": lead.get("title") or "",
            "paragraph": _cut(lead.get("leadParagraph") or "", 80),
        },
        "主图位": {"title": lead.get("title") or ""},
        "页脚": "内部阅读",
    }
    source = (lead.get("source") or {}).get("name") or ""
    if source:
        plates["头版"]["source"] = source
    if rows[:3]:
        plates["导读"] = [
            {"label": label, "title": item.get("title") or ""} for label, item in rows[:3]
        ]
    if rows[3:6]:
        plates["底栏"] = [
            {
                "label": label,
                "title": item.get("title") or "",
                "summary": _cut(_first_sentence(item.get("summary") or ""), 40),
            }
            for label, item in rows[3:6]
        ]
    return plates


def _rows(daily):
    lead_title = ((daily.get("lead") or {}).get("title") or "").strip()
    rows = []
    for section in daily.get("sections") or []:
        label = section.get("label") or ""
        for item in section.get("items") or []:
            if (item.get("title") or "").strip() == lead_title:
                continue
            rows.append((label, item))
    for item in daily.get("flashes") or []:
        if (item.get("title") or "").strip() == lead_title:
            continue
        rows.append(("快讯", item))
    return rows


def _cut(text, limit):
    if len(text) <= limit:
        return text
    return text[:limit] + "…"


def _first_sentence(text):
    for mark in ("。", "！", "？"):
        if mark in text:
            return text[: text.index(mark) + 1]
    return text
